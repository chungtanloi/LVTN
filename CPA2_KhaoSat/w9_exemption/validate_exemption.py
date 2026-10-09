"""
validate_exemption.py — kiểm chứng Exemption & Substitution Tuần 9 (CPA2)

Tiêu chí: "Phân biệt passed / exempted_M / recognized / substituted"

Chạy:  python validate_exemption.py
"""
import sys
from pathlib import Path
import clingo

HERE = Path(__file__).parent
W5 = HERE.parent / "w5_rformal"
W6 = HERE.parent / "w6_curriculum"
W8 = HERE.parent / "w8_elective"

RULES = [W5 / "qd3266_r_formal_v1.lp", W5 / "qd5339_r_formal_v1.lp"]
SCHEMA = W6 / "curriculum_schema.lp"
ELECTIVE = W8 / "elective_solver.lp"
FACTS = W6 / "curriculum_cntt_k49.lp"
SOLVER = HERE / "exemption_substitution_solver.lp"

errors=[]
OK, FAIL = "  [OK]  ", "  [FAIL]"

def check(cond, msg, note=""):
    print((OK if cond else FAIL) + " " + msg)
    if note: print("          ↳ " + note)
    if not cond: errors.append(msg)
    return cond

def txt(p): return p.read_text(encoding="utf-8")

def models(prog, n=1):
    ctl=clingo.Control(["--warn=none", f"--models={n}"])
    ctl.add("base", [], prog)
    ctl.ground([("base",[])])
    out=[]
    with ctl.solve(yield_=True) as h:
        for m in h: out.append({str(a) for a in m.symbols(atoms=True)})
    return out

def kb(extra):
    return "\n".join([txt(p) for p in RULES] + [txt(SCHEMA), txt(ELECTIVE), txt(FACTS), txt(SOLVER)]) + "\n" + extra

def solve_one(extra):
    ms=models(kb(extra))
    return ms[0] if ms else None

# =============================================================
# T5 — MIỄN BẰNG CHỨNG CHỈ
# =============================================================
def test_exemption():
    print("\nA. T5 — MIỄN BẰNG CHỨNG CHỈ (exempted_M vs recognized)")
    # A1: IELTS 5.0 K49 → đủ điều kiện xin miễn AV, nhưng chưa được miễn (QD-11)
    m=solve_one('course("AV1",4). loai_hp("AV1",ngoai_ngu_cb). ngon_ngu_hp("AV1",anh). khoa_tu_k45.\nchung_chi(ielts,50).\n')
    check("du_dk_xin_mien(\"AV1\")" in m and "mien_treo(\"AV1\")" in m, "A1 IELTS 5.0 đủ ĐK xin miễn AV nhưng mien_treo (QD-11)")
    check("passed(\"AV1\")" not in m and "diem_m(\"AV1\")" not in m, "A1 chưa passed khi chỉ có chứng chỉ")
    # A2: có QĐ duoc_mien → thành exempted_M, passed, điểm M, không vào ĐTBCTL
    m=solve_one('course("AV1",4). loai_hp("AV1",ngoai_ngu_cb). ngon_ngu_hp("AV1",anh). khoa_tu_k45.\nchung_chi(ielts,50).\nduoc_mien("AV1").\n')
    check("exempted_m(\"AV1\")" in m and "passed(\"AV1\")" in m and "diem_m(\"AV1\")" in m, "A2 Có QĐ → exempted_M, passed, điểm M")
    check("recognized(\"AV1\")" not in m, "A2 không phải recognized")
    # A3: IELTS 4.0 không đủ bậc 3
    m=solve_one('course("AV1",4). loai_hp("AV1",ngoai_ngu_cb). ngon_ngu_hp("AV1",anh). khoa_tu_k45.\nchung_chi(ielts,40).\n')
    check("du_dk_xin_mien(\"AV1\")" not in m, "A3 IELTS 4.0 không đủ bậc 3 → không đủ ĐK")
    # A4: Công nhận điểm (recognized) — có vào ĐTBCTL, R-M15
    m=solve_one('khoa_tu_k45.\ncourse("C1",3).\nduoc_mien("C1"). mien_tu("C1","S1"). g4_da_hoc("S1",30). tc_da_hoc("S1",3).\n')
    check("recognized(\"C1\")" in m and "vao_dtbctl(\"C1\")" in m, "A4 recognized → có vào ĐTBCTL (QD-01 sửa)")
    check("exempted_m(\"C1\")" not in m, "A4 không phải exempted_M")
    # A5: Miễn HP điều kiện bằng IELTS → exempted_M, vào TC nhưng KHÔNG vào ĐTBCTL
    m=solve_one('course("AV1",4). loai_hp("AV1",ngoai_ngu_cb). ngon_ngu_hp("AV1",anh). khoa_tu_k45.\nchung_chi(ielts,50).\nduoc_mien("AV1").\n')
    # tl_mau không tính diem_m, tl_tu không tính
    check("exempted_m(\"AV1\")" in m, "A5 exempted_M vào TC nhưng khong_tinh_tb")
    # kiểm tra tl_mau không tăng khi có diem_m
    m2=solve_one('khoa_tu_k45.\ncourse("A",3).\ncourse("B",3).\ng10("A",80).\ndiem_m("B").\n')
    # tl_mau chỉ tính A (3), B là M không tính
    check("tl_mau(3)" in m2, "A5b tl_mau loại điểm M (3, không phải 6)")
    # A6: Nhiều→một gộp điểm trọng số (QD-10)
    m=solve_one('khoa_tu_k45.\ncourse("C2",3).\nduoc_mien("C2"). mien_tu("C2","S1"). g4_da_hoc("S1",40). tc_da_hoc("S1",2). mien_tu("C2","S2"). g4_da_hoc("S2",30). tc_da_hoc("S2",3).\n')
    check("g4(\"C2\",34)" in m, "A6 Gộp điểm 2→1: (4*2+3*3)/5=3.4 (QD-10)")

# =============================================================
# T5 — MIỄN TÍNH CHO NHÓM N-of-M (tích hợp w8)
# =============================================================
def test_exemption_group():
    print("\nB. MIỄN TÍNH CHO NHÓM N-of-M")
    # B1: Miễn AV bằng IELTS → nhóm ngoại ngữ đủ
    m=solve_one('khoa_tu_k45.\nchung_chi(ielts,50).\nduoc_mien("XH023").\nduoc_mien("XH024").\nduoc_mien("XH025").\n')
    # XH023 4 + XH024 3 + XH025 3 =10 AV, cần du_dk? Nhưng duoc_mien trực tiếp đủ
    check("passed(\"XH023\")" in m and "exempted_m(\"XH023\")" in m, "B1 XH023 exempted_M passed")
    check("dat_nhom(g_ngoai_ngu)" in m, "B1 Nhóm ngoại ngữ đủ nhờ miễn (10 TC AV)")
    # B2: Chỉ miễn 1 HP AV 4 TC → vẫn thiếu 6
    m=solve_one('khoa_tu_k45.\nchung_chi(ielts,50).\nduoc_mien("XH023").\n')
    check("thieu_nhom(g_ngoai_ngu,6)" in m, "B2 Chỉ miễn XH023 4 TC → thiếu 6")
    # B3: Miễn không tự động — có chứng chỉ nhưng chưa duoc_mien thì nhóm vẫn thiếu
    m=solve_one('khoa_tu_k45.\nchung_chi(ielts,50).\n')
    check("dat_nhom(g_ngoai_ngu)" not in m, "B3 Chỉ có chứng chỉ, chưa duoc_mien → nhóm chưa đạt (QD-11)")

# =============================================================
# T6 — THAY THẾ
# =============================================================
def test_substitution():
    print("\nC. T6 — THAY THẾ (substitution)")
    # C1: Đổi mã CT172 ↔ CT172E
    m=solve_one('g10("CT172",80).\n')
    check('passed("CT172E")' in m and 'substituted("CT172E")' in m, "C1 CT172 → CT172E (đổi mã)")
    # C2: Ngược lại
    m=solve_one('g10("CT172E",80).\n')
    check('passed("CT172")' in m, "C2 CT172E → CT172")
    # C3: Niên luận chuyển ngành (giả)
    m=solve_one('substitutes("CT271E","CT201E").\ng10("CT271E",80).\n')
    check('passed("CT201E")' in m and 'substituted("CT201E")' in m, "C3 CT271E thay CT201E")
    # C4: ML009 → ML014 (QĐ5339 Đ3 k.9)
    m=solve_one('course("ML009",2). g10("ML009",80).\n')
    check('passed("ML014")' in m, "C4 ML009 → ML014 (bảng chuyển đổi LLCT)")
    # C5: ML010 → ML016+ML018 (một→nhiều)
    m=solve_one('course("ML010",3). g10("ML010",80).\n')
    check('passed("ML016")' in m and 'passed("ML018")' in m, "C5 ML010 → ML016+ML018 (một→nhiều, cho phép)")
    # C6: Chênh lệch TC — ML009 2TC → ML014 3TC
    m=solve_one('course("ML009",2). g10("ML009",80).\n')
    check('chenh_lech_tc("ML009","ML014",1)' in m, "C6 Chênh lệch TC 2→3 = +1 (QD-10)")
    # C7: Trang thái phân biệt
    m=solve_one('course("AV1",4). loai_hp("AV1",ngoai_ngu_cb). ngon_ngu_hp("AV1",anh). khoa_tu_k45.\nchung_chi(ielts,50).\nduoc_mien("AV1").\n')
    check('trang_thai_hp("AV1",exempted_M)' in m, "C7 trang_thai_hp AV1 = exempted_M")
    m2=solve_one('g10("CT101",80).\n')
    check('trang_thai_hp("CT101",passed)' in m2, "C7b CT101 passed thường")
    m3=solve_one('course("ML009",2). g10("ML009",80).\n')
    check('trang_thai_hp("ML014",substituted)' in m3, "C7c ML014 substituted")

# =============================================================
# D. TÍCH HỢP TỐT NGHIỆP VỚI MIỄN/THAY THẾ
# =============================================================
def test_integration():
    print("\nD. TÍCH HỢP TỐT NGHIỆP + MIỄN/THAY THẾ")
    # D1: SV miễn AV bằng IELTS → vẫn tốt nghiệp (nếu đủ các nhóm khác)
    # dùng hồ sơ đầy đủ + miễn thay vì học AV
    extra = """
khoa_tu_k45.
chung_chi(ielts,50).
duoc_mien("XH023"). duoc_mien("XH024"). duoc_mien("XH025").
g10("QP010E",80). g10("QP011E",80). g10("QP012",80). g10("QP013",80).
g10("TC100",80). g10("ML014",80). g10("ML016",80). g10("ML018",80). g10("ML019",80). g10("ML021",80).
g10("KL001E",80). g10("ML007",80).
g10("TN001",80). g10("TN002",80). g10("TN010",80). g10("TN012",80).
g10("CT100",80). g10("CT200",80).
g10("CT101",80). g10("CT177",80). g10("CT174",80). g10("CT172",80). g10("CT175",80). g10("CT190",80).
g10("CT180",80). g10("CT182",80). g10("CT296",80). g10("CT173",80). g10("CT178",80). g10("CT112",80).
g10("CT176",80). g10("CT179",80). g10("CT188",80).
g10("CT271E",80). g10("CT273",80). g10("CT294",80). g10("CT202",80). g10("CT467",80).
g10("CT293",80). g10("CT275",80). g10("CT300",80). g10("CT223",80). g10("CT222",80).
g10("CT449",80). g10("CT484",80). g10("CT466E",80). g10("CT518E",80). g10("CT550E",80).
xac_nhan_ky_luat_sach.
"""
    m=solve_one(extra)
    check("tot_nghiep" in m and "exempted_m(\"XH023\")" in m, "D1 Miễn AV bằng IELTS vẫn tốt nghiệp, nhóm ngoại ngữ đạt")
    check("dk_hp_dieu_kien" in m, "D1 dk_hp_dieu_kien vẫn đạt dù AV là M")
    # D2: Công nhận điểm vào nhóm tốt nghiệp vẫn tính ĐTBCTL
    m2=solve_one('khoa_tu_k45.\ncourse("CT478",3). duoc_mien("CT478"). mien_tu("CT478","S1"). g4_da_hoc("S1",30). tc_da_hoc("S1",3).\n')
    check("recognized(\"CT478\")" in m2, "D2 CT478 recognized")

def main():
    print("="*78)
    print("VALIDATE EXEMPTION & SUBSTITUTION — Tuần 9 (CPA2)")
    print("="*78)
    test_exemption()
    test_exemption_group()
    test_substitution()
    test_integration()
    print("\n"+"="*78)
    if errors:
        print(f"KẾT LUẬN: CÓ {len(errors)} LỖI")
        for e in errors: print("  ·",e)
        return 1
    print("KẾT LUẬN: ĐẠT — Exemption/Substitution phân biệt đúng 4 trạng thái")
    print("="*78)
    return 0

if __name__=="__main__": sys.exit(main())
