"""main.py — ứng dụng FastAPI. Chạy:  uvicorn cpa2_api.main:tao_app --factory --host 0.0.0.0 --port 8000

Hợp đồng chung (xem README):
  • MỌI phản hồi có `trang_thai` và `ket_luan`. `ket_luan` chỉ khác null khi trang_thai = ok (TRUE/FALSE/UNKNOWN/DA_HOAN_THANH) hoặc
    ho_so_mau_thuan (MAU_THUAN). Lỗi kỹ thuật không bao giờ thành kết luận học vụ.
  • MỌI phản hồi không-ok có đủ `thong_bao` (chuỗi) và `chi_tiet` (danh sách) — một hình dạng để máy khách TypeScript xử lý bằng một nhánh.
  • HTTP 200 cho kết quả nghiệp vụ (kể cả không hỗ trợ / sai đầu vào), 401 sai khoá, 413 quá lớn, 422 sai dạng yêu cầu, 400 body hỏng,
    500 lỗi hệ thống, 503 chưa cấu hình khoá / quá tải, 504 hết giờ.
  • Xác thực làm TRƯỚC khi đọc body. Log chỉ có thông tin vận hành (endpoint, trạng thái, thời gian, loại lỗi, mã lỗi) — không có hồ sơ,
    câu hỏi, khoá hay nội dung ngoại lệ. Mọi phản hồi: Cache-Control: no-store.
"""
import hmac
import io
import json
import logging
import sys
import time
import uuid
from functools import lru_cache
from typing import Annotated

from anyio import CapacityLimiter, to_thread
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictInt, StringConstraints
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import PHIEN_BAN
from . import ho_so as HS
from .cau_hinh import CauHinh
from .dich_vu import phien_ban_kb
from .tien_trinh import HetGio, LoiTienTrinh, NhomTienTrinh, QuaTai, TrongTienTrinh

log = logging.getLogger("cpa2_api")
KHAI_BAO_KIEU = {"xac_nhan_ky_luat_sach": lambda v: isinstance(v, bool), "che_do_sv_chon_tich_luy": lambda v: isinstance(v, bool),
                 "da_hoc_nam2": lambda v: isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 100,
                 "tc_cong_nhan": lambda v: isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 400,
                 "khong_tinh_tich_luy": lambda v: isinstance(v, list) and len(v) <= 100 and all(isinstance(x, str) and HS._MA.match(x) for x in v),
                 "dtbchk_khai_bao": lambda v: isinstance(v, dict) and len(v) <= 20 and all(isinstance(k, str) and len(k) <= 40 and isinstance(x, (int, float, str))
                                                                                            and not isinstance(x, bool) and len(str(x)) <= 12 for k, x in v.items())}
THONG_BAO_HTTP = {400: "Nội dung yêu cầu không đọc được.", 404: "Không tìm thấy.", 405: "Phương thức không được hỗ trợ.",
                  413: "Nội dung yêu cầu quá lớn.", 422: "Yêu cầu sai dạng."}


def loi_chung(trang_thai, thong_bao, chi_tiet=None, **them):
    """Hình dạng chung của mọi phản hồi không-ok."""
    return {"trang_thai": trang_thai, "ket_luan": None, "thong_bao": thong_bao, "chi_tiet": chi_tiet or [], **them}


def _json(status, obj):
    return JSONResponse(obj, status_code=status)


class XacThucVaTieuDe:
    """Middleware ASGI thuần, ngoài cùng: (1) /v1/* cần X-API-Key — kiểm TRƯỚC khi đọc body; chưa cấu hình khoá → 503 (đóng);
    (2) gắn Cache-Control: no-store + X-Content-Type-Options: nosniff vào MỌI phản hồi (kể cả lỗi)."""

    def __init__(self, app, cfg):
        self.app, self.cfg = app, cfg

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        da_bat_dau = False

        async def gui(m):
            nonlocal da_bat_dau
            if m["type"] == "http.response.start":
                da_bat_dau = True
                hd = [(k, v) for k, v in m.get("headers", []) if k.lower() not in (b"cache-control", b"x-content-type-options")]
                m = {**m, "headers": hd + [(b"cache-control", b"no-store"), (b"x-content-type-options", b"nosniff")]}
            await send(m)
        if scope["path"].startswith("/v1/"):
            loi = None
            if not self.cfg.api_key:
                loi = (503, loi_chung("loi_he_thong", "Dịch vụ chưa cấu hình khoá xác thực."))
            else:
                khoa = next((v for k, v in scope["headers"] if k.lower() == b"x-api-key"), b"")      # tiêu đề ĐẦU TIÊN (không để tiêu đề trùng lách proxy)
                if not khoa or not hmac.compare_digest(khoa, self.cfg.api_key.encode("utf-8")):
                    loi = (401, loi_chung("khong_xac_thuc", "Thiếu hoặc sai khoá."))
            if loi:
                return await _json(*loi)(scope, receive, gui)
        try:
            await self.app(scope, receive, gui)
        except _QuaLon:
            raise
        except Exception as e:  # noqa: BLE001 — ngoại lệ chưa bắt: cùng hình dạng + tiêu đề an toàn (nếu không, Starlette trả text/plain trần)
            ma = uuid.uuid4().hex[:8]
            log.error("path=%s loi_chua_bat=%s ma=%s", scope["path"], type(e).__name__, ma)
            if da_bat_dau:
                raise
            await _json(500, loi_chung("loi_he_thong", "Lỗi nội bộ khi xử lý yêu cầu.", ma_loi=ma))(scope, receive, gui)


class _QuaLon(Exception):
    pass


class GioiHanBody:
    """Middleware ASGI thuần: từ chối body vượt giới hạn (theo Content-Length, và đếm byte thực khi chunked) trước khi parse."""

    def __init__(self, app, cfg):
        self.app, self.cfg = app, cfg

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        gh = self.cfg.max_body_ocr if scope["path"].startswith("/v1/ocr") else self.cfg.max_body_json
        cl = dict(scope["headers"]).get(b"content-length", b"")
        if cl.isdigit() and int(cl) > gh:
            return await self._413(send)
        da = 0
        da_gui = False
        vuot = False

        async def nhan():
            nonlocal da, vuot
            m = await receive()
            if m["type"] == "http.request":
                da += len(m.get("body", b""))
                if da > gh:
                    vuot = True
                    raise _QuaLon()
            return m

        async def gui(m):
            nonlocal da_gui
            if vuot:                       # FastAPI nuốt ngoại lệ đọc body và định trả 400 → thay bằng 413, bỏ phần còn lại
                if not da_gui:
                    da_gui = True
                    await self._413(send)
                return
            if m["type"] == "http.response.start":
                da_gui = True
            await send(m)
        try:
            await self.app(scope, nhan, gui)
        except _QuaLon:
            pass
        if vuot and not da_gui:
            await self._413(send)

    @staticmethod
    async def _413(send):
        body = json.dumps(loi_chung("loi_dau_vao", THONG_BAO_HTTP[413]), ensure_ascii=False, separators=(",", ":")).encode()
        await send({"type": "http.response.start", "status": 413, "headers": [(b"content-type", b"application/json"),
                                                                           (b"content-length", str(len(body)).encode())]})
        await send({"type": "http.response.body", "body": body})


Cau = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class AdviceIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ho_so: dict
    cau_hoi: Cau


class LookupIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    truy_van: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]
    k: StrictInt = Field(default=5, ge=1, le=10)


class RecIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ho_so: dict
    hoc_ky: StrictInt = Field(ge=1, le=3)


def _cau_hinh_log():
    """Dưới uvicorn, logger gốc không có handler → dòng INFO của ứng dụng bị nuốt. Gắn handler riêng (vẫn lan lên root để test bắt được)."""
    if not log.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
        log.addHandler(h)
    log.setLevel(logging.INFO)


def _rong_tu_van(trang_thai, thong_bao, chi_tiet=None, **kw):
    return loi_chung(trang_thai, thong_bao, chi_tiet, **{"claim": None, "loi_giai": thong_bao, "chung_chi": None, "nguon": [], "du_kien_thieu": [],
                                                         "can_bo_sung": [], "mau_thuan": [], "canh_bao": [], "phien_ban_kb": None, **kw})


def _kiem_anh(data, cfg):
    """Kiểm định dạng + khổ ảnh TRƯỚC khi giải nén, rồi giải nén thử (ảnh cắt dở lộ ra ở đây). Trả danh sách lỗi hoặc None."""
    from PIL import Image, UnidentifiedImageError
    tong_px = 0
    for i, b in enumerate(data):
        try:
            with Image.open(io.BytesIO(b)) as im:
                if im.format not in ("PNG", "JPEG"):
                    return [{"duong_dan": f"anh.{i}", "thong_bao": "chỉ nhận ảnh PNG hoặc JPEG"}]
                px = im.size[0] * im.size[1]
                if px > cfg.max_pixels:
                    return [{"duong_dan": f"anh.{i}", "thong_bao": f"ảnh quá lớn (> {cfg.max_pixels} điểm ảnh)"}]
                tong_px += px
                if tong_px > cfg.max_pixels_tong:
                    return [{"duong_dan": "anh", "thong_bao": f"tổng điểm ảnh của yêu cầu vượt {cfg.max_pixels_tong}"}]
                im.load()
        except (UnidentifiedImageError, OSError, ValueError, SyntaxError, Image.DecompressionBombError):
            return [{"duong_dan": f"anh.{i}", "thong_bao": "không đọc được ảnh (hỏng hoặc bị cắt dở)"}]
    return None


def tao_app(cfg=None):
    cfg = cfg or CauHinh()
    _cau_hinh_log()
    app = FastAPI(title="CPA² API", version=PHIEN_BAN, docs_url=None, redoc_url=None, openapi_url=None, redirect_slashes=False)
    app.state.cfg = cfg
    tham_so = {"goc": str(cfg.cpa2_root)}
    if cfg.so_worker > 0:
        app.state.backend = NhomTienTrinh(cfg.khoi_tao_worker, tham_so, cfg.so_worker, cfg.cho_hang_doi, ram_mb=cfg.gioi_han_ram_mb, ten="chinh")
        # OCR nặng (tới timeout_ocr giây, nhiều RAM) có bể RIÊNG: không để vài yêu cầu OCR chiếm hết tiến trình của advice / lookup.
        # Bể này chỉ khởi động khi có yêu cầu OCR đầu tiên.
        app.state.backend_ocr = (NhomTienTrinh(cfg.khoi_tao_worker, tham_so, cfg.so_worker_ocr, cfg.cho_hang_doi, ram_mb=cfg.gioi_han_ram_mb, ten="ocr")
                                 if cfg.so_worker_ocr > 0 else app.state.backend)
    else:
        app.state.backend = app.state.backend_ocr = TrongTienTrinh(cfg.khoi_tao_worker, tham_so)
    app.state.gioi_han_giai_ma = CapacityLimiter(cfg.max_giai_ma_dong_thoi)
    HS.nap_ten_schema(cfg.cpa2_root)              # tên trường schema được nêu nguyên văn trong đường dẫn lỗi (validation 422 cũng dùng)
    kb = phien_ban_kb(str(cfg.cpa2_root))
    app.add_middleware(GioiHanBody, cfg=cfg)
    app.add_middleware(XacThucVaTieuDe, cfg=cfg)           # thêm SAU = ngoài cùng: xác thực chạy trước khi đọc body

    @app.exception_handler(RequestValidationError)
    async def _422(_, e):
        # KHÔNG phản hồi lại giá trị / tên trường do người dùng đặt: chỉ vị trí + loại lỗi
        ct = []
        for er in e.errors()[:20]:
            loc = list(er["loc"])[:-1] if er["type"] == "extra_forbidden" else list(er["loc"])
            ct.append({"duong_dan": ".".join(HS._seg(x) for x in loc), "loai": er["type"]})
        return _json(422, loi_chung("loi_dau_vao", THONG_BAO_HTTP[422], ct))

    @app.exception_handler(StarletteHTTPException)
    async def _http(_, e):
        # 400 (body hỏng / lồng quá sâu / số quá dài), 404, 405… : cùng hình dạng, không phản hồi lại `detail`
        return _json(e.status_code, loi_chung("loi_dau_vao", THONG_BAO_HTTP.get(e.status_code, "Yêu cầu không hợp lệ.")))

    def chay(ten, ten_pt, args, timeout, backend=None):
        t, ma = time.perf_counter(), uuid.uuid4().hex[:8]
        try:
            kq = (backend or app.state.backend).goi(ten_pt, *args, timeout=timeout)
        except HetGio:
            log.warning("endpoint=%s het_gio timeout=%ss", ten, timeout)
            return _json(504, loi_chung("het_gio", "Yêu cầu xử lý quá lâu và đã bị dừng. Hãy thử lại hoặc đơn giản hoá hồ sơ."))
        except QuaTai:
            log.warning("endpoint=%s qua_tai", ten)
            return _json(503, loi_chung("qua_tai", "Hệ thống đang bận. Hãy thử lại sau ít giây."))
        except Exception as e:  # noqa: BLE001 — chỉ ghi LOẠI ngoại lệ (thông điệp có thể chứa nội dung hồ sơ)
            log.error("endpoint=%s loi=%s ma=%s", ten, type(e).__name__ if not isinstance(e, LoiTienTrinh) else f"TienTrinh:{e}", ma)
            return _json(500, loi_chung("loi_he_thong", "Lỗi nội bộ khi xử lý yêu cầu.", ma_loi=ma))
        log.info("endpoint=%s trang_thai=%s ket_luan=%s ms=%d", ten, kq.get("trang_thai"), kq.get("ket_luan"), (time.perf_counter() - t) * 1000)
        return kq

    @app.api_route("/health", methods=["GET", "HEAD"])
    def health():
        # Bể tiến trình đã từng chạy mà nay rỗng (dựng lại thất bại) → 503 để nền tảng khởi động lại container. Chưa dùng lần nào ≠ hỏng.
        bo, bo_ocr = app.state.backend.tinh_trang(), app.state.backend_ocr.tinh_trang()
        khoe = bo["khoe"] and bo_ocr["khoe"]
        kq = {"trang_thai": "ok" if khoe else "loi_he_thong", "ket_luan": None, "dich_vu": "cpa2_api", "phien_ban": PHIEN_BAN, "kb": kb,
              "bo_xu_ly": bo, "bo_xu_ly_ocr": bo_ocr}
        if not khoe:
            kq.update(thong_bao="Bể tiến trình xử lý không còn tiến trình nào.", chi_tiet=[])
        return _json(200 if khoe else 503, kq)

    @app.post("/v1/advice")
    def advice(body: AdviceIn):
        kq = HS.kiem_tra(body.ho_so, cfg)
        if kq.khong_ho_tro:
            return _rong_tu_van("khong_ho_tro_ho_so", kq.khong_ho_tro, phien_ban_kb=kb)
        if kq.loi:
            return _rong_tu_van("loi_dau_vao", "Hồ sơ chưa hợp lệ.", kq.loi, phien_ban_kb=kb)
        return chay("advice", "tu_van", (kq.ho_so, body.cau_hoi, kq.canh_bao), cfg.timeout_advice)

    @app.post("/v1/lookup")
    def lookup(body: LookupIn):
        return chay("lookup", "tra_cuu", (body.truy_van, body.k), cfg.timeout_lookup)

    @app.post("/v1/recommendations")
    def recommendations(body: RecIn):
        kq = HS.kiem_tra(body.ho_so, cfg)
        base = {"hoc_ky": body.hoc_ky, "dang_ky": [], "tong_tc": 0, "can_xac_minh": [], "mau_thuan": [], "canh_bao": [], "phien_ban_kb": kb}
        if kq.khong_ho_tro:
            return loi_chung("khong_ho_tro_ho_so", kq.khong_ho_tro, **base)
        if kq.loi:
            return loi_chung("loi_dau_vao", "Hồ sơ chưa hợp lệ.", kq.loi, **base)
        return chay("recommendations", "de_xuat", (kq.ho_so, body.hoc_ky, kq.canh_bao), cfg.timeout_recs)

    @app.post("/v1/ocr")
    async def ocr(anh: list[UploadFile] = File(...), khai_bao: str | None = Form(None)):
        def loi(chi_tiet, thong_bao="Ảnh hoặc khai báo chưa hợp lệ."):
            return loi_chung("loi_dau_vao", thong_bao, chi_tiet, da_xac_minh=False, ho_so_nhap=None, bao_cao=None, canh_bao=[],
                             so_trang=0, phien_ban_kb=kb)
        if len(anh) > cfg.max_files_ocr:
            return loi([{"duong_dan": "anh", "thong_bao": f"tối đa {cfg.max_files_ocr} ảnh mỗi lần"}])
        data = []
        for i, f in enumerate(anh):
            b = await f.read(cfg.max_bytes_file + 1)
            if len(b) > cfg.max_bytes_file:
                return loi([{"duong_dan": f"anh.{i}", "thong_bao": f"ảnh vượt {cfg.max_bytes_file} byte"}])
            data.append(b)
        # giải mã ảnh là việc nặng CPU + RAM: không chạy trong vòng lặp sự kiện, và không quá `max_giai_ma_dong_thoi` yêu cầu cùng lúc
        # (mỗi yêu cầu tới 60 triệu điểm ảnh ≈ 240 MB trong tiến trình cha, không có RLIMIT_AS)
        loi_anh = await to_thread.run_sync(_kiem_anh, data, cfg, limiter=app.state.gioi_han_giai_ma)
        if loi_anh:
            return loi(loi_anh)
        kb_ = {}
        canh_bao = []
        if khai_bao:
            try:
                j = json.loads(khai_bao)
                if not isinstance(j, dict):
                    raise ValueError
            except (ValueError, RecursionError):
                return loi([{"duong_dan": "khai_bao", "thong_bao": "phải là đối tượng JSON"}])
            sai = [k for k in j if k in KHAI_BAO_KIEU and not KHAI_BAO_KIEU[k](j[k])]
            if sai:
                return loi([{"duong_dan": f"khai_bao.{k}", "thong_bao": "sai kiểu hoặc ngoài khoảng cho phép"} for k in sai])
            kb_ = {k: v for k, v in j.items() if k in KHAI_BAO_KIEU}
            la = sorted(set(j) - set(kb_))
            if la:
                canh_bao.append("khai báo không hỗ trợ bị bỏ qua: " + ", ".join(HS._cat(x, 20) for x in la[:10]))
        kq = await run_in_threadpool(chay, "ocr", "ocr", (data, kb_), cfg.timeout_ocr, app.state.backend_ocr)
        if isinstance(kq, dict):
            kq["canh_bao"] = canh_bao
        return kq

    return app
