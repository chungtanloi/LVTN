# TUẦN 23 — SO SÁNH CPA² VỚI BASELINE · PHÂN TÍCH CA SAI

**Giai đoạn:** Evaluation (Tuần 23/24) · **Mục tiêu:** so CPA² với ba baseline không có solver (LLM thuần, RAG thuần, tool-calling) trên cùng bộ ca, cùng cách chấm; phân tích ca sai
**Sản phẩm:** `w23_so_sanh/so_sanh.py` (đã có, `9248cb1`) · `bang_so_sanh_{dev,test}.md/.json` · báo cáo này
**Tiêu chí hoàn thành:** có bảng so sánh trên tập test + phân tích ca sai

> **Trạng thái 19/11/2026: KHUNG.** Công cụ so sánh đã xong và có kiểm thử, nhưng **chưa có lần chạy baseline thật nào**. Mục 1 (giao thức) viết **trước** lần chạy baseline đầu tiên, để không chỉnh cách so sau khi đã thấy số. Mục 2–4 để trống, chỉ điền từ file kết quả.

---

## 1. Giao thức (đăng ký TRƯỚC lần chạy baseline thật, commit riêng)

Phần này không sửa sau khi đã có kết quả baseline. Nếu buộc phải đổi, ghi thành mục "Sửa giao thức" có ngày và lý do, giữ nguyên bản cũ.

### 1.1 Bộ ca

| Split | Ca chấm | G-Truth | OCR-Noise | gold TRUE / FALSE / UNKNOWN | `[cau_hoi_ro]` |
|---|---|---|---|---|---|
| dev | 78 | 58 | 20 | 40 / 24 / 14 | 49 |
| test | 76 | 56 | 20 | 41 / 19 / 16 | 50 |

- Gold G-Truth và OCR-Noise: viết tay, đóng băng `312b7ff`. Errata (`gtruth_errata.json`) chỉ thêm dòng `[theo errata]`; số chính thức theo gold đóng băng.
- **Q-Noise không dùng để so.** Đây là bộ đo parser của CPA² (chấm chặt theo ý định), còn baseline không có parser riêng.
- **`[cau_hoi_ro]`:** câu hỏi của benchmark chưa công bằng với baseline ở 29/78 ca dev và 26/76 ca test (Tuần 21 §3, `run_baseline.cau_hoi_kem`). Có ca rỗng (dev 10 / test 10), hỏi bằng ký hiệu ASP (9 / 7), đề xuất đảo chiều (6 / 6), "xếp hạng gì?" (3 / 1) và "công nhận" (1 / 2). Mọi bảng đều báo **hai dòng** `tong` và `[cau_hoi_ro]`; kết luận so sánh dựa trên `[cau_hoi_ro]` (xem A20 ở mục 1.6).

### 1.2 Các hệ

| Hệ | Nguồn kết quả | Ghi chú |
|---|---|---|
| **CPA²** (chính thức) | `w20_benchmark/ket_qua_{gtruth,ocr_noise}_<split>.json` | test: lần chạy một lần ngày 02/11/2026 trên `e880ee4` (Tuần 22). dev: lần chạy gốc ngày 20/10, **đã nhiễm** (đã sửa hệ thống sau khi xem lỗi dev) |
| CPA² sau sửa (không chính thức) | `…_sau_A17.json` | sau C20, C21, C25, A17. Test đã nhiễm từ Tuần 22, nên dòng này chỉ cho biết lỗi đã sửa, **không** dùng làm số so sánh chính |
| b1 LLM thuần · b2 RAG thuần · b3 tool-calling | `w21_baseline/ket_qua_baseline_<bl>_<nha>_<split>.json` | 2 họ model (OpenAI, Gemini), gọi **qua OpenRouter** (`meta.qua`, `phuc_vu` từng ca). ID model và giá ghi ở mục 1.5 lúc chạy |

### 1.3 Lệnh (`PYTHONIOENCODING=utf-8`)

```
# 1) đóng băng prompt (một lần, TRƯỚC lần chạy thật đầu tiên) rồi commit prompt_dong_bang.json
cd w21_baseline && python run_baseline.py --ghi-bang --ghi-de
# 2) ước lượng chi phí, rồi chạy dev cho từng cấu hình
python run_baseline.py --bl b1 --nha gemini --split dev --uoc-luong
python run_baseline.py --bl b1 --nha gemini --split dev --chay-that      # lặp cho b1/b2/b3 × openai/gemini
# 3) bảng dev
cd ../w23_so_sanh && python so_sanh.py --split dev --cpa2-hau-to _sau_A17 --ra
# 4) test: MỘT lần cho mỗi cấu hình, chỉ sau khi xong mục 1.6
cd ../w21_baseline && python run_baseline.py --bl b1 --nha gemini --split test --chay-that --cho-phep-test
cd ../w23_so_sanh && python so_sanh.py --split test --cpa2-hau-to _sau_A17 --ra
```

### 1.4 Chỉ số và cách so

- **Cùng hàm chấm** `run_adversarial.cham / tong_hop` cho mọi hệ:
  - Soundness = 1 − (số kết luận TRUE/FALSE sai) / n; Coverage; Selective Accuracy; đúng gold; từ chối thừa.
  - LOI tính là SAI.
  - "Hỏi đúng" chỉ đo được với CPA².
- **Tập ca chung** lấy theo các hệ **chính thức**. Hệ không chính thức (không khớp bản đóng băng, có hậu tố) có n riêng và mang nhãn ở mọi bảng.
- **Kiểm định:** McNemar chính xác hai phía, cặp CPA² với từng baseline, trên "đúng gold" và trên "không unsound".
  - Tập nhỏ (≤ 78 ca) nên lực kiểm định thấp: p lớn **không** chứng minh hai hệ như nhau.
  - Có 6 phép so cho mỗi chỉ số. Báo p thô kèm ngưỡng Bonferroni 0,05/6 ≈ 0,0083; không chọn riêng phép so nào có p đẹp.
- **Mốc tham chiếu** (hệ "trả lời hằng", tính bằng chính `cham/tong_hop` trên gold), để đọc Soundness đúng nghĩa:

  | Mốc | dev: Soundness · Coverage · đúng gold | test: Soundness · Coverage · đúng gold |
  |---|---|---|
  | luôn UNKNOWN | 100% · 0% · 14/78 | 100% · 0% · 16/76 |
  | luôn TRUE | 51,3% · 100% · 40/78 | 53,9% · 100% · 41/76 |
  | luôn FALSE | 30,8% · 100% · 24/78 | 25,0% · 100% · 19/76 |

  Soundness cao **không** đủ: hệ chỉ từ chối cũng đạt 100%. Mọi nhận định "sound hơn" phải đi kèm Coverage và từ chối thừa.
- **Câu hỏi so sánh chính** (đặt trước): trên test, dòng `[cau_hoi_ro]`, CPA² chính thức so với baseline tốt nhất của từng loại (b1, b2, b3):
  1. số kết luận sai (unsound);
  2. Selective Accuracy;
  3. Coverage.

  Không đặt ngưỡng "hơn bao nhiêu" từ trước, vì chưa có cơ sở.

### 1.5 Môi trường và chi phí (điền lúc chạy, trước khi xem số)

| Mục | Giá trị |
|---|---|
| Commit lúc chạy | `<<điền>>` |
| `prompt_dong_bang.json` (sha256 / sha256_dau_vao) | `<<điền sau --ghi-bang>>` |
| Model OpenAI-family (ID OpenRouter) · giá vào/ra USD/1M token | `<<điền>>` |
| Model Gemini-family (ID OpenRouter) · giá vào/ra | `<<điền>>` |
| Nhiệt độ · max_out | `<<điền>>` (mặc định `llm.THAM_SO`) |
| Trần `BASELINE_MAX_USD` | `<<điền>>` |
| Nhà hạ tầng thực phục vụ | lấy từ `phuc_vu` trong file kết quả |

Phí nạp credit của OpenRouter không nằm trong giá token, nên chi phí thực cao hơn cột USD một chút.

### 1.6 Quyết định phải chốt TRƯỚC khi chạy test

- [ ] **A20:** viết câu hỏi tự nhiên cho 29 + 26 ca `cau_hoi_kem` (kèm soát độc lập + đóng băng như gold), **hay** chỉ báo hai dòng `tong` / `[cau_hoi_ro]`. Đề xuất: chỉ báo hai dòng (không đổi bộ ca sau đóng băng).
- [ ] **A21:** gold TN-01/03/08 (giả định thiếu `tc_cong_nhan` = 0) lệch R21. Chọn (a) errata → UNKNOWN, (b) thêm `tc_cong_nhan: 0` vào hồ sơ (sửa đầu vào sau đóng băng = errata), hay (c) giữ. Ảnh hưởng **cả** CPA² lẫn baseline vì dùng chung gold.

### 1.7 Xử lý khi thấy lỗi

- Không sửa prompt, công cụ, bộ ca hay cách chấm sau khi đã thấy số dev. Nếu buộc phải sửa: chạy lại với `--hau-to`, giữ số chính thức, ghi lý do.
- Mỗi ca unsound, từ chối thừa, thiếu nhãn hay LOI của baseline được xếp vào một loại ở mục 4.1, kèm trích đoạn câu trả lời thô (`tra_loi_tho`).
- Lỗi phát hiện ở CPA² trong lúc so: ghi thành mục C mới ở `Viec_ton_dong.md`, sửa theo quy trình (TDD + `_sau_<mã>`), **không** đổi số chính thức.

---

## 2. Kết quả dev (kiểm đường ống, KHÔNG phải số so sánh chính)

> Chưa chạy baseline. Hai dòng CPA² lấy từ `so_sanh.py --split dev --cpa2-hau-to _sau_A17` (19/11/2026). Phần còn lại dán từ `w23_so_sanh/bang_so_sanh_dev.md`.

### 2.1 `tong` (78 ca)

| Hệ | n | Soundness | unsound | Coverage | Selective Acc | đúng gold | từ chối thừa | thiếu nhãn | LOI | USD |
|---|---|---|---|---|---|---|---|---|---|---|
| CPA² (chính thức, 20/10, đã nhiễm) | 78 | 92,3% | 6 | 78,2% | 90,2% | 67 | 5 | 0 | 0 | 0 |
| CPA² `_sau_A17` (không chính thức) | 78 | 100,0% | 0 | 71,8% | 100,0% | 70 | 8 | 0 | 0 | 0 |
| b1 · b2 · b3 × openai · gemini | | *chưa chạy* | | | | | | | | |

### 2.2 `[cau_hoi_ro]` (49 ca)

| Hệ | n | Soundness | unsound | Coverage | Selective Acc | đúng gold | từ chối thừa |
|---|---|---|---|---|---|---|---|
| CPA² (chính thức) | 49 | 93,9% | 3 | 77,6% | 92,1% | 43 | 3 |
| CPA² `_sau_A17` | 49 | 100,0% | 0 | 63,3% | 100,0% | 41 | 8 |
| baseline | | *chưa chạy* | | | | | |

---

## 3. Kết quả test (số so sánh chính — chạy MỘT lần)

> Chưa chạy baseline. Chỉ chạy sau mục 1.6. Hai dòng CPA² có sẵn từ Tuần 22 (lấy qua `so_sanh.py --split test`).

### 3.1 `tong` (76 ca)

| Hệ | n | Soundness | unsound | Coverage | Selective Acc | đúng gold | từ chối thừa | thiếu nhãn | LOI | USD |
|---|---|---|---|---|---|---|---|---|---|---|
| CPA² (chính thức, Tuần 22) | 76 | 93,4% | 5 | 63,2% | 89,6% | 58 | 13 | 0 | 0 | 0 |
| CPA² `_sau_A17` (không chính thức, test đã nhiễm) | 76 | 100,0% | 0 | 61,8% | 100,0% | 63 | 13 | 0 | 0 | 0 |
| b1 · b2 · b3 × openai · gemini | | *chưa chạy* | | | | | | | | |

### 3.2 `[cau_hoi_ro]` (50 ca) · 3.3 `[theo errata]` · 3.4 McNemar

> Chưa chạy.

---

## 4. Phân tích ca sai

> Chưa có dữ liệu. Danh sách ca lấy từ mục "Ca bất đồng" của `bang_so_sanh_test.md`.

### 4.1 Cách phân loại (định trước)

| Mã | Loại lỗi của baseline | Dấu hiệu trong `tra_loi_tho` |
|---|---|---|
| L1 | Tính sai số (ĐTBCTL, tổng TC, ngưỡng %) | phép tính hoặc kết quả số sai |
| L2 | Bịa hoặc dùng sai quy định | dẫn điều/khoản không có, hoặc nội dung trái QĐ3266/QĐ5339 |
| L3 | Đúng quy định nhưng bỏ sót dữ kiện hồ sơ | bỏ qua HP F, miễn, song hành, thời gian học |
| L4 | Kết luận khi phải từ chối (gold UNKNOWN) | trả TRUE/FALSE thay vì nêu thiếu dữ kiện |
| L5 | Từ chối thừa (gold TRUE/FALSE) | UNKNOWN dù hồ sơ đủ |
| L6 | Không theo định dạng | thiếu hoặc mơ hồ dòng `NHAN:` |
| L7 | Câu hỏi của benchmark gây lỗi | ca thuộc `cau_hoi_kem` |
| L8 | Lỗi gọi API (LOI) | `tra_loi = LOI` |

Một ca có thể thuộc nhiều loại; ghi loại chính trước. CPA² dùng lại phân loại của Tuần 22 §3 (parser · KB · OCR · thiếu dữ kiện · gold).

### 4.2 CPA² đúng, baseline sai · 4.3 Baseline đúng, CPA² sai · 4.4 Cả hai cùng sai

> Chưa có dữ liệu.

---

## 5. Hạn chế (đã biết trước khi chạy)

- **Bộ ca, gold và baseline đều do em viết.** Chưa có người thứ hai soát (A7).
- **Tập nhỏ:** 76 ca test, nên các khác biệt dưới khoảng 10 ca khó có ý nghĩa thống kê.
- **Mỗi họ model chỉ một model.** Mỗi model chạy một lần ở nhiệt độ đã đóng băng; chưa đo độ dao động giữa các lần chạy của LLM.
- **Đi qua OpenRouter:** nhà hạ tầng thực có thể khác nhau giữa các ca (`phuc_vu`).
- **Dev của CPA² đã nhiễm,** nên so sánh dev chỉ để kiểm đường ống.
- **CPA² test chính thức là bản 02/11:** các lỗi đã sửa sau đó (C20, C21, C25, A17) vẫn tính vào số chính thức. Dòng `_sau_A17` chỉ minh hoạ, vì test đã nhiễm.
- **Câu hỏi:** CPA² đọc `claim`, baseline đọc `cau_hoi`. `[cau_hoi_ro]` chỉ giảm chứ không loại hết khác biệt đầu vào này.

## 6. Việc còn lại

- [ ] **A19 (cần Loi):** điền ID model, giá và trần vào `.env` → `--ghi-bang --ghi-de` → commit → ước lượng → chạy dev 6 cấu hình.
- [ ] **A20, A21 (cần Loi):** chốt trước khi chạy test (mục 1.6).
- [ ] Điền mục 1.5, chạy `so_sanh.py --split dev --ra`, điền mục 2.
- [ ] Chạy test một lần cho mỗi cấu hình, điền mục 3, phân tích mục 4.
- [ ] Cập nhật checklist Excel: chỉ tích ô có bằng chứng.
