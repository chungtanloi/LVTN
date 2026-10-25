"""cau_hinh.py — cấu hình dịch vụ. Khoá API đọc từ biến môi trường CPA2_API_KEY (không hardcode, không log)."""
import os
from dataclasses import dataclass, field
from pathlib import Path


def _mac_dinh_goc():
    # CPA2_ROOT: thư mục CPA2_KhaoSat (Docker: /app/CPA2_KhaoSat). Mặc định: cạnh thư mục services/ của repo.
    return Path(os.environ.get("CPA2_ROOT") or Path(__file__).resolve().parents[3] / "CPA2_KhaoSat")


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
    max_pixels_tong: int = 60_000_000       # tổng điểm ảnh của MỘT yêu cầu OCR (chặn ngốn RAM khi nhiều ảnh lớn)
    max_mau_thuan: int = 3                  # số bản ghi tự mâu thuẫn tối đa: mỗi bản ghi mở 4 nhánh → solver nổ tổ hợp (x4,5/bản ghi)
    # --- tiến trình + thời gian. so_worker = 0: chạy trong tiến trình (phát triển / test); > 0: bể tiến trình con, giết được khi quá giờ
    so_worker: int = field(default_factory=lambda: int(os.environ.get("CPA2_WORKERS") or 2))
    khoi_tao_worker: str = "cpa2_api.dich_vu:tao_dich_vu"
    timeout_advice: float = 25.0            # giây
    timeout_lookup: float = 10.0
    timeout_recs: float = 25.0
    timeout_ocr: float = 240.0
    cho_hang_doi: float = 5.0               # giây chờ một tiến trình rảnh trước khi trả 503 qua_tai
