"""tien_trinh.py — bể tiến trình con có GIỚI HẠN THỜI GIAN CỨNG cho lõi CPA² (clingo, OCR không tự dừng được).

Mỗi tiến trình con nạp lõi MỘT lần (khởi động chậm vài giây), rồi nhận lệnh `(tên phương thức, tham số)` qua ống. Quá `timeout` → giết
tiến trình và dựng tiến trình mới (yêu cầu sau vẫn được phục vụ). Không có tiến trình rảnh trong `cho_hang_doi` giây → QuaTai.
Dùng 'spawn' (không 'fork'): tiến trình cha có nhiều luồng, fork từ đó không an toàn.

  HetGio      quá thời gian → API trả 504 het_gio
  QuaTai      không có tiến trình rảnh → 503 qua_tai
  LoiTienTrinh  tiến trình con chết hoặc ném ngoại lệ → 500 loi_he_thong. Chỉ mang TÊN loại ngoại lệ (thông điệp có thể chứa nội dung hồ sơ).
"""
import importlib
import multiprocessing
import os
import queue
import threading
import time


class HetGio(Exception):
    pass


class QuaTai(Exception):
    pass


class LoiTienTrinh(Exception):
    pass


def _vong_lap(conn, khoi_tao, tham_so):
    os.environ.setdefault("OMP_THREAD_LIMIT", "1")          # Tesseract dùng 1 luồng: song song hoá bằng nhiều tiến trình, không tranh CPU
    mod, ham = khoi_tao.split(":")
    dv = getattr(importlib.import_module(mod), ham)(**tham_so)
    conn.send(("san_sang", None))
    while True:
        try:
            ten, args = conn.recv()
        except EOFError:
            return
        try:
            if ten.startswith("_"):
                raise PermissionError("phương thức riêng")
            conn.send(("ok", getattr(dv, ten)(*args)))
        except BaseException as e:  # noqa: BLE001 — gửi TÊN loại, không gửi thông điệp
            conn.send(("loi", type(e).__name__))


class _Worker:
    def __init__(self, ctx, khoi_tao, tham_so):
        self.ctx, self.khoi_tao, self.tham_so = ctx, khoi_tao, tham_so
        self.proc = self.conn = None
        self.khoi_dong()

    def khoi_dong(self):
        cha, con = self.ctx.Pipe()
        self.proc = self.ctx.Process(target=_vong_lap, args=(con, self.khoi_tao, self.tham_so), daemon=True)
        self.proc.start()
        con.close()
        self.conn = cha

    def san_sang(self, timeout):
        if not self.conn.poll(timeout):
            raise HetGio("tiến trình con không khởi động kịp")
        self.conn.recv()

    def giet(self):
        for f in (lambda: self.proc.kill(), lambda: self.proc.join(5), lambda: self.conn.close()):
            try:
                f()
            except Exception:  # noqa: BLE001
                pass


class NhomTienTrinh:
    def __init__(self, khoi_tao, tham_so, so_worker, cho_hang_doi=5.0, khoi_dong_toi_da=120.0):
        self.khoi_tao, self.tham_so, self.n, self.cho = khoi_tao, tham_so, so_worker, cho_hang_doi
        self.khoi_dong_toi_da = khoi_dong_toi_da
        self.ranh = queue.Queue()
        self.ds = []
        self._khoa = threading.Lock()
        self.da_khoi_dong = False

    def _bat_dau(self):
        with self._khoa:
            if self.da_khoi_dong:
                return
            ctx = multiprocessing.get_context("spawn")
            self.ds = [_Worker(ctx, self.khoi_tao, self.tham_so) for _ in range(self.n)]
            for w in self.ds:
                w.san_sang(self.khoi_dong_toi_da)
                self.ranh.put(w)
            self.da_khoi_dong = True

    def _hoi_sinh(self, w):
        """Giết tiến trình hỏng và dựng tiến trình mới Ở LUỒNG NỀN (yêu cầu lỗi trả về ngay); rảnh lại khi sẵn sàng."""
        def lam():
            w.giet()
            try:
                w.khoi_dong()
                w.san_sang(self.khoi_dong_toi_da)
                self.ranh.put(w)
            except Exception:  # noqa: BLE001 — không dựng được thì bể nhỏ đi; sẽ qua_tai thay vì treo
                pass
        threading.Thread(target=lam, daemon=True).start()

    def goi(self, ten, *args, timeout):
        self._bat_dau()
        try:
            w = self.ranh.get(timeout=self.cho)
        except queue.Empty:
            raise QuaTai() from None
        hong = False
        try:
            w.conn.send((ten, args))
            if not w.conn.poll(timeout):
                hong = True
                raise HetGio()
            kq = w.conn.recv()
        except HetGio:
            raise
        except (EOFError, BrokenPipeError, ConnectionError, OSError):
            hong = True
            raise LoiTienTrinh("tiến trình con chết") from None
        finally:
            if hong:
                self._hoi_sinh(w)
            else:
                self.ranh.put(w)
        if kq[0] != "ok":
            raise LoiTienTrinh(kq[1])              # ngoại lệ Python trong tiến trình con: tiến trình vẫn dùng tiếp được
        return kq[1]

    def cho_san_sang(self, timeout=10.0):
        """Chờ mọi tiến trình rảnh trở lại (sau hết giờ / chết). Dùng trong test và khi tắt máy."""
        han = time.time() + timeout
        while time.time() < han:
            if self.da_khoi_dong and self.ranh.qsize() == self.n:
                return True
            time.sleep(0.05)
        return False

    def dong(self):
        for w in self.ds:
            w.giet()
        self.ds, self.da_khoi_dong = [], False
        self.ranh = queue.Queue()


class TrongTienTrinh:
    """Chế độ so_worker = 0: gọi thẳng trong tiến trình (phát triển, test, mock). KHÔNG có giới hạn thời gian."""

    def __init__(self, khoi_tao, tham_so):
        mod, ham = khoi_tao.split(":")
        self.dv = getattr(importlib.import_module(mod), ham)(**tham_so)

    def goi(self, ten, *args, timeout):
        try:
            return getattr(self.dv, ten)(*args)
        except Exception as e:  # noqa: BLE001
            raise LoiTienTrinh(type(e).__name__) from None

    def dong(self):
        pass
