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
    "em đủ điều kiện làm luận văn chưa": "du_dk_tc",
    "em đủ điều kiện làm tiểu luận chưa": "du_dk_tc",   # Tuần 18: nhánh TLTN của Eligibility
    "chứng chỉ ielts của em miễn được môn nào": "du_dk_xin_mien",
    "nếu em rớt CT177 thì trễ mấy kỳ": "counterfactual",
    "em đủ điều kiện tốt nghiệp chưa": "tot_nghiep",
    "tot_nghiep": "tot_nghiep",
}

DE_XUAT = re.compile(r"\bnen\s+(?:dang ky|hoc)\b")   # Tuần 19: "kỳ này em (có) nên đăng ký gì" → Recommendation

# P20-5 (Q-Noise, Tuần 20): mọi khớp mẫu chạy trên MỘT dạng chuẩn. Trước đây từ khoá/loại trừ chỉ có dạng có dấu →
# "lam luan van tot nghiep" thành tot_nghiep; "đk/đc/tn/lv/hp" không nhận ra.
# Review: bỏ dấu MỌI từ làm từ khác trùng từ khoá (thế→the, dự/dư→du, nền→nen) → câu trước đây bị từ chối nay bị
# trả lời như câu khác. Nên chỉ bỏ dấu từ CÓ trong bộ từ khoá dưới đây; từ có dấu khác giữ nguyên (không khớp mẫu
# ASCII). Từ gõ KHÔNG dấu vẫn mơ hồ ("the", "du") → chốt chặn câu hỏi mở + loại trừ ở từng ý định.
TU_KHOA = set("""đăng ký kí được không chưa đủ điều kiện tốt nghiệp trường luận văn tiểu nên nếu thì học phần môn kỳ kì
miễn lại điểm rớt hủy huỷ rút của với cùng thay gì nào để đề tài trước tiên quyết song hành làm nhận thể kịp đtbctl hồ sơ
loại hạng phí bổng nộp xét này hè đã có còn thiếu bao nhiêu tín chỉ chứng mấy trễ niên xong là ở đâu giờ sao đk đki đky
đc xếp giỏi khá xuất sắc trung bình bằng đạt""".split())   # C12: từ xếp loại (khá/bằng chỉ dùng kèm loại/hạng/bằng)
VIET_TAT = [   # (mẫu trên dạng đã chuẩn, dạng đầy đủ) — theo thứ tự; viết tắt mơ hồ chỉ mở khi có ngữ cảnh
    (r"\b(?:dki|dky|dang ki)\b", "dang ky"),
    (r"\bdk(?=\s+(?:hp|hoc phan|mon|huy|rut|[a-z]{2}\d{3}e?\b))", "dang ky"),   # đk + HP/mã/hủy/rút = đăng ký
    (r"\bdk\b", "dieu kien"),
    (r"\bdc\b", "duoc"),
    (r"\b(?:ko|k|khg|hok)\b", "khong"),
    (r"\blvtn\b", "luan van tot nghiep"), (r"\btltn\b", "tieu luan tot nghiep"), (r"\btl tn\b", "tieu luan tot nghiep"),
    (r"\blv\b", "luan van"), (r"\bhp\b", "hoc phan"), (r"\bhk\b", "hoc ky"), (r"\bki\b", "ky"), (r"\be\b", "em"),
    # "tn" cũng là tin nhắn / tình nguyện ("em tn cho thầy", "em được tn mùa hè xanh") → chỉ là tốt nghiệp sau
    # xét / điều kiện / luận văn / tiểu luận (review lượt 2)
    (r"\b(xet|kien|van|luan) tn\b", r"\1 tot nghiep"),
]
HOI_MO = re.compile(r"\bth(?:e|ế) nao\b|\bo dau\b|\bla gi\b|\bkhi nao\b|\bbao nhieu\b|\bbao gio\b|\blam sao\b|\bra sao\b"
                    r"|\bmay\b|\b(?:vi|vì|tai|tại) sao\b")


def bo_dau(s: str) -> str:
    s = unicodedata.normalize("NFC", s).replace("đ", "d").replace("Đ", "D").replace("Ð", "D")
    return "".join(ch for ch in unicodedata.normalize("NFD", s) if unicodedata.category(ch) != "Mn")


def chuan_hoa(q: str) -> str:
    """Câu hỏi → dạng chuẩn để khớp ý định: NFC, chữ thường, gộp khoảng trắng, bỏ dấu TỪ KHOÁ, mở viết tắt."""
    s = re.sub(r"\s+", " ", unicodedata.normalize("NFC", q).lower()).strip()
    s = re.sub(r"\w+", lambda m: bo_dau(m.group(0)) if m.group(0) in TU_KHOA else m.group(0), s)
    for mau, day_du in VIET_TAT:
        s = re.sub(mau, day_du, s)
    return s


def _la_tot_nghiep(ql):
    """câu hỏi có/không về TỐT NGHIỆP — trừ câu về luận văn, ĐTBCTL, tín chỉ, miễn, hồ sơ, lễ/thẻ, xếp loại, học
    phí/học bổng, việc "khi tốt nghiệp" (claim khác hoặc chưa hỗ trợ) và câu hỏi mở (thế nào, ở đâu …)."""
    return bool(re.search(r"tot nghiep|ra truong", ql) and re.search(r"\b(?:du|duoc|chua|the|kip)\b", ql)
                and not HOI_MO.search(ql)
                and not re.search(r"luan van|tieu luan|\bmien\b|dtbctl|tin chi|\bho so\b|\bloai\b|\bhang\b"
                                  r"|\bbang (?:loai|hang|xuat sac|gioi|kha|trung binh)\b"     # C12: "bằng trung bình" = hạng
                                  r"|hoc phi|hoc bong|\bnop\b|\bkhi tot nghiep\b"
                                  # từ ngoài TU_KHOA giữ dấu → loại trừ phải có cả dạng có dấu (review lượt 2)
                                  r"|\bl(?:e|ễ)\b|\bth(?:e|ẻ) (?:sinh vien|sv)|thẻ|đồ án|do an|khóa luận|khoá luận|khoa luan"
                                  r"|thực tập|thuc tap|giỏi|gioi|xuất sắc|xuat sac|hoãn|hoan", ql))   # "X khi tốt nghiệp" hỏi việc khác


# C12 (Tuần 20): xếp loại tốt nghiệp (QĐ3266 Đ34 — R-F06 hạng gốc theo ĐTBCTL, R-F07 hạ một bậc). Câu mở → "xep_loai"
# (tìm hạng); câu có/không về MỘT hạng → hang_cuoi(hạng). QD-15 (Loi chọn (a), 19/10/2026): "có đạt loại giỏi không" hỏi
# ĐÚNG hạng giỏi — hạng thực là xuất sắc thì FALSE và nêu hạng thực (bằng ghi đúng một hạng).
HANG_TU = {"xuat sac": "xuat_sac", "gioi": "gioi", "kha": "kha", "trung binh": "trung_binh"}
TEN_HANG = {"xuat_sac": "xuất sắc", "gioi": "giỏi", "kha": "khá", "trung_binh": "trung bình"}


# Review C12 lượt 2: danh sách CHẶN vẫn lọt (phủ định, ngưỡng "trở lên", hạng đứng sau, câu ghép, người khác …) →
# DANH SÁCH CHO PHÉP: chỉ nhận vài MẪU câu, khớp TOÀN câu (sau khi bỏ lời gọi đầu câu, trợ từ cuối câu và tiền tố
# "nếu tốt nghiệp (thì)"). "đủ / trở lên / ít nhất loại X" là câu NGƯỠNG (≥ X), khác QD-15 (đúng hạng) → chưa hỗ trợ.
# Lượt 3: mẫu khớp trên câu CHỈ bỏ dấu TỪ KHOÁ (chuan_hoa) — bỏ dấu toàn câu làm cô→có, hàng→hạng, bảng→bằng, đặt→đạt,
# tối→tôi; BẮT BUỘC chủ ngữ ngôi thứ nhất; "bằng gì/nào" là hỏi TÊN văn bằng (kỹ sư, cử nhân), không phải hạng.
_X = r"(xuat sac|gioi|kha|trung binh)"
_TOI = r"(?:em|e|mình|minh|tôi|toi) "
_TN = r"(?:tot nghiep|ra truong|tn)"
MAU_MO = [   # câu mở → xep_loai
    rf"^{_TOI}(?:se )?(?:duoc )?xep (?:loai|hang)(?: {_TN})? (?:loai |hang )?(?:gi|nao)$",
    rf"^{_TOI}(?:se )?{_TN} (?:se )?(?:duoc )?(?:xep )?(?:loai|hang|bang loai|bang hang) (?:gi|nao)$",
    rf"^bang(?: {_TN})? cua (?:em|mình|minh|tôi|toi)(?: se)?(?: la)? (?:loai|hang) (?:gi|nao)$",
    rf"^(?:hang|xep loai|xep hang) {_TN}(?: du kien)? cua (?:em|mình|minh|tôi|toi)(?: la)? (?:gi|loai gi|loai nao|hang gi|hang nao)$",
    rf"^(?:{_TOI})?{_TN} {_TOI}(?:se )?(?:duoc )?(?:loai|hang|bang) {_X} hay {_X}$",
]
MAU_CO_KHONG = [   # câu có/không về ĐÚNG một hạng (QD-15) → hang_cuoi(X)
    rf"^{_TOI}(?:co )?(?:dat|duoc|se dat|se duoc|duoc xep) (?:loai|hang|bang) {_X}(?: (?:khi|lúc|luc) {_TN})?(?: (?:khong|chua))?$",
    rf"^{_TOI}(?:co )?{_TN} (?:se )?(?:dat |duoc )?(?:loai|hang|bang) {_X}(?: (?:khong|chua))?$",
    rf"^{_TOI}{_TN} (?:se )?(?:duoc |dat )?(?:loai |hang |bang )?{_X} (?:duoc |dat )?(?:khong|chua)$",
    rf"^{_TN} {_TOI}(?:co )?(?:se )?(?:dat|duoc) (?:loai|hang|bang) {_X}(?: (?:khong|chua))?$",
]
_DAU = re.compile(r"^(?:(?:ad|admin|anh chi|anh|chi|thay|co|mn|moi nguoi|ban) oi,?\s*)?(?:cho (?:em|e|minh|toi) hoi(?: xiu| chut| voi)?,?\s*)?")
# Review bảo mật (Mốc 1 web): dạng cũ `(?:[\s?!.,]+|\b(?:…)\b)*$` có lượng từ lồng nhau → bùng nổ tổ hợp (ReDoS) khi sau chuỗi dấu
# câu / trợ từ có đuôi KHÔNG khớp: câu hỏi 53 ký tự treo > 20 giây. Dạng dưới cùng ngôn ngữ (dấu câu*, rồi (trợ từ dấu câu*)*), tuyến tính.
_CUOI = re.compile(r"[\s?!.,]*(?:\b(?:a|ad|nhe|nha|vay|ha|z)\b[\s?!.,]*)*$")


def _xep_loai(ql):
    """'xep_loai' / 'hang_cuoi(X)' / None — CHỈ khi cả câu khớp một mẫu cho phép (xem MAU_MO, MAU_CO_KHONG).
    Lời gọi đầu câu và trợ từ cuối câu tìm trên bản bỏ dấu toàn bộ (cùng độ dài với câu NFC) rồi cắt trên câu gốc."""
    qb = bo_dau(ql)
    if len(qb) != len(ql):
        return None
    a = _DAU.match(qb).end()
    b = a + _CUOI.search(qb[a:]).start()
    q = ql[a:b].strip()
    q2 = re.sub(r"^neu (?:em |mình |minh )?(?:duoc )?(?:tot nghiep|ra truong),? (?:thi )?", "", q)
    if not (q2 != q or re.search(r"\b(?:tot nghiep|ra truong|tn|bang)\b", q2)):
        return None
    for mau in MAU_CO_KHONG:
        m = re.match(mau, q2)
        if m:
            return f"hang_cuoi({HANG_TU[m.group(1)]})"
    for mau in MAU_MO:
        if re.match(mau, q2):
            return "xep_loai"
    return None


PARSER_STUB_CHUAN = {chuan_hoa(k): v for k, v in PARSER_STUB.items()}


def parse_question(q: str) -> str:
    ql = chuan_hoa(q)   # Unicode tổ hợp (NFD), không dấu, viết tắt → cùng một dạng (Bài học, P20-5)
    xl = _xep_loai(ql)  # C12: trước chốt "nếu" — "nếu tốt nghiệp, em xếp hạng gì" không phải phản thực tế
    if xl:
        return xl
    # đề xuất chung — câu hỏi về MỘT học phần / luận văn / tiểu luận đi nhánh riêng
    if DE_XUAT.search(ql) and not HOI_MO.search(ql) and not re.search(r"[a-z]{2}\d{3}|luan van|tieu luan", ql):
        return "de_xuat"
    # đăng ký MỘT học phần → claim có đối số (P18-1: claim không đối số luôn FALSE). Khoá stub chứa chữ hoa
    # (CT180) nên trước đây không bao giờ khớp câu đã lower() → rơi về tot_nghiep (sửa sau Tuần 19)
    if re.search(r"\bneu\b", ql):          # câu điều kiện / phản thực tế (RQ3 — chưa hỗ trợ); "nếu" thiếu "thì" cũng vậy
        return "counterfactual"
    ma = re.search(r"\b([a-z]{2}\d{3}e?)\b", ql)
    if ma and DE_XUAT.search(ql) and not HOI_MO.search(ql) and not re.search(r"duoc\s*(?:chua|khong)", ql):
        # "có NÊN đăng ký X (không)" là xin tư vấn; "nên đăng ký X được chưa" vẫn là hỏi điều kiện
        return "de_xuat"
    c = ma.group(1) if ma else None
    dk = re.search(rf"dang ky\s+(?P<khe>[^\d,.?!]{{0,40}}?\s)?{c}\b", ql) if c else None
    # P20-3: cho phép TÊN học phần chen giữa ("đăng ký học phần niên luận CT466E"); review: khe không được nói về
    # HP KHÁC (tiên quyết CỦA, song hành VỚI, thay thế), hủy/rút, hay hỏi "HP gì/nào để …". Bỏ dấu: "để" = "đề"
    # (đề tài) → "de" chỉ xấu khi không theo sau bởi "tai"
    khe_xau = dk and dk.group("khe") and re.search(
        r"\b(?:cua|voi|cung|thay|huy|rut|gi|nao|de(?! tai)|truoc|tien quyet|song hanh)\b", dk.group("khe"))
    # câu có/không (được/chưa/không), không phải câu hỏi mở ("đk CT180 là gì", "đăng ký CT180 ở đâu")
    # review lượt 2: một mã HP duy nhất (hai mã = cùng lúc/trước/thay thế HP khác); không hỏi trạng thái "đã đăng ký"
    co_khong = re.search(r"\b(?:duoc|chua|khong)\b", ql) and not HOI_MO.search(ql)
    mot_ma = len(set(re.findall(r"\b[a-z]{2}\d{3}e?\b", ql))) == 1
    if c and re.search(rf"\b{c}\b.*\bthi\b", ql):   # "đăng ký X THÌ có bị trùng lịch…" hỏi hệ quả, không hỏi được đăng ký
        co_khong = None
    if c and co_khong and mot_ma and not re.search(r"\bmien\b|\bxong\b|\blai\b|\bdiem\b|\brot\b|\bhuy\b|\brut\b|\bda dang ky\b", ql) and (
            (dk and not khe_xau)
            or re.search(rf"\bhoc\s+(?:(?:mon|hoc phan)\s+)?{c}\s+duoc\s+(?:khong|chua)\b", ql)):
        return f'duoc_dang_ky("{c.upper()}")'
    for k, v in PARSER_STUB_CHUAN.items():
        if k in ql and (v != "tot_nghiep" or _la_tot_nghiep(ql) or ql == "tot_nghiep"):
            return v
    # đủ điều kiện LÀM luận văn/tiểu luận (diễn đạt khác stub) → Eligibility (w18)
    # chỉ "làm luận văn/tiểu luận (tốt nghiệp) chưa/không" — không phải "làm luận văn NHÓM", "tiểu luận THAY luận văn"
    if re.search(r"(?:du dieu kien|duoc)\s+(?:lam|nhan de tai)\s+(?:luan van|tieu luan)(?: tot nghiep)?\s*(?:khong|chua)?"
                 r"\s*(?:a|ạ)?[\s?!.]*$", ql) and not HOI_MO.search(ql):
        return "du_dk_tc"
    # câu tốt nghiệp diễn đạt khác stub ("em ra trường được chưa")
    if _la_tot_nghiep(ql):
        return "tot_nghiep"
    # P20-2 (Tuần 20): KHÔNG mặc định tot_nghiep — câu không nhận ra ý định → UNKNOWN "chưa hỗ trợ" (họ lỗi P18-1/P19-4)
    return "khong_ro"

# ---------- Tầng 2+3: KB + Solver ----------
def txt(p): return p.read_text(encoding="utf-8")

def doc_ho_so(nguon):
    """Hồ sơ từ đường dẫn file (CLI) HOẶC từ dict (API web: không nhận đường dẫn của người dùng). Luôn trả bản sao —
    không sửa hồ sơ của nơi gọi."""
    if isinstance(nguon, dict):
        return json.loads(json.dumps(nguon))
    return json.loads(Path(nguon).read_text(encoding="utf-8"))

def load_student(path):
    """Hồ sơ JSON (đường dẫn hoặc dict) → (dữ kiện ASP, student_id, mâu thuẫn) qua loader chung (w7_student_facts/loader.py)."""
    j=doc_ho_so(path)
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
    dt = "tltn" if "tieu luan" in chuan_hoa(question) else "lvtn"     # P20-5: cả "tieu luan"/"tltn" không dấu
    if not student_path:      # không có hồ sơ → không kết luận về sinh viên (thế giới đóng sẽ cho FALSE sai)
        cert = {"claim": f"du_dk({dt})", "verdict": "UNKNOWN", "proof": {"steps": []}, "missing_facts": ["ho_so"]}
        return {"verdict": "UNKNOWN", "certificate": cert, "explanation_vi": "Cần hồ sơ học tập để xét điều kiện.",
                "missing_facts": ["ho_so"], "can_bo_sung": [], "mau_thuan": [], "claim": f"du_dk({dt})"}
    r = eligibility.xet(doc_ho_so(student_path), dt)
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
    ql = chuan_hoa(question)       # P20-5 review: "ky 2", "hoc ki 3", "hk he" không dấu (P19-3: không lặng lẽ về HK1)
    k = re.search(r"(?:\bky|\bhk)\s*(\d+|i{1,3})\b", ql)
    # "kỳ N" trước; "he" không dấu cũng là "hệ" (hệ CLC) → chỉ là hè khi có dấu hoặc sau kỳ/học/mùa (review lượt 2)
    he = "hè" in unicodedata.normalize("NFC", question).lower() or re.search(r"\b(?:ky|hk|hoc|mua) he\b", ql)
    hk = 3 if he and not k else ({"i": 1, "ii": 2, "iii": 3}.get(k.group(1)) or int(k.group(1))) if k else 1
    if hk not in (1, 2, 3):   # QĐ3266 Đ6 k1: một năm học có 3 HK — không lặng lẽ đổi sang HK1
        return {"verdict": "UNKNOWN", "claim": "de_xuat", "missing_facts": ["hoc_ky"],
                "explanation_vi": f"Không có học kỳ {hk} — một năm học có 3 học kỳ (QĐ3266 Điều 6 khoản 1). "
                                  "Bạn muốn đăng ký học kỳ 1, 2 hay 3 (hè)?",
                "certificate": {"claim": "de_xuat", "proof": {"steps": []}}}
    r = recommendation.de_xuat(doc_ho_so(student_path), hk)
    if r.get("vo_nghiem"):     # solver vô nghiệm (như nhánh UNSAT của answer): KHÔNG đề xuất, không giả vờ "chưa có học phần hợp lệ"
        return {"verdict": "UNSAT", "claim": "de_xuat", "missing_facts": [], "can_bo_sung": [], "mau_thuan": r["mau_thuan"],
                "certificate": {"claim": "de_xuat", "verdict": "UNSAT", "proof": {"steps": []}, "missing_facts": [], "can_bo_sung": []},
                "explanation_vi": "Hồ sơ mâu thuẫn với quy chế hoặc với chính nó — hệ thống không đề xuất. Hãy kiểm tra lại hồ sơ."}
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

def tong_hop_hang(ds_hang):
    """Hạng (hang_cuoi) của từng thế giới → (verdict câu mở, các hạng có thể). Mọi thế giới cùng MỘT hạng → TRUE;
    mọi thế giới không đạt mức nào → FALSE; còn lại → UNKNOWN (ba trị theo số thế giới, không theo đa số)."""
    tat_ca = sorted(set().union(*ds_hang)) if ds_hang else []
    if ds_hang and all(len(h) == 1 for h in ds_hang) and len(tat_ca) == 1:
        return "TRUE", tat_ca
    if ds_hang and all(not h for h in ds_hang):
        return "FALSE", []
    return "UNKNOWN", tat_ca


def _hang_co_the(m):
    """Một thế giới → tập hạng CUỐI (hang_cuoi của KB), None nếu chưa có ĐTBCTL. C15 (R-Formal v1.11): KB tự hạ một mức
    hạng xuất sắc/giỏi theo Đ34 k2 a+b và MỞ NHÁNH khi chưa khai báo (graduation_solver mục 0) — prototype không còn
    phải tự né như bản C12."""
    if not any(a.startswith("tl_mau(") and a != "tl_mau(0)" for a in m):
        return None
    return {a[len("hang_cuoi("):-1] for a in m if a.startswith("hang_cuoi(")}


def answer_xep_loai(claim, student_path):
    """C12: 'xep_loai' (câu mở) hoặc 'hang_cuoi(X)' (câu có/không, QD-15: đúng hạng X). Luôn nêu hạng tính được, ghi rõ
    là DỰ KIẾN theo ĐTBCTL hiện tại (hang_cuoi không phụ thuộc việc đã đủ điều kiện tốt nghiệp)."""
    def tra(verdict, text, cert=None, missing=()):
        return {"verdict": verdict, "claim": claim, "certificate": cert or {"claim": claim, "proof": {"steps": []}},
                "explanation_vi": text, "missing_facts": list(missing), "can_bo_sung": [{"bien": b} for b in missing]}
    if not student_path:
        return tra("UNKNOWN", "Cần hồ sơ học tập để tính hạng tốt nghiệp.", missing=["ho_so"])
    extra, sid, mt = load_student(student_path)
    hoi = TEN_HANG.get(claim[len("hang_cuoi("):-1]) if claim.startswith("hang_cuoi(") else None   # câu có/không
    verdict, models, cautious, brave = solve_verdict(claim if hoi else "hang_cuoi(_)", extra)
    if verdict == "UNSAT":
        return {**tra("UNSAT", "Hồ sơ mâu thuẫn — không tính hạng."), "mau_thuan": mt}
    co_the = [_hang_co_the(m) for m in models]
    if any(h is None for h in co_the):
        return tra("UNKNOWN", "Chưa có ĐTBCTL (chưa có học phần nào tính vào điểm trung bình tích lũy) — chưa tính được hạng.",
                   missing=["diem_hoc_phan"])
    vd, hang = tong_hop_hang(co_the)
    if hoi:
        x = claim[len("hang_cuoi("):-1]
        verdict = ("TRUE" if all(h == {x} for h in co_the) else "FALSE" if all(x not in h for h in co_the) else "UNKNOWN")
    else:
        verdict, claim = vd, (f"hang_cuoi({hang[0]})" if vd == "TRUE" else "xep_loai")
    cert = build_certificate(claim, verdict, models, cautious, brave)
    if verdict == "UNKNOWN" and hang and not cert["can_bo_sung"]:   # câu mở: claim "xep_loai" không có trong thế giới nào
        cert["can_bo_sung"] = abstention.bang_chung_thieu(f"hang_cuoi({hang[0]})", [frozenset(m) for m in models])
        cert["missing_facts"] = [b["bien"] for b in cert["can_bo_sung"]]
    # chứng chỉ chỉ khẳng định hạng cuối khi nó CHẮC (mọi thế giới); luôn kèm bước hạng gốc (R-F06)
    chac = {f"hang_cuoi({h})" for h in hang} if vd == "TRUE" or (hoi and verdict == "TRUE") else set()
    cert["proof"]["steps"] = [s_ for s_ in cert["proof"]["steps"] if not s_["atom"].startswith("hang_cuoi(") or s_["atom"] in chac]
    co = {s_["atom"] for s_ in cert["proof"]["steps"]}
    cat = {r["asp"]: r for r in json.loads(CATALOG.read_text(encoding="utf-8"))["rules"] if r.get("asp")}
    chung = set.intersection(*[set(m) for m in models])
    for w in sorted(a for a in chung if a.startswith(("why(hang_goc", "why(hang_cuoi", "why(vuot_5", "why(ky_luat_canh"))):
        m = re.match(r"why\((.+),\s*(\w+)\)", w)
        if m and m.group(2) in cat and m.group(1) not in co and (not m.group(1).startswith("hang_cuoi(") or m.group(1) in chac):
            r = cat[m.group(2)]
            cert["proof"]["steps"].insert(0, {"atom": m.group(1), "rule_id": m.group(2), "source": {
                "van_ban": r["van_ban"], "dieu": r["dieu"], "khoan": r["khoan"], "trich": r["trich"][:150]}})
    if not any(co_the):                                     # không thế giới nào đạt mức nào → nguồn: ngưỡng R-F06
        r6 = next((r for r in cat.values() if r["id"] == "R-F06"), None)
        if r6:
            cert["proof"]["steps"].insert(0, {"atom": "khong_dat_muc_hang", "rule_id": r6["asp"], "source": {
                "van_ban": r6["van_ban"], "dieu": r6["dieu"], "khoan": r6["khoan"], "trich": r6["trich"][:150]}})
    goc = sorted({a[len("hang_goc("):-1] for m in models for a in m if a.startswith("hang_goc(")})
    if not hang:
        mo_ta = "ĐTBCTL hiện tại chưa đạt mức xếp hạng tốt nghiệp nào (dưới mức trung bình)"
    elif vd == "TRUE":
        mo_ta = f"Hạng tốt nghiệp dự kiến của bạn: {TEN_HANG[hang[0]]}"
    else:
        mo_ta = (f"Hạng tốt nghiệp dự kiến của bạn chưa chắc: có thể là {' hoặc '.join(TEN_HANG[h] for h in hang)}"
                 + (", hoặc chưa đạt mức nào" if any(not h for h in co_the) else ""))
    hoi_bo_sung = [b for b in cert["can_bo_sung"]
                   if b.get("bien") in ("f_ngoai_ho_so_vuot_5", "hp_dk_tinh_vao_tong", "ky_luat_canh_cao_cap_truong")]
    if hoi_bo_sung and goc:
        mo_ta += (f". Hạng gốc theo ĐTBCTL là {' / '.join(TEN_HANG[g] for g in goc)}; hạng xuất sắc và giỏi bị giảm một mức nếu "
                  "khối lượng học phần bị điểm F vượt quá năm phần trăm tổng TC của CTĐT (không tính học cải thiện) hoặc đã "
                  "bị kỷ luật từ mức cảnh cáo cấp Trường — còn thiếu: " + " ".join(b["hoi"] for b in hoi_bo_sung))
    if hoi:
        mo_ta = f"{ {'TRUE': 'Có', 'FALSE': 'Không', 'UNKNOWN': 'Chưa chắc'}[verdict]} đạt loại {hoi}. " + mo_ta
    text = (mo_ta.rstrip(".") + ("" if mo_ta.rstrip(".").endswith("?") else ".")
            + " Đây là hạng DỰ KIẾN theo ĐTBCTL hiện tại, chưa xét bạn đã đủ điều kiện tốt nghiệp hay chưa.")
    cert_text = " ".join([s_["atom"] for s_ in cert["proof"]["steps"]] + cert["missing_facts"])
    lech = [c for c in re.findall(r"[A-Z]{1,3}\d{2,3}E?", text) if c not in cert_text]
    if lech:                                                  # hậu kiểm (bất biến prototype)
        return {**tra("BLOCKED", f"HẬU KIỂM CHẶN: mã {lech[0]} trong lời giải thích nhưng không có trong chứng chỉ", cert)}
    return {"verdict": verdict, "claim": claim, "certificate": cert, "explanation_vi": text,
            "missing_facts": cert["missing_facts"], "can_bo_sung": cert["can_bo_sung"], "mau_thuan": mt, "student_id": sid}


def answer(question, student_path):
    claim=parse_question(question)
    if claim == "xep_loai" or claim.startswith("hang_cuoi("):
        return answer_xep_loai(claim, student_path)
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
    if verdict == "UNSAT":     # solver vô nghiệm (hồ sơ trái quy chế, vd. loại HP bắt buộc khỏi tích lũy): KHÔNG kết luận, không ngoại lệ
        cert = {"claim": claim, "verdict": "UNSAT", "proof": {"steps": []}, "missing_facts": [], "can_bo_sung": []}
        return {"verdict": "UNSAT", "claim": claim, "certificate": cert, "missing_facts": [], "can_bo_sung": [], "mau_thuan": mt,
                "explanation_vi": "Hồ sơ mâu thuẫn với quy chế hoặc với chính nó — hệ thống không kết luận. Hãy kiểm tra lại hồ sơ.",
                "student_id": sid}
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
