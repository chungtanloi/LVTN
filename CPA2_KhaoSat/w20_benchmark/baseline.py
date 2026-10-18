"""
baseline.py — đầu vào TRUNG LẬP cho baseline Tuần 21 (LLM thuần, RAG thuần, tool-calling) trên G-Truth / OCR-Noise

Mỗi ca → {id, cau_hoi, ho_so | bang_diem_ocr + khai_bao, mo_ta, dang_cau_tra_loi}. KHÔNG chứa gold, lý do, nguồn,
sự thật, tiền đề oracle, tên hồ sơ gốc (student_id, meta) — cùng nguyên tắc w17 dau_vao_baseline (hồ sơ gốc còn giữ
điểm thật của HP "chưa rõ" → lộ đáp án).

Chạy:  python baseline.py --split dev     → baseline_dev.jsonl   (Tuần 21 đọc file này)
"""
import argparse, json, sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "w17_adversarial"))
import dau_vao

TRA_LOI = ("Trả lời đúng MỘT nhãn: TRUE (đúng/đủ điều kiện), FALSE (không đúng/không đủ), hoặc UNKNOWN (chưa đủ "
           "dữ kiện để kết luận, kèm dữ kiện cần bổ sung). Câu hỏi về sinh viên dựa trên hồ sơ đính kèm.")


def _sach(hs):
    hs = dict(hs)
    hs.pop("student_id", None)
    hs.pop("meta", None)
    return hs


def dau_vao_baseline(ca):
    v = dau_vao.vat_lieu_hoa(ca)
    out = {"id": ca["id"], "cau_hoi": ca.get("cau_hoi", ""), "dang_cau_tra_loi": TRA_LOI}
    if ca["dau_vao"]["loai"] == "ho_so":
        out["ho_so"] = _sach(v["ho_so"])
        out["mo_ta"] = dau_vao.mo_ta_cho_nguoi(ca)
    else:
        out["bang_diem_ocr"] = v["doc"]
        out["khai_bao"] = v["khai_bao"]
        out["mo_ta"] = "Bảng điểm đọc bằng OCR (có độ tin cậy từng ô) và các khai báo của sinh viên (đính kèm)."
    if ca["he"] == "rec":
        out["mo_ta"] += f" Câu hỏi về phương án đăng ký học kỳ {ca['hk']} (học kỳ 3 là học kỳ hè)."
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "test"], required=True)
    a = ap.parse_args()
    n = 0
    with open(HERE / f"baseline_{a.split}.jsonl", "w", encoding="utf-8") as f:
        for ten in ("gtruth.json", "ocr_noise.json"):
            for c in json.loads((HERE / ten).read_text(encoding="utf-8"))["cases"]:
                if c["split"] == a.split:
                    f.write(json.dumps(dau_vao_baseline(c), ensure_ascii=False) + "\n")
                    n += 1
    print(f"đã ghi baseline_{a.split}.jsonl ({n} ca)")


if __name__ == "__main__":
    main()
