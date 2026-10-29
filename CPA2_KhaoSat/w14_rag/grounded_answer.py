"""
grounded_answer.py — Prototype v1 (Tuần 12) + grounding nguồn (Tuần 14)

Câu hỏi cá nhân  → solver ba trị → certificate → passage nguồn của từng bước → trích dẫn (đã hậu kiểm)
Câu hỏi tra cứu  → truy hồi top-k (không có hồ sơ: không kết luận gì về sinh viên, chỉ trả văn bản)

Chạy: python grounded_answer.py --student ../w7_student_facts/students/sv_mien_ielts.json
      python grounded_answer.py --tra-cuu "điểm W là gì"
"""
import argparse, json, sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "w12_integration"))

from retriever import Retriever, kiem_trich_dan, source_excerpt, source_documents, requested_articles, requested_decisions, bo_dau, resolve_source_passage
import re
import prototype


def tra_loi(question, student_path, r=None):
    r = r or Retriever(ranked=False)  # certificate grounding never depends on the trained search ranker
    res = prototype.answer(question, student_path)
    cert = r.ground_certificate(res["certificate"])
    trich = r.trich_dan(cert)
    ok, sai = kiem_trich_dan(cert, [t["passage_id"] for t in trich])
    if not ok:
        return {"verdict": "BLOCKED", "reason": "GROUNDING_SOURCE_INVALID",
                "ly_do": "Chưa thể xác nhận kết luận vì chứng chỉ thiếu nguồn hợp lệ.",
                "grounding_errors": sai}
    res["nguon"] = trich
    return res


def tra_cuu(question, k=3, r=None):
    r = r or Retriever()
    passages = []
    sources = source_documents()
    # An exact legal address is a deterministic source lookup, including the
    # clause that was previously merged into another clause by OCR.
    articles, decisions = requested_articles(question), requested_decisions(question)
    clauses = set(re.findall(r'\bkhoan\s+(\d\w*)', bo_dau(question.lower())))
    if articles and clauses:
        matches = [p for p in sources.values() if str(p.get('dieu')) in articles
                   and str(p.get('khoan')) in clauses
                   and (not decisions or p['van_ban'].removeprefix('qd') in decisions)]
    else:
        matches = [resolve_source_passage(p, question) for p, _ in r.search(question, k=k)]
    for p in matches[:k]:
        excerpt, start, end = source_excerpt(question, p)
        passages.append({"passage_id": p["id"], "dia_chi": p.get("dia_chi") or p["tieu_de"], "trang": p["trang"],
                         "trich": excerpt, "text": p['text'], "excerpt_start": start, "excerpt_end": end,
                         'source_quality': p.get('source_quality')})
    return passages


def lookup_response(question):
    words = bo_dau(question.lower())
    codes = re.findall(r'\b[A-Z]{2}\d{3}E?\b', question.upper())
    if not codes and re.search(r'\b(?:mon|hoc phan) (?:nay|do)\b', words):
        return {'passages': [], 'clarification': {
            'message': 'Bạn đang hỏi học phần nào? Hãy bổ sung mã môn để tra đúng quy định hoặc tiên quyết.',
            'examples': ['Môn CT177 có tiên quyết là gì?', 'Điểm F thì có phải học lại không?']}}
    if (re.search(r'\b(?:em|minh|toi)\b', words)
            and re.search(r'\b(?:chua|co duoc|duoc khong|hay khong)\b', words)):
        return {'passages': [], 'clarification': {
            'message': 'Để kiểm tra trường hợp của bạn, mở Tư vấn học vụ với hồ sơ đã xác nhận. Nếu chỉ tra văn bản, hãy nêu nội dung quy chế cần tìm.',
            'examples': ['Điều kiện xét tốt nghiệp gồm những gì?', 'Quy định đăng ký học phần']}}
    return {'passages': tra_cuu(question)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--question", default="em đủ điều kiện tốt nghiệp chưa?")
    ap.add_argument("--student")
    ap.add_argument("--tra-cuu", dest="tra_cuu")
    a = ap.parse_args()
    out = tra_cuu(a.tra_cuu) if a.tra_cuu else tra_loi(a.question, a.student)
    print(json.dumps(out, ensure_ascii=False, indent=2))
