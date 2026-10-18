"""
validate_rformal.py — kiểm chứng R-Formal v1 (Tuần 5, CPA²).

Ba nhóm kiểm tra, chạy tự động, không phụ thuộc người đọc:

  A. BẤT BIẾN CON TRỎ NGUỒN  (tiêu chí hoàn thành của Tuần 5: "mỗi rule có nguồn")
     A1. mọi RuleId xuất hiện trong why/2 đều có rule_src/5 trong các file .lp
     A2. mọi rule_src/5 đều có bản ghi tương ứng trong r_formal_v1.json
     A3. con trỏ (văn bản, điều, khoản, điểm) trong .lp trùng khớp với JSON
     A4. mọi quy tắc có trường "asp" trong JSON đều thực sự xuất hiện trong .lp
     A5. mọi bản ghi trong JSON đều có trích nguyên văn không rỗng
     A6. mọi quy tắc trong miền đều trỏ tới một điều
     A7. mọi mã văn bản dùng trong .lp đều được khai báo ở meta.van_ban

  B. ĐỘ PHỦ HÌNH THỨC HOÁ (số liệu cho RQ1)

  C. KIỂM THỬ NGỮ NGHĨA — chạy clingo trên các hồ sơ thử, đối chiếu kết luận
     mong đợi. Trọng tâm là các NGƯỠNG SỐ, vì đó là chỗ prototype Tuần 4 sai.

PHỤ THUỘC
    pip install -r requirements.txt      (chỉ cần clingo >= 5.6)
    Phần A và B KHÔNG cần clingo — chúng chỉ đọc JSON và các file .lp dạng văn bản.
    Nếu thiếu clingo, script vẫn chạy A và B, báo phần C là BỎ QUA, và thoát với mã 2
    để phân biệt với "đã chạy và có lỗi" (mã 1) và "đạt toàn bộ" (mã 0).

Chạy:  python3 validate_rformal.py
"""
import json
import re
import sys
from pathlib import Path

try:
    import clingo
    CLINGO_OK = True
    CLINGO_ERR = ""
except ImportError as _e:            # phần A và B vẫn chạy được khi thiếu clingo
    clingo = None
    CLINGO_OK = False
    CLINGO_ERR = str(_e)

HERE = Path(__file__).parent
LP_FILES = [HERE / "qd3266_r_formal_v1.lp", HERE / "qd5339_r_formal_v1.lp"]
# CTĐT là DỮ LIỆU của một (ngành, khoá) cụ thể, không phải quy tắc quy chế — chỉ nạp
# cho những ca kiểm thử khai báo ctdt=True, để không nhiễm tham số vào các ca khác.
# v1.5 (Tuần 6): nạp Curriculum KB v1 — khung CTĐT đầy đủ 78 dòng, sinh tự động —
# thay cho ctdt_cntt_k49.lp chép tay một phần (file cũ giữ lại để đối chiếu lịch sử).
CTDT_FILES = [HERE.parent / "w6_curriculum" / "curriculum_schema.lp",
              HERE.parent / "w6_curriculum" / "curriculum_cntt_k49.lp"]
JSON = HERE / "r_formal_v1.json"

OK, FAIL = "  [OK]  ", "  [FAIL]"
errors = []


def check(cond, msg):
    print((OK if cond else FAIL) + " " + msg)
    if not cond:
        errors.append(msg)
    return cond


# =============================================================================
# A. BẤT BIẾN CON TRỎ NGUỒN
# =============================================================================
def section_a(cat, lp_text):
    print("\n" + "=" * 78)
    print("A. BẤT BIẾN CON TRỎ NGUỒN")
    print("=" * 78)

    src = {}
    for m in re.finditer(
            r"rule_src\((\w+),\s*(\w+),\s*(\d+),\s*(\w+),\s*(\w+)\)\.", lp_text):
        src[m.group(1)] = (m.group(2), int(m.group(3)), m.group(4), m.group(5))
    why_ids = set(re.findall(r"why\([^,]*(?:\([^)]*\))?[^,]*,\s*(\w+)\)", lp_text))
    # lấy id ở vế ĐẦU của why(...) — chỉ những id bắt đầu bằng r_
    why_ids = {i for i in why_ids if i.startswith("r_")}

    by_asp = {r["asp"]: r for r in cat["rules"] if r.get("asp")}

    print(f"  · rule_src khai báo trong .lp : {len(src)}")
    print(f"  · RuleId dùng trong why/2     : {len(why_ids)}")

    missing = sorted(why_ids - set(src))
    check(not missing, f"A1. mọi RuleId trong why/2 đều có rule_src  (thiếu: {missing})")

    orphan = sorted(set(src) - set(by_asp))
    check(not orphan, f"A2. mọi rule_src đều có bản ghi JSON  (mồ côi: {orphan})")

    mismatch = []
    for rid, (vb, d, k, dm) in src.items():
        rec = by_asp.get(rid)
        if not rec:
            continue
        jd_ = 0 if rec["dieu"] is None else rec["dieu"]
        jk = "none" if rec["khoan"] is None else str(rec["khoan"])
        jdm = "none" if rec["diem"] is None else str(rec["diem"])
        if (vb, d, k, dm) != (rec["van_ban"], jd_, jk, jdm):
            mismatch.append(f"{rid}: lp=({vb},{d},{k},{dm}) "
                            f"json=({rec['van_ban']},{jd_},{jk},{jdm})")
    check(not mismatch, f"A3. con trỏ .lp khớp JSON, kể cả mã văn bản  (lệch: {mismatch})")

    known_docs = set(cat["meta"]["van_ban"])
    bad_doc = sorted({vb for (vb, _, _, _) in src.values()} - known_docs)
    check(not bad_doc, f"A7. mã văn bản trong .lp đều được khai báo ở meta  (lạ: {bad_doc})")

    declared = {r["asp"] for r in cat["rules"] if r.get("asp")}
    not_in_lp = sorted(declared - set(src))
    check(not not_in_lp, f"A4. mọi 'asp' trong JSON đều có mặt trong .lp  (thiếu: {not_in_lp})")

    empty = [r["id"] for r in cat["rules"] if not r["trich"].strip()]
    check(not empty, f"A5. mọi bản ghi đều có trích nguyên văn  (rỗng: {empty})")

    no_src = [r["id"] for r in cat["rules"]
              if r["lop"] != "X" and r["dieu"] is None and "Phụ lục" not in r["trich"]]
    check(not no_src, f"A6. mọi quy tắc trong miền đều trỏ tới một điều  (thiếu: {no_src})")
    # A8 (sau Tuần 19): trang 20 QĐ3266 (OCR trắng) đã chép tay từ PDF gốc → đủ khoản Đ33 và có tiêu đề Đ33/Đ34
    d33 = sorted(r["khoan"] for r in cat["rules"] if r["van_ban"] == "qd3266" and r["dieu"] == 33 and r["khoan"])
    check(d33 == [1, 2, 3, 4], f"A8. QĐ3266 Điều 33 đủ khoản 1–4 trong danh mục  (có: {d33})")
    td = {d: any(t in (r.get("ghi_chu") or "") for r in cat["rules"] if r["van_ban"] == "qd3266" and r["dieu"] == d)
          for d, t in ((33, "Xử lý sinh viên quá hạn thời gian học tập"), (34, "Bằng tốt nghiệp và hạng tốt nghiệp"))}
    check(all(td.values()), f"A9. tiêu đề Điều 33, 34 (PDF gốc tr.20) ghi trong danh mục  ({td})")
    return src


# =============================================================================
# B. ĐỘ PHỦ HÌNH THỨC HOÁ (RQ1)
# =============================================================================
def section_b(cat):
    print("\n" + "=" * 78)
    print("B. ĐỘ PHỦ HÌNH THỨC HOÁ — số liệu cho RQ1")
    print("=" * 78)
    rules = cat["rules"]
    inm = [r for r in rules if r["lop"] != "X"]
    n = len(inm)
    f = [r for r in inm if r["lop"] == "F"]
    p = [r for r in inm if r["lop"] == "P"]
    nn = [r for r in inm if r["lop"] == "N"]
    fco = [r for r in f if r["du_lieu"] == "co"]
    khong = [r for r in inm if r["du_lieu"] == "khong"]

    for k, v in cat["meta"]["van_ban"].items():
        print(f"  Văn bản {k:8s}: {v['so_dieu']:2d} điều, {v['so_trang']} trang")
    print(f"  Số bản ghi trong danh mục                    : {len(rules)}")
    print(f"  – ngoài miền tư vấn học vụ (X)               : {len(rules) - n}")
    print(f"  – trong miền (F + P + N)                     : {n}")
    print()
    print(f"  F  Formalizable                              : {len(f):3d}  ({100*len(f)/n:.1f}%)")
    print(f"  P  Partially formalizable                    : {len(p):3d}  ({100*len(p)/n:.1f}%)")
    print(f"  N  Not formalizable                          : {len(nn):3d}  ({100*len(nn)/n:.1f}%)")
    print()
    print(f"  >>> Formalization Coverage  = F/(F+P+N)      = {100*len(f)/n:.1f}%")
    print(f"  >>> Executable Coverage     = (F ∧ có dữ liệu)/n = {100*len(fco)/n:.1f}%")
    print(f"      (chênh {100*(len(f)-len(fco))/n:.1f} điểm phần trăm là các điều khoản hình")
    print(f"       thức hoá được nhưng KHÔNG thi hành được vì thiếu dữ kiện)")
    print()
    print(f"  Điều khoản buộc trả UNKNOWN vì thiếu dữ kiện : {len(khong)}  "
          f"({100*len(khong)/n:.1f}%)")

    print("\n  Lý do khiến điều khoản KHÔNG thi hành được trọn vẹn")
    print("  (gồm cả lớp P/N lẫn lớp F nhưng thiếu dữ kiện):")
    from collections import Counter
    reasons = Counter(r["ly_do_PN"] for r in inm if r["ly_do_PN"])
    label = {"tham_so": "tham số do người/đơn vị quy định",
             "tham_quyen": "thẩm quyền mở (Hiệu trưởng/đơn vị quyết định)",
             "du_lieu_khuyet": "dữ kiện không tồn tại trong phạm vi CPA²",
             "con_tro_ngoai": "con trỏ tới văn bản khác",
             "ngon_ngu_mo": "thuật ngữ/ngôn ngữ không định nghĩa",
             "xung_dot_van_ban": "hai văn bản cùng hiệu lực quy định khác nhau",
             "quyen_chon_SV": "quy chế trao quyền chọn cho sinh viên"}
    for k, v in reasons.most_common():
        print(f"    – {label.get(k,k):48s} : {v}")

    print("\n  Phân bố theo nhóm điều khoản ưu tiên (Tuần 1 mục 5.1):")
    groups = {}
    for r in inm:
        groups.setdefault(r["nhom"], []).append(r["lop"])
    for g, ls in sorted(groups.items(), key=lambda x: -len(x[1])):
        c = Counter(ls)
        print(f"    – {g:20s} : {len(ls):3d}  (F={c['F']}, P={c['P']}, N={c['N']})")

    print("\n  Phân bố theo loại ràng buộc T1–T8 (taxonomy Tuần 2):")
    tx = Counter(t for r in inm for t in r["taxo"])
    for t in sorted(tx):
        print(f"    – {t} : {tx[t]}")
    untagged = [r["id"] for r in inm if not r["taxo"]]
    print(f"    – không thuộc T1–T8 : {len(untagged)}  {untagged}")

    print("\n  Quyết định diễn giải phải ghi công khai trong KB:")
    for r in inm:
        if r["quyet_dinh"]:
            print(f"    – {r['id']} (Điều {r['dieu']}): {r['quyet_dinh'][:100]}...")
    return {"n": n, "F": len(f), "P": len(p), "N": len(nn), "Fco": len(fco)}


# =============================================================================
# C. KIỂM THỬ NGỮ NGHĨA
# =============================================================================
def solve(facts, ctdt=False):
    if ctdt:
        facts = "\n".join(f.read_text(encoding="utf-8") for f in CTDT_FILES) + "\n" + facts
    ctl = clingo.Control(["--models=1", "--warn=none"])
    ctl.add("base", [], "\n".join(f.read_text(encoding="utf-8") for f in LP_FILES)
                        + "\n" + facts)
    ctl.ground([("base", [])])
    out = set()
    with ctl.solve(yield_=True) as h:
        for m in h:
            out = {str(a) for a in m.symbols(atoms=True)}
            break
    return out


# --- CTĐT thu nhỏ dùng chung cho các ca kiểm thử ----------------------------
def ctdt(courses):
    """courses: list (ma, tin_chi, loai) — loai ∈ bat_buoc/tu_chon/gdqp/gdtc"""
    out = []
    for c, cr, kind in courses:
        out.append(f'course({c},{cr}).')
        if kind == "bat_buoc":
            out.append(f'bat_buoc({c}).')
        elif kind in ("gdqp", "gdtc", "ngoai_ngu_cb", "tin_hoc_cb"):
            out.append(f'loai_hp({c},{kind}).')
    return "\n".join(out)


TESTS = []


def test(name, facts, expect_true=(), expect_false=(), note="", ctdt=False):
    TESTS.append((name, facts, expect_true, expect_false, note, ctdt))


# --- C1. Ngưỡng cảnh báo học tập: 0,80 ở HK đầu (KHÔNG phải 1,00 hay 1,20) ---
BASE_CB = ctdt([("a", 3, "bat_buoc"), ("b", 3, "bat_buoc")]) + """
khoa_tu_k47. khoa_tu_k45. khoa_den_k49.
hoc_ky(hk1). hk_dau_khoa(hk1).
hoc_trong_hk(hk1,a). hoc_trong_hk(hk1,b).
"""
test("C1 ĐTBCHK 0,75 ở HK đầu → CẢNH BÁO (ngưỡng 0,80)",
     BASE_CB + "g10(a,45). g10(b,35).",   # D=1,0 và F=0,0 → ĐTBCHK = 0,50
     expect_true=["canh_bao(hk1)"],
     note="Điều 18 k.2 điểm a")

test("C2 ĐTBCHK 0,90 ở HK đầu → KHÔNG cảnh báo theo điểm a",
     ctdt([("a", 9, "bat_buoc"), ("b", 1, "bat_buoc")]) + """
khoa_tu_k45. khoa_den_k49.
hoc_ky(hk1). hk_dau_khoa(hk1).
hoc_trong_hk(hk1,a). hoc_trong_hk(hk1,b).
g10(a,45). g10(b,35).
""",   # (1,0×9 + 0,0×1)/10 = 0,90 — trên ngưỡng 0,80 của HK đầu
     expect_false=["canh_bao(hk1)"],
     note="REGRESSION Tuần 4: prototype dùng WARNING_TERM_GPA = 1,20 nên ca này bị báo "
          "cảnh báo SAI. Ngưỡng đúng của HK đầu là 0,80.")

test("C2b Cùng ĐTBCHK 0,90 nhưng ở HK KHÔNG phải đầu khóa → CÓ cảnh báo (ngưỡng 1,00)",
     ctdt([("a", 9, "bat_buoc"), ("b", 1, "bat_buoc")]) + """
khoa_tu_k45. khoa_den_k49.
hoc_ky(hk3).
hoc_trong_hk(hk3,a). hoc_trong_hk(hk3,b).
g10(a,45). g10(b,35).
""",
     expect_true=["canh_bao(hk3)"],
     note="cùng một điểm số cho hai kết luận trái ngược tuỳ vị trí học kỳ — ngưỡng kép "
          "0,80/1,00 của Điều 18 k.2 điểm a")

# --- C3/C4. Xếp trình độ năm học — biên 70/71 (Điều 30) ---------------------
test("C3 TC tích lũy = 70 → trình độ NĂM THỨ HAI",
     ctdt([("x", 70, "bat_buoc")]) + "khoa_tu_k45. g10(x,80).",
     expect_true=["trinh_do_nam(2)"], expect_false=["trinh_do_nam(3)"],
     note="Điều 30, cột 'từ K.45 trở về sau'")

test("C4 TC tích lũy = 71 → trình độ NĂM THỨ BA",
     ctdt([("x", 71, "bat_buoc")]) + "khoa_tu_k45. g10(x,80).",
     expect_true=["trinh_do_nam(3)"], expect_false=["trinh_do_nam(2)"],
     note="ca biên — lệch 1 TC đổi trình độ, kéo theo đổi ngưỡng cảnh báo ĐTBCTL")

# --- C5. Điểm M: vào TC tích lũy nhưng KHÔNG vào ĐTBCTL (Điều 22 k.5 đ.a) ---
test("C5 Điểm M tính vào TC tích lũy nhưng không vào ĐTBCTL",
     ctdt([("m1", 3, "bat_buoc"), ("g1", 3, "bat_buoc")]) + """
khoa_tu_k45. diem_m(m1). g10(g1,90).
""",
     expect_true=["tc_tich_luy(6)", "tl_mau(3)", "passed(m1)"],
     note="QD-01: nếu M vào ĐTBCTL thì tl_mau phải là 6 — kiểm tra trực tiếp mẫu số")

# --- C6/C7. Ngưỡng GDQP&AN 5,0 THANG 10 (Điều 32 k.1 đ.b) -------------------
test("C6 ĐTB GDQP = 5,0 (thang 10) → ĐẠT điều kiện GDQP",
     ctdt([("qp", 4, "gdqp")]) + "khoa_tu_k45. g10(qp,50).",
     expect_true=["dk_gdqp"],
     note="Điều 32 k.1 điểm b — ngưỡng trên THANG 10, không phải thang 4")

test("C7 ĐTB GDQP = 4,9 → KHÔNG đạt",
     ctdt([("qp", 4, "gdqp")]) + "khoa_tu_k45. g10(qp,49).",
     expect_false=["dk_gdqp"],
     note="ca biên 4,9 / 5,0")

# --- C8. Tốt nghiệp: đủ học vụ nhưng trục kỷ luật không có dữ liệu ----------
FULL = ctdt([("a", 60, "bat_buoc"), ("qp", 4, "gdqp")]) + """
khoa_tu_k45. khoa_tu_k47.
g10(a,80). g10(qp,70).
tc_toi_thieu_ctdt(60).
"""
test("C8 Đủ điều kiện học vụ nhưng KHÔNG kết luận tốt nghiệp (thiếu dữ kiện kỷ luật)",
     FULL,
     expect_true=["du_dk_hoc_vu", "truc_ky_luat_khong_co_du_lieu"],
     expect_false=["tot_nghiep"],
     note="Điều 32 k.1 điểm c — xác nhận thiết kế ba trị của Tuần 2 (cond_discipline)")

test("C9 Bổ sung dữ kiện kỷ luật sạch → kết luận tốt nghiệp",
     FULL + "xac_nhan_ky_luat_sach.",
     expect_true=["tot_nghiep"],
     note="cùng hồ sơ C8, chỉ thêm một dữ kiện → chân trị đổi từ UNKNOWN sang TRUE")

# --- C9b. Tốt nghiệp phải trong thời gian tối đa (Điều 5) — P16-2, Tuần 16 -----
test("C9b Đủ học vụ + kỷ luật sạch nhưng đã học 19 nửa năm (trần 18) → KHÔNG tốt nghiệp",
     FULL + "xac_nhan_ky_luat_sach. thiet_ke_nam2(9). da_hoc_nam2(19).",
     expect_true=["qua_thoi_gian_toi_da"], expect_false=["tot_nghiep"],
     note="HỒI QUY P16-2: v1.6 cho tot_nghiep TRUE. Điều 5: thời gian tối đa để SV HOÀN THÀNH CTĐT")
test("C9c Biên: đã học đúng 18 nửa năm (= trần) → vẫn tốt nghiệp",
     FULL + "xac_nhan_ky_luat_sach. thiet_ke_nam2(9). da_hoc_nam2(18).",
     expect_true=["tot_nghiep"], expect_false=["qua_thoi_gian_toi_da"])

# --- C10. Hạng tốt nghiệp bị giảm một mức do điểm F > 5% (Điều 34 k.2 đ.a) --
test("C10 ĐTBCTL 3,7 (xuất sắc) + TC điểm F > 5% CTĐT → hạng cuối là GIỎI",
     ctdt([("a", 10, "bat_buoc")]) + """
khoa_tu_k45. g10(a,95). tc_toi_thieu_ctdt(120). tc_diem_f(7).
""",
     expect_true=["hang_goc(xuat_sac)", "vuot_5_phan_tram", "hang_cuoi(gioi)"],
     expect_false=["hang_cuoi(xuat_sac)"],
     note="7/120 = 5,83% > 5%")

test("C11 Cùng hồ sơ nhưng TC điểm F = 6 (đúng 5%) → giữ hạng XUẤT SẮC",
     ctdt([("a", 10, "bat_buoc")]) + """
khoa_tu_k45. g10(a,95). tc_toi_thieu_ctdt(120). tc_diem_f(6).
""",
     expect_true=["hang_cuoi(xuat_sac)"], expect_false=["vuot_5_phan_tram"],
     note="ca biên: 'vượt quá 5%' — đúng 5% thì KHÔNG giảm")

# --- C12. Trần 20 TC/HK (Điều 14 k.1) và phát hiện âm tính về sàn ----------
test("C12 Đăng ký 21 TC → vượt trần 20 TC/HK",
     "khoa_tu_k45. hoc_ky(hk1). tong_tc_dang_ky(hk1,21).",
     expect_true=["vuot_tran_dang_ky(hk1)"], note="Điều 14 k.1")

test("C13 Đăng ký 8 TC → KHÔNG vi phạm (quy chế không có sàn tín chỉ)",
     "khoa_tu_k45. hoc_ky(hk1). tong_tc_dang_ky(hk1,8).",
     expect_false=["vuot_tran_dang_ky(hk1)"],
     note="R-C03 phát hiện âm tính: mốc 12 TC chỉ dùng cho học bổng/xếp loại")

# --- C14. Buộc thôi học chỉ ở mức "thuộc diện xem xét" (QD-04) --------------
test("C14 Đã cảnh báo + HK kế tiếp ĐTBCHK < 1,00 → chỉ 'thuộc diện xem xét'",
     ctdt([("a", 3, "bat_buoc"), ("b", 3, "bat_buoc")]) + """
khoa_tu_k45. hoc_ky(hk1). hoc_ky(hk2). hk_dau_khoa(hk1). ke_tiep(hk1,hk2).
hoc_trong_hk(hk1,a). hoc_trong_hk(hk2,b).
g10(a,35). g10(b,35).
""",
     expect_true=["canh_bao(hk1)", "dien_xem_xet_thoi_hoc(hk2)"],
     note="Điều 18 k.5 điểm b — mệnh đề 'trường hợp đặc biệt do Hiệu trưởng quyết định' "
          "hạ trần chân trị: hệ thống KHÔNG kết luận buộc thôi học")

# --- C15. Thời gian học tập tối đa (Điều 5) --------------------------------
test("C15 CTĐT 4 năm, không được công nhận TC → trần 8 năm (16 nửa năm)",
     "khoa_tu_k45. khoa_den_k49. thiet_ke_nam2(8). da_hoc_nam2(15).",
     expect_true=["thoi_gian_toi_da_hk(24)"], expect_false=["qua_thoi_gian_toi_da"],
     note="Điều 5 bảng — OCR mất bảng này, phải đọc ảnh trang 4")

test("C16 Được công nhận 18 TC (K49) → trần giảm 2 HK còn 22 HK (7⅓ năm); đã học 15 nửa năm → quá hạn",
     "khoa_tu_k45. khoa_den_k49. thiet_ke_nam2(8). da_hoc_nam2(15). tc_cong_nhan(18).",
     expect_true=["giam_hk(2)", "thoi_gian_toi_da_hk(22)", "qua_thoi_gian_toi_da"],
     note="Điều 5 đoạn 2 — mỗi 9 TC (K≤49) giảm 1 HK; v1.8: 1 HK = 1/3 năm (Điều 6 k1) → 8 năm = 24 HK − 2 = 22 HK; "
          "đã học 15 nửa năm = 22,5 HK > 22")

test("C16b 27 TC công nhận (K49), thiết kế 4,5 năm: trần 27 − 3 = 24 HK = 8 năm; đã học 16 nửa năm = 8 năm → CHƯA quá hạn",
     "khoa_tu_k45. khoa_den_k49. thiet_ke_nam2(9). da_hoc_nam2(16). tc_cong_nhan(27).",
     expect_true=["giam_hk(3)", "thoi_gian_toi_da_hk(24)"], expect_false=["qua_thoi_gian_toi_da"],
     note="HỒI QUY P17-3: v1.7 trừ 1 HK = 1 nửa năm → trần 15 nửa năm < 16 → quá hạn (sai). "
          "QĐ3266 Điều 6 khoản 1 (tr.5): một năm học có 03 HK")


# =============================================================================
# C17–C26 — NHÓM T5/T6 từ QĐ5339 (bổ sung ở R-Formal v1.1)
# =============================================================================

AV = 'course(av1,4). loai_hp(av1,ngoai_ngu_cb). ngon_ngu_hp(av1,anh). khoa_tu_k45.\n'

test("C17 IELTS 5.0, K49 → ĐỦ ĐIỀU KIỆN XIN MIỄN, nhưng CHƯA được miễn",
     AV + "chung_chi(ielts,50).",
     expect_true=["du_dk_xin_mien(av1)", "bac_ngoai_ngu(3)", "mien_treo(av1)"],
     expect_false=["passed(av1)", "diem_m(av1)"],
     note="QD-11 (QĐ5339 Điều 2 k.6): miễn KHÔNG tự động. Trả lời 'em đã được miễn' khi mới "
          "chỉ có chứng chỉ là NÓI SAI — ca đối kháng bắt buộc")

test("C18 Có thêm quyết định xét miễn → mới thành ĐƯỢC MIỄN, mang điểm M",
     AV + "chung_chi(ielts,50). duoc_mien(av1).",
     expect_true=["diem_m(av1)", "passed(av1)", "exempted_m(av1)"],
     expect_false=["mien_treo(av1)"],
     note="cùng hồ sơ C17, thêm đúng một dữ kiện quyết định → chân trị đổi")

test("C19 IELTS 4.0, K49 → KHÔNG đủ điều kiện (ngưỡng là bậc 3 = IELTS 4.5)",
     AV + "chung_chi(ielts,40).",
     expect_true=["bac_ngoai_ngu(2)"],
     expect_false=["du_dk_xin_mien(av1)", "bac_ngoai_ngu(3)"],
     note="QĐ5339 Điều 3 k.5 đ.a — K45 trở về sau cần bậc 3; K44 trở về trước chỉ cần bậc 2")

test("C19b IELTS 6.0 KHÔNG cho xin miễn Pháp văn (QĐ5339 Đ3 k5 điểm a ≠ điểm b)",
     AV + "course(fl1,4). loai_hp(fl1,ngoai_ngu_cb). ngon_ngu_hp(fl1,phap). chung_chi(ielts,60).",
     expect_true=["du_dk_xin_mien(av1)", "bac_nn(anh,4)"],
     expect_false=["du_dk_xin_mien(fl1)", "mien_treo(fl1)", "bac_nn(phap,4)"],
     note="Hồi quy Tuần 7: v1.4 gộp điểm a/b → chứng chỉ tiếng Anh cho xin miễn cả Pháp văn")

test("C19c TOEIC 600 (lưu ×10 = 6000) → bậc 4, đủ điều kiện xin miễn Anh văn",
     AV + "chung_chi(toeic,6000).",
     expect_true=["bac_nn(anh,4)", "du_dk_xin_mien(av1)"],
     expect_false=["bac_nn(anh,5)"],
     note="Hồi quy Tuần 7: loader chỉ nhân 10 cho IELTS → TOEIC 600 thành 600 < 4000, không đạt bậc nào")

test("C20 Công nhận điểm học phần thường → CÓ vào ĐTBCTL (SỬA QD-01)",
     "khoa_tu_k45. course(c1,3). duoc_mien(c1). mien_tu(c1,s1). "
     "g4_da_hoc(s1,30). tc_da_hoc(s1,3).",
     expect_true=["recognized(c1)", "vao_dtbctl(c1)", "g4(c1,30)", "tl_mau(3)"],
     expect_false=["diem_m(c1)", "exempted_m(c1)"],
     note="QĐ5339 Điều 3 k.11 — v1.0 kết luận SAI rằng mọi học phần được miễn đều nằm "
          "ngoài ĐTBCTL. So sánh trực tiếp với C5 (điểm M → tl_mau loại ra)")

test("C21 Miễn 1 học phần từ 2 học phần đã học → trung bình có trọng số",
     "khoa_tu_k45. course(c2,3). duoc_mien(c2). "
     "mien_tu(c2,s1). g4_da_hoc(s1,40). tc_da_hoc(s1,2). "
     "mien_tu(c2,s2). g4_da_hoc(s2,30). tc_da_hoc(s2,3).",
     expect_true=["g4(c2,34)"],
     note="QĐ5339 Điều 3 k.3 (QD-10): (4,0×2 + 3,0×3)/5 = 3,4 — LƯU Ý kết quả 3,4 KHÔNG nằm "
          "trên thang 8 bậc của bảng quy đổi; quy tắc gộp sinh ra điểm ngoài lưới")

test("C22 GDQP đạt điểm D → tích lũy theo QĐ3266 nhưng KHÔNG đạt theo QĐ5339",
     "khoa_tu_k45. course(qp,4). loai_hp(qp,gdqp). g10(qp,45).",
     expect_true=["passed(qp)", "khong_dat_gdqp(qp)"],
     note="QĐ5339 Điều 3 k.2 đặt ngưỡng D+ riêng cho GDQP&AN; QĐ3266 Điều 22 k.3 chỉ nói D. "
          "Hai vị từ cùng đúng trong một mô hình = xung đột lộ ra chứ không bị giấu")

test("C23 Điểm CHUYỂN ĐỔI 4,5/10 → KHÔNG tích lũy (QD-09 đã đóng)",
     "khoa_tu_k45. g10_ngoai(x1,45).",
     expect_true=["khong_tich_luy_chuyen(x1)", "bat_doi_xung_qd09(x1)", "dien_giai(qd09)"],
     expect_false=["tich_luy_chuyen(x1)", "g4_chuyen(x1,10)"],
     note="QD-09 đã đóng: ngưỡng 5,0 của QĐ5339 áp cho điểm chuyển đổi. dien_giai(qd09) buộc "
          "chứng chỉ nêu rõ đây là quyết định diễn giải, không phải câu chữ quy chế")

test("C23b Điểm CHUYỂN ĐỔI đúng 5,0 → tích lũy được, quy đổi thành D+ (1,5)",
     "khoa_tu_k45. g10_ngoai(x2,50).",
     expect_true=["tich_luy_chuyen(x2)", "g4_chuyen(x2,15)"],
     expect_false=["khong_tich_luy_chuyen(x2)", "bat_doi_xung_qd09(x2)"],
     note="ca biên 4,9 / 5,0 của ngưỡng tích lũy điểm chuyển đổi")

test("C23c BẤT ĐỐI XỨNG: cùng 4,5 điểm, học tại ĐHCT thì tích lũy được",
     "khoa_tu_k45. course(y1,3). g10(y1,45).",
     expect_true=["passed(y1)", "g4(y1,10)"],
     note="cùng con số 4,5: tích lũy tại ĐHCT (C23c) nhưng KHÔNG tích lũy nếu chuyển từ "
          "trường khác (C23). Hệ quả trực tiếp của QD-09 — ca đối kháng Tuần 17")

test("C24 Olympic giải khuyến khích (8,9) nhưng điểm học thật 9,5 → lấy 9,5",
     "khoa_tu_k45. course(c3,3). mien_thi(c3,khuyen_khich). g10_hoc(c3,95).",
     expect_true=["diem_hoc_cao_hon(c3)", "g10(c3,95)"],
     expect_false=["g10(c3,89)"],
     note="QĐ5339 Điều 3 k.10 — cùng nguyên tắc max với QĐ3266 Điều 17 k.2 (học cải thiện)")

test("C25 Miễn thi 3 học phần trong một học kỳ → vượt hạn mức 2 học phần",
     "khoa_tu_k45. hoc_ky(hk1). "
     "course(d1,3). course(d2,3). course(d3,3). "
     "mien_thi(d1,giai_nhat). mien_thi(d2,giai_nhi). mien_thi(d3,thanh_vien). "
     "hoc_trong_hk(hk1,d1). hoc_trong_hk(hk1,d2). hoc_trong_hk(hk1,d3).",
     expect_true=["vuot_han_mien_thi(hk1)"],
     note="QĐ5339 Điều 3 k.10 — trần 2 học phần/HK và 4 TC/học phần")

test("C26 ML010 → ML016 + ML018: một học phần đã học sinh hai học phần được miễn",
     'khoa_tu_k45. course("ML010",3). g10("ML010",80). '
     'course("ML016",2). course("ML018",2). '
     'duoc_mien("ML016"). duoc_mien("ML018"). '
     'g4_da_hoc("ML010",35). tc_da_hoc("ML010",3).',
     expect_true=['mien_tu("ML016","ML010")', 'mien_tu("ML018","ML010")',
                  'g4("ML016",35)', 'g4("ML018",35)'],
     note="QĐ5339 Điều 3 k.9 — bảng thay thế Lý luận chính trị, ca MỘT → NHIỀU: cả hai học "
          "phần được miễn đều nhận nguyên điểm của học phần đã học")


# =============================================================================
# C27–C31 — ĐỊNH NGHĨA VẬN HÀNH "TC NỢ ĐỌNG" (QD-03, chưa xác nhận nguồn)
# =============================================================================
HS_NO = """
khoa_tu_k45. khoa_tu_k47. che_do(suy_no_dong). hoc_ky(hk5).
course(m1,3). course(m2,3). course(m3,4). course(m4,3). course(m5,2).
dang_ky(hk1,m1). dang_ky(hk1,m2). dang_ky(hk2,m3). dang_ky(hk3,m4). dang_ky(hk4,m5).
g10(m1,80). g10(m2,70).          % m1, m2 da tich luy
g10(m3,35).                       % m3 diem F -> no 4 TC
dang_hoc(m4).                     % m4 dang hoc, chua co diem -> 3 TC
diem_w(m5).                       % m5 da rut hop le -> 2 TC
"""

test("C27 Nợ đọng theo mặc định = môn rớt + môn đang học (không tính môn đã rút)",
     HS_NO,
     expect_true=["tc_no_dong_suy(7)", "no_dong(m3)", "no_dong(m4)", "dien_giai(qd03)"],
     expect_false=["no_dong(m1)", "no_dong(m5)"],
     note="QD-03: 4 TC (m3 điểm F) + 3 TC (m4 đang học) = 7. m5 điểm W không tính")

test("C28 QD-03a tắt: không tính môn đang học → nợ đọng chỉ còn môn rớt",
     HS_NO + "chinh_sach_tat(tinh_dang_hoc).",
     expect_true=["tc_no_dong_suy(4)"],
     expect_false=["no_dong(m4)"],
     note="cùng một bảng điểm, hai chính sách cho 7 TC và 4 TC — chênh lệch đủ để đổi "
          "kết luận cảnh báo học vụ, nên đây không phải chi tiết vụn vặt")

test("C29 QD-03b bật: tính cả môn đã rút → nợ đọng tăng thêm 2 TC",
     HS_NO + "chinh_sach_bat(tinh_diem_w).",
     expect_true=["tc_no_dong_suy(9)", "no_dong(m5)"],
     note="phạt sinh viên vì đã dùng quyền rút học phần mà Điều 15 cho phép — "
          "nêu ra để thấy vì sao mặc định chọn ngược lại")

test("C30 Nợ đọng đúng 24 TC → KHÔNG cảnh báo ('vượt quá 24' nghĩa là > 24)",
     "khoa_tu_k47. khoa_tu_k45. hoc_ky(hk5). tc_no_dong(hk5,24).",
     expect_false=["canh_bao(hk5)"],
     note="Điều 18 k.2 đ.c — ca biên của ngưỡng")

test("C31 Nợ đọng 25 TC → CÓ cảnh báo",
     "khoa_tu_k47. khoa_tu_k45. hoc_ky(hk5). tc_no_dong(hk5,25).",
     expect_true=["canh_bao(hk5)"],
     note="Điều 18 k.2 đ.c")


# =============================================================================
# C32–C36 — SỐ LIỆU THẬT CỦA CTĐT CNTT K49 (v1.4)
# =============================================================================
test("C32 CTĐT CNTT K49: 4,5 năm thiết kế → trần 9 năm (18 nửa năm)",
     "da_hoc_nam2(17).",
     expect_true=["thoi_gian_toi_da_hk(27)"],
     expect_false=["qua_thoi_gian_toi_da", "thoi_gian_toi_da_hk(24)"],
     note="SỬA LỖI v1.0: tài liệu ghi nhầm K49 thiết kế 4 năm → trần 8 năm. CTĐT ghi rõ "
          "'Thời gian đào tạo: 4.5 năm', nên theo QĐ3266 Điều 5 trần là 9 năm",
     ctdt=True)

test("C33 Ba khối của CTĐT cộng đúng tổng 161 TC",
     "",
     expect_true=["tc_toi_thieu_ctdt(161)", "tc_bat_buoc_ctdt(125)"],
     note="ràng buộc nội tại trong ctdt_cntt_k49.lp: 56+46+59=161 và 41+46+38=125. "
          "Nếu gõ sai một số thì chương trình VÔ NGHIỆM, không im lặng cho kết quả sai",
     ctdt=True)

test("C34 Tiên quyết theo NGƯỠNG TÍN CHỈ (loại T4b mới): 119 TC chưa đủ làm luận văn",
     "course(x,119). g10(x,80).",
     expect_true=['thieu_tc("CT550E",1)'],
     expect_false=["du_dk_tin_chi_lam_lvtn"],
     note="CT550E Luận văn tốt nghiệp yêu cầu ≥120 TC — dạng tiên quyết mà taxonomy Tuần 2 "
          "chưa có: ngưỡng trên tiến độ tích lũy, không phải quan hệ giữa hai học phần",
     ctdt=True)

test("C35 Đủ 120 TC → đủ điều kiện VỀ TÍN CHỈ để làm luận văn",
     "course(x,120). g10(x,80).",
     expect_true=["du_dk_tin_chi_lam_lvtn", 'du_dk_tc("CT550E")'],
     note="trả lời được một phần câu hỏi mà QĐ3266 Điều 31 để ngỏ; các điều kiện khác của "
          "đơn vị đào tạo vẫn nằm ngoài nên kết luận dừng ở mức 'về tín chỉ'",
     ctdt=True)

test("C36 Nhóm chuyên ngành là 'chọn một trong ba cặp', không phải '10 chọn 2'",
     'course("CT211",3). course("CT297",3). g10("CT211",80). g10("CT297",70).',
     expect_true=["dat_nhom_cn", "chon_cn(cn1)"],
     expect_false=["nhieu_hon_mot_cn", "chon_cn(cn2)"],
     note="cấu trúc thật của CTĐT: 6 TC từ ĐÚNG MỘT cặp CN1/CN2/CN3, khác hẳn giả định "
          "'nhóm 10 chọn 2' dùng ở Tuần 2 và prototype Tuần 4",
     ctdt=True)


def section_c():
    print("\n" + "=" * 78)
    print("C. KIỂM THỬ NGỮ NGHĨA (clingo)")
    print("=" * 78)
    if not CLINGO_OK:
        print("  [BỎ QUA] Không nạp được clingo: " + CLINGO_ERR)
        print("  Phần A và B ở trên KHÔNG phụ thuộc clingo và vẫn có giá trị.")
        print("  Để chạy đủ 3 phần:  pip install -r requirements.txt")
        print(f"  ({len(TESTS)} ca kiểm thử chưa được chạy trong lần này.)")
        return 0, len(TESTS)
    passed = 0
    for name, facts, et, ef, note, ctdt in TESTS:
        model = solve(facts, ctdt=ctdt)
        miss = [a for a in et if a not in model]
        extra = [a for a in ef if a in model]
        ok = not miss and not extra
        passed += ok
        print((OK if ok else FAIL) + f" {name}")
        if note:
            print(f"          ↳ {note}")
        if not ok:
            if miss:
                print(f"          THIẾU  : {miss}")
            if extra:
                print(f"          THỪA   : {extra}")
            errors.append(name)
    print(f"\n  Kết quả: {passed}/{len(TESTS)} ca kiểm thử đạt")
    return passed, len(TESTS)


def main():
    cat = json.loads(JSON.read_text(encoding="utf-8"))
    lp_text = "\n".join(f.read_text(encoding="utf-8") for f in LP_FILES)
    print("=" * 78)
    print(f"KIỂM CHỨNG R-FORMAL v{cat['meta']['phien_ban']} — CPA² Tuần 5")
    for k, v in cat["meta"]["van_ban"].items():
        print(f"Nguồn {k}: {v['ten'][:66]}...")
    print("=" * 78)
    section_a(cat, lp_text)
    stats = section_b(cat)
    p, t = section_c()

    print("\n" + "=" * 78)
    if errors:
        print(f"KẾT LUẬN: CÓ {len(errors)} LỖI — R-Formal v1 CHƯA đạt tiêu chí hoàn thành.")
        for e in errors:
            print("   · " + e)
        return 1
    if not CLINGO_OK:
        print("KẾT LUẬN: A và B ĐẠT; phần C CHƯA CHẠY (thiếu clingo).")
        print(f"  · Formalization Coverage = {100*stats['F']/stats['n']:.1f}% "
              f"(F={stats['F']}, P={stats['P']}, N={stats['N']} trên {stats['n']} đơn vị)")
        print("  · Cài clingo rồi chạy lại để kiểm chứng đầy đủ: "
              "pip install -r requirements.txt")
        print("=" * 78)
        return 2
    print("KẾT LUẬN: ĐẠT.")
    print("  · Mọi quy tắc đều có con trỏ nguồn tới điều/khoản của "
          + " và ".join(cat["meta"]["van_ban"]).upper() + ".")
    print(f"  · Formalization Coverage = {100*stats['F']/stats['n']:.1f}% "
          f"(F={stats['F']}, P={stats['P']}, N={stats['N']} trên {stats['n']} đơn vị trong miền)")
    print(f"  · {p}/{t} ca kiểm thử ngữ nghĩa đạt.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
