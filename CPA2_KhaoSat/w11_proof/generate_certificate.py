"""
generate_certificate.py — sinh Proof Certificate Claim→Proof→Rule→Fact→Source (CPA2 Tuần 11)

Lược đồ: proof_schema.json
Đầu vào: claim (atom), hồ sơ facts (g10/2, duoc_mien/1, ...), KB (R-Formal + Curriculum)
Đầu ra: JSON certificate với verdict TRUE/FALSE/UNKNOWN + proof steps có rule_src/5 + source trích

Chạy:  python generate_certificate.py --claim tot_nghiep --student w7_student_facts/students/sv_lvtn.json
       python generate_certificate.py --claim thieu_nhom --student demo --extra 'g10("XH023",80).'
"""
import json, sys, argparse
from pathlib import Path
import clingo

HERE = Path(__file__).parent
W5 = HERE.parent / "w5_rformal"
W6 = HERE.parent / "w6_curriculum"
W8 = HERE.parent / "w8_elective"
W9 = HERE.parent / "w9_exemption"
W10 = HERE.parent / "w10_graduation"
W7 = HERE.parent / "w7_student_facts"

RULES = [W5 / "qd3266_r_formal_v1.lp", W5 / "qd5339_r_formal_v1.lp"]
SCHEMA = W6 / "curriculum_schema.lp"
ELECTIVE = W8 / "elective_solver.lp"
EXEMPT = W9 / "exemption_substitution_solver.lp"
FACTS = W6 / "curriculum_cntt_k49.lp"
GRAD = W10 / "graduation_solver.lp"
CATALOG = W5 / "r_formal_v1.json"

def txt(p): return p.read_text(encoding="utf-8")

def load_student(path):
    j=json.loads(Path(path).read_text(encoding="utf-8"))
    lines=[]
    for code,g in j.get("grades",{}).items():
        th=g.get("thang10"); diem=g.get("diem")
        if diem=="M": lines.append(f'diem_m("{code}").')
        elif diem=="W": lines.append(f'diem_w("{code}").')
        elif diem=="I": lines.append(f'diem_i("{code}").')
        elif th is not None: lines.append(f'g10("{code}",{th}).')
    for c in j.get("khong_tinh_tich_luy",[]): lines.append(f'khong_tinh_tich_luy("{c}").')
    if j.get("xac_nhan_ky_luat_sach") is True: lines.append('xac_nhan_ky_luat_sach.')
    elif j.get("xac_nhan_ky_luat_sach") is False: lines.append('khai_bao(ky_luat).')  # null/thiếu → mở nhánh (Tuần 16)
    for k in ("da_hoc_nam2","tc_cong_nhan"):
        if j.get(k) is not None: lines.append(f'{k}({j[k]}).')
    for c in j.get("certificates",[]):
        loai=c["loai"]; diem=int(c["diem"]) if loai=="ctu_abc" else round(c["diem"]*10)  # nguong_cc lưu điểm ×10
        lines.append(f'chung_chi({loai},{diem}).')
    for ex in j.get("exemptions",[]):
        if ex["quyet_dinh"]: lines.append(f'duoc_mien("{ex["ma_hp"]}").')
    return "\n".join(lines)

def kb(extra):
    return "\n".join([txt(p) for p in RULES] + [txt(SCHEMA), txt(ELECTIVE), txt(EXEMPT), txt(FACTS), txt(GRAD)]) + "\n" + extra

def all_models(extra, n=0):
    prog=kb(extra)
    ctl=clingo.Control(["--warn=none", f"--models={n}"])
    ctl.add("base", [], prog)
    ctl.ground([("base",[])])
    out=[]
    with ctl.solve(yield_=True) as h:
        for m in h: out.append({str(a) for a in m.symbols(atoms=True)})
    return out

def verdict_for(claim, extra):
    ms=all_models(extra, n=0)
    if not ms: return "UNSAT", []
    co=[claim in m for m in ms]
    if all(co): return "TRUE", ms
    if not any(co): return "FALSE", ms
    return "UNKNOWN", ms

def build_certificate(claim, extra, student_id="demo"):
    verdict, models = verdict_for(claim, extra)
    # lấy 1 model đại diện để trích why
    rep = models[0] if models else set()
    # thu thập why(atom, rule_id) trong rep
    whys = [a for a in rep if a.startswith("why(")]
    # map rule_id -> source từ catalog
    cat=json.loads(CATALOG.read_text(encoding="utf-8"))
    by_asp={r["asp"]: r for r in cat["rules"] if r.get("asp")}
    # rule_src map
    import re
    lp_text="\n".join([txt(p) for p in RULES] + [txt(SCHEMA), txt(ELECTIVE), txt(EXEMPT), txt(FACTS), txt(GRAD)])
    src={}
    for m in re.finditer(r"rule_src\((\w+),\s*(\w+),\s*(\d+),\s*(\w+),\s*(\w+)\)\.", lp_text):
        src[m.group(1)]=(m.group(2), int(m.group(3)), m.group(4), m.group(5))
    # build steps: mỗi why tương ứng với 1 bước
    steps=[]
    qd_set=set()
    for w in sorted(whys):
        # why(atom, rule_id) -> parse
        m=re.match(r"why\((.+),\s*(\w+)\)", w)
        if not m: continue
        atom, rid = m.group(1), m.group(2)
        if rid not in by_asp: continue
        rec=by_asp[rid]
        # chỉ lấy các bước liên quan đến claim hoặc điều kiện thành phần
        # Ở đây lấy tất cả để demo; thực tế sẽ lọc theo dependency graph
        facts=[]  # facts liên quan — đơn giản: liệt kê g10/diem_m/duoc_mien trong rep
        # heuristically: nếu atom là tot_nghiep thì facts là các dk_*
        steps.append({
            "atom": atom,
            "rule_id": rid,
            "source": {
                "van_ban": rec["van_ban"],
                "dieu": rec["dieu"],
                "khoan": rec["khoan"],
                "diem": rec["diem"],
                "trich": rec["trich"][:200]
            },
            "facts": facts
        })
        if rec.get("quyet_dinh"):
            qd_set.add(rec["quyet_dinh"].split()[0])
    # missing facts khi UNKNOWN: brave \ cautious
    missing=[]
    if verdict=="UNKNOWN":
        # cautious = giao, brave = hợp
        cautious=set.intersection(*models) if models else set()
        brave=set.union(*models) if models else set()
        diff=sorted(brave - cautious)
        # lọc chỉ các atom liên quan đến claim
        missing=[a for a in diff if "g10" in a or "passed" in a or "tich_luy" in a or "duoc_mien" in a][:10]
    return {
        "claim": claim,
        "verdict": verdict,
        "proof": {"steps": steps[:20]},
        "missing_facts": missing,
        "meta": {"student_id": student_id, "solver": "clingo", "qd_dien_giai": sorted(qd_set)}
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--claim", required=True, help="atom claim, vd tot_nghiep")
    ap.add_argument("--student", help="đường dẫn JSON hồ sơ w7")
    ap.add_argument("--extra", default="", help="facts ASP bổ sung")
    args=ap.parse_args()
    extra=""
    sid="demo"
    if args.student:
        extra+=load_student(args.student)+"\n"
        sid=Path(args.student).stem
    extra+=args.extra
    cert=build_certificate(args.claim, extra, sid)
    print(json.dumps(cert, ensure_ascii=False, indent=2))

if __name__=="__main__": main()
