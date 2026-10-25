"""tien_trinh.py — bể tiến trình con có GIỚI HẠN THỜI GIAN CỨNG cho lõi CPA² (clingo, OCR không tự dừng được).

Mỗi tiến trình con nạp lõi MỘT lần (khởi động chậm vài giây), rồi nhận lệnh `(tên phương thức, tham số)` qua ống. Quá `timeout` → giết
CẢ NHÓM tiến trình (tiến trình con tự thành trưởng nhóm bằng setsid, nên tesseract do nó sinh ra cũng bị giết, không mồ côi) và dựng
tiến trình mới (yêu cầu sau vẫn được phục vụ). Không có tiến trình rảnh trong `cho_hang_doi` giây → QuaTai.
Dùng 'spawn' (không 'fork'): tiến trình cha có nhiều luồng, fork từ đó không an toàn.

Độ bền (review bảo mật vòng 2):
  • khởi động hỏng → giết hết tiến trình đã tạo, bể về trạng thái "chưa khởi động" (lần gọi sau thử lại), không để mồ côi / cộng dồn
  • tiến trình RẢNH chết (OOM killer…) → phát hiện lúc lấy ra, thay thế rồi lấy cái khác, yêu cầu không bị lỗi
  • dựng lại thất bại → thử lại có lùi bước; vẫn hỏng thì bỏ khỏi bể; bể rỗng hoặc lần khởi động gần nhất hỏng → `tinh_trang()` báo để /health trả 503
  • khoá khởi động có hạn chờ (qua_tai) và /health đọc trạng thái không khoá: khởi động chậm/treo không làm cả API (kể cả /health) đứng
  • mỗi tiến trình con bị giới hạn bộ nhớ ảo (RLIMIT_AS): cấp phát quá mức → MemoryError (500) thay vì kéo cả container bị OOM-kill
  • khoá API không được chép sang môi trường tiến trình con

  HetGio      quá thời gian → API trả 504 het_gio
  QuaTai      không có tiến trình rảnh → 503 qua_tai
  LoiTienTrinh  tiến trình con chết hoặc ném ngoại lệ → 500 loi_he_thong. Chỉ mang TÊN loại ngoại lệ (thông điệp có thể chứa nội dung hồ sơ).
"""
import importlib
import logging
import multiprocessing
import os
import queue
import signal
import threading
import time

log = logging.getLogger("cpa2_api")
_KHOA_MOI_TRUONG = threading.Lock()
BIEN_KHONG_CHEP_SANG_CON = ("CPA2_API_KEY",)
LUI_BUOC_HOI_SINH = (0.0, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0)          # giây chờ trước mỗi lần thử dựng lại (tổng ~31s: qua cơn thiếu tài nguyên thoáng qua)


class HetGio(Exception):
    pass


class QuaTai(Exception):
    pass


class LoiTienTrinh(Exception):
    pass


def _gioi_han_ram(ram_mb):
    """RLIMIT_AS (bộ nhớ ảo). Chỉ có trên Unix; lỗi/không hỗ trợ thì bỏ qua (nền tảng phát triển)."""
    if not ram_mb:
        return
    try:
        import resource
        b = int(ram_mb) * 1024 * 1024
        _, cung = resource.getrlimit(resource.RLIMIT_AS)
        resource.setrlimit(resource.RLIMIT_AS, (b if cung in (-1, resource.RLIM_INFINITY) else min(b, cung), cung))
    except (ImportError, ValueError, OSError):
        pass


def _vong_lap(conn, khoi_tao, tham_so, ram_mb=0):
    try:
        os.setsid()                                          # trưởng nhóm tiến trình: giết cả nhóm sẽ diệt cả tesseract cháu
    except (AttributeError, OSError):
        pass
    _gioi_han_ram(ram_mb)
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
    def __init__(self, ctx, khoi_tao, tham_so, ram_mb=0):
        self.ctx, self.khoi_tao, self.tham_so, self.ram_mb = ctx, khoi_tao, tham_so, ram_mb
        self.proc = self.conn = None
        self._pid_nhom = None
        self.khoi_dong()

    def khoi_dong(self):
        cha, con = self.ctx.Pipe()
        self.proc = self.ctx.Process(target=_vong_lap, args=(con, self.khoi_tao, self.tham_so, self.ram_mb), daemon=True)
        # 'spawn' kế thừa môi trường tại thời điểm start → tạm bỏ khoá khỏi os.environ (tiến trình con không cần và không được thấy nó)
        with _KHOA_MOI_TRUONG:
            giu = {k: os.environ.pop(k) for k in BIEN_KHONG_CHEP_SANG_CON if k in os.environ}
            try:
                self.proc.start()
            finally:
                os.environ.update(giu)
        self._pid_nhom = self.proc.pid
        con.close()
        self.conn = cha

    def san_sang(self, timeout):
        if not self.conn.poll(timeout):
            raise HetGio("tiến trình con không khởi động kịp")
        self.conn.recv()                                     # EOFError nếu tiến trình con chết lúc nạp lõi

    def song(self):
        return self.proc is not None and self.proc.is_alive()

    def giet(self):
        pid, self._pid_nhom = self._pid_nhom, None            # chỉ giết nhóm MỘT lần (pid có thể được hệ điều hành dùng lại sau đó)
        for f in (lambda: pid and hasattr(os, "killpg") and os.killpg(pid, signal.SIGKILL), lambda: self.proc.kill(),
                  lambda: self.proc.join(5), lambda: self.conn.close()):
            try:
                f()
            except Exception:  # noqa: BLE001 — nhóm đã hết / chưa kịp setsid / đã đóng
                pass


class NhomTienTrinh:
    def __init__(self, khoi_tao, tham_so, so_worker, cho_hang_doi=5.0, khoi_dong_toi_da=120.0, ram_mb=0, ten="chinh"):
        self.khoi_tao, self.tham_so, self.n, self.cho = khoi_tao, tham_so, so_worker, cho_hang_doi
        self.khoi_dong_toi_da, self.ram_mb, self.ten = khoi_dong_toi_da, ram_mb, ten
        self.ranh = queue.Queue()
        self.ds = []
        self._khoa = threading.Lock()                         # bảo vệ `ds` (ngắn, không bao giờ giữ lúc chặn)
        self._khoa_khoi_dong = threading.Lock()               # giữ suốt lúc khởi động bể (chậm, tới n×khoi_dong_toi_da) — chỉ người khởi động và người chờ
        self.da_khoi_dong = False
        self.loi_khoi_dong = False                            # lần khởi động gần nhất hỏng (cấu hình sai, lõi không nạp được…)
        self._the_he = 0                                      # tăng mỗi lần dong(): luồng hồi sinh của thế hệ cũ phải bỏ cuộc
        self.da_thu = False                                   # đã từng khởi động (bể rỗng SAU đó mới là hỏng; trước đó chỉ là chưa dùng)

    def _bat_dau(self):
        if self.da_khoi_dong:
            return
        # Người đến trong lúc bể đang khởi động chờ tối đa `cho` giây rồi qua_tai (không giữ luồng xử lý vô hạn, /health không bị chặn)
        if not self._khoa_khoi_dong.acquire(timeout=self.cho):
            raise QuaTai()
        try:
            if self.da_khoi_dong:
                return
            ctx = multiprocessing.get_context("spawn")
            ds = []
            try:
                for _ in range(self.n):
                    ds.append(_Worker(ctx, self.khoi_tao, self.tham_so, self.ram_mb))
                for w in ds:
                    w.san_sang(self.khoi_dong_toi_da)
            except BaseException as e:  # noqa: BLE001 — dọn sạch rồi báo lỗi; không để tiến trình mồ côi
                for w in ds:
                    w.giet()
                self.ds = []
                self.loi_khoi_dong = True
                log.error("bo=%s khoi_dong_hong loai=%s", self.ten, type(e).__name__)
                raise LoiTienTrinh("khởi động bể") from None
            self.ds = ds
            self.ranh = queue.Queue()
            for w in ds:
                self.ranh.put(w)
            self.loi_khoi_dong = False
            self.da_khoi_dong = self.da_thu = True
        finally:
            self._khoa_khoi_dong.release()

    def _bo_khoi_bo(self, w):
        with self._khoa:
            if w in self.ds:
                self.ds.remove(w)
            if not self.ds:
                self.da_khoi_dong = False                     # bể rỗng: lần gọi sau khởi động lại cả bể

    def _hoi_sinh(self, w):
        """Giết tiến trình hỏng và dựng tiến trình mới Ở LUỒNG NỀN (yêu cầu lỗi trả về ngay); rảnh lại khi sẵn sàng."""
        the_he = self._the_he

        def lam():
            w.giet()
            for cho in LUI_BUOC_HOI_SINH:
                time.sleep(cho)
                if self._the_he != the_he:                    # bể đã bị dong() (và có thể khởi động lại): không đụng vào bể mới
                    return
                try:
                    w.khoi_dong()
                    w.san_sang(self.khoi_dong_toi_da)
                except Exception as e:  # noqa: BLE001
                    log.warning("bo=%s hoi_sinh_hong loai=%s", self.ten, type(e).__name__)
                    w.giet()
                    continue
                if self._the_he != the_he:
                    w.giet()
                    return
                self.ranh.put(w)
                return
            log.error("bo=%s hoi_sinh_bo_cuoc", self.ten)
            self._bo_khoi_bo(w)
        threading.Thread(target=lam, daemon=True).start()

    def _lay_worker(self):
        han = time.monotonic() + self.cho
        for _ in range(self.n + 1):                           # mỗi tiến trình rảnh chết chỉ tốn một lần lấy thêm
            try:
                w = self.ranh.get(timeout=max(0.0, han - time.monotonic()))
            except queue.Empty:
                raise QuaTai() from None
            if w.song():
                return w
            self._hoi_sinh(w)
        raise QuaTai()

    def goi(self, ten, *args, timeout):
        self._bat_dau()
        w = self._lay_worker()
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

    def tinh_trang(self):
        """Cho /health. `khoe` sai khi bể ĐÃ từng chạy mà nay không còn tiến trình nào (dựng lại thất bại)."""
        tong = len(self.ds)                                   # đọc không khoá: /health không được chờ bể đang khởi động
        return {"tong": tong, "san_sang": self.ranh.qsize(), "khoe": not (self.loi_khoi_dong or (self.da_thu and tong == 0))}

    def cho_san_sang(self, timeout=10.0):
        """Chờ mọi tiến trình rảnh trở lại (sau hết giờ / chết). Dùng trong test và khi tắt máy."""
        han = time.time() + timeout
        while time.time() < han:
            if self.da_khoi_dong and self.ranh.qsize() == self.n:
                return True
            time.sleep(0.05)
        return False

    def dong(self):
        self._the_he += 1
        for w in list(self.ds):
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

    def tinh_trang(self):
        return {"tong": 0, "san_sang": 0, "khoe": True}

    def dong(self):
        pass
