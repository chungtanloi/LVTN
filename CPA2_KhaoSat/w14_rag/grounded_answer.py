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

from retriever import Retriever, kiem_trich_dan
import prototype


def tra_loi(question, student_path, r=None):
    r = r or Retriever(ranked=False)  # certificate grounding never depends on the trained search ranker
    res = prototype.answer(question, student_path)
    cert = r.ground_certificate(res["certificate"])
    trich = r.trich_dan(cert)
    ok, sai = kiem_trich_dan(cert, [t["passage_id"] for t in trich])
    if not ok:
        return {"verdict": "BLOCKED", "ly_do": f"trích passage ngoài chứng minh: {sai}"}
    res["nguon"] = trich
    return res


def tra_cuu(question, k=3, r=None):
    r = r or Retriever()
    return [{"passage_id": p["id"], "dia_chi": p.get("dia_chi") or p["tieu_de"], "trang": p["trang"],
             "trich": p["text"][:300]} for p, _ in r.search(question, k=k)]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--question", default="em đủ điều kiện tốt nghiệp chưa?")
    ap.add_argument("--student")
    ap.add_argument("--tra-cuu", dest="tra_cuu")
    a = ap.parse_args()
    out = tra_cuu(a.tra_cuu) if a.tra_cuu else tra_loi(a.question, a.student)
    print(json.dumps(out, ensure_ascii=False, indent=2))
