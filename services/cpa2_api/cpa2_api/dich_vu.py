"""dich_vu.py — gọi lõi CPA² (CPA2_KhaoSat/) và đổi kết quả sang hợp đồng của API. Chạy TRONG tiến trình con của bể (tien_trinh.py) hoặc
trong tiến trình chính khi so_worker = 0. Hồ sơ chỉ đi vào lõi dưới dạng dict đã chuẩn hoá (ho_so.kiem_tra), không bao giờ dưới dạng
đường dẫn file.

Trạng thái trả về (trang_thai) — lỗi kỹ thuật KHÔNG bao giờ thành kết luận học vụ:
  ok               có kết luận TRUE / FALSE / UNKNOWN / DA_HOAN_THANH do solver + chứng chỉ, VÀ claim thuộc danh sách đã hình thức hoá
  ngoai_pham_vi    câu hỏi chưa hỗ trợ: ket_luan null, KHÔNG mang chứng chỉ / nguồn (claim khong_ro, counterfactual, hoặc claim chưa có
                   lời giải đúng như thieu_bat_buoc / thieu_nhom / du_dk_xin_mien — claim KHÔNG đối số không bao giờ có trong answer set
                   nên CLI luôn trả FALSE sai (họ lỗi P18-1); API không chuyển nó thành kết luận)
  hau_kiem_chan    hậu kiểm (BLOCKED) chặn câu trả lời: ket_luan null, không mang chứng chỉ / nguồn / nội dung bị chặn
  ho_so_mau_thuan  solver vô nghiệm (UNSAT): ket_luan MAU_THUAN
  (khong_ho_tro_ho_so / loi_dau_vao / khong_xac_thuc / het_gio / qua_tai / loi_he_thong đặt ở lớp HTTP)
"""
import hashlib
import io
import re
import sys
from functools import lru_cache
from pathlib import Path

# claim mà prototype/grounded_answer trả lời ĐÚNG và có chứng chỉ (Tuần 12–20). Mọi claim khác → ngoai_pham_vi.
CLAIM_DUOC_PHEP = re.compile(r'^(?:tot_nghiep|xep_loai|de_xuat|du_dk\((?:lvtn|tltn)\)|duoc_dang_ky\("[A-Za-z0-9_]{1,20}"\)|'
                             r'hang_cuoi\((?:xuat_sac|gioi|kha|trung_binh)\))$')
KET_LUAN_HOP_LE = ("TRUE", "FALSE", "UNKNOWN", "DA_HOAN_THANH")
LOI_GIAI_NGOAI_PHAM_VI = ("Hệ thống chưa hỗ trợ loại câu hỏi này (ngoài phần quy chế đã hình thức hoá, hoặc chưa có lời giải đúng) "
                          "— không đoán. Bạn có thể hỏi về tốt nghiệp, đăng ký học phần, điều kiện luận văn / tiểu luận, xếp loại tốt nghiệp, "
                          "hoặc đề xuất đăng ký.")
LOI_GIAI_BI_CHAN = "Câu trả lời bị hậu kiểm chặn vì không đủ căn cứ nguồn — hệ thống không đưa ra kết luận."

# tệp ảnh hưởng đến kết quả → vào hash phiên bản KB (cả mã: parser / loader / schema, không chỉ luật)
TEP_PHIEN_BAN = ("w7_student_facts/loader.py", "w7_student_facts/student_fact_schema.json", "w12_integration/prototype.py",
                 "w14_rag/retriever.py", "w14_rag/grounded_answer.py", "w16_abstention/abstention.py", "w18_eligibility/eligibility.py",
                 "w19_recommendation/recommendation.py", "w15_ocr/ocr_transcript.py", "w5_rformal/r_formal_v1.json", "w14_rag/corpus.jsonl",
                 "w6_curriculum/curriculum_cntt_k49.json")


def nap_duong_dan(goc):
    goc = Path(goc)
    for d in ("w12_integration", "w14_rag", "w15_ocr", "w16_abstention", "w18_eligibility", "w19_recommendation", "w7_student_facts"):
        p = str(goc / d)
        if p not in sys.path:
            sys.path.insert(0, p)


def an_toan(x):
    """Đổi sang kiểu JSON: tập → danh sách có thứ tự, khoá không phải chuỗi → chuỗi, kiểu lạ → chuỗi."""
    if isinstance(x, dict):
        return {str(k): an_toan(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [an_toan(v) for v in x]
    if isinstance(x, (set, frozenset)):
        return sorted((an_toan(v) for v in x), key=str)
    if x is None or isinstance(x, (str, int, float, bool)):
        return x
    return str(x)


@lru_cache(maxsize=4)
def phien_ban_kb(goc):
    """Phiên bản KB: R-Formal (đọc từ đầu file .lp) + hash ngắn của MỌI tệp luật (*.lp), mã suy diễn / parser / loader, schema, corpus, CTĐT.
    Không phụ thuộc kiểu xuống dòng Windows/Linux."""
    goc = Path(goc)
    h = hashlib.sha256()
    for f in sorted([*goc.glob("w*/*.lp"), *(goc / t for t in TEP_PHIEN_BAN)]):
        h.update(f.name.encode("utf-8"))
        h.update(f.read_bytes().replace(b"\r\n", b"\n"))
    lp = (goc / "w5_rformal" / "qd3266_r_formal_v1.lp").read_text(encoding="utf-8")
    m = re.search(r"R-Formal v1 \(v(\d+\.\d+)", lp)
    return {"r_formal": f"v{m.group(1)}" if m else "khong_ro", "sha256": h.hexdigest()[:12], "ctdt": "cntt_k49"}


class DichVu:
    def __init__(self, goc):
        self.goc = Path(goc)
        nap_duong_dan(self.goc)
        import grounded_answer
        import prototype
        import recommendation
        from retriever import Retriever
        self.grounded, self.prototype, self.recommendation = grounded_answer, prototype, recommendation
        self.retriever = Retriever(self.goc / "w14_rag" / "corpus.jsonl")
        self.kb = phien_ban_kb(str(self.goc))

    # ---------------------------------------------------------------- tư vấn
    def tu_van(self, ho_so, cau_hoi, canh_bao):
        if not isinstance(ho_so, dict):                       # phòng thủ: lõi nhận cả đường dẫn file, API tuyệt đối không được
            raise TypeError("ho_so phải là dict")
        res = self.grounded.tra_loi(cau_hoi, ho_so, r=self.retriever)
        v, claim = res.get("verdict"), res.get("claim")
        base = {"claim": claim, "canh_bao": canh_bao, "phien_ban_kb": self.kb, "thong_bao": "", "chi_tiet": []}
        if v == "BLOCKED":
            return an_toan({**base, "trang_thai": "hau_kiem_chan", "ket_luan": None, "claim": None, "loi_giai": LOI_GIAI_BI_CHAN,
                            "chung_chi": None, "nguon": [], "du_kien_thieu": [], "can_bo_sung": [], "mau_thuan": []})
        if v == "UNSAT":
            return an_toan({**base, "trang_thai": "ho_so_mau_thuan", "ket_luan": "MAU_THUAN", "loi_giai": res.get("explanation_vi"),
                            "chung_chi": None, "nguon": [], "du_kien_thieu": [], "can_bo_sung": [], "mau_thuan": res.get("mau_thuan", [])})
        if not (isinstance(claim, str) and CLAIM_DUOC_PHEP.match(claim)):
            return an_toan({**base, "trang_thai": "ngoai_pham_vi", "ket_luan": None, "loi_giai": LOI_GIAI_NGOAI_PHAM_VI,
                            "chung_chi": None, "nguon": [], "du_kien_thieu": [], "can_bo_sung": [], "mau_thuan": []})
        if v not in KET_LUAN_HOP_LE:
            raise ValueError("verdict lạ")
        return an_toan({**base, "trang_thai": "ok", "ket_luan": v, "loi_giai": res.get("explanation_vi"),
                        "chung_chi": res.get("certificate"), "nguon": res.get("nguon", []),
                        "du_kien_thieu": res.get("missing_facts", []), "can_bo_sung": res.get("can_bo_sung", []),
                        "mau_thuan": res.get("mau_thuan", [])})

    # ---------------------------------------------------------------- tra cứu
    def tra_cuu(self, truy_van, k):
        return an_toan({"trang_thai": "ok", "ket_luan": None, "thong_bao": "", "chi_tiet": [], "ket_qua": [
            {"id": p["id"], "van_ban": p.get("van_ban"), "dia_chi": p.get("dia_chi") or p.get("tieu_de"), "trang": p.get("trang"),
             "tieu_de": p.get("tieu_de"), "loai": p.get("loai"), "noi_dung": p["text"], "diem": round(diem, 3)}
            for p, diem in self.retriever.search(truy_van, k=k)], "phien_ban_kb": self.kb})

    # ---------------------------------------------------------------- đề xuất đăng ký một học kỳ
    def de_xuat(self, ho_so, hoc_ky, canh_bao):
        if not isinstance(ho_so, dict):
            raise TypeError("ho_so phải là dict")
        r = self.recommendation.de_xuat(ho_so, hoc_ky)
        out = {k: v for k, v in r.items() if k != "hk"}
        for x in out.get("dang_ky", []):
            x["chung_chi"] = x.get("chung_chi") or []
        return an_toan({"trang_thai": "ok", "ket_luan": None, "thong_bao": "", "chi_tiet": [], "hoc_ky": hoc_ky, **out,
                        "canh_bao": canh_bao, "phien_ban_kb": self.kb})

    # ---------------------------------------------------------------- OCR → hồ sơ NHÁP
    def ocr(self, anh_bytes, khai_bao):
        """Danh sách ảnh (bytes đã qua kiểm tra ở lớp HTTP) → hồ sơ nháp + báo cáo. Không đưa ra kết luận học vụ.
        Ảnh đổi sang thang xám ngay khi giải nén (tiết kiệm RAM); pytesseract chạy trong tiến trình con có giới hạn thời gian."""
        from PIL import Image
        import ocr_transcript as O
        anh = []
        for b in anh_bytes:
            with Image.open(io.BytesIO(b)) as im:
                anh.append(im.convert("L"))
        doc = O.doc_bang_diem(anh)
        hs, _extra, bc = O.sang_ho_so(doc, khai_bao=khai_bao or {})
        bao_cao = {k: bc.get(k) for k in ("khong_chac", "hoc_ky_lech", "can_hoi", "khai_bao_thieu", "can_xac_nhan", "ngoai_ctdt",
                                         "khai_bao_loi", "tich_luy_kiem_cheo", "dtbchk_khai_bao", "tong_dong", "nhan", "loai", "dong_an")}
        return an_toan({"trang_thai": "ok", "ket_luan": None, "thong_bao": "", "chi_tiet": [], "da_xac_minh": False, "ho_so_nhap": hs,
                        "bao_cao": bao_cao, "so_trang": len(anh), "phien_ban_kb": self.kb})


def tao_dich_vu(goc):
    return DichVu(goc)
