"""
parser.py — Semantic Parser v1 (CPA2, Tuần 13)

Nhiệm vụ: Q tiếng Việt → formal query (claim atom + params)
Kiến trúc Tuần 1 tầng 1: LLM bị cấm suy luận về SV, chỉ được dịch câu hỏi.

Tuần 13 v1: hybrid
  - Tầng template (regex) cho 7 câu hỏi trọng tâm (đảm bảo ≥80%)
  - Tầng LLM stub (gọi API nếu có OPENAI_API_KEY, fallback về template)

Formal query dạng:
  {"intent": "tot_nghiep"|"thieu_mon"|"thieu_tc"|"dang_ky"|"du_dk_luan_van"|"mien"|"counterfactual",
   "claim": "tot_nghiep" | "thieu_nhom(g_ngoai_ngu,_)" | "du_dk_dang_ky(\"CT180\")" | ...,
   "params": {"ma_hp": "CT180", ...},
   "confidence": 0.0-1.0}

Chạy:  python parser.py --question "em đủ điều kiện tốt nghiệp chưa?"
       python parser.py --test
"""
import re, json, os
from pathlib import Path

# 7 intent chính (Tuan2 ma trận độ phủ) — thứ tự ưu tiên: cụ thể → chung
INTENTS = {
    "counterfactual":   {"claim": "counterfactual", "patterns": [r"nếu.*rớt", r"rớt.*thì", r"giả sử.*rớt", r"what.?if", r"không qua", r"rớt.*thì.*sao", r"nếu.*không qua"]},
    "mien":             {"claim": "du_dk_xin_mien", "patterns": [r"miễn", r"ielts", r"toeic", r"toefl", r"chứng chỉ.*miễn"]},
    "du_dk_luan_van":   {"claim": "du_dk_tc", "patterns": [r"luận văn", r"tiểu luận", r"làm.*luận văn", r"điều kiện.*luận văn"]},
    "dang_ky":          {"claim": "du_dk_dang_ky", "patterns": [r"đăng ký.*được.*chưa", r"được.*đăng ký", r"học.*được.*chưa", r"môn.*học.*được", r"đăng ký.*không"]},
    "thieu_mon":        {"claim": "thieu_bat_buoc", "patterns": [r"thiếu.*môn", r"còn.*môn", r"môn.*còn thiếu", r"học phần.*còn", r"còn.*học phần", r"nợ.*môn", r"thiếu.*học phần"]},
    "thieu_tc":         {"claim": "thieu_nhom", "patterns": [r"thiếu.*tín chỉ", r"còn.*tín chỉ", r"bao nhiêu.*tín chỉ", r"thiếu.*tc\b", r"còn.*tc\b", r"tín chỉ.*thiếu", r"tín chỉ.*còn"]},
    "tot_nghiep":       {"claim": "tot_nghiep", "patterns": [r"tốt nghiệp", r"ra trường", r"đủ.*điều kiện.*tốt nghiệp", r"được.*tốt nghiệp"]},
}

# regex mã HP: CTxxx, MLxxx, QPxxx, FLxxx, XHxxx, KNxxx
MA_HP_RE = re.compile(r"\b([A-Z]{1,3}\d{2,3}E?)\b", re.I)

def template_parse(q: str):
    ql = q.lower()
    best_intent = None
    best_score = 0
    for intent, info in INTENTS.items():
        for pat in info["patterns"]:
            if re.search(pat, ql):
                best_intent = intent
                best_score = 1.0
                break
        if best_intent: break
    if not best_intent:
        # fallback: nếu có mã HP → dang_ky, nếu hỏi thiếu → thieu
        if MA_HP_RE.search(q):
            best_intent = "dang_ky"
        else:
            best_intent = "tot_nghiep"
        best_score = 0.5

    info = INTENTS[best_intent]
    claim = info["claim"]
    params = {}

    # trích mã HP
    m = MA_HP_RE.search(q)
    if m:
        ma = m.group(1).upper()
        params["ma_hp"] = ma
        if best_intent == "dang_ky":
            claim = f'du_dk_dang_ky("{ma}")'
        elif best_intent == "counterfactual":
            claim = f'counterfactual("{ma}")'
        elif best_intent == "mien":
            claim = f'du_dk_xin_mien("{ma}")'

    # trích chứng chỉ
    if "ielts" in ql:
        params["chung_chi"] = "ielts"
        m2 = re.search(r"ielts\s*(\d\.?\d?)", ql)
        if m2: params["diem"] = float(m2.group(1))
    if "toeic" in ql:
        params["chung_chi"] = "toeic"
        m2 = re.search(r"toeic\s*(\d{3,4})", ql)
        if m2: params["diem"] = int(m2.group(1))

    return {"intent": best_intent, "claim": claim, "params": params, "confidence": best_score, "method": "template"}

def llm_parse(q: str):
    # stub: nếu có OPENAI_API_KEY thì gọi LLM, không thì fallback
    key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
    if not key:
        return None
    # TODO Tuần 13: gọi LLM với prompt few-shot, yêu cầu JSON
    # Hiện chưa cài, trả về None để fallback
    return None

def parse(q: str):
    # thử LLM trước, nếu có
    llm_res = llm_parse(q)
    if llm_res: return llm_res
    return template_parse(q)

# ---------- Test nội bộ ----------

TEST_CASES = [
    ("em đủ điều kiện tốt nghiệp chưa?", "tot_nghiep"),
    ("Em còn thiếu môn gì để ra trường?", "thieu_mon"),
    ("Em còn thiếu bao nhiêu tín chỉ?", "thieu_tc"),
    ("Kỳ này em đăng ký CT180 được chưa?", "dang_ky"),
    ("Em đủ điều kiện làm luận văn tốt nghiệp chưa?", "du_dk_luan_van"),
    ("Chứng chỉ IELTS 5.5 của em miễn được môn nào?", "mien"),
    ("Nếu em rớt CT177 thì tốt nghiệp trễ mấy kỳ?", "counterfactual"),
    ("Em có được tốt nghiệp không?", "tot_nghiep"),
    ("Còn thiếu những học phần nào nữa ạ?", "thieu_mon"),
    ("Em thiếu bao nhiêu TC nữa thì đủ?", "thieu_tc"),
    ("Cho em hỏi đăng ký CT182 có được không?", "dang_ky"),
    ("IELTS 6.0 miễn được Anh văn không?", "mien"),
    ("Giả sử em rớt CT101 thì sao?", "counterfactual"),
    ("Em có đủ điểm làm tiểu luận không?", "du_dk_luan_van"),
    ("Điều kiện tốt nghiệp gồm những gì?", "tot_nghiep"),
    ("Môn CT177 em học được chưa?", "dang_ky"),
    ("TOEIC 500 có miễn được gì không?", "mien"),
    ("Nếu em không qua CT112 thì sao?", "counterfactual"),
    ("Em còn nợ bao nhiêu môn bắt buộc?", "thieu_mon"),
    ("Tín chỉ tích lũy của em còn thiếu mấy?", "thieu_tc"),
]

def run_tests():
    ok=0
    for q, expect in TEST_CASES:
        res=parse(q)
        pred=res["intent"]
        # cho phép tot_nghiep vs thieu_mon lẫn nhau ở câu mơ hồ? Ở đây strict
        correct = (pred==expect)
        # một số câu có thể map khác nhưng vẫn hợp lệ: thieu_mon và thieu_tc đều hỏi thiếu
        # nhưng test này giữ strict để đo
        mark="OK" if correct else "FAIL"
        print(f"[{mark}] Q: {q[:45]:45s} → {pred:15s} (expect {expect})")
        if correct: ok+=1
    acc=ok/len(TEST_CASES)
    print(f"\nAccuracy: {ok}/{len(TEST_CASES)} = {acc:.1%} {'(đạt ≥80%)' if acc>=0.8 else '(CHƯA ĐẠT)'}")
    return acc

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--question", help="câu hỏi tiếng Việt")
    ap.add_argument("--test", action="store_true")
    args=ap.parse_args()
    if args.test:
        run_tests()
    elif args.question:
        print(json.dumps(parse(args.question), ensure_ascii=False, indent=2))
    else:
        run_tests()
