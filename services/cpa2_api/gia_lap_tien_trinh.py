"""gia_lap_tien_trinh.py — dịch vụ GIẢ chỉ dùng trong validate_api (phần J): kiểm bể tiến trình mà không cần nạp lõi CPA².
Hành vi theo câu hỏi: 'ngu:N' ngủ N giây; 'chet' thoát tiến trình đột ngột; 'loi' ném ngoại lệ chứa chuỗi nhạy cảm;
'ram' xin 900 MB (MemoryError khi bị giới hạn bộ nhớ); 'env' báo biến môi trường CPA2_API_KEY có trong tiến trình con không;
'con:<tệp>' sinh một tiến trình cháu (như tesseract), ghi pid vào tệp rồi ngủ. OCR ngủ GIA_OCR_NGU giây (biến môi trường)."""
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
        elif cau_hoi == "ram":
            x = bytearray(900 * 1024 * 1024)
            x[-1] = 1
        elif cau_hoi.startswith("con:"):
            import subprocess
            con = subprocess.Popen(["sleep", "60"])
            with open(cau_hoi[4:], "w") as f:
                f.write(str(con.pid))
            time.sleep(30)
        elif cau_hoi == "env":
            return {"trang_thai": "ok", "ket_luan": "UNKNOWN", "claim": "gia", "chung_chi": None, "nguon": [], "du_kien_thieu": [],
                    "can_bo_sung": [], "mau_thuan": [], "canh_bao": canh_bao, "phien_ban_kb": {},
                    "loi_giai": "CO_KHOA" if "CPA2_API_KEY" in os.environ else "KHONG_CO_KHOA"}
        return {"trang_thai": "ok", "ket_luan": "UNKNOWN", "claim": "gia", "loi_giai": "giả", "chung_chi": None, "nguon": [],
                "du_kien_thieu": [], "can_bo_sung": [], "mau_thuan": [], "canh_bao": canh_bao, "phien_ban_kb": {}}

    def tra_cuu(self, truy_van, k):
        return {"trang_thai": "ok", "ket_qua": [], "phien_ban_kb": {}}

    def de_xuat(self, ho_so, hoc_ky, canh_bao):
        return {"trang_thai": "ok", "hoc_ky": hoc_ky, "dang_ky": [], "tong_tc": 0, "can_xac_minh": [], "mau_thuan": [], "canh_bao": canh_bao,
                "phien_ban_kb": {}}

    def ocr(self, anh, khai_bao):
        time.sleep(float(os.environ.get("GIA_OCR_NGU") or 0))
        return {"trang_thai": "ok", "da_xac_minh": False, "ho_so_nhap": {}, "bao_cao": {}, "so_trang": len(anh), "phien_ban_kb": {}}


def tao(goc=None):
    time.sleep(float(os.environ.get("GIA_KHOI_NGU") or 0))          # khởi động chậm (test khoá của bể)
    return Gia()
