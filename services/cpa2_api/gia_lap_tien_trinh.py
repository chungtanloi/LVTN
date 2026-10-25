"""gia_lap_tien_trinh.py — dịch vụ GIẢ chỉ dùng trong validate_api (phần J): kiểm bể tiến trình mà không cần nạp lõi CPA².
Hành vi theo câu hỏi: 'ngu:N' ngủ N giây; 'chet' thoát tiến trình đột ngột; 'loi' ném ngoại lệ chứa chuỗi nhạy cảm."""
import os
import time


class Gia:
    def tu_van(self, ho_so, cau_hoi, canh_bao):
        if cau_hoi.startswith("ngu:"):
            time.sleep(float(cau_hoi[4:]))
        elif cau_hoi == "chet":
            os._exit(1)
        elif cau_hoi == "loi":
            raise RuntimeError("BI_MAT_TRONG_NGOAI_LE CT180 9.5")
        return {"trang_thai": "ok", "ket_luan": "UNKNOWN", "claim": "gia", "loi_giai": "giả", "chung_chi": None, "nguon": [],
                "du_kien_thieu": [], "can_bo_sung": [], "mau_thuan": [], "canh_bao": canh_bao, "phien_ban_kb": {}}

    def tra_cuu(self, truy_van, k):
        return {"trang_thai": "ok", "ket_qua": [], "phien_ban_kb": {}}

    def de_xuat(self, ho_so, hoc_ky, canh_bao):
        return {"trang_thai": "ok", "hoc_ky": hoc_ky, "dang_ky": [], "tong_tc": 0, "can_xac_minh": [], "mau_thuan": [], "canh_bao": canh_bao,
                "phien_ban_kb": {}}

    def ocr(self, anh, khai_bao):
        return {"trang_thai": "ok", "da_xac_minh": False, "ho_so_nhap": {}, "bao_cao": {}, "so_trang": len(anh), "phien_ban_kb": {}}


def tao(goc=None):
    return Gia()
