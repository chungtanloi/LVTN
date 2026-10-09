"""
validate_elective.py — kiểm chứng Elective & N-of-M Solver Tuần 8 (CPA2)

Tiêu chí Tuần 8: "Pass bộ test N-of-M"

Ba nhóm:
  A. ĐẾM TÍN CHỈ (tin_chi): g_gdtc 3, g_xa_hoi 2, g_tot_nghiep 15
  B. MỘT NHÁNH (mot_nhanh): g_ngoai_ngu 10 (AV/PV), g_chuyen_nganh 6 (CN1/2/3)
  C. ĐẾM MÔN (dem_mon): nhóm demo "10 chọn 2" — không có ở K49, tạo tạm để test

Chạy:  python validate_elective.py
Mã thoát: 0 đạt, 1 có lỗi
"""
import sys
from pathlib import Path
import clingo

HERE = Path(__file__).parent
W5 = HERE.parent / "w5_rformal"
W6 = HERE.parent / "w6_curriculum"
W7 = HERE.parent / "w7_student_facts"

SCHEMA = W6 / "curriculum_schema.lp"
FACTS = W6 / "curriculum_cntt_k49.lp"
ELECTIVE = HERE / "elective_solver.lp"
RULES = [W5 / "qd3266_r_formal_v1.lp", W5 / "qd5339_r_formal_v1.lp"]

errors = []
OK, FAIL = "  [OK]  ", "  [FAIL]"

def check(cond, msg, note=""):
    print((OK if cond else FAIL) + " " + msg)
    if note: print("          ↳ " + note)
    if not cond: errors.append(msg)
    return cond

def txt(p): return p.read_text(encoding="utf-8")

def models(program, n=1):
    ctl = clingo.Control(["--warn=none", f"--models={n}"])
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    out=[]
    with ctl.solve(yield_=True) as h:
        for m in h: out.append({str(a) for a in m.symbols(atoms=True)})
    return out

def kb(extra="", with_elective=True):
    parts = [txt(p) for p in RULES] + [txt(SCHEMA), txt(FACTS)]
    if with_elective: parts.append(txt(ELECTIVE))
    return "\n".join(parts) + "\n" + extra

def solve_one(extra, with_elective=True):
    ms = models(kb(extra, with_elective))
    return ms[0] if ms else None

# =============================================================
# Helpers — sinh facts giống validate_curriculum.sv()
# =============================================================
BB = [h["ma"] for h in __import__("json").loads((W6 / "curriculum_cntt_k49.json").read_text(encoding="utf-8"))["hoc_phan"] if h["cot"]=="BB"]

def sv(chon, diem=80, bo=(), them=""):
    ds=[c for c in BB if c not in bo] + list(chon)
    return "\n".join(f'g10("{c}",{diem}).' for c in ds) + "\n" + them

CHUAN = ["TC100","XH023","XH024","XH025","ML007","CT449","CT484"]
KY_LUAT = "xac_nhan_ky_luat_sach.\n"

# =============================================================
# A. NHÓM ĐẾM TÍN CHỈ
# =============================================================
def test_tin_chi():
    print("\nA. NHÓM ĐẾM TÍN CHỈ (tin_chi)")
    # A1: GDTC thiếu
    m=solve_one(sv([], them=KY_LUAT))
    check(m is not None and "thieu_nhom(g_gdtc,3)" in m, "A1 GDTC rỗng → thiếu 3 TC")
    # A2: GDTC đủ (TC100 3 TC)
    m=solve_one(sv(["TC100"], them=KY_LUAT))
    check("dat_nhom(g_gdtc)" in m, "A2 GDTC đủ 3 TC (TC100)")
    # A3: Xã hội thiếu 2
    m=solve_one(sv(["TC100","XH023","XH024","XH025"], them=KY_LUAT))
    check("thieu_nhom(g_xa_hoi,2)" in m, "A3 Xã hội chưa học môn nào → thiếu 2")
    # A4: Xã hội đủ 2 (ML007 2 TC)
    m=solve_one(sv(["TC100","XH023","XH024","XH025","ML007"], them=KY_LUAT))
    check("dat_nhom(g_xa_hoi)" in m, "A4 Xã hội đủ 2 TC (ML007)")
    # A5: Xã hội dư (học 2 môn 4 TC)
    m=solve_one(sv(["TC100","XH023","XH024","XH025","ML007","XH028"], them=KY_LUAT))
    check("dat_nhom(g_xa_hoi)" in m and "tc_nhom_dat(g_xa_hoi,4)" in m, "A5 Xã hội dư 4 TC (>2) vẫn đạt", "T3 ca biên 3: dư không bị loại")
    # A6: Tốt nghiệp thiếu
    m=solve_one(sv(CHUAN, them=KY_LUAT))
    check("thieu_nhom(g_tot_nghiep,15)" in m, "A6 Tốt nghiệp chưa có HP nào → thiếu 15")
    # A7: Tốt nghiệp đủ LVTN
    m=solve_one(sv(CHUAN+["CT550E"], them=KY_LUAT))
    check("dat_nhom(g_tot_nghiep)" in m, "A7 Tốt nghiệp đủ LVTN 15 TC")
    # A8: Tốt nghiệp đủ TLTN+3HP
    m=solve_one(sv(CHUAN+["CT501E","CT478","CT283","CT233"], them=KY_LUAT))
    check("dat_nhom(g_tot_nghiep)" in m, "A8 Tốt nghiệp đủ TLTN 6+9=15")
    # A9: Tốt nghiệp đủ 5 HP lẻ (không qua LVTN/TLTN)
    m=solve_one(sv(CHUAN+["CT478","CT283","CT233","CT482","CT210"], them=KY_LUAT))
    check("dat_nhom(g_tot_nghiep)" in m, "A9 Tốt nghiệp đủ 5 HP lẻ 15 TC (QĐ31k3)")
    # A10: Tốt nghiệp thiếu 12 (chỉ có 3 TC)
    m=solve_one(sv(CHUAN+["CT478"], them=KY_LUAT))
    check("thieu_nhom(g_tot_nghiep,12)" in m, "A10 Tốt nghiệp chỉ 3 TC → thiếu 12")

# =============================================================
# B. NHÓM MỘT NHÁNH
# =============================================================
def test_mot_nhanh():
    print("\nB. NHÓM MỘT NHÁNH (mot_nhanh) — tín chỉ KHÔNG cộng dồn qua nhánh")
    # B1: Ngoại ngữ đủ AV
    m=solve_one(sv(["TC100","XH023","XH024","XH025","ML007","CT449","CT484","CT550E"], them=KY_LUAT))
    check("dat_nhom(g_ngoai_ngu)" in m and "dat_nhanh(g_ngoai_ngu,av)" in m, "B1 Ngoại ngữ đủ AV 10 TC (4+3+3)")
    # B2: Ngoại ngữ đủ PV
    m=solve_one(sv(["TC100","FL001","FL002","FL003","ML007","CT449","CT484","CT550E"], them=KY_LUAT))
    check("dat_nhom(g_ngoai_ngu)" in m and "dat_nhanh(g_ngoai_ngu,pv)" in m, "B2 Ngoại ngữ đủ PV 10 TC")
    # B3: Ngoại ngữ trộn AV 4 + PV 7 =11 nhưng thiếu (phải 10 trong MỘT nhánh)
    m=solve_one(sv(["TC100","XH023","FL001","FL002","ML007","CT449","CT484","CT550E"], them=KY_LUAT))
    check("thieu_nhom(g_ngoai_ngu,3)" in m and "dat_nhom(g_ngoai_ngu)" not in m, "B3 Trộn AV 4+PV 7 → thiếu 3 (I5)", "CQ-02: không cộng dồn")
    # B4: Ngoại ngữ thiếu 6 (chỉ AV 4)
    m=solve_one(sv(["TC100","XH023","ML007","CT449","CT484","CT550E"], them=KY_LUAT))
    check("thieu_nhom(g_ngoai_ngu,6)" in m, "B4 Ngoại ngữ chỉ AV 4 → thiếu 6")
    # B5: Ngoại ngữ AV 7 (4+3) thiếu 3
    m=solve_one(sv(["TC100","XH023","XH024","ML007","CT449","CT484","CT550E"], them=KY_LUAT))
    # XH023 4 + XH024 3 =7
    check("thieu_nhom(g_ngoai_ngu,3)" in m, "B5 Ngoại ngữ AV 7 → thiếu 3")
    # B6: Chuyên ngành đủ CN1
    m=solve_one('g10("CT211",80). g10("CT297",80).', with_elective=True)
    # cần kèm KB đầy đủ nhưng không cần BB
    # Dùng sv rỗng + 2 môn CN1
    extra = 'g10("CT211",80).\ng10("CT297",80).\n'
    m=solve_one(extra)
    check("dat_nhom(g_chuyen_nganh)" in m and "dat_nhanh(g_chuyen_nganh,cn1)" in m, "B6 Chuyên ngành đủ CN1 (6 TC)")
    # B7: Chuyên ngành đủ CN2
    m=solve_one('g10("CT449",80).\ng10("CT484",80).\n')
    check("dat_nhanh(g_chuyen_nganh,cn2)" in m, "B7 Chuyên ngành đủ CN2")
    # B8: Chuyên ngành đủ CN3
    m=solve_one('g10("CT522",80).\ng10("CT279",80).\n')
    check("dat_nhanh(g_chuyen_nganh,cn3)" in m, "B8 Chuyên ngành đủ CN3")
    # B9: Chuyên ngành chéo CN1+CN2 (3+3 nhưng khác nhánh) → thiếu
    m=solve_one('g10("CT211",80).\ng10("CT449",80).\n')
    check("dat_nhom(g_chuyen_nganh)" not in m and "thieu_nhom(g_chuyen_nganh,3)" in m, "B9 Chéo CT211(CN1)+CT449(CN2) → thiếu 3 (I9)")
    # B10: Chuyên ngành chỉ 1 môn 3 TC → thiếu 3
    m=solve_one('g10("CT211",80).\n')
    check("thieu_nhom(g_chuyen_nganh,3)" in m, "B10 Chuyên ngành 1 môn 3 TC → thiếu 3")

# =============================================================
# C. ĐẾM MÔN (dem_mon) — nhóm demo
# =============================================================
def test_dem_mon():
    print("\nC. NHÓM ĐẾM MÔN (dem_mon) — nhóm demo '10 chọn 2' (không có ở K49)")
    demo = """
course("DEMO1",3). course("DEMO2",3). course("DEMO3",3). course("DEMO4",3).
nhom(g_demo). nhom_kieu(g_demo,dem_mon). nhom_min_mon(g_demo,2).
thuoc_nhom(g_demo,"DEMO1"). thuoc_nhom(g_demo,"DEMO2").
thuoc_nhom(g_demo,"DEMO3"). thuoc_nhom(g_demo,"DEMO4").
"""
    # C1: 0 môn → thiếu 2
    m=solve_one(demo)
    check(m is not None and "thieu_nhom(g_demo,2)" in m, "C1 Demo 0 môn → thiếu 2")
    # C2: 1 môn → thiếu 1
    m=solve_one(demo + 'g10("DEMO1",80).\n')
    check("thieu_nhom(g_demo,1)" in m, "C2 Demo 1 môn → thiếu 1")
    # C3: 2 môn → đủ
    m=solve_one(demo + 'g10("DEMO1",80).\ng10("DEMO2",80).\n')
    check("dat_nhom(g_demo)" in m, "C3 Demo 2 môn → đủ")
    # C4: 3 môn → dư
    m=solve_one(demo + 'g10("DEMO1",80).\ng10("DEMO2",80).\ng10("DEMO3",80).\n')
    check("dat_nhom(g_demo)" in m and "mon_nhom_dat(g_demo,3)" in m, "C4 Demo 3 môn → đủ + dư")
    # C5: môn rớt (F) không tính
    m=solve_one(demo + 'g10("DEMO1",30).\n g10("DEMO2",80).\n')  # 30 = F
    check("thieu_nhom(g_demo,1)" in m, "C5 Môn điểm F không tính → vẫn thiếu 1")

# =============================================================
# D. TÍCH HỢP VỚI STUDENT FACTS TUẦN 7 + R-FORMAL
# =============================================================
def test_integration():
    print("\nD. TÍCH HỢP Student Facts Tuần 7 + R-Formal")
    import json
    # sv_lvtn đã đủ 161
    j=json.loads((W7 / "students/sv_lvtn.json").read_text(encoding="utf-8"))
    # chuyển thành g10 facts
    facts="\n".join(f'g10("{k}",{v["thang10"]}).' for k,v in j["grades"].items() if v.get("thang10") is not None)
    facts+="\nxac_nhan_ky_luat_sach.\n"
    m=solve_one(facts)
    check("dat_nhom(g_gdtc)" in m and "dat_nhom(g_ngoai_ngu)" in m and "dat_nhom(g_tot_nghiep)" in m, "D1 sv_lvtn đủ mọi nhóm → tot_nghiep", "kiểm tra tích hợp w7")
    check("tot_nghiep" in m, "D2 sv_lvtn tot_nghiep TRUE")
    # sv_tron_ngoai_ngu thiếu
    j2=json.loads((W7 / "students/sv_tron_ngoai_ngu.json").read_text(encoding="utf-8"))
    facts2="\n".join(f'g10("{k}",{v["thang10"]}).' for k,v in j2["grades"].items() if v.get("thang10") is not None)
    facts2+="\nxac_nhan_ky_luat_sach.\n"
    m2=solve_one(facts2)
    check("thieu_nhom(g_ngoai_ngu,3)" in m2 and "tot_nghiep" not in m2, "D3 sv_tron_ngoai_ngu thiếu ngoại ngữ → không tốt nghiệp")
    # elective missing helper
    check("hp_thieu_trong_nhom(g_ngoai_ngu,\"FL007\")" in m2 or "hp_thieu_trong_nhom(g_ngoai_ngu,\"XH024\")" in m2, "D4 hp_thieu_trong_nhom gợi ý HP còn thiếu")

def main():
    print("="*78)
    print("VALIDATE ELECTIVE & N-of-M — Tuần 8 (CPA2)")
    print("="*78)
    test_tin_chi()
    test_mot_nhanh()
    test_dem_mon()
    test_integration()
    print("\n"+"="*78)
    if errors:
        print(f"KẾT LUẬN: CÓ {len(errors)} LỖI")
        for e in errors: print("  ·",e)
        return 1
    print("KẾT LUẬN: ĐẠT — Elective Solver pass toàn bộ N-of-M")
    print("="*78)
    return 0

if __name__=="__main__": sys.exit(main())
