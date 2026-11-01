# TUẦN 22 — ĐÁNH GIÁ CPA² TRÊN TẬP TEST

**Giai đoạn:** Evaluation (Tuần 22/24) · **Mục tiêu:** Soundness, Coverage, Selective Accuracy, consistency trên tập test
**Sản phẩm:** CPA² results (`w20_benchmark/ket_qua_*_test.json`, `run_output_*_test.txt`)
**Tiêu chí hoàn thành:** Có số liệu + error analysis

---

## 1. Giao thức (đăng ký TRƯỚC lần chạy test, commit riêng)

Phần này viết và commit **trước** khi chạy bất kỳ ca test nào. Kết quả ghi ở các mục sau, không sửa mục 1.

### 1.1 Dữ liệu

| Bộ | Ca test chấm điểm | Gold | Ghi chú |
|---|---|---|---|
| G-Truth v1 | 56 | viết tay, đóng băng `312b7ff` | errata `gtruth_errata.json` có 3 ca test (HG-02, HG-04, HG-08) — chỉ in dòng `[theo errata]`, số chính thức theo gold đóng băng |
| OCR-Noise v1 | 20 | viết tay, đóng băng `312b7ff` | không có errata |
| Q-Noise | 110 | tổng hợp, kế thừa gold G-Truth, đóng băng `qnoise_dong_bang.json` | chấm chặt theo ý định; báo RIÊNG, không gộp vào G-Truth, không thay Q-Real |

Dev đã bị nhiễm (hệ thống đã sửa sau khi xem lỗi dev: P20, P20-4, P20-5, C12, C14, C15). Số dev chỉ để đối chiếu; số chính thức là test.

### 1.2 Lệnh (chạy từ `w20_benchmark/`, `PYTHONIOENCODING=utf-8`)

```
python run_cpa2.py --bo gtruth    --split test > run_output_gtruth_test.txt
python run_cpa2.py --bo ocr_noise --split test > run_output_ocr_noise_test.txt
python run_cpa2.py --bo qnoise    --split test > run_output_qnoise_test.txt
```

Tính tất định: chạy G-Truth test lần hai với `--hau-to _lap2`, chỉ so khớp từng ca (verdict + câu hỏi bổ sung) với lần một; không dùng để chọn gì.

### 1.3 Chỉ số và chỉ tiêu

Cách chấm của `w17_adversarial/run_adversarial.cham / tong_hop` (dùng chung với baseline Tuần 21), không đổi:
Soundness = 1 − #kết luận TRUE/FALSE sai / n · Coverage · Selective Accuracy · Đúng gold · Từ chối thừa · Hỏi đúng. LOI tính là SAI.

- Chỉ tiêu (Tuần 1, mức "Tối thiểu"): **Soundness = 100% trên G-Truth**. Áp cho test G-Truth, số chính thức theo gold đóng băng.
- Coverage, Selective Accuracy: báo cáo, không có ngưỡng đặt trước.
- Báo tách `[quy_che]` / `[thiet_ke]` như Tuần 20.

### 1.4 Xử lý khi thấy lỗi

- Không sửa hệ thống, gold hoặc cách chấm trước khi ghi xong số test.
- Mọi ca unsound / từ chối thừa / LOI được phân tích nguyên nhân (parser · KB · OCR · thiếu dữ kiện · gold) kèm điều/khoản.
- Gold sai phát hiện sau → errata, không sửa gold. Nếu sửa hệ thống sau đó: chạy với `--hau-to _sau_<mã>`, số chính thức giữ nguyên, tập test coi như đã nhiễm.

### 1.5 Môi trường

Nhánh `codex/cpa2-web-deploy` (bản đang chạy trên web), commit giao thức là con của `ab080bb`. Windows 11, Python 3.14.0, clingo 5.8.2, Tesseract v5.5.0.20241111 (`C:/Program Files/Tesseract-OCR`). Số OCR-Noise chỉ so được với lượt chạy cùng môi trường.

Trước khi chạy: toàn bộ `w*/validate_*.py` phải ĐẠT (gồm `validate_benchmark` B6 — hash gold khớp).
