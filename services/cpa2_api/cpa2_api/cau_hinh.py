"""cau_hinh.py — cấu hình dịch vụ. Khoá API đọc từ biến môi trường CPA2_API_KEY (không hardcode, không log)."""
import os
import re
from dataclasses import dataclass, field
from pathlib import Path


def _mac_dinh_goc():
    # CPA2_ROOT: thư mục CPA2_KhaoSat (Docker: /app/CPA2_KhaoSat). Mặc định: cạnh thư mục services/ của repo.
    return Path(os.environ.get("CPA2_ROOT") or Path(__file__).resolve().parents[3] / "CPA2_KhaoSat")


def _so_tu_env(ten, mac_dinh, toi_da):
    """Biến môi trường số nguyên 0..toi_da; thiếu/rỗng → mặc định; sai → lỗi rõ ràng LÚC KHỞI ĐỘNG (không nuốt, không đoán)."""
    v = (os.environ.get(ten) or "").strip()
    if not v:
        return mac_dinh
    if not re.fullmatch(r"[0-9]{1,4}", v) or int(v) > toi_da:
        raise ValueError(f"{ten} phải là số nguyên trong [0, {toi_da}]")
    return int(v)


@dataclass
class CauHinh:
    api_key: str | None = field(default_factory=lambda: os.environ.get("CPA2_API_KEY") or None)
    cpa2_root: Path = field(default_factory=_mac_dinh_goc)
    max_body_json: int = 1_000_000          # byte, mọi endpoint JSON
    max_body_ocr: int = 40_000_000          # byte, /v1/ocr (nhiều ảnh)
    max_files_ocr: int = 12                 # số trang ảnh mỗi lần
    max_bytes_file: int = 8_000_000         # byte mỗi ảnh
    max_pixels: int = 25_000_000            # điểm ảnh mỗi ảnh — chặn "bom giải nén"
    max_grades: int = 400                   # số học phần tối đa trong một hồ sơ
    max_giai_ma_dong_thoi: int = 2          # số yêu cầu OCR được giải mã ảnh CÙNG LÚC trong tiến trình cha (RAM)
    max_pixels_tong: int = 60_000_000       # tổng điểm ảnh của MỘT yêu cầu OCR (chặn ngốn RAM khi nhiều ảnh lớn)
    max_mau_thuan: int = 2                  # số bản ghi tự mâu thuẫn tối đa: mỗi bản ghi mở 4 nhánh → solver nổ tổ hợp (x4,5/bản ghi)
    # --- tiến trình + thời gian. so_worker = 0: chạy trong tiến trình (phát triển / test); > 0: bể tiến trình con, giết được khi quá giờ
    so_worker: int = field(default_factory=lambda: _so_tu_env("CPA2_WORKERS", 2, 16))
    so_worker_ocr: int = field(default_factory=lambda: _so_tu_env("CPA2_WORKERS_OCR", 1, 8))   # bể RIÊNG cho /v1/ocr (nặng, tới 240s)
    gioi_han_ram_mb: int = field(default_factory=lambda: _so_tu_env("CPA2_RAM_MB", 4096, 65536))   # RLIMIT_AS mỗi tiến trình con (0 = tắt)
    khoi_tao_worker: str = "cpa2_api.dich_vu:tao_dich_vu"
    timeout_advice: float = 25.0            # giây
    timeout_lookup: float = 10.0
    timeout_recs: float = 25.0
    timeout_ocr: float = 240.0
    cho_hang_doi: float = 5.0               # giây chờ một tiến trình rảnh trước khi trả 503 qua_tai
