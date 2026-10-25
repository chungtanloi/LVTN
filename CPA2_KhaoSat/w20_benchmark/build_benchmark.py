"""
build_benchmark.py — sinh G-Truth v1 và OCR-Noise v1 (CPA2, Tuần 20) → gtruth.json, ocr_noise.json, gold_dong_bang.json

GOLD VIẾT TAY ở đây (literal TRUE/FALSE/UNKNOWN), kèm lý do + con trỏ nguồn, và được commit + đóng băng hash
TRƯỚC lần chạy CPA² đầu tiên. Không ca nào lấy gold từ kết quả hệ thống. Bộ MỚI — không trùng ca nào của w17
(bộ đối kháng w17 đã nhiễm sau P17-1/P17-2).

Hàm phụ ở đây CHỈ DỰNG DỮ LIỆU (chọn học phần bỏ đi để đạt đúng số TC mục tiêu, chọn học phần nâng điểm để đạt
đúng ĐTBCTL mục tiêu); con số mục tiêu là tiền đề viết tay trong trường "oracle" và validate_benchmark.py kiểm lại
bằng oracle Python độc lập (w17/oracle.py — không clingo, không đọc .lp).

Hệ ("he") — đường chạy của CPA² (baseline Tuần 21 nhận cùng đầu vào trung lập qua baseline.py):
  kb    claim ASP trên hồ sơ (w16 abstention)            elig  Eligibility w18 (ELIGIBLE→TRUE, NOT/DA_HOAN_THANH→FALSE)
  rec   bất biến Recommendation w19 ("khong_de_xuat:X@hk" = X KHÔNG được có trong phương án HK hk; "tong_tc_le_20@hk")
  nl    câu tiếng Việt qua prototype w12 (parser → KB)     ocr   bảng điểm OCR (w15 sang_ho_so → ket_luan)

Số trang "tr." = trang của bản OCR (w5_rformal/source/*_ocr_raw.txt); tr.20 QĐ3266 = bản chép tay.
Chia dev/test: phân tầng theo nhóm, seed 20, xen kẽ. Chỉ tinh chỉnh trên dev; test chỉ chạy để báo cáo (Tuần 22).

Chạy:  python build_benchmark.py          (ghi gtruth.json, ocr_noise.json)
       python build_benchmark.py --dong-bang   (ghi thêm gold_dong_bang.json — CHỈ một lần, trước lần chạy đầu)
"""
import hashlib, json, random, sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "w17_adversarial"))
import oracle, dau_vao

CT = oracle._CT

# ------------------------------------------------------------------ nguồn
N_TQ = "QĐ3266 Điều 7 khoản 4, tr.5 (R-A03: tiên quyết phải đã tích lũy)"
N_SH = "QĐ3266 Điều 7 khoản 5, tr.5 (R-A04: song hành phải học trước hoặc học cùng lúc; 'học' ≠ 'tích lũy' — quyết định (a), Loi 18/10/2026)"
N_TCTQ = "CTĐT CNTT K49 (QĐ2423) tr.4 — tiên quyết theo số TC tích lũy + QĐ3266 Điều 24 khoản 1, tr.15"
N_DIEM = "QĐ3266 Điều 22 khoản 2–3, tr.13–14 (bảng quy đổi; tích lũy từ D)"
N_TN = "QĐ3266 Điều 32 khoản 1, tr.19"
N_KL = "QĐ3266 Điều 32 khoản 1 điểm c, tr.19 (R-F03)"
N_QP = "QĐ3266 Điều 32 khoản 1 điểm b, tr.19 (hoàn thành HP điều kiện; TB GDQP&AN ≥ 5,0 thang 10)"
N_TG = "QĐ3266 Điều 5, tr.4–5 (thiết kế 4,5 năm → tối đa 9 năm; K ≤ 49: mỗi 9 TC công nhận giảm 1 HK) + Điều 6 khoản 1, tr.5 (3 HK/năm)"
N_TL = "QĐ3266 Điều 24 khoản 4, tr.15 (ĐTBCTL không gồm F và HP điều kiện)"
N_HANG = "QĐ3266 Điều 34 khoản 2, tr.20 (chép tay từ PDF gốc): XS 3,60–4,00 · Giỏi 3,20–3,59 · Khá 2,50–3,19 · TB 2,00–2,49"
N_CTDT = "CTĐT CNTT K49 (QĐ2423) tr.3–4 — khung 161 TC, nhóm tự chọn ('10 AV hoặc PV'; chuyên ngành chọn một cặp)"
N_CC = "QĐ5339 Điều 3 khoản 5 điểm a, tr.5–6 + Phụ lục 1, tr.11 (K45 trở về sau: bậc 3 — IELTS 4.5 / TOEIC 450 / TOEFL iBT 45 / CTU A-B-C bậc 3)"
N_CC_NN = "QĐ5339 Điều 3 khoản 5 điểm a ≠ điểm b (chứng chỉ tiếng Anh chỉ xét miễn Anh văn)"
N_ML = "QĐ5339 Điều 3 khoản 9, tr.8 (R-M13: bảng chuyển đổi Lý luận chính trị — ML009→ML014, ML010→ML016+ML018, ML011→ML019, ML006→ML021)"
N_ML_QD = N_ML + " + Điều 2 khoản 6, tr.4 (phải làm đơn, đơn vị xét duyệt — công nhận KHÔNG tự động; cùng tinh thần QD-11)"
N_LV = "QĐ3266 Điều 31, tr.19 + QD-12 (điều kiện nhận đề tài chỉ là ngưỡng TC — Loi 18/10/2026) + CTĐT K49 (CT550E/CT501E ≥ 120 TC)"
N_LV_F = "QĐ3266 Điều 31 (đoạn cuối), tr.19: nhận điểm F của LVTN/TLTN phải đăng ký làm lại hoặc học HP thay thế"
N_31 = "QĐ3266 Điều 31, tr.19: SV thực hiện MỘT trong ba hình thức; đơn vị đào tạo công bố hình thức cho SV"
N_31K3 = "QĐ3266 Điều 31 khoản 3, tr.19 (tích lũy TC tốt nghiệp thay LVTN/TLTN)"
N_MO = "CTĐT CNTT K49 — học kỳ mở học phần (cột HK); GDQP&AN do Trường bố trí riêng"
N_14 = "QĐ3266 Điều 14 khoản 1, tr.8 (R-C01: tối đa 20 TC/HK)"
N_TK = "Nguyên tắc thiết kế CPA² (Tuần 1): không kết luận điều KB không hình thức hoá / không có dữ kiện — KHÔNG phải nội dung quy chế"
N_OCR = "Tuần 15 (OCR): không chắc ≠ sai — dòng/học kỳ đọc không chắc thì không được kết luận"

Q = {
    "tot_nghiep": "Em đã đủ điều kiện xét tốt nghiệp chưa?",
    "dk_dtbctl": "ĐTBCTL của em đã đạt mức tối thiểu 2,00 để xét tốt nghiệp chưa?",
    "dk_tin_chi": "Em đã tích lũy đủ 161 tín chỉ của CTĐT chưa?",
    "dk_gdqp": "Điểm trung bình các học phần Giáo dục quốc phòng của em đã đạt 5,0 chưa?",
    "thieu_dk(thoi_gian)": "Em có bị quá thời gian học tập tối đa không?",
    "dk_bat_buoc": "Em đã tích lũy đủ các học phần bắt buộc chưa?",
    "dk_hp_dieu_kien": "Em đã hoàn thành các học phần điều kiện chưa?",
}


# ------------------------------------------------------------------ dựng dữ liệu (không quyết định gold)
def hs(goc, *bd):
    return {"loai": "ho_so", "goc": goc, "bien_doi": list(bd)}


def ocr(goc, *bd, that=()):
    return {"loai": "ocr_doc", "goc": goc, "that": list(that), "bien_doi": list(bd), "khai_bao_bo": []}


THU_TU_BO = ["CT223", "CT222", "CT467", "CT293", "CT275", "CT300", "CT202", "CT294", "CT273", "CT179", "CT188",
             "CT112", "CT178", "CT173", "CT296", "CT175", "CT190", "CT172", "CT200", "CT100", "TN012", "TN010",
             "TN002", "TN001", "ML007", "KL001E", "ML021", "ML019", "ML018", "ML016", "CT449", "CT484", "CT180",
             "CT182", "CT174", "CT177", "CT101", "ML014", "CT176", "CT271E", "CT466E", "CT518E"]


def bo_den(goc, tc_muc_tieu, giu=(), bo_truoc=()):
    """Danh sách mã cần xoá (theo THU_TU_BO, bỏ qua `giu`) để hồ sơ còn ĐÚNG tc_muc_tieu TC tích lũy."""
    j = dau_vao.ho_so_goc(goc)
    tc = oracle.tinh(j)["tc_tich_luy"] - sum(j["grades"][m]["credits"] for m in bo_truoc)
    bo = list(bo_truoc)
    for m in THU_TU_BO:
        if tc == tc_muc_tieu:
            break
        if m in giu or m in bo or m not in j["grades"]:
            continue
        cr = j["grades"][m]["credits"]
        if tc - cr >= tc_muc_tieu and (tc - cr - tc_muc_tieu) != 1:
            bo.append(m)
            tc -= cr
    if tc != tc_muc_tieu:
        raise ValueError(f"không dựng được {tc_muc_tieu} TC từ {goc}")
    return bo


def nang_diem(goc, tc_cao, diem_cao, diem_thap):
    """Mọi HP không điều kiện của hồ sơ = diem_thap, trừ một tập có ĐÚNG tc_cao TC = diem_cao (subset-sum)."""
    j = dau_vao.ho_so_goc(goc)
    hp = sorted((m, g["credits"]) for m, g in j["grades"].items() if g.get("thang10") is not None and not oracle.dieu_kien(m))
    kq = {0: []}
    for m, cr in hp:
        for s, ds in list(kq.items()):
            if s + cr not in kq:
                kq[s + cr] = ds + [m]
    if tc_cao not in kq:
        raise ValueError(f"không chọn được {tc_cao} TC")
    return [["tat_ca_khong_dk", diem_thap]] + [["diem", m, diem_cao] for m in kq[tc_cao]]


# Gold dựa trên NGUYÊN TẮC THIẾT KẾ (không kết luận khi không có dữ kiện / ngoài KB; chính sách tư vấn; OCR mâu thuẫn
# hoặc mất dòng) chứ không phải câu chữ quy chế → báo cáo TÁCH RIÊNG (soát độc lập trước đóng băng).
THIET_KE = {"DK-22", "NL-05", "NL-06", "NL-07", "NL-10", "RC-03", "RC-08"}


def ca(id_, nhom, he, claim, dau_vao_, gold, ly_do, nguon, **kw):
    d = {"id": id_, "nhom": nhom, "he": he, "claim": claim, "cau_hoi": kw.pop("cau_hoi", Q.get(claim, "")),
         "dau_vao": dau_vao_, "gold": gold, "ly_do": ly_do, "nguon": nguon, "cham_diem": True,
         "loai_gold": "thiet_ke" if id_ in THIET_KE or id_[-2:] in ("M3", "M4") else "quy_che"}
    d.update(kw)
    return d


def dk(id_, ma, dv, gold, ly, nguon, **kw):
    return ca(id_, "dang_ky", "kb", f'duoc_dang_ky("{ma}")', dv, gold, ly, nguon,
              cau_hoi=f"Kỳ này em đăng ký học phần {ma} được không?", **kw)


def rec(id_, claim, dv, ly, nguon, **kw):
    ma, hk = (claim.split(":")[1] if ":" in claim else claim).split("@")
    q = (f"Hệ thống có thể đề xuất em đăng ký {ma} ở học kỳ {hk} không?" if ":" in claim
         else f"Phương án đăng ký học kỳ {hk} đề xuất cho em có vượt 20 tín chỉ không?")
    return ca(id_, "de_xuat", "rec", claim, dv, "TRUE", ly, nguon, cau_hoi=q, hk=int(hk), **kw)


ML010 = ["diem_tho", "ML010", {"credits": 3, "thang10": 80, "letter": "B+", "status": "passed"}]
NAM2_BO = ["CT177", "CT174", "CT175", "CT180", "CT182", "CT296", "CT467", "CT178", "CT112", "CT293", "CT271E",
           "CT273", "CT294", "CT202", "CT275", "CT300", "CT223", "CT222", "CT449", "CT484", "CT466E", "CT550E",
           "CT518E", "ML018", "ML019", "ML021", "XH025", "CT179", "CT188"]
P2 = ["xoa_diem", NAM2_BO]
CT550_119 = bo_den("sv_lvtn", 119, giu=("CT177", "CT176"), bo_truoc=("CT550E",))
CT550_120 = bo_den("sv_lvtn", 120, giu=("CT177", "CT176"), bo_truoc=("CT550E",))

# =================================================================== G-TRUTH v1
GT = [
    # ---------------------------------------------------------------- ĐĂNG KÝ MỘT HP (tiên quyết + song hành)
    dk("DK-01", "CT182", hs("sv_lvtn", ["xoa_diem", "CT182"]), "TRUE",
       "Đã tích lũy CT176 (tiên quyết) và đã học CT180 (song hành).", N_TQ + "; " + N_SH),
    dk("DK-02", "CT182", hs("sv_lvtn", ["xoa_diem", ["CT182", "CT180"]]), "TRUE",
       "Chưa học CT180 nhưng CT180 đăng ký được (đã có CT177) → được, với điều kiện học CT180 cùng kỳ.", N_TQ + "; " + N_SH),
    dk("DK-03", "CT182", hs("sv_lvtn", ["xoa_diem", ["CT182", "CT180", "CT177"]]), "FALSE",
       "Chưa học CT180 và CT180 không đăng ký được (thiếu CT177) → không học trước, không học cùng lúc được.", N_TQ + "; " + N_SH),
    dk("DK-04", "CT182", hs("sv_lvtn", ["xoa_diem", ["CT182", "CT176"]]), "FALSE",
       "Thiếu tiên quyết CT176.", N_TQ),
    dk("DK-05", "CT182", hs("sv_lvtn", ["xoa_diem", "CT182"], ["diem", "CT180", 30]), "TRUE",
       "CT180 đã HỌC (bị F) — song hành chỉ đòi 'học', không đòi 'tích lũy'.", N_SH),
    dk("DK-06", "CT182", hs("sv_lvtn", ["xoa_diem", "CT182"], ["diem_dac_biet", "CT180", "W"]), "TRUE",
       "CT180 điểm W (đã rút) không tính là đã học, nhưng CT180 đăng ký được → được, kèm điều kiện học cùng kỳ.", N_SH),
    dk("DK-07", "CT182", hs("sv_lvtn", ["xoa_diem", "CT182"], ["diem", "CT176", 35]), "FALSE",
       "CT176 bị F (3,5) → chưa tích lũy tiên quyết.", N_TQ + "; " + N_DIEM),
    dk("DK-08", "CT182", hs("sv_lvtn", ["xoa_diem", "CT182"], ["diem", "CT176", 40]), "TRUE",
       "CT176 đạt D (4,0) → đã tích lũy tiên quyết.", N_TQ + "; " + N_DIEM),
    dk("DK-09", "CT182", hs("sv_lvtn", ["xoa_diem", "CT182"], ["khong_chac", "CT176", [30, 80]]), "UNKNOWN",
       "Điểm CT176 (tiên quyết) chưa rõ 3,0 hay 8,0.", N_TQ, can_hoi=['g10("CT176")']),
    dk("DK-10", "CT550E", hs("sv_lvtn", ["xoa_diem", CT550_119]), "FALSE",
       "119 TC tích lũy < 120.", N_TCTQ, oracle={"tc_tich_luy": "119"}),
    dk("DK-11", "CT550E", hs("sv_lvtn", ["xoa_diem", CT550_120]), "TRUE",
       "Đúng 120 TC tích lũy (biên).", N_TCTQ, oracle={"tc_tich_luy": "120"}),
    dk("DK-12", "XH025", hs("sv_lvtn", ["xoa_diem", "XH025"]), "TRUE",
       "XH025 song hành XH024 — đã học XH024.", N_SH),
    dk("DK-13", "XH025", hs("sv_lvtn", ["xoa_diem", ["XH023", "XH024", "XH025"]]), "TRUE",
       "Chưa học XH024, XH023 nhưng cả chuỗi đăng ký được cùng kỳ (không có tiên quyết) → được, kèm điều kiện.", N_SH),
    dk("DK-14", "CT271E", hs("sv_lvtn", ["xoa_diem", "CT271E"], ["diem", "CT174", 20]), "FALSE",
       "CT174 (tiên quyết của niên luận cơ sở) bị F.", N_TQ),
    dk("DK-15", "CT271E", hs("sv_lvtn", ["xoa_diem", "CT271E"], ["diem", "CT174", 45]), "TRUE",
       "CT174 đạt D (4,5), CT176 đạt → đủ tiên quyết.", N_TQ + "; " + N_DIEM),
    dk("DK-16", "CT466E", hs("sv_lvtn", ["xoa_diem", bo_den("sv_lvtn", 80, bo_truoc=("CT466E",))]), "TRUE",
       "Niên luận cần ≥ 80 TC; có đúng 80.", N_TCTQ, oracle={"tc_tich_luy": "80"}),
    dk("DK-17", "CT466E", hs("sv_lvtn", ["xoa_diem", bo_den("sv_lvtn", 79, bo_truoc=("CT466E",))]), "FALSE",
       "79 TC < 80.", N_TCTQ, oracle={"tc_tich_luy": "79"}),
    dk("DK-18", "CT518E", hs("sv_lvtn", ["xoa_diem", bo_den("sv_lvtn", 125, bo_truoc=("CT518E",))]), "TRUE",
       "Thực tập cần ≥ 125 TC; có đúng 125.", N_TCTQ, oracle={"tc_tich_luy": "125"}),
    dk("DK-19", "CT518E", hs("sv_lvtn", ["xoa_diem", bo_den("sv_lvtn", 124, bo_truoc=("CT518E",))]), "FALSE",
       "124 TC < 125.", N_TCTQ, oracle={"tc_tich_luy": "124"}),
    dk("DK-20", "ML019", hs("sv_lvtn", ["xoa_diem", ["ML019", "ML018"]]), "FALSE",
       "Thiếu tiên quyết ML018.", N_TQ),
    dk("DK-21", "ML019", hs("sv_lvtn", ["xoa_diem", ["ML019", "ML018", "ML016"]], ML010), "FALSE",
       "ML018 (tiên quyết của ML019) mới ĐỦ ĐIỀU KIỆN được xét công nhận từ ML010 — chưa có quyết định công nhận → "
       "chưa tích lũy. [Sửa trước đóng băng sau soát độc lập: bản đầu ghi TRUE.]", N_TQ + "; " + N_ML_QD),
    dk("DK-22", "CT999", hs("sv_lvtn"), "UNKNOWN",
       "Mã CT999 không có trong CTĐT K49 — hệ thống không có dữ kiện về học phần này → không được kết luận 'không'.",
       N_TK, can_hoi=[]),

    # ---------------------------------------------------------------- ĐỦ ĐIỀU KIỆN (Eligibility)
    ca("EL-01", "du_dieu_kien", "elig", "lvtn", hs("sv_lvtn", ["xoa_diem", "CT550E"]), "TRUE",
       "146 TC ≥ 120, chưa hoàn thành hình thức nào, không khai báo hình thức khác.", N_LV,
       cau_hoi="Em có đủ điều kiện làm luận văn tốt nghiệp không?"),
    ca("EL-02", "du_dieu_kien", "elig", "lvtn", hs("sv_lvtn", ["xoa_diem", "CT550E"], ["dat", "hinh_thuc_cuoi_khoa", "tltn"]),
       "FALSE", "Đơn vị đã công bố hình thức TLTN cho SV → không làm LVTN.", N_31,
       cau_hoi="Em có đủ điều kiện làm luận văn tốt nghiệp không?"),
    ca("EL-03", "du_dieu_kien", "elig", "tltn", hs("sv_lvtn", ["xoa_diem", "CT550E"], ["dat", "hinh_thuc_cuoi_khoa", "tltn"]),
       "TRUE", "Đã công bố TLTN, đủ 146 TC.", N_LV, cau_hoi="Em có đủ điều kiện làm tiểu luận tốt nghiệp không?"),
    ca("EL-04", "du_dieu_kien", "elig", "lvtn", hs("sv_lvtn", ["xoa_diem", CT550_119]), "FALSE",
       "119 TC < 120.", N_LV, oracle={"tc_tich_luy": "119"}, cau_hoi="Em có đủ điều kiện làm luận văn tốt nghiệp không?"),
    ca("EL-05", "du_dieu_kien", "elig", "tltn", hs("sv_lvtn", ["xoa_diem", CT550_120]), "TRUE",
       "Đúng 120 TC.", N_LV, oracle={"tc_tich_luy": "120"}, cau_hoi="Em có đủ điều kiện làm tiểu luận tốt nghiệp không?"),
    ca("EL-06", "du_dieu_kien", "elig", "lvtn", hs("sv_lvtn", ["diem", "CT550E", 30]), "TRUE",
       "LVTN bị F → được đăng ký làm lại.", N_LV_F, cau_hoi="Em bị F luận văn, em có được làm lại luận văn không?"),
    ca("EL-07", "du_dieu_kien", "elig", "tich_luy_tc", hs("sv_lvtn", ["xoa_diem", "CT550E"]), "TRUE",
       "Chưa làm LVTN/TLTN, nhóm tốt nghiệp chưa đủ → được chọn tích lũy TC thay thế.", N_31K3,
       cau_hoi="Em có thể học các học phần thay thế thay cho luận văn không?"),
    ca("EL-08", "du_dieu_kien", "elig", "nien_luan", hs("sv_lvtn", ["xoa_diem", bo_den("sv_lvtn", 81, bo_truoc=("CT466E",))]),
       "TRUE", "81 TC ≥ 80.", N_TCTQ, oracle={"tc_tich_luy": "81"}, cau_hoi="Em có đủ điều kiện làm niên luận không?"),
    ca("EL-09", "du_dieu_kien", "elig", "nien_luan", hs("sv_lvtn", ["xoa_diem", bo_den("sv_lvtn", 78, bo_truoc=("CT466E",))]),
       "FALSE", "78 TC < 80.", N_TCTQ, oracle={"tc_tich_luy": "78"}, cau_hoi="Em có đủ điều kiện làm niên luận không?"),
    ca("EL-10", "du_dieu_kien", "elig", "thuc_tap", hs("sv_lvtn", ["xoa_diem", bo_den("sv_lvtn", 130, bo_truoc=("CT518E",))]),
       "TRUE", "130 TC ≥ 125.", N_TCTQ, oracle={"tc_tich_luy": "130"}, cau_hoi="Em có đủ điều kiện đi thực tập doanh nghiệp không?"),
    ca("EL-11", "du_dieu_kien", "elig", "thuc_tap", hs("sv_lvtn", ["xoa_diem", bo_den("sv_lvtn", 122, bo_truoc=("CT518E",))]),
       "FALSE", "122 TC < 125.", N_TCTQ, oracle={"tc_tich_luy": "122"}, cau_hoi="Em có đủ điều kiện đi thực tập doanh nghiệp không?"),
    ca("EL-12", "du_dieu_kien", "elig", "nien_luan_co_so", hs("sv_lvtn", ["xoa_diem", ["CT271E", "CT176"]]), "FALSE",
       "Thiếu tiên quyết CT176.", N_TQ, cau_hoi="Em có đủ điều kiện làm niên luận cơ sở không?"),
    ca("EL-13", "du_dieu_kien", "elig", "nien_luan_co_so", hs("sv_lvtn", ["xoa_diem", "CT271E"], ["khong_chac", "CT176", [35, 85]]),
       "UNKNOWN", "Điểm CT176 chưa rõ 3,5 hay 8,5.", N_TQ, can_hoi=['g10("CT176")'],
       cau_hoi="Em có đủ điều kiện làm niên luận cơ sở không?"),
    ca("EL-14", "du_dieu_kien", "elig", "nien_luan_co_so", hs("sv_lvtn", ["xoa_diem", "CT271E"], ["diem", "CT176", 40]),
       "TRUE", "CT176 đạt D (4,0) là đã tích lũy.", N_TQ + "; " + N_DIEM, cau_hoi="Em có đủ điều kiện làm niên luận cơ sở không?"),
    ca("EL-15", "du_dieu_kien", "elig", "thay_the:ML018", hs("sv_lvtn", ["xoa_diem", ["ML016", "ML018"]], ML010), "TRUE",
       "Đạt ML010 → được công nhận thay ML016 và ML018 (một → nhiều).", N_ML,
       cau_hoi="Em đã học Lý luận chính trị cũ ML010, em có được công nhận ML018 không?"),
    ca("EL-16", "du_dieu_kien", "elig", "thay_the:ML019",
       hs("sv_lvtn", ["xoa_diem", "ML019"], ["diem_tho", "ML011", {"credits": 3, "thang10": 30, "letter": "F", "status": "failed"}]),
       "FALSE", "ML011 bị F → không có học phần cũ đã đạt để công nhận ML019.", N_ML,
       cau_hoi="Em học ML011 rồi, em có được công nhận ML019 không?"),
    ca("EL-17", "du_dieu_kien", "elig", "thay_the:ML021",
       hs("sv_lvtn", ["xoa_diem", "ML021"], ["diem_tho", "ML006", {"credits": 2, "thang10": 65, "letter": "C+", "status": "passed"}]),
       "TRUE", "Đạt ML006 → công nhận ML021.", N_ML, cau_hoi="Em học ML006 rồi, em có được công nhận ML021 không?"),

    # ---------------------------------------------------------------- BẤT BIẾN ĐỀ XUẤT (Recommendation)
    rec("RC-01", "khong_de_xuat:CT174@1", hs("sv_lvtn", P2), "CT174 cần CT177 (chưa tích lũy).", N_TQ),
    rec("RC-02", "khong_de_xuat:CT177@3", hs("sv_lvtn", P2), "CT177 chỉ mở HK1, HK2.", N_MO),
    rec("RC-03", "khong_de_xuat:CT101@1", hs("sv_lvtn", P2), "CT101 đã tích lũy.", N_DIEM),
    rec("RC-04", "khong_de_xuat:CT182@1", hs("sv_lvtn", P2),
        "CT182 song hành CT180: chưa học CT180 và CT180 không đăng ký được (thiếu CT177).", N_SH),
    rec("RC-05", "khong_de_xuat:FL001@2", hs("sv_lvtn", P2), "Đã học nhánh Anh văn (XH023, XH024) → không học Pháp văn.", N_CTDT),
    rec("RC-06", "khong_de_xuat:CT550E@1", hs("sv_lvtn", P2), "Chưa đủ 120 TC.", N_TCTQ),
    rec("RC-07", "khong_de_xuat:CT518E@1", hs("sv_lvtn", P2), "CT518E chỉ mở HK3 (và cần 125 TC).", N_MO + "; " + N_TCTQ),
    rec("RC-08", "khong_de_xuat:QP012@1", hs("sv_lvtn", ["xoa_diem", ["QP012", "CT177", "CT174"]]),
        "GDQP&AN do Trường bố trí, không thuộc phương án tự đăng ký.", N_MO),
    rec("RC-09", "tong_tc_le_20@1", hs("sv_lvtn", P2), "Không vượt 20 TC/HK.", N_14),
    rec("RC-10", "tong_tc_le_20@3", hs("sv_lvtn", P2), "Không vượt 20 TC/HK (cả học kỳ 3).", N_14),
    rec("RC-11", "khong_de_xuat:CT182@1", hs("sv_lvtn", ["xoa_diem", ["CT182", "CT176"]], ["khong_chac", "CT176", [30, 80]]),
        "Tiên quyết CT176 chưa rõ → không được đề xuất như thể chắc chắn.", N_TQ + "; " + N_TK),
    rec("RC-12", "khong_de_xuat:CT501E@1", hs("sv_lvtn", ["xoa_diem", "CT550E"], ["dat", "hinh_thuc_cuoi_khoa", "lvtn"]),
        "Đơn vị đã công bố hình thức LVTN → không làm TLTN.", N_31),

    # ---------------------------------------------------------------- TỐT NGHIỆP VÀ ĐIỀU KIỆN
    ca("TN-01", "tot_nghiep", "kb", "tot_nghiep", hs("sv_tltn", ["diem", "CT182", 40]), "TRUE",
       "Hồ sơ TLTN đủ 161 TC; CT182 đạt D (4,0) vẫn tích lũy, ĐTBCTL vẫn ≥ 2.", N_TN + "; " + N_DIEM,
       oracle={"tc_tich_luy": "161", "dtbctl_ge_2": True}),
    ca("TN-02", "tot_nghiep", "kb", "tot_nghiep", hs("sv_5hp", ["diem", "CT478", 45]), "TRUE",
       "Tích lũy 15 TC thay LVTN (5 HP); CT478 đạt D (4,5) vẫn tính.", N_TN + "; " + N_31K3, oracle={"tc_tich_luy": "161"}),
    ca("TN-03", "tot_nghiep", "kb", "tot_nghiep", hs("sv_lvtn", ["diem", "CT180", 40]), "TRUE",
       "CT180 đạt D (4,0) vẫn tích lũy; ĐTBCTL vẫn ≥ 2.", N_DIEM + "; " + N_TN, oracle={"dtbctl_ge_2": True}),
    ca("TN-04", "tot_nghiep", "kb", "tot_nghiep", hs("sv_lvtn", ["diem", "CT180", 39]), "FALSE",
       "CT180 (bắt buộc) 3,9 = F → chưa tích lũy.", N_DIEM + "; " + N_TN),
    ca("TN-05", "tot_nghiep", "kb", "tot_nghiep", hs("sv_lvtn", ["diem", "QP012", 30]), "FALSE",
       "QP012 bị F → chưa hoàn thành HP điều kiện GDQP&AN.", N_QP),
    ca("TN-06", "tot_nghiep", "kb", "dk_gdqp", hs("sv_lvtn", ["diem", "QP010E", 40], ["diem", "QP011E", 60], ["diem", "QP012", 50],
       ["diem", "QP013", 50]), "TRUE", "TB GDQP đúng 5,0 (biên).", N_QP, oracle={"gdqp_tb": "5"}),
    ca("TN-07", "tot_nghiep", "kb", "dk_gdqp", hs("sv_lvtn", ["diem", "QP010E", 40], ["diem", "QP011E", 50], ["diem", "QP012", 50],
       ["diem", "QP013", 50]), "FALSE", "TB GDQP 4,75 < 5,0.", N_QP, oracle={"gdqp_tb": "19/4"}),
    ca("TN-08", "tot_nghiep", "kb", "thieu_dk(thoi_gian)", hs("sv_lvtn", ["dat", "da_hoc_nam2", 18]), "FALSE",
       "Đúng 9 năm = 27 HK, chưa vượt.", N_TG, oracle={"tran_hk": "27", "qua_han": False}),
    ca("TN-09", "tot_nghiep", "kb", "thieu_dk(thoi_gian)", hs("sv_lvtn", ["dat", "da_hoc_nam2", 19]), "TRUE",
       "9,5 năm > 9 năm.", N_TG, oracle={"qua_han": True}),
    ca("TN-10", "tot_nghiep", "kb", "thieu_dk(thoi_gian)", hs("sv_lvtn", ["dat", "da_hoc_nam2", 18], ["dat", "tc_cong_nhan", 9]),
       "TRUE", "9 TC công nhận → giảm 1 HK (26 HK); đã học 27 HK.", N_TG, oracle={"tran_hk": "26", "qua_han": True}),
    ca("TN-11", "tot_nghiep", "kb", "thieu_dk(thoi_gian)", hs("sv_lvtn", ["dat", "da_hoc_nam2", 16], ["dat", "tc_cong_nhan", 18]),
       "FALSE", "18 TC công nhận → 25 HK; đã học 8 năm = 24 HK. KHÔNG CHẤM: Đ5 có hai cách đọc — câu chính giảm 'thời gian theo "
       "kế hoạch học tập chuẩn' (4,5 năm − 2 HK → trần khác) còn ví dụ giảm trần 9 năm; hai cách cho gold khác nhau (soát độc lập).",
       N_TG, oracle={"tran_hk": "25", "qua_han": False}, cham_diem=False),
    ca("TN-12", "tot_nghiep", "kb", "thieu_dk(thoi_gian)", hs("sv_lvtn", ["dat", "da_hoc_nam2", 18], ["dat", "tc_cong_nhan", 8]),
       "FALSE", "8 TC < 9 → không giảm; 27 HK đúng trần.", N_TG, oracle={"tran_hk": "27", "qua_han": False}),
    ca("TN-13", "tot_nghiep", "kb", "dk_tin_chi", hs("sv_lvtn", ["xoa_diem", "KL001E"]), "FALSE",
       "159 TC < 161.", N_CTDT, oracle={"tc_tich_luy": "159"}),
    ca("TN-14", "tot_nghiep", "kb", "dk_tin_chi", hs("sv_lvtn", ["diem", "CT211", 70]), "TRUE",
       "164 TC (học dư CT211) ≥ 161.", N_CTDT, oracle={"tc_tich_luy": "164"}),
    ca("TN-15", "tot_nghiep", "kb", "tot_nghiep", hs("sv_lvtn", ["xoa_diem", "CT484"]), "FALSE",
       "Nhóm chuyên ngành còn 3/6 TC (chỉ CT449).", N_CTDT),
    ca("TN-16", "tot_nghiep", "kb", "tot_nghiep", hs("sv_lvtn", ["dat", "xac_nhan_ky_luat_sach", None], ["xoa_diem", "CT484"]),
       "FALSE", "Thiếu nhóm chuyên ngành → không tốt nghiệp bất kể kỷ luật (dữ kiện thiếu không quyết định).", N_CTDT + "; " + N_KL),
    ca("TN-17", "tot_nghiep", "kb", "tot_nghiep", hs("sv_lvtn", ["diem_dac_biet", "CT484", "W"]), "FALSE",
       "CT484 điểm W → không tích lũy → nhóm chuyên ngành thiếu.", "QĐ3266 Điều 22 khoản 5 điểm c, tr.14; " + N_CTDT),
    ca("TN-18", "tot_nghiep", "kb", "tot_nghiep", hs("sv_5hp", ["khong_chac", "CT210", [30, 80]]), "UNKNOWN",
       "Nhóm tốt nghiệp đúng 15 TC — CT210 F thì thiếu.", N_DIEM + "; " + N_31K3, can_hoi=['g10("CT210")']),
    ca("TN-19", "tot_nghiep", "kb", "tot_nghiep", hs("sv_5hp", ["khong_chac", "CT210", [70, 80]]), "TRUE",
       "CT210 7,0 hay 8,0 đều đạt → không cần hỏi.", N_DIEM),
    ca("TN-20", "tot_nghiep", "kb", "tot_nghiep", hs("sv_lvtn", ["khong_chac", "QP013", [30, 70]]), "UNKNOWN",
       "QP013 F thì chưa hoàn thành GDQP.", N_QP, can_hoi=['g10("QP013")']),
    ca("TN-21", "tot_nghiep", "kb", "tot_nghiep", hs("sv_lvtn", ["dat", "da_hoc_nam2", 20]), "FALSE",
       "10 năm > 9 năm tối đa.", N_TG, oracle={"qua_han": True}),
    ca("TN-22", "tot_nghiep", "kb", "dk_dtbctl", hs("sv_lvtn", ["tat_ca_khong_dk", 50]), "FALSE",
       "Mọi HP D+ (1,5) → ĐTBCTL 1,50.", N_TL, oracle={"dtbctl": "3/2"}),
    ca("TN-23", "tot_nghiep", "kb", "dk_dtbctl", hs("sv_lvtn", ["tat_ca_khong_dk", 65]), "TRUE",
       "Mọi HP C+ (2,5) → ĐTBCTL 2,50.", N_TL, oracle={"dtbctl": "5/2"}),
    ca("TN-24", "tot_nghiep", "kb", "dk_dtbctl", hs("sv_lvtn", *nang_diem("sv_lvtn", 3, 65, 55), ["diem", "CT484", 20]), "TRUE",
       "Mọi HP C (2,0) trừ 3 TC C+; CT484 F bị LOẠI khỏi ĐTBCTL → ĐTBCTL > 2 (bẫy tính cả F).", N_TL,
       oracle={"dtbctl_ge_2": True}),

    # ---------------------------------------------------------------- NHÓM TỰ CHỌN
    ca("NH-01", "nhom", "kb", "dat_nhom(g_chuyen_nganh)", hs("sv_lvtn", ["xoa_diem", "CT484"], ["diem", "CT211", 80]), "FALSE",
       "CT449 (cn2) + CT211 (cn1) — trộn hai nhánh, không nhánh nào đủ 6 TC.", N_CTDT),
    ca("NH-02", "nhom", "kb", "dat_nhom(g_chuyen_nganh)", hs("sv_lvtn", ["xoa_diem", ["CT449", "CT484"]], ["diem", "CT211", 80],
       ["diem", "CT297", 70]), "TRUE", "CT211 + CT297 = nhánh cn1 đủ 6 TC.", N_CTDT),
    ca("NH-03", "nhom", "kb", "dat_nhom(g_ngoai_ngu)", hs("sv_lvtn", ["xoa_diem", ["XH023", "XH024", "XH025"]],
       ["diem", "FL001", 80], ["diem", "FL002", 75], ["diem", "FL003", 70]), "TRUE", "Pháp văn 4+3+3 = 10 TC.", N_CTDT),
    ca("NH-04", "nhom", "kb", "dat_nhom(g_ngoai_ngu)", hs("sv_lvtn", ["xoa_diem", "XH025"], ["diem", "FL003", 80]), "FALSE",
       "AV 7 TC + PV 3 TC — không cộng dồn giữa hai nhánh.", N_CTDT),
    ca("NH-05", "nhom", "kb", "dat_nhom(g_gdtc)", hs("sv_lvtn", ["xoa_diem", "TC100"]), "FALSE", "Chưa có GDTC.", N_CTDT),
    ca("NH-06", "nhom", "kb", "dat_nhom(g_xa_hoi)", hs("sv_lvtn", ["xoa_diem", "ML007"]), "FALSE",
       "Nhóm xã hội cần 2 TC, không còn HP nào.", N_CTDT),
    ca("NH-07", "nhom", "kb", "dat_nhom(g_tot_nghiep)", hs("sv_lvtn", ["xoa_diem", "CT550E"], ["diem", "CT501E", 70],
       ["diem", "CT478", 70], ["diem", "CT283", 70], ["diem", "CT233", 70]), "TRUE", "TLTN 6 + 3×3 = 15 TC.", N_CTDT + "; " + N_31K3),
    ca("NH-08", "nhom", "kb", "dat_nhom(g_tot_nghiep)", hs("sv_lvtn", ["xoa_diem", "CT550E"], ["diem", "CT501E", 70],
       ["diem", "CT478", 70], ["diem", "CT283", 70]), "FALSE", "TLTN 6 + 2×3 = 12 TC < 15.", N_CTDT),

    # ---------------------------------------------------------------- MIỄN VÀ THAY THẾ
    ca("MT-01", "mien_thay_the", "kb", 'du_dk_xin_mien("XH024")', hs("sv_lvtn", ["chung_chi", "toeic", 450]), "TRUE",
       "TOEIC 450 = bậc 3 (biên).", N_CC),
    ca("MT-02", "mien_thay_the", "kb", 'du_dk_xin_mien("XH024")', hs("sv_lvtn", ["chung_chi", "toeic", 445]), "FALSE",
       "TOEIC 445 < 450.", N_CC),
    ca("MT-03", "mien_thay_the", "kb", 'du_dk_xin_mien("XH025")', hs("sv_lvtn", ["chung_chi", "ielts", 4.5]), "TRUE",
       "IELTS 4.5 = bậc 3 (biên).", N_CC),
    ca("MT-04", "mien_thay_the", "kb", 'du_dk_xin_mien("XH025")', hs("sv_lvtn", ["chung_chi", "ielts", 4.0]), "FALSE",
       "IELTS 4.0 < 4.5 (bậc 2).", N_CC),
    ca("MT-05", "mien_thay_the", "kb", 'du_dk_xin_mien("XH025")', hs("sv_lvtn", ["chung_chi", "ctu_abc", 3]), "TRUE",
       "Chứng chỉ CTU bậc 3.", N_CC),
    ca("MT-06", "mien_thay_the", "kb", 'du_dk_xin_mien("XH025")', hs("sv_lvtn", ["chung_chi", "ctu_abc", 2]), "FALSE",
       "Chứng chỉ CTU bậc 2 < bậc 3 (K45 trở về sau).", N_CC),
    ca("MT-07", "mien_thay_the", "kb", 'du_dk_xin_mien("FL002")', hs("sv_lvtn", ["chung_chi", "ielts", 7.0]), "FALSE",
       "IELTS là tiếng Anh — không xét miễn Pháp văn.", N_CC_NN),
    ca("MT-08", "mien_thay_the", "kb", 'passed("ML016")', hs("sv_lvtn", ["xoa_diem", ["ML016", "ML018"]], ML010), "FALSE",
       "ML010 đạt chỉ cho ĐỦ ĐIỀU KIỆN xét công nhận ML016; chưa có quyết định → chưa đạt. [Sửa trước đóng băng: bản đầu TRUE.]",
       N_ML_QD),
    ca("MT-09", "mien_thay_the", "kb", 'passed("ML018")', hs("sv_lvtn", ["xoa_diem", ["ML016", "ML018"]], ML010), "FALSE",
       "Như MT-08 với ML018 (một → nhiều). [Sửa trước đóng băng: bản đầu TRUE.]", N_ML_QD),
    ca("MT-10", "mien_thay_the", "kb", 'passed("ML021")',
       hs("sv_lvtn", ["xoa_diem", "ML021"], ["diem_tho", "ML006", {"credits": 2, "thang10": 30, "letter": "F", "status": "failed"}]),
       "FALSE", "ML006 bị F → không có gì để công nhận ML021.", N_ML),
    ca("MT-11", "mien_thay_the", "kb", 'passed("ML019")',
       hs("sv_lvtn", ["xoa_diem", "ML019"], ["diem_tho", "ML011", {"credits": 3, "thang10": 40, "letter": "D", "status": "passed"}]),
       "FALSE", "ML011 đạt D (4,0) → đủ điều kiện XÉT công nhận ML019, chưa có quyết định → chưa đạt. [Sửa trước đóng băng: bản đầu TRUE.]",
       N_ML_QD + "; " + N_DIEM),
    ca("MT-12", "mien_thay_the", "kb", 'passed("XH024")', hs("sv_lvtn", ["xoa_diem", "XH024"], ["chung_chi", "ielts", 6.5]),
       "FALSE", "Đủ điều kiện XIN miễn nhưng chưa có quyết định miễn → chưa đạt (QD-11).",
       "QĐ5339 Điều 2 khoản 6, tr.4 (R-M16, QD-11: miễn phải có đơn và quyết định)"),

    # ---------------------------------------------------------------- HẠNG TỐT NGHIỆP
    ca("HG-01", "hang", "kb", "hang_cuoi(kha)", hs("sv_lvtn"), "TRUE", "ĐTBCTL 439/140 ≈ 3,14 → khá.", N_HANG,
       oracle={"dtbctl": "439/140"}, cau_hoi="Nếu tốt nghiệp, em xếp hạng gì?"),
    ca("HG-02", "hang", "kb", "hang_cuoi(gioi)", hs("sv_lvtn", *nang_diem("sv_lvtn", 77, 90, 70)), "TRUE",
       "ĐTBCTL đúng 3,55 → giỏi (3,20–3,59). [Ca này nảy ra khi đọc code KB — gold theo câu chữ Đ34.]", N_HANG,
       oracle={"dtbctl": "71/20"}, cau_hoi="Nếu tốt nghiệp, em có đạt loại giỏi không?"),
    ca("HG-03", "hang", "kb", "hang_cuoi(xuat_sac)", hs("sv_lvtn", *nang_diem("sv_lvtn", 84, 90, 70)), "TRUE",
       "ĐTBCTL đúng 3,60 → xuất sắc (biên).", N_HANG, oracle={"dtbctl": "18/5"}, cau_hoi="Nếu tốt nghiệp, em có đạt loại xuất sắc không?"),
    ca("HG-04", "hang", "kb", "hang_cuoi(gioi)", hs("sv_lvtn", *nang_diem("sv_lvtn", 28, 90, 70)), "TRUE",
       "ĐTBCTL đúng 3,20 → giỏi (biên dưới).", N_HANG, oracle={"dtbctl": "16/5"}, cau_hoi="Nếu tốt nghiệp, em có đạt loại giỏi không?"),
    ca("HG-05", "hang", "kb", "hang_cuoi(kha)", hs("sv_lvtn", *nang_diem("sv_lvtn", 27, 90, 70)), "TRUE",
       "ĐTBCTL 447/140 ≈ 3,19 → khá.", N_HANG, oracle={"dtbctl": "447/140"}, cau_hoi="Nếu tốt nghiệp, em xếp hạng gì?"),
    ca("HG-06", "hang", "kb", "hang_cuoi(kha)", hs("sv_lvtn", ["tat_ca_khong_dk", 65]), "TRUE",
       "ĐTBCTL đúng 2,50 → khá (biên dưới).", N_HANG, oracle={"dtbctl": "5/2"}, cau_hoi="Nếu tốt nghiệp, em xếp hạng gì?"),
    ca("HG-07", "hang", "kb", "hang_cuoi(trung_binh)", hs("sv_lvtn", *nang_diem("sv_lvtn", 137, 65, 55)), "TRUE",
       "ĐTBCTL 697/280 ≈ 2,489 → trung bình.", N_HANG, oracle={"dtbctl": "697/280"}, cau_hoi="Nếu tốt nghiệp, em xếp hạng gì?"),
    ca("HG-08", "hang", "kb", "hang_cuoi(gioi)", hs("sv_lvtn", *nang_diem("sv_lvtn", 70, 80, 70)), "TRUE",
       "ĐTBCTL đúng 3,25 (B+ 70 TC, B 70 TC) → giỏi.", N_HANG, oracle={"dtbctl": "13/4"}, cau_hoi="Nếu tốt nghiệp, em có đạt loại giỏi không?"),

    # ---------------------------------------------------------------- CÂU TỰ NHIÊN qua prototype (đầu-cuối)
    ca("NL-01", "cau_tu_nhien", "nl", "nl", hs("sv_lvtn", ["xoa_diem", ["CT182", "CT180"]]), "TRUE",
       "Như DK-02 nhưng qua parser.", N_TQ + "; " + N_SH, cau_hoi="Kỳ này em đăng ký CT182 được không ạ?"),
    ca("NL-02", "cau_tu_nhien", "nl", "nl", hs("sv_lvtn", ["xoa_diem", ["CT182", "CT180", "CT177"]]), "FALSE",
       "Như DK-03 nhưng qua parser.", N_SH, cau_hoi="Cho em hỏi em học CT182 được chưa?"),
    ca("NL-03", "cau_tu_nhien", "nl", "nl", hs("sv_lvtn", ["xoa_diem", "CT550E"]), "TRUE",
       "146 TC ≥ 120.", N_LV, cau_hoi="Em đủ điều kiện làm luận văn chưa ạ?"),
    ca("NL-04", "cau_tu_nhien", "nl", "nl", hs("sv_tltn"), "TRUE", "Như TN-01.", N_TN,
       cau_hoi="Cho em hỏi em đủ điều kiện tốt nghiệp chưa ạ?"),
    ca("NL-05", "cau_tu_nhien", "nl", "nl", hs("sv_lvtn"), "UNKNOWN", "Câu phản thực tế — RQ3 chưa hỗ trợ.", N_TK,
       cau_hoi="Nếu em rớt CT296 thì em tốt nghiệp trễ mấy học kỳ?"),
    ca("NL-06", "cau_tu_nhien", "nl", "nl", hs("sv_lvtn"), "UNKNOWN", "Học phí do Hiệu trưởng quyết định — KB không có.",
       "QĐ3266 Điều 10 khoản 1, tr.6; " + N_TK, cau_hoi="Học phí học kỳ này của em là bao nhiêu?"),
    ca("NL-07", "cau_tu_nhien", "nl", "nl", hs("sv_lvtn"), "UNKNOWN",
       "Học bổng cần ĐTBCHK + điểm rèn luyện học kỳ trước — hồ sơ không có.", N_TK,
       cau_hoi="Em có được xét học bổng khuyến khích học tập không?"),
    ca("NL-08", "cau_tu_nhien", "nl", "nl", hs("sv_lvtn"), "UNKNOWN",
       "Cảnh báo học vụ xét theo ĐTBCHK từng học kỳ — hồ sơ không có điểm theo học kỳ.", "QĐ3266 Điều 18, tr.10–11; " + N_TK,
       cau_hoi="Em có bị cảnh báo học vụ không?"),
    ca("NL-09", "cau_tu_nhien", "nl", "nl", hs("sv_lvtn"), "FALSE", "ĐTBCTL ≈ 3,14 < 3,20.", N_HANG,
       cau_hoi="ĐTBCTL của em có đủ xếp loại giỏi khi tốt nghiệp không?"),
    ca("NL-10", "cau_tu_nhien", "nl", "nl", hs("sv_lvtn"), "UNKNOWN", "Chuyển ngành — ngoài phạm vi KB.", N_TK,
       cau_hoi="Em muốn chuyển ngành thì cần điều kiện gì?"),
    ca("NL-11", "cau_tu_nhien", "nl", "nl", hs("sv_lvtn", ["xoa_diem", "CT466E"]), "TRUE", "158 TC ≥ 80.", N_TCTQ,
       cau_hoi="Kỳ này em đăng ký niên luận CT466E được không?"),
    ca("NL-12", "cau_tu_nhien", "nl", "nl", hs("sv_lvtn", ["xoa_diem", "CT484"]), "FALSE", "Như TN-15.", N_CTDT,
       cau_hoi="Em ra trường được chưa ạ?"),
]

# =================================================================== OCR-NOISE v1
# 10 kịch bản (hồ sơ, HP quyết định, claim) × 4 mức nhiễu. Hồ sơ thật đều đạt claim (sự thật TRUE).
#   M1 nhiễu nhẹ, KHÔNG quyết định: confidence cột điểm thi 0,4 nhưng T.Hợp và chữ đọc rõ → TRUE
#   M2 mất kiểm chéo: không đọc được ĐTBCHK của học kỳ chứa HP (không có lỗi nào khác) → TRUE
#   M3 sai có thể phát hiện: chữ của HP đọc thành F trong khi T.Hợp đạt → mâu thuẫn → UNKNOWN
#   M4 mất dòng: dòng của HP biến mất, tổng TC học kỳ lệch → có HP bị ẩn → UNKNOWN
KB_OCR = [("sv_lvtn", "CT180", "tot_nghiep"), ("sv_lvtn", "CT296", "dk_bat_buoc"), ("sv_tltn", "CT501E", "tot_nghiep"),
          ("sv_5hp", "CT478", "tot_nghiep"), ("sv_lvtn", "ML019", 'passed("ML019")'), ("sv_lvtn", "CT484", "dat_nhom(g_chuyen_nganh)"),
          ("sv_lvtn", "ML016", 'passed("ML016")'), ("sv_lvtn", "CT173", 'passed("CT173")'), ("sv_tltn", "CT182", "tot_nghiep"),
          ("sv_5hp", "XH024", "dk_hp_dieu_kien")]


def hk_cua(goc, ma):
    doc = dau_vao.doc_tu_ho_so(dau_vao.ho_so_goc(goc))
    return next(i for i, hk in enumerate(doc["hoc_ky"]) for d in hk["dong"] if d["ma"] == ma)


ON = []
for i, (goc, ma, claim) in enumerate(KB_OCR, 1):
    for muc, bd, gold, ly in (
            ("M1", [["conf", ma, "thi", 0.4]], "TRUE", f"Cột điểm thi của {ma} đọc kém nhưng T.Hợp và điểm chữ rõ, khớp nhau."),
            ("M2", [["doi_dtbchk", hk_cua(goc, ma), None]], "TRUE", "ĐTBCHK không đọc được — mất kiểm chéo nhưng không có lỗi nào."),
            ("M3", [["doi_chu", ma, "F"]], "UNKNOWN", f"Điểm chữ {ma} đọc thành F trái với T.Hợp → điểm {ma} không chắc."),
            ("M4", [["mat_dong", ma]], "UNKNOWN", f"Dòng {ma} mất, tổng TC học kỳ lệch → có HP bị ẩn.")):
        ON.append(ca(f"ON-{i:02d}{muc}", muc, "ocr", claim, ocr(goc, *bd), gold, ly,
                     N_OCR + ("" if gold == "UNKNOWN" else "; " + N_TN), su_that="TRUE",
                     cau_hoi=Q.get(claim) or f"Bảng điểm OCR đính kèm — {claim}?"))


def chia(cases, seed=20):
    rnd = random.Random(seed)
    theo = {}
    for c in cases:
        theo.setdefault(c["nhom"], []).append(c)
    for ds in theo.values():
        rnd.shuffle(ds)
        for k, c in enumerate(ds):
            c["split"] = "dev" if k % 2 == 0 else "test"
    return cases


def main():
    gt, on = chia(GT), chia(ON)
    (HERE / "gtruth.json").write_text(json.dumps({"meta": {"ten": "CPA² G-Truth v1 (Tuần 20)", "seed": 20,
        "ghi_chu": "Gold viết tay trong build_benchmark.py, đóng băng (gold_dong_bang.json) TRƯỚC lần chạy đầu."},
        "cases": gt}, ensure_ascii=False, indent=1), encoding="utf-8")
    (HERE / "ocr_noise.json").write_text(json.dumps({"meta": {"ten": "CPA² OCR-Noise v1 (Tuần 20)", "seed": 20},
        "cases": on}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"G-Truth {len(gt)} ca · OCR-Noise {len(on)} ca")
    if "--dong-bang" in sys.argv:
        from validate_benchmark import hash_gold, hash_nguon
        (HERE / "gold_dong_bang.json").write_text(json.dumps({"gtruth": hash_gold(gt), "ocr_noise": hash_gold(on),
            "nguon_du_lieu": hash_nguon(),
            "ngay": "2026-10-18", "ghi_chu": "Đóng băng TRƯỚC lần chạy CPA² đầu tiên. Sai sót phát hiện sau → errata, KHÔNG sửa gold."},
            ensure_ascii=False, indent=1), encoding="utf-8")
        print("đã ghi gold_dong_bang.json")


if __name__ == "__main__":
    main()
