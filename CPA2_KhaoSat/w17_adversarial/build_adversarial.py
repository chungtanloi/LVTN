"""
build_adversarial.py — sinh Adversarial set v1 (CPA2, Tuần 17) → adversarial_set.json

GOLD ĐƯỢC VIẾT TAY ở đây, kèm lý do + con trỏ nguồn, TRƯỚC khi chạy CPA² (commit riêng). Không ca nào
lấy gold từ kết quả của hệ thống. Tiền đề số học (ĐTBCTL, TC, TB GDQP, trần thời gian) ghi ở trường
"oracle" và được validate_adversarial.py kiểm lại bằng oracle.py (Python thuần, không clingo).

  gold     câu trả lời đúng với THÔNG TIN CÓ TRONG ĐẦU VÀO (TRUE/FALSE/UNKNOWN)
  su_that  tình trạng thật của sinh viên phía sau (chỉ ghi khi biết và khác ý nghĩa với gold, vd ca OCR)
  khong_phat_hien_duoc  lỗi OCR nhất quán mà mọi kiểm chéo đều không thấy — gold = sự thật; dùng để đo rủi ro
  can_hoi  với gold UNKNOWN: dữ kiện quyết định mà hệ thống nên hỏi lại
  cham_diem=False: ca phụ thuộc diễn giải chưa chốt / ca mức ảnh phụ thuộc môi trường — không tính vào số đo

Chia dev/test: phân tầng theo nhóm, xáo trộn với seed 17, xen kẽ. Chỉ tinh chỉnh trên dev.

Chạy:  python build_adversarial.py
"""
import json, random
from pathlib import Path

HERE = Path(__file__).parent

Q = {
    "tot_nghiep": "Em đã đủ điều kiện xét tốt nghiệp chưa?",
    "dk_dtbctl": "ĐTBCTL của em đã đạt mức tối thiểu để xét tốt nghiệp (2,00) chưa?",
    "dk_tin_chi": "Em đã tích lũy đủ số tín chỉ tối thiểu của CTĐT (161 TC) chưa?",
    'du_dk_tc("CT550E")': "Em đã đủ 120 tín chỉ tích lũy để đăng ký Luận văn tốt nghiệp (CT550E) chưa?",
    'passed("CT177")': "Học phần CT177 của em có được tính là đạt (được tích lũy) không?",
    'passed("XH023")': "Học phần Anh văn căn bản 1 (XH023) của em đã được tính là đạt/miễn chưa?",
    'du_dk_xin_mien("XH023")': "Với chứng chỉ ngoại ngữ hiện có, em có đủ điều kiện nộp đơn xin miễn Anh văn căn bản 1 (XH023) không?",
    'du_dk_xin_mien("FL001")': "Với chứng chỉ ngoại ngữ hiện có, em có đủ điều kiện nộp đơn xin miễn Pháp văn căn bản 1 (FL001) không?",
    "thieu_dk(thoi_gian)": "Em có bị quá thời gian học tập tối đa không?",
}

# nguồn hay dùng
N_TN = "QĐ3266 Điều 32 khoản 1"
N_KL = "QĐ3266 Điều 32 khoản 1 điểm c (R-F03)"
N_TG = "QĐ3266 Điều 5, tr.4–5 (R-E01, R-E02)"
N_DIEM = "QĐ3266 Điều 22 khoản 2–3, tr.14 (bảng quy đổi; tích lũy từ D)"
N_TL = "QĐ3266 Điều 24 (ĐTBCTL không gồm F và HP điều kiện)"
N_QP = "QĐ3266 Điều 32 khoản 1 điểm b (TB GDQP&AN ≥ 5,0)"
N_CC = "QĐ5339 Điều 3 khoản 5 điểm a + Phụ lục 1 (K45 trở về sau: bậc 3 — IELTS 4.5 / TOEIC 450 / TOEFL iBT 45)"
N_MIEN = "QĐ5339 Điều 2 khoản 6 (R-M16, QD-11: miễn phải có đơn và quyết định)"
N_120 = "CTĐT CNTT K49 dòng 70 (CT550E: tiên quyết ≥ 120 TC tích lũy) + QĐ3266 Điều 24 k1"
N_CTDT = "CTĐT CNTT K49 (QĐ2423) — khung 161 TC, các nhóm tự chọn"
N_TK = "Nguyên tắc thiết kế CPA² (Tuần 1): không kết luận từ dữ kiện mâu thuẫn — KHÔNG phải nội dung quy chế"
N_OCR = "Tuần 15 (OCR): không chắc ≠ sai — học phần/học kỳ đọc không chắc thì không được kết luận"

C2 = ["tat_ca_khong_dk", 60]       # mọi HP không phải điều kiện = 6,0 (C, 2,0) → ĐTBCTL đúng 2,00
QP = ["QP010E", "QP011E", "QP012", "QP013"]
BO_120 = ["CT550E", "CT101", "CT172", "CT200", "TN002", "TN012", "CT100", "CT190", "KL001E"]   # 146 − 26 = 120
BO_119 = ["CT550E", "CT101", "CT172", "CT200", "TN002", "TN012", "CT100", "CT177", "KL001E"]   # 146 − 27 = 119
RUNG_F = ["CT211", "CT219", "CT279", "CT297", "CT312", "CT522"]                                  # 6 HP tự chọn 3 TC
BO_AV = ["XH023", "XH024", "XH025"]


def hs(goc, *bd):
    return {"loai": "ho_so", "goc": goc, "bien_doi": list(bd)}


def ocr(goc, *bd, that=(), khai_bao_bo=()):
    return {"loai": "ocr_doc", "goc": goc, "that": list(that), "bien_doi": list(bd), "khai_bao_bo": list(khai_bao_bo)}


def ca(id_, nhom, claim, dau_vao, gold, ly_do, nguon, **kw):
    d = {"id": id_, "nhom": nhom, "claim": claim, "cau_hoi": kw.pop("cau_hoi", Q.get(claim)),
         "dau_vao": dau_vao, "gold": gold, "ly_do": ly_do, "nguon": nguon, "cham_diem": True}
    d.update(kw)
    return d


CASES = [
    # ======================= THIẾU DỮ LIỆU =======================
    ca("TD-01", "thieu_du_lieu", "tot_nghiep", hs("sv_lvtn", ["dat", "xac_nhan_ky_luat_sach", None]), "UNKNOWN",
       "Đủ học vụ nhưng chưa biết tình trạng kỷ luật — điều kiện c không kiểm được từ bảng điểm.", N_KL,
       can_hoi=["xac_nhan_ky_luat_sach"]),
    ca("TD-02", "thieu_du_lieu", "tot_nghiep", hs("sv_lvtn", ["xoa", "xac_nhan_ky_luat_sach"]), "UNKNOWN",
       "Như TD-01 nhưng hồ sơ không có hẳn trường kỷ luật.", N_KL, can_hoi=["xac_nhan_ky_luat_sach"]),
    ca("TD-03", "thieu_du_lieu", "tot_nghiep", hs("sv_lvtn", ["dat", "xac_nhan_ky_luat_sach", False]), "FALSE",
       "Đã khai báo KHÔNG có xác nhận kỷ luật sạch → không đạt điều kiện c (khác với 'chưa biết').", N_KL),
    ca("TD-04", "thieu_du_lieu", "tot_nghiep", hs("sv_lvtn", ["xoa", "da_hoc_nam2"]), "UNKNOWN",
       "Chưa biết đã học bao lâu → không kiểm được thời gian tối đa (Đ5 là điều kiện hoàn thành CTĐT, P16-2).",
       N_TG, can_hoi=["qua_thoi_gian_toi_da"]),
    ca("TD-05", "thieu_du_lieu", "tot_nghiep", hs("sv_lvtn", ["xoa", "da_hoc_nam2"], ["dat", "xac_nhan_ky_luat_sach", None]),
       "UNKNOWN", "Thiếu cả kỷ luật và thời gian đã học.", N_KL + "; " + N_TG,
       can_hoi=["xac_nhan_ky_luat_sach", "qua_thoi_gian_toi_da"]),
    ca("TD-06", "thieu_du_lieu", "tot_nghiep", hs("sv_tron_ngoai_ngu", ["dat", "xac_nhan_ky_luat_sach", None]), "FALSE",
       "Đã thiếu nhóm ngoại ngữ (trộn AV/PV) nên dù kỷ luật thế nào cũng không tốt nghiệp — dữ kiện thiếu không quyết định.",
       N_CTDT + " ('10 AV hoặc PV', CQ-02); " + N_TN),
    ca("TD-07", "thieu_du_lieu", "tot_nghiep", hs("sv_tron_ngoai_ngu", ["xoa", "da_hoc_nam2"]), "FALSE",
       "Như TD-06, dữ kiện thiếu là thời gian.", N_CTDT + "; " + N_TN),
    ca("TD-08", "thieu_du_lieu", "tot_nghiep", hs("sv_lvtn", ["xoa_diem", "CT177"]), "FALSE",
       "BẪY NGƯỢC: học phần bắt buộc CHƯA HỌC (không có trên bảng điểm) là thiếu học phần, không phải thiếu dữ liệu.",
       N_TN + " điểm a (tích lũy đủ các học phần)", oracle={"tc_tich_luy": 158}),
    ca("TD-09", "thieu_du_lieu", "tot_nghiep", hs("sv_lvtn", ["xoa_diem", "CT550E"]), "FALSE",
       "Chưa có học phần nào của nhóm tốt nghiệp (0/15 TC) và chỉ 146 TC.", N_CTDT + "; " + N_TN,
       oracle={"tc_tich_luy": 146}),
    ca("TD-10", "thieu_du_lieu", "tot_nghiep", hs("sv_lvtn", ["diem_dac_biet", "CT550E", "I"]), "FALSE",
       "LVTN đang mang điểm I (chưa thi kết thúc) → chưa tích lũy tại thời điểm hỏi. QD-05 chỉ mở về việc điểm I "
       "sau này thành gì, không làm cho học phần đã đạt.", "QĐ3266 Điều 22 khoản 3 và khoản 5 điểm b"),
    ca("TD-11", "thieu_du_lieu", "tot_nghiep", hs("sv_lvtn", ["khong_chac", "CT550E", [75, 30]]), "UNKNOWN",
       "Điểm LVTN chưa rõ là 7,5 hay 3,0: đạt → tốt nghiệp, F → không.", N_DIEM, can_hoi=['g10("CT550E")'],
       su_that="TRUE"),
    ca("TD-12", "thieu_du_lieu", "tot_nghiep", hs("sv_lvtn", ["khong_chac", "CT484", [70, 75]]), "TRUE",
       "Điểm CT484 chưa rõ nhưng cả hai giá trị (7,0 / 7,5) đều đạt và ĐTBCTL vẫn ≥ 2 → không cần hỏi (bẫy từ chối thừa).",
       N_DIEM + "; " + N_TL),
    ca("TD-13", "thieu_du_lieu", "tot_nghiep", hs("sv_lvtn", ["khong_chac", "CT177", [0, 40, 100]]), "UNKNOWN",
       "Điểm CT177 (bắt buộc) chưa rõ trong F/D/A: F → thiếu học phần bắt buộc.", N_DIEM, can_hoi=['g10("CT177")'],
       su_that="TRUE"),
    ca("TD-14", "thieu_du_lieu", "tot_nghiep", hs("sv_mien_ielts", ["mien_chua_ro", "XH025"]), "UNKNOWN",
       "Đủ điều kiện xin miễn XH025 nhưng chưa biết đã có quyết định miễn chưa — có QĐ thì đủ 10 TC AV, chưa thì thiếu.",
       N_MIEN, can_hoi=['duoc_mien("XH025")'], su_that="TRUE"),
    ca("TD-15", "thieu_du_lieu", "tot_nghiep", hs("sv_mien_ielts", ["bo_mien", "XH025"], ["mien", "XH025", False]),
       "FALSE", "XH025 mới đủ điều kiện xin miễn (quyet_dinh=false) → chưa được miễn → nhóm ngoại ngữ thiếu 3 TC.",
       N_MIEN + "; " + N_CTDT),
    ca("TD-16", "thieu_du_lieu", "dk_dtbctl", hs("sv_lvtn", ["dat", "xac_nhan_ky_luat_sach", None]), "TRUE",
       "Thiếu dữ kiện kỷ luật không liên quan tới ĐTBCTL → vẫn trả lời được (bẫy từ chối thừa).", N_TL,
       oracle={"dtbctl_ge_2": True}),
    ca("TD-17", "thieu_du_lieu", 'du_dk_tc("CT550E")', hs("sv_lvtn", ["xoa", "da_hoc_nam2"]), "TRUE",
       "Thiếu thời gian đã học không ảnh hưởng điều kiện 120 TC để đăng ký LVTN.", N_120, oracle={"tc_tich_luy": 161}),

    # ======================= SÁT NGƯỠNG =======================
    ca("NG-01", "sat_nguong", "dk_dtbctl", hs("sv_lvtn", C2), "TRUE",
       "Mọi HP tính ĐTBCTL đều C (2,0) → ĐTBCTL đúng 2,00 = ngưỡng ('từ 2,00 trở lên').", N_TN + " điểm a; " + N_TL,
       oracle={"dtbctl": 2}),
    ca("NG-02", "sat_nguong", "tot_nghiep", hs("sv_lvtn", C2), "TRUE",
       "ĐTBCTL đúng 2,00, các điều kiện khác như sv_lvtn → tốt nghiệp.", N_TN, oracle={"dtbctl_ge_2": True}),
    ca("NG-03", "sat_nguong", "tot_nghiep", hs("sv_lvtn", C2, ["diem", "CT177", 55]), "TRUE",
       "CT177 = 5,5 vẫn là C (cận dưới) → ĐTBCTL vẫn 2,00.", N_DIEM, oracle={"dtbctl": 2}),
    ca("NG-04", "sat_nguong", "tot_nghiep", hs("sv_lvtn", C2, ["diem", "CT177", 54]), "FALSE",
       "CT177 = 5,4 là D+ (1,5) → ĐTBCTL < 2,00 dù mọi HP đều đạt.", N_DIEM + "; " + N_TN + " điểm a",
       oracle={"dtbctl_ge_2": False}),
    ca("NG-05", "sat_nguong", 'passed("CT177")', hs("sv_lvtn", ["diem", "CT177", 40]), "TRUE",
       "4,0 là D — cận dưới của mức tích lũy.", N_DIEM),
    ca("NG-06", "sat_nguong", 'passed("CT177")', hs("sv_lvtn", ["diem", "CT177", 39]), "FALSE",
       "3,9 < 4,0 → F, không tích lũy.", N_DIEM),
    ca("NG-07", "sat_nguong", "tot_nghiep", hs("sv_lvtn", ["diem", "CT177", 40]), "TRUE",
       "CT177 = 4,0 (D) vẫn tích lũy, ĐTBCTL vẫn ≥ 2.", N_DIEM + "; " + N_TN, oracle={"dtbctl_ge_2": True, "tc_tich_luy": 161}),
    ca("NG-08", "sat_nguong", "tot_nghiep", hs("sv_lvtn", ["diem", "CT177", 39]), "FALSE",
       "CT177 = 3,9 (F) → học phần bắt buộc chưa tích lũy.", N_DIEM + "; " + N_TN + " điểm a", oracle={"tc_tich_luy": 158}),
    ca("NG-09", "sat_nguong", "tot_nghiep", hs("sv_lvtn", *[["diem", m, 50] for m in QP]), "TRUE",
       "Bốn HP GDQP&AN đều 5,0 → TB đúng 5,0 = ngưỡng.", N_QP, oracle={"gdqp_tb": 5}),
    ca("NG-10", "sat_nguong", "tot_nghiep", hs("sv_lvtn", ["diem", "QP010E", 49], *[["diem", m, 50] for m in QP[1:]]),
       "FALSE", "TB GDQP&AN = 4,975 < 5,0 (mọi HP vẫn đạt D trở lên).", N_QP, oracle={"gdqp_tb": "199/40"}),
    ca("NG-11", "sat_nguong", 'du_dk_tc("CT550E")', hs("sv_lvtn", ["xoa_diem", BO_120]), "TRUE",
       "Đúng 120 TC tích lũy = ngưỡng tiên quyết của LVTN.", N_120, oracle={"tc_tich_luy": 120}),
    ca("NG-12", "sat_nguong", 'du_dk_tc("CT550E")', hs("sv_lvtn", ["xoa_diem", BO_119]), "FALSE",
       "119 TC < 120.", N_120, oracle={"tc_tich_luy": 119}),
    ca("NG-13", "sat_nguong", "dk_tin_chi", hs("sv_lvtn"), "TRUE",
       "Đúng 161 TC = tổng TC tối thiểu của CTĐT.", N_CTDT + "; " + N_TN + " điểm a", oracle={"tc_tich_luy": 161}),
    ca("NG-14", "sat_nguong", "dk_tin_chi", hs("sv_lvtn", ["xoa_diem", "ML007"]), "FALSE",
       "Bỏ ML007 (2 TC) → 159 < 161.", N_CTDT + "; " + N_TN + " điểm a", oracle={"tc_tich_luy": 159}),
    ca("NG-15", "sat_nguong", "tot_nghiep", hs("sv_lvtn", ["dat", "da_hoc_nam2", 18]), "TRUE",
       "CTĐT 4,5 năm → tối đa 9 năm = 18 nửa năm; đã học đúng 18 → chưa quá hạn.", N_TG,
       oracle={"tran_nam2": 18, "qua_han": False}),
    ca("NG-16", "sat_nguong", "tot_nghiep", hs("sv_lvtn", ["dat", "da_hoc_nam2", 19]), "FALSE",
       "19 nửa năm > 18 → quá thời gian tối đa để hoàn thành CTĐT.", N_TG, oracle={"qua_han": True}),
    ca("NG-17", "sat_nguong", "tot_nghiep", hs("sv_lvtn", ["dat", "da_hoc_nam2", 18], ["dat", "tc_cong_nhan", 9]), "FALSE",
       "K49: 9 TC được công nhận → trần giảm 1 HK còn 17 nửa năm; đã học 18 → quá hạn.", N_TG,
       oracle={"tran_nam2": 17, "qua_han": True}),
    ca("NG-18", "sat_nguong", "tot_nghiep", hs("sv_lvtn", ["dat", "da_hoc_nam2", 18], ["dat", "tc_cong_nhan", 8]), "TRUE",
       "8 TC công nhận < 9 → trần không giảm, vẫn 18.", N_TG, oracle={"tran_nam2": 18, "qua_han": False}),
    ca("NG-19", "sat_nguong", 'du_dk_xin_mien("XH023")', hs("sv_lvtn", ["chung_chi", "ielts", 4.5]), "TRUE",
       "IELTS 4.5 = bậc 3 = ngưỡng cho K45 trở về sau.", N_CC),
    ca("NG-20", "sat_nguong", 'du_dk_xin_mien("XH023")', hs("sv_lvtn", ["chung_chi", "ielts", 4.0]), "FALSE",
       "IELTS 4.0 chỉ bậc 2 < 3.", N_CC),
    ca("NG-21", "sat_nguong", 'du_dk_xin_mien("XH023")', hs("sv_lvtn", ["chung_chi", "toeic", 450]), "TRUE",
       "TOEIC 450 = ngưỡng bậc 3.", N_CC),
    ca("NG-22", "sat_nguong", 'du_dk_xin_mien("XH023")', hs("sv_lvtn", ["chung_chi", "toeic", 445]), "FALSE",
       "TOEIC 445 < 450.", N_CC),
    ca("NG-23", "sat_nguong", 'du_dk_xin_mien("XH023")', hs("sv_lvtn", ["chung_chi", "toefl_ibt", 45]), "TRUE",
       "TOEFL iBT 45 = ngưỡng bậc 3.", N_CC),
    ca("NG-24", "sat_nguong", 'du_dk_xin_mien("XH023")', hs("sv_lvtn", ["chung_chi", "toefl_ibt", 44]), "FALSE",
       "TOEFL iBT 44 < 45.", N_CC),

    # ======================= BẪY QUY CHẾ =======================
    ca("BQ-01", "bay_quy_che", "tot_nghiep", hs("sv_lvtn", ["xoa_diem", BO_AV], ["chung_chi", "ielts", 6.0]), "FALSE",
       "QD-11: có IELTS 6.0 nhưng CHƯA có quyết định miễn → nhóm ngoại ngữ chưa đạt (0/10 TC).", N_MIEN,
       oracle={"tc_tich_luy": 151}),
    ca("BQ-02", "bay_quy_che", 'du_dk_xin_mien("XH023")', hs("sv_lvtn", ["xoa_diem", BO_AV], ["chung_chi", "ielts", 6.0]),
       "TRUE", "Cùng hồ sơ BQ-01: ĐỦ ĐIỀU KIỆN XIN miễn (bậc 4 ≥ 3) — khác với đã được miễn.", N_CC),
    ca("BQ-03", "bay_quy_che", 'passed("XH023")', hs("sv_lvtn", ["xoa_diem", BO_AV], ["chung_chi", "ielts", 6.0]),
       "FALSE", "Cùng hồ sơ BQ-01: chưa học, chưa có QĐ miễn → chưa đạt.", N_MIEN),
    ca("BQ-04", "bay_quy_che", 'passed("CT177")', hs("sv_lvtn", ["diem", "CT177", 45]), "TRUE",
       "Bẫy B-01 ('đạt từ 5,0'): 4,5 là D → tích lũy được. Ngưỡng 5,0 chỉ cho điểm chuyển đổi (QD-09).",
       N_DIEM + "; QD-09"),
    ca("BQ-05", "bay_quy_che", "tot_nghiep", hs("sv_lvtn", C2, ["diem", "CT478", 30]), "TRUE",
       "Thêm một HP tự chọn bị F: F không vào ĐTBCTL nên ĐTBCTL vẫn 2,00 (tính cả F thì < 2 → kết luận sai).", N_TL,
       oracle={"dtbctl": 2, "tc_tich_luy": 161}),
    ca("BQ-06", "bay_quy_che", "tot_nghiep", hs("sv_lvtn", C2, *[["diem", m, 50] for m in QP]), "TRUE",
       "GDQP&AN D+ (1,5) không vào ĐTBCTL (HP điều kiện) → ĐTBCTL vẫn 2,00; TB GDQP đúng 5,0.", N_TL + "; " + N_QP,
       oracle={"dtbctl": 2, "gdqp_tb": 5}),
    ca("BQ-07", "bay_quy_che", "dk_tin_chi", hs("sv_mien_ielts"), "TRUE",
       "10 TC Anh văn mang điểm M (đã có QĐ miễn) VẪN tính vào tổng TC tích lũy → 151 + 10 = 161.",
       "QĐ3266 Điều 22 khoản 5 điểm a", oracle={"tc_tich_luy": 161}),
    ca("BQ-08", "bay_quy_che", "tot_nghiep", hs("sv_tron_ngoai_ngu"), "FALSE",
       "AV 4 TC + PV 7 TC = 11 TC nhưng nhóm '10 AV hoặc PV' là một nhánh, không cộng dồn.",
       N_CTDT + " (CQ-02)", oracle={"tc_tich_luy": 162}),
    ca("BQ-09", "bay_quy_che", "tot_nghiep", hs("sv_5hp"), "TRUE",
       "Không làm LVTN/TLTN, học 5 HP tự chọn 3 TC = 15 TC nhóm tốt nghiệp → vẫn tốt nghiệp (LVTN là tự chọn).",
       N_CTDT + "; QĐ3266 Điều 31 khoản 3 (QD-07)"),
    ca("BQ-10", "bay_quy_che", "tot_nghiep", hs("sv_5hp", ["xoa_diem", "CT210"]), "FALSE",
       "Chỉ 4 HP = 12 TC < 15 TC nhóm tốt nghiệp.", N_CTDT, oracle={"tc_tich_luy": 158}),
    ca("BQ-11", "bay_quy_che", "tot_nghiep", hs("sv_tltn"), "TRUE",
       "TLTN 6 TC + 3 HP 3 TC = 15 TC.", N_CTDT),
    ca("BQ-12", "bay_quy_che", "tot_nghiep", hs("sv_lvtn", *[["diem", m, 30] for m in RUNG_F]), "TRUE",
       "Bẫy B-03 ('nợ quá 150%'/nợ TC chặn tốt nghiệp): 18 TC F ở HP tự chọn dư không chặn tốt nghiệp; 24 TC nợ là "
       "ngưỡng CẢNH BÁO, không phải điều kiện tốt nghiệp.", "QĐ3266 Điều 17 khoản 1, Điều 18 khoản 2 điểm c; " + N_TN,
       oracle={"tc_tich_luy": 161, "dtbctl_ge_2": True}),
    ca("BQ-13", "bay_quy_che", 'du_dk_xin_mien("FL001")', hs("sv_lvtn", ["chung_chi", "ielts", 6.0]), "FALSE",
       "Chứng chỉ tiếng Anh không cho xin miễn Pháp văn (điểm a ≠ điểm b).", "QĐ5339 Điều 3 khoản 5 điểm a, b"),
    ca("BQ-14", "bay_quy_che", "tot_nghiep", hs("sv_lvtn", ["dat", "da_hoc_nam2", 17]), "TRUE",
       "8,5 năm: CTĐT 4,5 năm có trần 9 năm (không phải 8 năm như CTĐT 4 năm).", N_TG,
       oracle={"tran_nam2": 18, "qua_han": False}),
    ca("BQ-15", "bay_quy_che", 'du_dk_tc("CT550E")', hs("sv_lvtn", ["xoa_diem", BO_119], ["diem", "CT478", 30]), "FALSE",
       "Đã ĐĂNG KÝ 122 TC nhưng 3 TC bị F không tích lũy → 119 < 120.", N_120 + "; " + N_DIEM,
       oracle={"tc_tich_luy": 119}),

    # ======================= HỒ SƠ LỖI / MÂU THUẪN =======================
    ca("HL-01", "ho_so_loi", "tot_nghiep", hs("sv_lvtn", ["diem_tho", "CT177", {"credits": 3, "thang10": 80, "letter": "F", "status": "failed"}]),
       "UNKNOWN", "CT177: 8,0 nhưng ghi F/failed — hai trường mâu thuẫn, không biết cái nào đúng.", N_TK + "; " + N_DIEM),
    ca("HL-02", "ho_so_loi", "tot_nghiep", hs("sv_lvtn", ["diem_tho", "CT177", {"credits": 3, "thang10": 30, "letter": "F", "status": "passed"}]),
       "UNKNOWN", "CT177: 3,0 (F) nhưng trạng thái passed.", N_TK + "; " + N_DIEM),
    ca("HL-03", "ho_so_loi", "tot_nghiep", hs("sv_lvtn", ["diem_tho", "CT177", {"credits": 3, "thang10": 150, "letter": "A", "status": "passed"}]),
       "UNKNOWN", "Điểm 15,0 ngoài thang 0–10 (vi phạm schema).", N_TK + "; QĐ3266 Điều 22 khoản 1"),
    ca("HL-04", "ho_so_loi", "tot_nghiep", hs("sv_lvtn", ["diem_tho", "CT177", {"credits": 4, "thang10": 75, "letter": "B", "status": "passed"}]),
       "UNKNOWN", "CT177 ghi 4 TC trong khi CTĐT là 3 TC — không rõ bản ghi hay mã sai.", N_TK + "; " + N_CTDT),
    ca("HL-05", "ho_so_loi", "tot_nghiep", hs("sv_lvtn", ["diem_tho", "CT177", {"credits": 3, "thang10": 80, "letter": "B", "status": "passed"}]),
       "UNKNOWN", "8,0 phải là B+, không phải B — điểm chữ và điểm số mâu thuẫn.", N_TK + "; " + N_DIEM),
    ca("HL-06", "ho_so_loi", "tot_nghiep", hs("sv_lvtn", ["dat", "da_hoc_nam2", 0]), "UNKNOWN",
       "Đã học 0 nửa năm mà có 161 TC — không thể (trần 20 TC/HK, Điều 14 k1).", N_TK + "; QĐ3266 Điều 14 khoản 1"),

    # ======================= OCR SAI (mức tài liệu) =======================
    ca("OC-01", "ocr_sai", "tot_nghiep", ocr("sv_lvtn"), "TRUE",
       "Bảng điểm đọc hoàn hảo — kiểm độ phủ (không được từ chối thừa).", N_TN),
    ca("OC-02", "ocr_sai", "tot_nghiep", ocr("sv_tron_ngoai_ngu"), "FALSE",
       "Bảng điểm đọc hoàn hảo của hồ sơ trộn AV/PV.", N_CTDT + " (CQ-02)"),
    ca("OC-03", "ocr_sai", "tot_nghiep", ocr("sv_lvtn", ["doi_chu", "CT177", "F"]), "UNKNOWN",
       "Điểm chữ CT177 đọc thành F trong khi T.Hợp là B → mâu thuẫn R-B02, điểm CT177 không chắc.", N_OCR + "; " + N_DIEM,
       su_that="TRUE"),
    ca("OC-04", "ocr_sai", "tot_nghiep", ocr("sv_lvtn", ["mat_dong", "CT177"]), "UNKNOWN",
       "OCR bỏ sót dòng CT177: tổng TC học kỳ lệch → có HP bị ẩn, không được kết luận 'thiếu môn'.", N_OCR, su_that="TRUE"),
    ca("OC-05", "ocr_sai", "tot_nghiep", ocr("sv_lvtn", ["doi_ma", "CT177", None]), "UNKNOWN",
       "Không đọc được mã của một dòng.", N_OCR, su_that="TRUE"),
    ca("OC-06", "ocr_sai", "tot_nghiep", ocr("sv_lvtn", ["doi_ma", "CT178", "CT478", "CT178"], ["conf", "CT478", "ma", 0.0]),
       "UNKNOWN", "Hai lần đọc mã ra hai mã hợp lệ khác nhau (CT478 / CT178) → không biết HP nào.", N_OCR, su_that="TRUE"),
    ca("OC-07", "ocr_sai", "tot_nghiep", ocr("sv_lvtn", ["doi_ma", "CT178", "CT478"]), "TRUE",
       "CT178 (bắt buộc) đọc NHẤT QUÁN thành CT478 (tự chọn, cùng 3 TC) — mọi kiểm chéo đều qua. Sự thật: đủ điều kiện. "
       "Đo rủi ro: hệ thống chỉ thấy 'thiếu CT178'.", N_OCR, su_that="TRUE", khong_phat_hien_duoc=True),
    ca("OC-08", "ocr_sai", "tot_nghiep", ocr("sv_lvtn", ["doi_tc", "CT177", 8]), "UNKNOWN",
       "TC của CT177 đọc thành 8 (CTĐT 3) → dòng không hợp lệ, tổng học kỳ lệch.", N_OCR, su_that="TRUE"),
    ca("OC-09", "ocr_sai", "tot_nghiep", ocr("sv_lvtn", *[["conf", "CT518E", k, 0.3] for k in ("thi", "thop", "chu")]),
       "UNKNOWN", "Điểm CT518E (bắt buộc, 5 TC) đọc với confidence 0,3 ở cả ba cột.", N_OCR, su_that="TRUE"),
    ca("OC-10", "ocr_sai", "tot_nghiep", ocr("sv_lvtn", ["doi_diem", "CT177", 30]), "UNKNOWN",
       "CT177 B đọc nhất quán thành 3,0/F nhưng ĐTBCHK in trên bảng điểm không khớp → học kỳ bị nghi ngờ.", N_OCR,
       su_that="TRUE"),
    ca("OC-11", "ocr_sai", "tot_nghiep", ocr("sv_lvtn", ["doi_diem", "CT177", 45], ["doi_dtbchk", 3, None],
                                             that=[["diem", "CT177", 30]]), "FALSE",
       "Sự thật CT177 = F. OCR đọc nhất quán thành 4,5/D và không đọc được ĐTBCHK → không kiểm chéo nào bắt được. "
       "Đo rủi ro: hệ thống sẽ thấy đủ điều kiện.", N_OCR + "; " + N_DIEM, su_that="FALSE", khong_phat_hien_duoc=True),
    ca("OC-12", "ocr_sai", "tot_nghiep", ocr("sv_lvtn", ["doi_diem", "CT177", 45], that=[["diem", "CT177", 30]]),
       "UNKNOWN", "Như OC-11 nhưng ĐTBCHK đọc được và không khớp → bắt được.", N_OCR, su_that="FALSE"),
    ca("OC-13", "ocr_sai", "tot_nghiep", ocr("sv_lvtn", ["doi_tong_dk", 3, 21]), "UNKNOWN",
       "Tổng TC đăng ký học kỳ đọc thành 21 (thật 19) → có thể có HP bị ẩn.", N_OCR, su_that="TRUE"),
    ca("OC-14", "ocr_sai", "tot_nghiep", ocr("sv_lvtn", ["doi_dtbchk", 4, 2.5]), "UNKNOWN",
       "ĐTBCHK đọc thành 2,50 (thật 3,08) → điểm cả học kỳ không chắc.", N_OCR, su_that="TRUE"),
    ca("OC-15", "ocr_sai", "tot_nghiep", ocr("sv_lvtn", ["hoc_lai", "CT177", 30, 7, True]), "TRUE",
       "CT177 học lần đầu F, học lại đạt B, cả hai dòng đọc rõ → điểm là điểm cao nhất.", "QĐ3266 Điều 17 khoản 2",
       su_that="TRUE"),
    ca("OC-16", "ocr_sai", "tot_nghiep", ocr("sv_lvtn", ["hoc_lai", "CT177", 30, 7, False]), "UNKNOWN",
       "CT177 lần đầu F đọc rõ, lần học lại không đọc được điểm → điểm cao nhất chưa biết.", "QĐ3266 Điều 17 khoản 2; " + N_OCR,
       su_that="TRUE"),
    ca("OC-17", "ocr_sai", "tot_nghiep", ocr("sv_lvtn", khai_bao_bo=["xac_nhan_ky_luat_sach"]), "UNKNOWN",
       "Bảng điểm không ghi tình trạng kỷ luật và sinh viên chưa khai báo.", N_KL, su_that="TRUE"),
    ca("OC-18", "ocr_sai", "tot_nghiep", ocr("sv_lvtn", khai_bao_bo=["da_hoc_nam2"]), "UNKNOWN",
       "Bảng điểm (theo học kỳ đã học) nhưng sinh viên chưa khai báo số nửa năm đã học — không suy từ số học kỳ in "
       "(có thể có học kỳ bảo lưu/không đăng ký).", N_TG, su_that="TRUE"),
]

KHONG_CHAM = [
    ca("KX-01", "bay_quy_che", "tot_nghiep", hs("sv_du_hp"), "UNKNOWN",
       "Học dư CT478 điểm D; SV được chọn HP tự chọn tính vào tích lũy (Đ17 k3, CQ-06) nhưng CHƯA khai báo. "
       "Đáp án phụ thuộc cách hiểu 'chưa chọn' (∀ hay ∃ cách chọn) — chưa chốt.", "QĐ3266 Điều 17 khoản 3 (CQ-06)",
       cham_diem=False, ly_do_khong_cham="diễn giải chưa chốt: SV chưa khai báo lựa chọn tích lũy"),
    ca("KX-02", "sat_nguong", "tot_nghiep", hs("sv_lvtn", ["diem", "QP010E", 45], *[["diem", m, 80] for m in QP[1:]]),
       "UNKNOWN", "QP010E = 4,5 (D), TB GDQP 7,1 ≥ 5,0. QĐ5339 Đ3 k2 ghi 'GDQP&AN phải đạt từ D+' nhưng trong ngữ cảnh "
       "miễn/công nhận điểm; áp cho điểm học tại ĐHCT hay không chưa chốt.", "QĐ5339 Điều 3 khoản 2; " + N_QP,
       cham_diem=False, ly_do_khong_cham="phạm vi áp dụng ngưỡng D+ của QĐ5339 cho GDQP chưa chốt"),
    ca("KX-03", "ho_so_loi", "tot_nghiep",
       hs("sv_lvtn", ["xoa_diem", "TC100"], *[["diem_tho", m, {"credits": 1, "thang10": 80, "letter": "B+", "status": "passed"}]
                                               for m in ("TC025", "TC026", "TC027")]),
       "UNKNOWN", "Bảng điểm thật ghi GDTC là TC025–027, KB K49 chỉ có TC100 (P15-3).", "Tuần 15 P15-3; " + N_CTDT,
       cham_diem=False, ly_do_khong_cham="ánh xạ TC025–027 ↔ TC100 chờ Phòng Đào tạo xác nhận"),
    ca("KX-04", "ocr_sai", "tot_nghiep", {"loai": "ocr_anh", "goc": "sv_lvtn", "bien_the": "sach"}, "TRUE",
       "Mức ảnh (render + Tesseract) — minh hoạ.", N_OCR, cham_diem=False,
       ly_do_khong_cham="mức ảnh: kết quả đổi theo font/phiên bản Tesseract (Tuần 16) — chỉ minh hoạ"),
    ca("KX-05", "ocr_sai", "tot_nghiep", {"loai": "ocr_anh", "goc": "sv_lvtn", "bien_the": "nghieng"}, "TRUE",
       "Mức ảnh, trang nghiêng 0,8° — minh hoạ.", N_OCR, cham_diem=False,
       ly_do_khong_cham="mức ảnh: kết quả đổi theo font/phiên bản Tesseract (Tuần 16) — chỉ minh hoạ"),
]


def chia(cases, seed=17):
    rng = random.Random(seed)
    for n in sorted({c["nhom"] for c in cases}):
        nhom = sorted((c for c in cases if c["nhom"] == n), key=lambda c: c["id"])
        rng.shuffle(nhom)
        for i, c in enumerate(nhom):
            c["split"] = "dev" if i % 2 == 0 else "test"


def main():
    chia(CASES)
    for c in KHONG_CHAM:
        c["split"] = None
    ds = {"meta": {"ten": "CPA² Adversarial set v1 (Tuần 17)", "seed": 17,
                   "ghi_chu": "Gold viết tay trong build_adversarial.py, commit TRƯỚC khi chạy CPA². "
                              "Chỉ tinh chỉnh trên dev; test chạy để báo cáo."},
          "cases": CASES + KHONG_CHAM}
    (HERE / "adversarial_set.json").write_text(json.dumps(ds, ensure_ascii=False, indent=1), encoding="utf-8")
    from collections import Counter
    print(f"{len(CASES)} ca chấm điểm + {len(KHONG_CHAM)} ca không chấm →", HERE / "adversarial_set.json")
    print(" ", dict(Counter((c["nhom"], c["split"]) for c in CASES)))
    print(" ", dict(Counter(c["gold"] for c in CASES)))


if __name__ == "__main__":
    main()
