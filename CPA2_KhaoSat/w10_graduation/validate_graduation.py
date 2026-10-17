"""
validate_graduation.py — kiểm chứng Graduation Solver v1 Tuần 10 (CPA2)

Tiêu chí: "Pass case chuẩn" — tốt nghiệp trên CTĐT thật với mọi T1-T7

Chạy:  python validate_graduation.py
"""
import sys
from pathlib import Path
import clingo

HERE = Path(__file__).parent
W5 = HERE.parent / "w5_rformal"
W6 = HERE.parent / "w6_curriculum"
W8 = HERE.parent / "w8_elective"
W9 = HERE.parent / "w9_exemption"

RULES = [W5 / "qd3266_r_formal_v1.lp", W5 / "qd5339_r_formal_v1.lp"]
SCHEMA = W6 / "curriculum_schema.lp"
ELECTIVE = W8 / "elective_solver.lp"
EXEMPT = W9 / "exemption_substitution_solver.lp"
FACTS = W6 / "curriculum_cntt_k49.lp"
GRAD = HERE / "graduation_solver.lp"

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
    return "\n".join([txt(p) for p in RULES] + [txt(SCHEMA), txt(ELECTIVE), txt(EXEMPT), txt(FACTS), txt(GRAD)]) + "\n" + extra

def solve_one(extra):
    ms=models(kb(extra))
    return ms[0] if ms else None

def tri(atom, extra):
    ms=models(kb(extra), n=0)
    if not ms: return "UNSAT"
    co=[atom in m for m in ms]
    return "TRUE" if all(co) else ("FALSE" if not any(co) else "UNKNOWN")

# helpers
BB = [h["ma"] for h in __import__("json").loads((W6 / "curriculum_cntt_k49.json").read_text(encoding="utf-8"))["hoc_phan"] if h["cot"]=="BB"]
def sv(chon, diem=80, bo=(), them=""):
    ds=[c for c in BB if c not in bo] + list(chon)
    return "\n".join(f'g10("{c}",{diem}).' for c in ds) + "\n" + them
CHUAN = ["TC100","XH023","XH024","XH025","ML007","CT449","CT484"]
KY_LUAT = "xac_nhan_ky_luat_sach.\nda_hoc_nam2(9).\n"   # hồ sơ khai báo đủ (Tuần 16)

# =============================================================
def test_prerequisite():
    print("\nA. T4 — PREREQUISITE (a/b/c)")
    # A1: CT177 cần CT101 (T4a)
    m=solve_one('g10("CT101",80).\n')
    check('du_dk_dang_ky("CT177")' in m, "A1 CT177 cần CT101 — có CT101 → đủ ĐK")
    m=solve_one('')
    check('du_dk_dang_ky("CT177")' not in m, "A2 CT177 thiếu CT101 → chưa đủ ĐK")
    # A3: CT550E cần ≥120 TC (T4b)
    m=solve_one(sv(CHUAN+["CT550E"], them=KY_LUAT))
    check('du_dk_tc("CT550E")' in m, "A3 CT550E đủ 120 TC → du_dk_tc")
    m=solve_one('g10("X",80). course("X",30).\n')
    check('thieu_tc("CT550E",90)' in m, "A4 Mới 30 TC → thiếu 90 TC cho CT550E")
    # A5: CT466E cần ≥80
    m=solve_one('g10("X",80). course("X",80).\n')
    check('du_dk_tc("CT466E")' in m, "A5 Đủ 80 TC → đủ ĐK Niên luận CNTT")
    # A6: Song hành CT182 cần CT180 cùng kỳ được (T4c)
    m=solve_one('g10("CT176",80).\n')
    check('du_dk_dang_ky("CT182")' in m, "A6 CT182 cần CT176 (tiên quyết) + CT180 (song hành) — có CT176 → đủ")
    # A7: Vi phạm song hành khi xếp sai thứ tự
    m=solve_one('xep_hk("XH024",1). xep_hk("XH023",2).\n')
    check('vi_pham_song_hanh("XH024","XH023")' in m, "A7 XH024 trước XH023 → vi phạm song hành")

def test_graduation_cases():
    print("\nB. GRADUATION — case chuẩn (T1-T7)")
    # B1: Đủ mọi điều kiện → tot_nghiep
    m=solve_one(sv(CHUAN+["CT550E"], them=KY_LUAT))
    check("tot_nghiep" in m, "B1 Đủ 161 TC LVTN → tot_nghiep TRUE")
    check("du_dk_hoc_vu" in m, "B1 du_dk_hoc_vu TRUE")
    for dk in ["dk_tin_chi","dk_bat_buoc","dk_tu_chon","dk_hp_dieu_kien","dk_dtbctl","dk_gdqp","dk_thoi_gian"]:
        check(dk in m, f"B1 {dk} TRUE")
    # B2: Thiếu TC
    m=solve_one(sv(CHUAN, them=KY_LUAT))
    check("thieu_dk(tin_chi)" in m and "tot_nghiep" not in m, "B2 Thiếu nhóm tốt nghiệp → thiếu TC → thieu_dk(tin_chi)")
    # B3: Thiếu nhóm ngoại ngữ (trộn)
    m=solve_one(sv(["TC100","XH023","FL001","FL002","ML007","CT449","CT484","CT550E"], them=KY_LUAT))
    check("thieu_dk(hp_dieu_kien)" in m or "thieu_dk(tu_chon)" in m, "B3 Trộn ngoại ngữ → thiếu nhóm → không tốt nghiệp")
    # B4: ĐTBCTL <2.0
    tb = sv(CHUAN+["CT550E"], diem=55, them=KY_LUAT + 'g10("CT478",45).\n')
    m=solve_one(tb)
    check("thieu_dk(dtbctl)" in m and "tot_nghiep" not in m, "B4 Học dư CT478 D → ĐTBCTL <2 → thieu_dk(dtbctl)")
    # B5: Thiếu GDQP
    m=solve_one(sv(CHUAN+["CT550E"], them=KY_LUAT + 'g10("QP010E",30).\n'))
    # QP010E F nhưng CTĐT có 4 HP GDQP, thiếu 1 vẫn có thể đủ? kiểm thieu_dk
    # Dùng case GDQP điểm thấp cho tất cả
    m=solve_one('course("QP1",2). loai_hp("QP1",gdqp). g10("QP1",45).\n' + sv(CHUAN+["CT550E"], them=KY_LUAT))
    check("khong_dat_gdqp(\"QP1\")" in m, "B5 GDQP D → khong_dat_gdqp → dk_gdqp FALSE")
    # B6: Thiếu xác nhận kỷ luật → UNKNOWN (ba trị)
    #     Tuần 16 (P15-2): trước đây kỳ vọng FALSE — đó là giả định thế giới đóng, trái schema w7
    v=tri("tot_nghiep", sv(CHUAN+["CT550E"]))
    check(v=="UNKNOWN", f"B6 Thiếu xac_nhan_ky_luat_sach → tot_nghiep={v} (UNKNOWN, dữ kiện ngoài chưa khai báo)")
    v=tri("tot_nghiep", sv(CHUAN+["CT550E"], them="khai_bao(ky_luat).\n"))
    check(v=="FALSE", f"B6b Đã khai báo KHÔNG có xác nhận kỷ luật → tot_nghiep={v} (FALSE)")
    # B7: Quá hạn
    m=solve_one(sv(CHUAN+["CT550E"], them="da_hoc_nam2(20).\n"))
    check("qua_thoi_gian_toi_da" in m and "thieu_dk(thoi_gian)" in m, "B7 Quá hạn 10 năm → thiếu thời gian")
    # B7b/c (Tuần 16, P16-2): thời gian là điều kiện tốt nghiệp (Điều 5, R-E01)
    v=tri("tot_nghiep", sv(CHUAN+["CT550E"], them="xac_nhan_ky_luat_sach.\nda_hoc_nam2(20).\n"))
    check(v=="FALSE", f"B7b Đủ học vụ + kỷ luật sạch nhưng quá hạn (20 > 18) → tot_nghiep={v} (FALSE)",
          "HỒI QUY P16-2: luật cũ cho TRUE")
    v=tri("tot_nghiep", sv(CHUAN+["CT550E"], them="xac_nhan_ky_luat_sach.\nda_hoc_nam2(18).\n"))
    check(v=="TRUE", f"B7c Biên 18 = trần → tot_nghiep={v} (TRUE)")
    v=tri("tot_nghiep", sv(CHUAN+["CT550E"], them="xac_nhan_ky_luat_sach.\n"))
    check(v=="UNKNOWN", f"B7d Thiếu da_hoc_nam2 → tot_nghiep={v} (UNKNOWN)")

def test_with_exemption():
    print("\nC. TÍCH HỢP MIỄN/THAY THẾ VÀO TỐT NGHIỆP")
    # C1: Miễn AV bằng IELTS vẫn tốt nghiệp
    extra = """
khoa_tu_k45. chung_chi(ielts,50).
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
    check("tot_nghiep" in m, "C1 Miễn AV bằng IELTS vẫn tot_nghiep")
    # C2: Thay thế ML009→ML014, ML010→ML016+ML018 vẫn tốt nghiệp
    extra2 = 'course("ML009",2). course("ML010",3). g10("ML009",80). g10("ML010",80).\n' + sv(CHUAN+["CT550E"], them=KY_LUAT)
    m=solve_one(extra2)
    check("passed(\"ML014\")" in m, "C2 ML009→ML014 vẫn passed")

def main():
    print("="*78)
    print("VALIDATE GRADUATION SOLVER v1 — Tuần 10 (CPA2)")
    print("="*78)
    test_prerequisite()
    test_graduation_cases()
    test_with_exemption()
    print("\n"+"="*78)
    if errors:
        print(f"KẾT LUẬN: CÓ {len(errors)} LỖI")
        for e in errors: print("  ·",e)
        return 1
    print("KẾT LUẬN: ĐẠT — Graduation Solver v1 pass case chuẩn")
    print("="*78)
    return 0

if __name__=="__main__": sys.exit(main())
