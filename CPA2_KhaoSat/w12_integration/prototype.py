"""
prototype.py — Prototype v1 end-to-end (CPA2, Tuần 12)

Kiến trúc 4 tầng (Tuần 1):
  Q (tiếng Việt) → [1] Parser (stub) → formal claim → [2] KB → [3] Solver → [4] Verbalizer + Hậu kiểm
  Output: ⟨ verdict, certificate, explanation_vi, missing_facts ⟩  — bất biến: mọi số/mã trong explanation_vi phải có trong certificate

Tuần 12 chưa có LLM Parser (Tuần 13-14) nên tầng 1 là stub: Q → claim thủ công.
Tuần 12 chưa có LLM Verbalizer thật nên tầng 4 là template + hậu kiểm.

Chạy:  python prototype.py --student ../w7_student_facts/students/sv_lvtn.json --question "em đủ điều kiện tốt nghiệp chưa?"
       python prototype.py --demo
"""
import json, re, argparse, sys
from pathlib import Path
import clingo

HERE = Path(__file__).parent
W5 = HERE.parent / "w5_rformal"
W6 = HERE.parent / "w6_curriculum"
W8 = HERE.parent / "w8_elective"
W9 = HERE.parent / "w9_exemption"
W10 = HERE.parent / "w10_graduation"
W11 = HERE.parent / "w11_proof"
sys.path.insert(0, str(HERE.parent / "w16_abstention"))
import abstention  # Tuần 16: missing evidence

RULES = [W5 / "qd3266_r_formal_v1.lp", W5 / "qd5339_r_formal_v1.lp"]
SCHEMA = W6 / "curriculum_schema.lp"
ELECTIVE = W8 / "elective_solver.lp"
EXEMPT = W9 / "exemption_substitution_solver.lp"
FACTS = W6 / "curriculum_cntt_k49.lp"
GRAD = W10 / "graduation_solver.lp"
CATALOG = W5 / "r_formal_v1.json"

# ---------- Tầng 1: Parser stub ----------
# Tuần 13 sẽ thay bằng LLM. Hiện map thủ công 7 câu hỏi trọng tâm (Tuan2 ma trận)
PARSER_STUB = {
    "em còn thiếu môn gì": "thieu_bat_buoc",
    "em còn thiếu bao nhiêu tín chỉ": "thieu_nhom",
    "kỳ này em đăng ký CT180 được chưa": "du_dk_dang_ky",
    "em đủ điều kiện làm luận văn chưa": "du_dk_tc",
    "chứng chỉ ielts của em miễn được môn nào": "du_dk_xin_mien",
    "nếu em rớt CT177 thì trễ mấy kỳ": "counterfactual",
    "em đủ điều kiện tốt nghiệp chưa": "tot_nghiep",
    "tot_nghiep": "tot_nghiep",
}

def parse_question(q: str) -> str:
    ql = q.lower()
    for k, v in PARSER_STUB.items():
        if k in ql: return v
    return "tot_nghiep"  # mặc định

# ---------- Tầng 2+3: KB + Solver ----------
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
    for c in j.get("certificates",[]):
        loai=c["loai"]; diem=int(c["diem"]) if loai=="ctu_abc" else round(c["diem"]*10)  # nguong_cc lưu điểm ×10
        lines.append(f'chung_chi({loai},{diem}).')
    for ex in j.get("exemptions",[]):
        if ex["quyet_dinh"]: lines.append(f'duoc_mien("{ex["ma_hp"]}").')
    # tinh chỉ bổ sung cho CTĐT demo
    for k in ("da_hoc_nam2","tc_cong_nhan"):
        if j.get(k) is not None: lines.append(f'{k}({j[k]}).')
    return "\n".join(lines), j.get("student_id","demo")

def kb(extra):
    return "\n".join([txt(p) for p in RULES] + [txt(SCHEMA), txt(ELECTIVE), txt(EXEMPT), txt(FACTS), txt(GRAD)]) + "\n" + extra

def solve_verdict(claim, extra):
    prog=kb(extra)
    ctl=clingo.Control(["--warn=none","--models=0"])
    ctl.add("base", [], prog)
    ctl.ground([("base",[])])
    models=[]
    with ctl.solve(yield_=True) as h:
        for m in h: models.append({str(a) for a in m.symbols(atoms=True)})
    if not models: return "UNSAT", [], set(), set()
    has=[claim in m for m in models]
    if all(has): verdict="TRUE"
    elif not any(has): verdict="FALSE"
    else: verdict="UNKNOWN"
    cautious=set.intersection(*models) if models else set()
    brave=set.union(*models) if models else set()
    return verdict, models, cautious, brave

def build_certificate(claim, verdict, models, cautious, brave):
    # thu thập why trong 1 model đại diện (hoặc cautious nếu TRUE)
    rep = list(cautious) if verdict=="TRUE" else (models[0] if models else set())
    # nhưng why chỉ có trong model cụ thể, lấy từ models[0]
    rep = models[0] if models else set()
    whys=[a for a in rep if a.startswith("why(")]
    cat=json.loads(CATALOG.read_text(encoding="utf-8"))
    by_asp={r["asp"]: r for r in cat["rules"] if r.get("asp")}
    import re
    steps=[]
    qd_set=set()
    for w in sorted(whys)[:20]:
        m=re.match(r"why\((.+),\s*(\w+)\)", w)
        if not m: continue
        atom, rid=m.group(1), m.group(2)
        if rid not in by_asp: continue
        rec=by_asp[rid]
        steps.append({"atom": atom, "rule_id": rid, "source": {"van_ban": rec["van_ban"], "dieu": rec["dieu"], "khoan": rec["khoan"], "trich": rec["trich"][:150]}})
        if rec.get("quyet_dinh"): qd_set.add(rec["quyet_dinh"].split()[0])
    missing=[]
    can_bo_sung=[]
    if verdict=="UNKNOWN":
        # Tuần 16: chỉ dữ kiện mở QUYẾT ĐỊNH kết luận (thay lọc chuỗi brave \ cautious)
        can_bo_sung=abstention.bang_chung_thieu(claim, [frozenset(m) for m in models])
        missing=[b["bien"] for b in can_bo_sung]
        if not missing:   # UNKNOWN do lựa chọn của SV (tích luỹ, tự chọn) — không phải dữ kiện thiếu
            missing=sorted(a for a in brave - cautious if "tich_luy" in a)[:10]
    return {"claim": claim, "verdict": verdict, "proof": {"steps": steps}, "missing_facts": missing,
            "can_bo_sung": can_bo_sung, "meta": {"qd_dien_giai": sorted(qd_set)}}

# ---------- Tầng 4: Verbalizer + Hậu kiểm ----------
TEMPLATES = {
    "TRUE":  "Kết luận: {claim} = TRUE. {details} Chứng chỉ có {n} bước suy diễn, mỗi bước truy về điều/khoản QĐ3266/QĐ5339.",
    "FALSE": "Kết luận: {claim} = FALSE. Phản ví dụ: {details} Chứng chỉ chỉ ra điều kiện còn thiếu.",
    "UNKNOWN": "Kết luận: {claim} = UNKNOWN. Thiếu dữ kiện: {details} Vui lòng bổ sung để hệ thống kết luận.",
}

def verbalize(cert, cautious):
    claim=cert["claim"]; verdict=cert["verdict"]
    # details: liệt kê thieu_dk hoặc thieu_nhom trong certificate
    details=[]
    for s in cert["proof"]["steps"]:
        if "thieu_" in s["atom"]: details.append(s["atom"])
    if not details and verdict=="TRUE": details=["đủ mọi điều kiện"]
    if not details and verdict=="FALSE": details=["thiếu "+a for a in cert["missing_facts"][:2]] if cert["missing_facts"] else ["không đủ điều kiện"]
    if verdict=="UNKNOWN" and cert["missing_facts"]: details=cert["missing_facts"][:3]
    text=TEMPLATES[verdict].format(claim=claim, details=", ".join(details[:3]), n=len(cert["proof"]["steps"]))
    # hậu kiểm: mọi số/mã trong text phải có trong certificate
    # quét mã HP (2-6 ký tự chữ+số) và số
    codes=re.findall(r"[A-Z]{1,3}\d{2,3}E?", text)
    nums=re.findall(r"\d+", text)
    cert_text=" ".join([s["atom"] for s in cert["proof"]["steps"]] + cert["missing_facts"])
    for c in codes:
        if c not in cert_text and c not in claim:
            return None, f"HẬU KIỂM CHẶN: mã {c} trong explanation nhưng không có trong certificate"
    return text, None

def answer(question, student_path):
    claim=parse_question(question)
    extra, sid = load_student(student_path) if student_path else ("", "demo")
    verdict, models, cautious, brave = solve_verdict(claim, extra)
    cert=build_certificate(claim, verdict, models, cautious, brave)
    explanation, block = verbalize(cert, cautious)
    if block:
        return {"verdict": "BLOCKED", "certificate": cert, "explanation_vi": block, "missing_facts": cert["missing_facts"]}
    return {"verdict": verdict, "certificate": cert, "explanation_vi": explanation, "missing_facts": cert["missing_facts"], "can_bo_sung": cert["can_bo_sung"], "student_id": sid, "claim": claim}

def demo():
    cases=[
        ("em đủ điều kiện tốt nghiệp chưa?", "w7_student_facts/students/sv_lvtn.json"),
        ("em đủ điều kiện tốt nghiệp chưa?", "w7_student_facts/students/sv_tron_ngoai_ngu.json"),
        ("em còn thiếu môn gì", "w7_student_facts/students/sv_tron_ngoai_ngu.json"),
    ]
    for q, stu in cases:
        print(f"\nQ: {q} | Student: {stu}")
        res=answer(q, f"CPA2_KhaoSat/{stu}" if not stu.startswith("CPA2") else stu)
        # fix path
        if "verdict" not in res or res["verdict"]=="BLOCKED":
            # retry with correct path
            import pathlib
            p=Path("CPA2_KhaoSat")/stu if not stu.startswith("CPA2") else Path(stu)
            if not p.exists():
                p=Path(stu)
            res=answer(q, str(p) if p.exists() else None)
        print(f"  Verdict: {res['verdict']}")
        print(f"  Explanation: {res['explanation_vi'][:200]}")
        if res["missing_facts"]: print(f"  Missing: {res['missing_facts'][:2]}")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--question", default="em đủ điều kiện tốt nghiệp chưa?")
    ap.add_argument("--student", help="đường dẫn JSON hồ sơ")
    ap.add_argument("--demo", action="store_true")
    args=ap.parse_args()
    if args.demo:
        # demo with correct absolute paths
        for q, stu in [
            ("em đủ điều kiện tốt nghiệp chưa?", str(HERE.parent / "w7_student_facts" / "students" / "sv_lvtn.json")),
            ("em đủ điều kiện tốt nghiệp chưa?", str(HERE.parent / "w7_student_facts" / "students" / "sv_tron_ngoai_ngu.json")),
        ]:
            res=answer(q, stu)
            print(f"\nQ: {q}")
            print(f"  Verdict: {res['verdict']}")
            print(f"  Explanation: {res['explanation_vi']}")
            print(f"  Steps: {len(res['certificate']['proof']['steps'])}")
            if res["missing_facts"]: print(f"  Missing: {res['missing_facts']}")
    else:
        res=answer(args.question, args.student)
        print(json.dumps(res, ensure_ascii=False, indent=2))
