"""
validate_proof.py — kiểm chứng Proof Certificate Tuần 11 (CPA2)

Tiêu chí: "Mỗi kết luận có trace" — Claim→Proof→Rule→Fact→Source

Chạy:  python validate_proof.py
"""
import json, re, sys
from pathlib import Path
import clingo

HERE = Path(__file__).parent
W5 = HERE.parent / "w5_rformal"
W6 = HERE.parent / "w6_curriculum"
W8 = HERE.parent / "w8_elective"
W9 = HERE.parent / "w9_exemption"
W10 = HERE.parent / "w10_graduation"

RULES = [W5 / "qd3266_r_formal_v1.lp", W5 / "qd5339_r_formal_v1.lp"]
SCHEMA = W6 / "curriculum_schema.lp"
ELECTIVE = W8 / "elective_solver.lp"
EXEMPT = W9 / "exemption_substitution_solver.lp"
FACTS = W6 / "curriculum_cntt_k49.lp"
GRAD = W10 / "graduation_solver.lp"
CATALOG = W5 / "r_formal_v1.json"

errors=[]
OK, FAIL = "  [OK]  ", "  [FAIL]"

def check(cond, msg, note=""):
    print((OK if cond else FAIL) + " " + msg)
    if note: print("          ↳ " + note)
    if not cond: errors.append(msg)
    return cond

def txt(p): return p.read_text(encoding="utf-8")

def kb(extra):
    return "\n".join([txt(p) for p in RULES] + [txt(SCHEMA), txt(ELECTIVE), txt(EXEMPT), txt(FACTS), txt(GRAD)]) + "\n" + extra

def models(prog, n=1):
    ctl=clingo.Control(["--warn=none", f"--models={n}"])
    ctl.add("base", [], prog)
    ctl.ground([("base",[])])
    out=[]
    with ctl.solve(yield_=True) as h:
        for m in h: out.append({str(a) for a in m.symbols(atoms=True)})
    return out

def verdict(claim, extra):
    ms=models(kb(extra), n=0)
    if not ms: return "UNSAT", ms
    co=[claim in m for m in ms]
    if all(co): return "TRUE", ms
    if not any(co): return "FALSE", ms
    return "UNKNOWN", ms

# chuẩn bị dữ liệu sinh viên như w7
def sv(chon, diem=80, them=""):
    BB=[h["ma"] for h in json.loads((W6 / "curriculum_cntt_k49.json").read_text(encoding="utf-8"))["hoc_phan"] if h["cot"]=="BB"]
    ds=[c for c in BB if c not in []] + list(chon)
    return "\n".join(f'g10("{c}",{diem}).' for c in ds) + "\n" + them
CHUAN=["TC100","XH023","XH024","XH025","ML007","CT449","CT484"]
KY_LUAT="xac_nhan_ky_luat_sach.\nda_hoc_nam2(9).\n"   # hồ sơ khai báo đủ (Tuần 16)

def test_invariant():
    print("\nA. BẤT BIẾN CON TRỎ NGUỒN (mở rộng từ w5)")
    lp_text="\n".join([txt(p) for p in RULES] + [txt(SCHEMA), txt(ELECTIVE), txt(EXEMPT), txt(FACTS), txt(GRAD)])
    src=set(re.findall(r"rule_src\((\w+),", lp_text))
    whys=set(re.findall(r"why\([^,]*,\s*(\w+)\)", lp_text))
    whys={w for w in whys if w.startswith("r_")}
    check(whys <= src, f"A1 mọi why/2 ({len(whys)}) đều có rule_src ({len(src)})")
    cat=json.loads(CATALOG.read_text(encoding="utf-8"))
    by_asp={r["asp"] for r in cat["rules"] if r.get("asp")}
    check(whys <= by_asp, f"A2 mọi why trong proof đều có bản ghi JSON")

def test_true_proof():
    print("\nB. TRUE — có proof đầy đủ")
    extra=sv(CHUAN+["CT550E"], them=KY_LUAT)
    v, ms = verdict("tot_nghiep", extra)
    check(v=="TRUE", f"B1 tot_nghiep TRUE khi đủ 161 TC LVTN (verdict={v})")
    m=ms[0] if ms else set()
    # why(tot_nghiep, r_f01a) hoặc r_f03 phải có
    has_why=any(a.startswith('why(tot_nghiep') for a in m)
    check(has_why, "B2 tot_nghiep có why/2 truy về rule_src")
    has_dk=any(a.startswith('why(du_dk_hoc_vu') for a in m)
    check(has_dk, "B3 du_dk_hoc_vu có why")
    # thieu_dk không có khi đủ
    check(not any('thieu_dk' in a for a in m if a.startswith('thieu_dk')), "B4 không có thieu_dk khi đủ")

def test_false_proof():
    print("\nC. FALSE — có phản ví dụ (counterexample)")
    extra=sv(CHUAN, them=KY_LUAT)  # thiếu nhóm tốt nghiệp
    v, ms = verdict("tot_nghiep", extra)
    check(v=="FALSE", f"C1 tot_nghiep FALSE khi thiếu nhóm (verdict={v})")
    m=ms[0] if ms else set()
    check('thieu_nhom(g_tot_nghiep,15)' in m, "C2 phản ví dụ: thieu_nhom(g_tot_nghiep,15)")
    check('why(thieu_nhom(g_tot_nghiep,15),r_a02)' in m, "C3 phản ví dụ có why truy về r_a02 (Đ7 k3)")

def test_unknown_proof():
    print("\nD. UNKNOWN — có missing_facts (brave \\ cautious)")
    # thiếu điểm LVTN: 2 thế giới (có/không đạt)
    extra=sv(CHUAN, them=KY_LUAT + '{ g10("CT550E",80); g10("CT550E",30) } = 1.\n')
    v, ms = verdict("tot_nghiep", extra)
    check(v=="UNKNOWN", f"D1 tot_nghiep UNKNOWN khi thiếu điểm LVTN (verdict={v})")
    # missing facts = bravery - cautious phải chứa g10(CT550E)
    cautious=set.intersection(*ms) if ms else set()
    brave=set.union(*ms) if ms else set()
    diff=brave - cautious
    has_missing=any('CT550E' in a for a in diff)
    check(has_missing, f"D2 missing_facts chứa CT550E (brave\\cautious = {sorted([a for a in diff if 'CT550E' in a])[:3]})")
    # tot_nghiep không cautious khi UNKNOWN
    has_cautious="tot_nghiep" in cautious
    check(not has_cautious, "D3 UNKNOWN: tot_nghiep không trong cautious (chứng chỉ phải nói UNKNOWN)")

def test_exemption_proof():
    print("\nE. PROOF CHO MIỄN/THAY THẾ")
    extra='course("AV1",4). loai_hp("AV1",ngoai_ngu_cb). ngon_ngu_hp("AV1",anh). khoa_tu_k45.\nchung_chi(ielts,50).\nduoc_mien("AV1").\n'
    v, ms = verdict('exempted_m("AV1")', extra)
    check(v=="TRUE", "E1 exempted_M có proof khi có duoc_mien")
    m=ms[0] if ms else set()
    check('why(exempted_m("AV1"),r_m15)' in m, "E1 why về r_m15 (Đ3 k11)")

def main():
    print("="*78)
    print("VALIDATE PROOF CERTIFICATE — Tuần 11 (CPA2)")
    print("Claim → Proof → Rule → Fact → Source")
    print("="*78)
    test_invariant()
    test_true_proof()
    test_false_proof()
    test_unknown_proof()
    test_exemption_proof()
    print("\n"+"="*78)
    if errors:
        print(f"KẾT LUẬN: CÓ {len(errors)} LỖI")
        for e in errors: print("  ·",e)
        return 1
    print("KẾT LUẬN: ĐẠT — Mỗi kết luận có trace Claim→Proof→Rule→Fact→Source")
    print("="*78)
    return 0

if __name__=="__main__": sys.exit(main())
