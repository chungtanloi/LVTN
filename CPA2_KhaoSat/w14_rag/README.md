# Tuần 14 — RAG grounding (CPA2)

**Sản phẩm:** RAG prototype: corpus quy chế + CTĐT theo điều/khoản, truy hồi, grounding certificate, hậu kiểm trích dẫn
**Tiêu chí hoàn thành:** Truy hồi đúng nguồn. Grounding cho kết luận ✅. Truy hồi tự do ⚠️ chưa đạt mục tiêu Recall (xem `../Tuan14_RAG_Grounding.md`)

## Chạy

```bash
pip install clingo            # không cần mạng, không cần model embedding
python build_corpus.py        # → corpus.jsonl, corpus_report.txt
python validate_rag.py        # tập dev
python validate_rag.py --test # tập test (chỉ để báo cáo — kết quả lưu ở validate_test_output.txt)
python grounded_answer.py --student ../w7_student_facts/students/sv_mien_ielts.json
python grounded_answer.py --tra-cuu "điểm W là gì"
```

## File

Ngày 29/10/2026, runtime tra cứu chuyển sang mô hình v3; xem phương pháp,
đánh đổi và số liệu trong [RETRIEVAL_V3.md](RETRIEVAL_V3.md). Các bộ TEST cũ
chỉ còn dùng chẩn đoán, chưa có bộ kiểm tra độc lập mới.

| File | Vai trò |
|---|---|
| `build_corpus.py` | OCR QĐ3266/QĐ5339 → passage theo (văn bản, điều, khoản); gắn trích R-Formal; trang OCR hỏng thì dựng từ trích; thêm passage CTĐT K49 |
| `retriever.py` | BM25 âm tiết + bigram, có/không dấu, mở rộng viết tắt; `ground_certificate` (tất định qua asp → passage); `kiem_trich_dan` |
| `rag_queries.json` | 48 câu hỏi, đáp án gán trước khi chạy; 24 dev / 24 test |
| `validate_rag.py` | A corpus · B truy hồi (báo cáo theo mục tiêu) · C grounding · D hậu kiểm |
| `grounded_answer.py` | Prototype v1 + nguồn trích dẫn đã hậu kiểm; chế độ tra cứu |

## Bất biến

> **Nguồn của một kết luận do chứng minh quyết định, không do truy hồi.** Mọi passage được trích trong câu trả lời có kết luận phải là nguồn của một bước trong certificate. Trích passage khác, dù truy hồi xếp hạng cao, đều bị chặn.
