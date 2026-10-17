# Tuần 17 — Adversarial set (CPA2)

**Sản phẩm:** Adversarial set v1: 80 ca chấm điểm (+ 5 ca không chấm), gold viết tay và đóng băng trước khi chạy
**Tiêu chí hoàn thành:** ≥ 60 case đối kháng ✅. `validate_adversarial.py` ĐẠT (xem `../Tuan17_Adversarial_Set.md`)

## Chạy

```bash
python build_adversarial.py            # sinh adversarial_set.json (KHÔNG sửa tay — validate G1 kiểm)
python validate_adversarial.py         # toàn vẹn bộ ca + oracle + gold đóng băng
python run_adversarial.py --split dev  # chấm CPA²; chỉ tinh chỉnh dựa trên dev
python run_adversarial.py --split test # chạy để báo cáo
```

## File

| File | Vai trò |
|---|---|
| `build_adversarial.py` | Định nghĩa 85 ca: đầu vào trung lập + **gold viết tay** + lý do + nguồn (điều/khoản/trang) |
| `adversarial_set.json` | Bộ ca (file sinh) |
| `gold_dong_bang.json` | Gold trích từ commit `200b860` — trước lần chạy CPA² đầu tiên |
| `oracle.py` | Tính ĐTBCTL, TC, TB GDQP, trần thời gian bằng Python thuần từ câu chữ quy chế (không clingo) |
| `dau_vao.py` | Dựng hồ sơ / tài liệu OCR từ mô tả ca; `dau_vao_baseline()` cho baseline Tuần 21 (không lộ đáp án) |
| `run_adversarial.py` | Chấm CPA²: Soundness, Coverage, Selective Accuracy, từ chối thừa, hỏi đúng |
| `ket_qua_{dev,test}.json`, `run_output_{dev,test}.txt` | Kết quả chạy |

## Bất biến

> **Gold có trước kết quả.** Gold nằm trong `build_adversarial.py`, được commit (`200b860`) trước khi CPA² chạy lần nào. `validate_adversarial.py` G1/G2 chặn mọi sửa đổi về sau. Sai sót phát hiện sau đó được ghi errata trong báo cáo, không sửa gold.
