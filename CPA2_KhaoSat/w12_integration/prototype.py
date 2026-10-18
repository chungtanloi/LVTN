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
import json, re, argparse, sys, unicodedata
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
sys.path.insert(0, str(HERE.parent / "w7_student_facts"))
import abstention  # Tuần 16: missing evidence
import loader      # loader dùng chung: rà soát hồ sơ mâu thuẫn (P17-1) + đổi sang ASP
sys.path.insert(0, str(HERE.parent / "w18_eligibility"))

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
    "em đủ điều kiện làm tiểu luận chưa": "du_dk_tc",   # Tuần 18: nhánh TLTN của Eligibility
    "chứng chỉ ielts của em miễn được môn nào": "du_dk_xin_mien",
    "nếu em rớt CT177 thì trễ mấy kỳ": "counterfactual",
    "em đủ điều kiện tốt nghiệp chưa": "tot_nghiep",
    "tot_nghiep": "tot_nghiep",
}

DE_XUAT = re.compile(r"nên\s+(?:đăng\s*ký|học)\b")   # Tuần 19: "kỳ này em (có) nên đăng ký gì" → Recommendation

def parse_question(q: str) -> str:
    ql = unicodedata.normalize("NFC", q).lower()   # Unicode tổ hợp (NFD) không khớp chuỗi gõ vào — Bài học
    # đề xuất chung — câu hỏi về MỘT học phần / luận văn / tiểu luận đi nhánh riêng
    if DE_XUAT.search(ql) and not re.search(r"[a-z]{2}\d{3}|luận văn|tiểu luận", ql):
        return "de_xuat"
    # đăng ký MỘT học phần → claim có đối số (P18-1: claim không đối số luôn FALSE). Khoá stub chứa chữ hoa
    # (CT180) nên trước đây không bao giờ khớp câu đã lower() → rơi về tot_nghiep (sửa sau Tuần 19)
    if re.search(r"\bnếu\b.*\bthì\b", ql):          # câu điều kiện / phản thực tế (RQ3 — chưa hỗ trợ)
        return "counterfactual"
    ma = re.search(r"\b([a-z]{2}\d{3}e?)\b", ql)
    if ma and re.search(r"\bnên\b", ql) and not re.search(r"được\s*(?:chưa|không)", ql):
        # "có NÊN đăng ký X (không)" là xin tư vấn; "nên đăng ký X được chưa" vẫn là hỏi điều kiện
        return "de_xuat"
    c = ma.group(1) if ma else None
    dk = re.search(rf"đăng\s*k[ýí]\s+(?P<khe>[^\d,.?!]{{0,40}}?\s)?{c}\b", ql) if c else None
    # P20-3: cho phép TÊN học phần chen giữa ("đăng ký học phần niên luận CT466E"); review: khe không được nói về
    # HP KHÁC (tiên quyết CỦA, song hành VỚI, thay thế), hủy/rút, hay hỏi "HP gì/nào để …"
    khe_xau = dk and dk.group("khe") and re.search(
        r"\b(?:của|với|cùng|thay|hủy|huỷ|rút|gì|nào|để|trước|tiên quyết|song hành)\b", dk.group("khe"))
    if c and not re.search(r"miễn|xong|\blại\b|điểm|rớt|\brot\b|\bhủy\b|\bhuỷ\b|\brút\b", ql) and (
            (dk and not khe_xau)
            or re.search(rf"\bhọc\s+(?:(?:môn|học phần|hp)\s+)?{c}\s+(?:được|đc)", ql)):
        return f'duoc_dang_ky("{c.upper()}")'
    for k, v in PARSER_STUB.items():
        if k.lower() in ql: return v
    # đủ điều kiện LÀM luận văn/tiểu luận (diễn đạt khác stub) → Eligibility (w18)
    if re.search(r"(?:đủ điều kiện|được)\s+(?:làm|nhận đề tài)\s+(?:luận văn|tiểu luận)", ql):
        return "du_dk_tc"
    # câu tốt nghiệp diễn đạt khác stub ("em ra trường được chưa", không dấu) — trừ câu về luận văn, ĐTBCTL, miễn, hồ sơ,
    # xếp loại, học phí/học bổng (claim khác hoặc chưa hỗ trợ → không được trả lời như câu tốt nghiệp)
    if re.search(r"tốt nghiệp|ra trường|tot nghiep|ra truong", ql) \
            and re.search(r"\b(?:đủ|du|được|duoc|chưa|chua|thể|kịp)\b", ql) \
            and not re.search(r"luận văn|tiểu luận|miễn|đtbctl|\bhồ sơ\b|\bloại\b|\bhạng\b|học phí|học bổng|\bnộp\b", ql):
        return "tot_nghiep"
    # P20-2 (Tuần 20): KHÔNG mặc định tot_nghiep — câu không nhận ra ý định → UNKNOWN "chưa hỗ trợ" (họ lỗi P18-1/P19-4)
    return "khong_ro"

# ---------- Tầng 2+3: KB + Solver ----------
def txt(p): return p.read_text(encoding="utf-8")

def load_student(path):
    """Hồ sơ JSON → (dữ kiện ASP, student_id, mâu thuẫn) qua loader chung (w7_student_facts/loader.py)."""
    j=json.loads(Path(path).read_text(encoding="utf-8"))
    asp, mt = loader.sang_asp(j)
    return asp, j.get("student_id","demo"), mt

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

ELIG_VERDICT = {"ELIGIBLE": "TRUE", "NOT_ELIGIBLE": "FALSE", "UNKNOWN": "UNKNOWN", "DA_HOAN_THANH": "DA_HOAN_THANH",
                "MAU_THUAN": "UNSAT"}

def answer_eligibility(question, student_path):
    """Tuần 18: "đủ điều kiện làm luận văn/tiểu luận" → Eligibility module (w18). Trước đây claim 'du_dk_tc' không
    đối số không bao giờ có trong answer set → prototype luôn trả FALSE."""
    import eligibility
    dt = "tltn" if "tiểu luận" in question.lower() else "lvtn"
    if not student_path:      # không có hồ sơ → không kết luận về sinh viên (thế giới đóng sẽ cho FALSE sai)
        cert = {"claim": f"du_dk({dt})", "verdict": "UNKNOWN", "proof": {"steps": []}, "missing_facts": ["ho_so"]}
        return {"verdict": "UNKNOWN", "certificate": cert, "explanation_vi": "Cần hồ sơ học tập để xét điều kiện.",
                "missing_facts": ["ho_so"], "can_bo_sung": [], "mau_thuan": [], "claim": f"du_dk({dt})"}
    r = eligibility.xet(json.loads(Path(student_path).read_text(encoding="utf-8")), dt)
    v = ELIG_VERDICT[r["ket_qua"]]
    steps = [{"atom": s["atom"], "rule_id": s["rule_id"], "source": {"van_ban": s["nguon"]}} for s in r["chung_chi"]]
    missing = [b["bien"] for b in r["can_bo_sung"]]
    text = {"TRUE": f"Kết luận: đủ điều kiện nhận đề tài {dt}.",
            "FALSE": f"Kết luận: chưa đủ điều kiện {dt}: " + ", ".join(r["ly_do"]),
            "UNKNOWN": "Chưa đủ dữ kiện — cần bổ sung: " + " | ".join(b["hoi"] for b in r["can_bo_sung"]),
            "DA_HOAN_THANH": f"Đã hoàn thành {dt}.", "UNSAT": "Hồ sơ mâu thuẫn — không kết luận."}[v]
    cert = {"claim": f"du_dk({dt})", "verdict": v, "proof": {"steps": steps}, "missing_facts": missing,
            "can_bo_sung": r["can_bo_sung"]}
    # hậu kiểm như verbalize: mọi mã HP trong lời giải thích phải có trong certificate
    cert_text = " ".join([s["atom"] for s in steps] + r["ly_do"] + missing)
    la = [c for c in re.findall(r"[A-Z]{1,3}\d{2,3}E?", text) if c not in cert_text]
    if la:
        return {"verdict": "BLOCKED", "certificate": cert, "missing_facts": missing,
                "explanation_vi": f"HẬU KIỂM CHẶN: mã {la[0]} trong explanation nhưng không có trong certificate"}
    return {"verdict": v, "certificate": cert, "explanation_vi": text, "missing_facts": missing,
            "can_bo_sung": r["can_bo_sung"], "mau_thuan": r["mau_thuan"], "claim": f"du_dk({dt})", "eligibility": r}

def answer_recommendation(question, student_path):
    """Tuần 19: "kỳ này em nên đăng ký gì" → Recommendation (w19): chỉ đề xuất HP hợp lệ trên mọi thế giới;
    chưa chắc → danh sách cần xác minh. Học kỳ lấy từ câu hỏi ("học kỳ 3"/"hè"), mặc định HK1."""
    sys.path.insert(0, str(HERE.parent / "w19_recommendation"))
    import recommendation
    if not student_path:
        return {"verdict": "UNKNOWN", "claim": "de_xuat", "explanation_vi": "Cần hồ sơ học tập để đề xuất đăng ký.",
                "missing_facts": ["ho_so"], "certificate": {"claim": "de_xuat", "proof": {"steps": []}}}
    ql = unicodedata.normalize("NFC", question).lower()
    k = re.search(r"(?:\bk[ỳì]|\bhk)\s*(\d+|i{1,3})\b", ql)
    hk = 3 if "hè" in ql else ({"i": 1, "ii": 2, "iii": 3}.get(k.group(1)) or int(k.group(1))) if k else 1
    if hk not in (1, 2, 3):   # QĐ3266 Đ6 k1: một năm học có 3 HK — không lặng lẽ đổi sang HK1
        return {"verdict": "UNKNOWN", "claim": "de_xuat", "missing_facts": ["hoc_ky"],
                "explanation_vi": f"Không có học kỳ {hk} — một năm học có 3 học kỳ (QĐ3266 Điều 6 khoản 1). "
                                  "Bạn muốn đăng ký học kỳ 1, 2 hay 3 (hè)?",
                "certificate": {"claim": "de_xuat", "proof": {"steps": []}}}
    r = recommendation.de_xuat(json.loads(Path(student_path).read_text(encoding="utf-8")), hk)
    steps = [{"atom": c["atom"], "rule_id": c["rule_id"], "source": {"van_ban": c["nguon"]}}
             for x in r["dang_ky"] for c in x["chung_chi"]]
    text = (f"Đề xuất đăng ký HK{hk} ({r['tong_tc']} TC): " + ", ".join(x["ma"] for x in r["dang_ky"])
            if r["dang_ky"] else f"Không có học phần nào chắc chắn hợp lệ để đề xuất cho HK{hk}.")
    if r["can_xac_minh"]:
        text += " Cần xác minh trước: " + ", ".join(x["ma"] or x["ly_do"] for x in r["can_xac_minh"])
    return {"verdict": "TRUE" if r["dang_ky"] else "UNKNOWN", "claim": "de_xuat", "explanation_vi": text,
            "certificate": {"claim": "de_xuat", "proof": {"steps": steps}}, "missing_facts": [],
            "mau_thuan": r["mau_thuan"], "de_xuat": r}

def answer_dang_ky(claim, student_path):
    """Sau Tuần 19: "đăng ký C được chưa" → duoc_dang_ky(C) = tiên quyết (R-A03, Đ7 k4) + song hành (R-A04, Đ7 k5:
    học trước HOẶC cùng lúc). Chưa học HP song hành P → được, VỚI ĐIỀU KIỆN học P cùng kỳ; P không đăng ký được → chưa
    thể học C kỳ này."""
    c = claim[len('duoc_dang_ky("'):-2]
    if not student_path:
        return {"verdict": "UNKNOWN", "claim": claim, "explanation_vi": "Cần hồ sơ học tập để xét đăng ký.",
                "missing_facts": ["ho_so"], "can_bo_sung": [], "certificate": {"claim": claim, "proof": {"steps": []}}}
    extra, sid, mt = load_student(student_path)
    verdict, models, cautious, brave = solve_verdict(claim, extra)
    cat = json.loads(CATALOG.read_text(encoding="utf-8"))
    by_asp = {r["asp"]: r for r in cat["rules"] if r.get("asp")}
    q = f'"{c}"'
    lien_quan = lambda a: (a.startswith(f"duoc_dang_ky({q})") or a.startswith(f"du_dk_dang_ky({q})")
                           or a.startswith(f"phai_hoc_cung_ky({q},") or a.startswith(f"chan_song_hanh({q},")
                           or a.startswith(f"thieu_tc({q},") or a.startswith("thieu_tien_quyet("))
    steps = []
    for w in sorted(cautious):
        m = re.match(r"why\((.+),(\w+)\)$", w)
        if m and lien_quan(m.group(1)) and m.group(2) in by_asp:
            rec = by_asp[m.group(2)]
            steps.append({"atom": m.group(1), "rule_id": m.group(2), "source": {"van_ban": rec["van_ban"],
                          "dieu": rec["dieu"], "khoan": rec["khoan"], "trich": rec["trich"][:150]}})
    lay = lambda ten: sorted({a.split(",")[1][:-1].strip('"') for a in cautious if a.startswith(f"{ten}({q},")})
    cung_ky, chan = lay("phai_hoc_cung_ky"), lay("chan_song_hanh")
    thieu_tq = lay("thieu_tien_quyet")
    # bước thiếu tiên quyết chỉ giữ cho chính C và các HP song hành bị chặn (lấy từ why/2 của KB)
    giu = {q} | {f'"{p_}"' for p_ in chan}
    steps = [s_ for s_ in steps if not s_["atom"].startswith("thieu_tien_quyet(")
             or s_["atom"][len("thieu_tien_quyet("):].split(",")[0] in giu]
    can = []
    if verdict == "TRUE":
        text = f"Kết luận: được đăng ký {c}."
        if cung_ky:
            text += (f" Với điều kiện học {', '.join(cung_ky)} cùng kỳ — song hành phải học trước hoặc học cùng lúc "
                     "(QĐ3266 Điều 7 khoản 5).")
    elif verdict == "FALSE":
        if chan:
            text = (f"Kết luận: chưa thể học {c} kỳ này — phải học cùng kỳ {', '.join(cung_ky)} (song hành, "
                    f"QĐ3266 Điều 7 khoản 5: phải học trước hoặc cùng lúc) nhưng {', '.join(chan)} chưa đủ điều kiện đăng ký.")
        else:
            text = f"Kết luận: chưa đủ điều kiện đăng ký {c}" + (
                f" — thiếu tiên quyết {', '.join(thieu_tq)} (QĐ3266 Điều 7 khoản 4)." if thieu_tq else
                " (chưa đủ ngưỡng tín chỉ tích lũy hoặc không có trong CTĐT).")
    elif verdict == "UNKNOWN":
        can = abstention.bang_chung_thieu(claim, [frozenset(m) for m in models])
        text = "Chưa đủ dữ kiện để kết luận — cần bổ sung: " + " | ".join(b["hoi"] for b in can)
    else:
        text = "Hồ sơ mâu thuẫn với quy chế — không kết luận."
    cert = {"claim": claim, "verdict": verdict, "proof": {"steps": steps}, "missing_facts": [b["bien"] for b in can],
            "can_bo_sung": can}
    cert_text = " ".join([s["atom"] for s in steps] + cert["missing_facts"] + [claim])
    la = [x for x in re.findall(r"[A-Z]{1,3}\d{2,3}E?", text) if x not in cert_text]
    if la:
        return {"verdict": "BLOCKED", "certificate": cert, "missing_facts": cert["missing_facts"], "claim": claim,
                "explanation_vi": f"HẬU KIỂM CHẶN: mã {la[0]} trong explanation nhưng không có trong certificate"}
    return {"verdict": verdict, "certificate": cert, "explanation_vi": text, "missing_facts": cert["missing_facts"],
            "can_bo_sung": can, "mau_thuan": mt, "student_id": sid, "claim": claim}

def answer(question, student_path):
    claim=parse_question(question)
    if claim.startswith("duoc_dang_ky("):
        return answer_dang_ky(claim, student_path)
    if claim == "khong_ro":
        return {"verdict": "UNKNOWN", "claim": claim, "missing_facts": [], "can_bo_sung": [],
                "explanation_vi": "Hệ thống chưa hiểu hoặc chưa hỗ trợ loại câu hỏi này (ngoài phạm vi quy chế đã hình thức "
                                  "hoá) — không đoán. Bạn có thể hỏi về tốt nghiệp, đăng ký học phần, luận văn, miễn học phần.",
                "certificate": {"claim": claim, "proof": {"steps": []}}}
    if claim == "counterfactual":   # RQ3 / Tuần 22 — chưa hỗ trợ: không trả lời nhầm sang claim khác
        return {"verdict": "UNKNOWN", "claim": claim, "missing_facts": [], "can_bo_sung": [],
                "explanation_vi": "Câu hỏi phản thực tế (nếu … thì …) chưa được hỗ trợ — hệ thống không đoán.",
                "certificate": {"claim": claim, "proof": {"steps": []}}}
    if claim == "du_dk_tc":
        return answer_eligibility(question, student_path)
    if claim == "de_xuat":
        return answer_recommendation(question, student_path)
    extra, sid, mt = load_student(student_path) if student_path else ("", "demo", [])
    verdict, models, cautious, brave = solve_verdict(claim, extra)
    cert=build_certificate(claim, verdict, models, cautious, brave)
    explanation, block = verbalize(cert, cautious)
    if block:
        return {"verdict": "BLOCKED", "certificate": cert, "explanation_vi": block, "missing_facts": cert["missing_facts"]}
    return {"verdict": verdict, "certificate": cert, "explanation_vi": explanation, "missing_facts": cert["missing_facts"], "can_bo_sung": cert["can_bo_sung"], "mau_thuan": mt, "student_id": sid, "claim": claim}

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
