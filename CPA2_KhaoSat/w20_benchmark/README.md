# w20_benchmark — bộ đánh giá Tuần 20

| Bộ | n | Nội dung | Gold |
|---|---|---|---|
| **G-Truth v1** (`gtruth.json`) | 115 (114 chấm) | đăng ký + song hành, eligibility, bất biến đề xuất, tốt nghiệp, nhóm tự chọn, miễn/thay thế, hạng tốt nghiệp, câu tự nhiên | viết tay, đóng băng `312b7ff` |
| **OCR-Noise v1** (`ocr_noise.json`) | 40 | 10 kịch bản × 4 mức nhiễu (M1 nhẹ · M2 mất kiểm chéo · M3 sai phát hiện được · M4 mất dòng) | viết tay, đóng băng `312b7ff` |
| **Q-Real** (`qreal/`) | 0 / 400 | câu hỏi thật, Loi cung cấp — xem `qreal/README.md` | nhãn ý định gán tay |
| **Q-Noise v1** (`qnoise.json`) — TỔNG HỢP | 240 | 48 câu G-Truth × V0 gốc / V1 bỏ dấu / V2 viết tắt / V3 gõ vội / V4 = V2 bỏ dấu — đo độ bền parser, **không** thay Q-Real | kế thừa G-Truth + ý định gán tay, đóng băng `5d8601c` |

```bash
python build_benchmark.py            # sinh lại json (KHÔNG --dong-bang: gold đã đóng băng)
python validate_benchmark.py         # B1–B10
python build_qnoise.py               # sinh lại qnoise.json (tất định; phải trùng hash đóng băng)
python run_cpa2.py --bo qnoise --split dev        # chấm chặt theo ý định + theo biến thể
python run_cpa2.py --bo gtruth --split dev        # Tuần 20 chỉ chạy dev; test → Tuần 22
python baseline.py --split dev       # đầu vào trung lập cho baseline Tuần 21
python nhap_qreal.py                 # nhập Q-Real từ qreal/_tho/
```

- `loai_gold`: `quy_che` (theo câu chữ quy chế/CTĐT) hoặc `thiet_ke` (nguyên tắc thiết kế: không kết luận ngoài KB, OCR mâu thuẫn/mất dòng, chính sách tư vấn). Hai loại được báo cáo tách riêng.
- Sai sót phát hiện sau khi đóng băng → **errata**, KHÔNG sửa gold (như w17).
- Chấm điểm dùng chung `w17_adversarial/run_adversarial.cham/tong_hop` (Soundness, Coverage, Selective Accuracy, hỏi đúng).
