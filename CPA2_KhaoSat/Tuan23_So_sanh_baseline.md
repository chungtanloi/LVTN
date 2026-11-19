# TUẦN 23 — SO SÁNH CPA² VỚI BASELINE · PHÂN TÍCH CA SAI

**Giai đoạn:** Evaluation (Tuần 23/24) · **Mục tiêu:** so CPA² với ba baseline không có solver (LLM thuần, RAG thuần, tool-calling) trên cùng bộ ca, cùng cách chấm; phân tích ca sai
**Sản phẩm:** `w23_so_sanh/so_sanh.py` (đã có, `9248cb1`) · `bang_so_sanh_{dev,test}.md/.json` · báo cáo này
**Tiêu chí hoàn thành:** có bảng so sánh trên tập test + phân tích ca sai

> **Trạng thái 20/11/2026: CÓ SỐ TEST + PHÂN TÍCH CA SAI.** Mục 1 (giao thức) commit **trước** lần chạy baseline đầu tiên (`eeff56d`). Dev 6/6 (mục 2, 7,37 USD). **Test 6/6, chạy một lần** (mục 3, 7,28 USD), phân tích ca sai ở mục 4.
>
> **Kết luận chính (mục 3.5):** trên `[cau_hoi_ro]` của test, không baseline nào vừa sai ít hơn vừa kết luận nhiều hơn CPA². Nhưng CPA² chính thức (bản 02/11) **không** sai ít hơn baseline OpenAI (2 vs 0 kết luận sai) — các baseline đó gần như luôn từ chối (Coverage 2–28%). Về số ca đúng gold, CPA² hơn 5/6 baseline có ý nghĩa thống kê (Bonferroni); với b3 Gemini thì chưa (p = 0,0094).

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
| Mục | Giá trị (dev, 19/11/2026) |
|---|---|
| Commit lúc chạy | b1 Gemini: `256df16`; b1 OpenAI, b2 Gemini, b2 OpenAI: `cd5f68c`; b3 Gemini, b3 OpenAI: `fd805dc`. Ba lần (b2 ×2, b3 OpenAI) ghi `chua_commit: true` vì file kết quả của lần chạy ngay trước chưa commit (không phải mã nguồn; hash đóng băng khớp) |
| `prompt_dong_bang.json` (sha256 / sha256_dau_vao) | `fad02fb25b67…` / `eff97ff7e5a5…` (đóng băng lại ở `256df16`, TRƯỚC lần gọi API thành công đầu tiên — xem ghi chú dưới) |
| Model OpenAI-family (ID OpenRouter) · giá vào/ra USD/1M token | `openai/gpt-6.1-sol` (ra mắt 30/09/2026) · 2 / 10 |
| Model Gemini-family (ID OpenRouter) · giá vào/ra | `google/gemini-4-argon` (ra mắt 13/10/2026) · 2 / 10 |
| Nhiệt độ · max_out | không gửi `temperature` (mặc định nhà cung cấp) · 16384 token ra/lần gọi (gồm token nghĩ) |
| Trần `BASELINE_MAX_USD` | 2 USD/lần chạy (dev b1, b2); 4 USD/lần chạy (dev b3, ước lượng ~3,2 USD). Trần không nằm trong bản đóng băng |
| Nhà hạ tầng thực phục vụ (`phuc_vu`, theo lượt gọi) | OpenAI: OpenAI ở mọi lượt (78, 78, 230 lượt). Gemini: Google 75 + Google AI Studio 3 (b1), 74 + 4 (b2), 218 + 16 (b3) |

Phí nạp credit của OpenRouter không nằm trong giá token, nên chi phí thực cao hơn cột USD một chút.

**Tiêu chí chọn model** (19/11/2026, giá lấy từ API công khai `openrouter.ai/api/v1/models`): đúng họ ghi trong CLAUDE.md (OpenAI "Sol" — logic nặng; Gemini cùng hạng và cùng giá); đã ra mắt ít nhất 2 tuần; có gọi công cụ (b3 cần); không dùng biến thể `:batch`.

**Hai lần đổi tham số đóng băng TRƯỚC khi có kết quả thật** (không có ca nào được chấm trước các lần đổi này):
1. `addb203`: `nhiet_do` 0 → không gửi. Bộ chặn đóng băng dừng lần chạy đầu vì `BASELINE_TEMPERATURE=none` khác bản đóng băng; model OpenAI đã chọn không nhận `temperature`. Để hai họ cùng cấu hình, cả hai đều không gửi.
2. `256df16`: `max_out` không đặt → 16384. Lần thử thứ hai trả HTTP 402 ngay ca đầu (OpenRouter giữ chỗ 65536 token/lần gọi khi không có trần; credit thấp). 0 ca xong, 0 USD.

### 1.6 Quyết định phải chốt TRƯỚC khi chạy test

- [x] **A20:** viết câu hỏi tự nhiên cho 29 + 26 ca `cau_hoi_kem` (kèm soát độc lập + đóng băng như gold), **hay** chỉ báo hai dòng `tong` / `[cau_hoi_ro]`. **Loi chọn 19/11/2026: chỉ báo hai dòng.**
- [x] **A21:** gold TN-01/03/08 (giả định thiếu `tc_cong_nhan` = 0) lệch R21. Chọn (a) errata → UNKNOWN, (b) thêm `tc_cong_nhan: 0` vào hồ sơ (sửa đầu vào sau đóng băng = errata), hay (c) giữ. Ảnh hưởng **cả** CPA² lẫn baseline vì dùng chung gold. **Loi chọn (a) 19/11/2026:** ba mục mới trong `gtruth_errata.json` (TN-01, TN-03 TRUE → UNKNOWN; TN-08 FALSE → UNKNOWN), ghi TRƯỚC lần chạy baseline test đầu tiên. Số chính thức vẫn theo gold đóng băng; dòng `[theo errata]` của CPA² test đổi theo (đúng gold 64, từ chối thừa 7).

### 1.7 Xử lý khi thấy lỗi

- Không sửa prompt, công cụ, bộ ca hay cách chấm sau khi đã thấy số dev. Nếu buộc phải sửa: chạy lại với `--hau-to`, giữ số chính thức, ghi lý do.
- Mỗi ca unsound, từ chối thừa, thiếu nhãn hay LOI của baseline được xếp vào một loại ở mục 4.1, kèm trích đoạn câu trả lời thô (`tra_loi_tho`).
- Lỗi phát hiện ở CPA² trong lúc so: ghi thành mục C mới ở `Viec_ton_dong.md`, sửa theo quy trình (TDD + `_sau_<mã>`), **không** đổi số chính thức.

---

## 2. Kết quả dev (kiểm đường ống, KHÔNG phải số so sánh chính)

> **6/6 cấu hình đã chạy (19/11/2026).** Số lấy từ `w23_so_sanh/bang_so_sanh_dev.md` (`so_sanh.py --split dev --cpa2-hau-to _sau_A17 --ra`). Mọi baseline khớp bản đóng băng (chính thức), 78/78 ca, 0 LOI. Thiếu nhãn chỉ có ở b3 (Gemini 9, OpenAI 1): đều là ca hết 6 lượt gọi công cụ mà chưa kết luận → tính UNKNOWN. **Dev chỉ để kiểm đường ống**: dòng CPA² chính thức là lần chạy 20/10 trên dev đã nhiễm.

### 2.1 `tong` (78 ca)

| Hệ | n | Soundness | unsound | Coverage | Selective Acc | đúng gold | từ chối thừa | thiếu nhãn | LOI | USD |
|---|---|---|---|---|---|---|---|---|---|---|
| CPA² (chính thức, 20/10, đã nhiễm) | 78 | 92,3% | 6 | 78,2% | 90,2% | 67 | 5 | 0 | 0 | 0 |
| CPA² `_sau_A17` (không chính thức) | 78 | 100,0% | 0 | 71,8% | 100,0% | 70 | 8 | 0 | 0 | 0 |
| b1 OpenAI (gpt-6.1-sol) | 78 | 100,0% | 0 | 3,8% | 100,0% | 17 | 61 | 0 | 0 | 0,54 |
| b1 Gemini (gemini-4-argon) | 78 | 79,5% | 16 | 55,1% | 62,8% | 38 | 24 | 0 | 0 | 0,66 |
| b2 OpenAI | 78 | 98,7% | 1 | 10,3% | 87,5% | 21 | 56 | 0 | 0 | 0,75 |
| b2 Gemini | 78 | 93,6% | 5 | 29,5% | 78,3% | 29 | 44 | 0 | 0 | 0,87 |
| b3 OpenAI | 78 | 89,7% | 8 | 44,9% | 77,1% | 38 | 32 | 1 | 0 | 2,19 |
| b3 Gemini | 78 | 85,9% | 11 | 53,8% | 73,8% | 38 | 29 | 9 | 0 | 2,35 |
| *mốc: luôn UNKNOWN* | 78 | 100% | 0 | 0% | — | 14 | 64 | | | |

### 2.2 `[cau_hoi_ro]` (49 ca)

| Hệ | n | Soundness | unsound | Coverage | Selective Acc | đúng gold | từ chối thừa |
|---|---|---|---|---|---|---|---|
| CPA² (chính thức) | 49 | 93,9% | 3 | 77,6% | 92,1% | 43 | 3 |
| CPA² `_sau_A17` | 49 | 100,0% | 0 | 63,3% | 100,0% | 41 | 8 |
| b1 OpenAI | 49 | 100,0% | 0 | 2,0% | 100,0% | 11 | 38 |
| b1 Gemini | 49 | 77,6% | 11 | 65,3% | 65,6% | 29 | 9 |
| b2 OpenAI | 49 | 98,0% | 1 | 10,2% | 80,0% | 14 | 34 |
| b2 Gemini | 49 | 95,9% | 2 | 30,6% | 86,7% | 22 | 25 |
| b3 OpenAI | 49 | 95,9% | 2 | 46,9% | 91,3% | 30 | 17 |
| b3 Gemini | 49 | 89,8% | 5 | 57,1% | 82,1% | 28 | 16 |

### 2.3 `[quy_che]` (65 ca) và `[thiet_ke]` (13 ca)

| Hệ | `[quy_che]` unsound · Coverage · đúng gold | `[thiet_ke]` unsound · Coverage · đúng gold |
|---|---|---|
| CPA² (chính thức) | 4 · 90,8% · 56 | 2 · 15,4% · 11 |
| CPA² `_sau_A17` | 0 · 86,2% · 57 | 0 · 0% · 13 |
| b1 OpenAI | 0 · 4,6% · 4 | 0 · 0% · 13 |
| b1 Gemini | 13 · 61,5% · 28 | 3 · 23,1% · 10 |
| b2 OpenAI | 1 · 12,3% · 8 | 0 · 0% · 13 |
| b2 Gemini | 2 · 30,8% · 19 | 3 · 23,1% · 10 |
| b3 OpenAI | 5 · 49,2% · 28 | 3 · 23,1% · 10 |
| b3 Gemini | 4 · 53,8% · 32 | 7 · 53,8% · 6 |

`[theo errata]`: số b1/b2 không đổi so với `tong`; CPA² chính thức 7 unsound / 66 đúng gold (gold đóng băng: 6 / 67); b3 OpenAI 9 / 37 (8 / 38); b3 Gemini 11 / 39 (11 / 38).

### 2.4 McNemar (CPA² chính thức vs baseline, 78 cặp)

| Baseline | đúng gold: CPA² kém / CPA² hơn / p | không unsound: CPA² kém / CPA² hơn / p |
|---|---|---|
| b1 OpenAI | 3 / 53 / < 0,0001 | **6 / 0 / 0,031** |
| b1 Gemini | 7 / 36 / < 0,0001 | 6 / 16 / 0,053 |
| b2 OpenAI | 3 / 49 / < 0,0001 | 6 / 1 / 0,125 |
| b2 Gemini | 7 / 45 / < 0,0001 | 6 / 5 / 1,000 |
| b3 OpenAI | 5 / 34 / < 0,0001 | 6 / 8 / 0,791 |
| b3 Gemini | 8 / 37 / < 0,0001 | 5 / 10 / 0,302 |

Ngưỡng Bonferroni 0,05/6 ≈ 0,0083 (mục 1.4). Ca bất đồng từng cặp: `bang_so_sanh_dev.md`.

### 2.5 Nhận xét trên dev (chưa phải kết luận — chờ test)

- **Hai họ model cư xử ngược nhau.** GPT-6.1-sol gần như luôn từ chối: 75/78 ca ở b1 trả UNKNOWN và nêu rõ lý do — "chưa có quy định điều kiện đăng ký … cần bổ sung" (b1 không có văn bản quy chế). Soundness 100% nhưng Coverage 3,8%, sát mốc "luôn UNKNOWN". Gemini kết luận nhiều hơn nhưng sai nhiều (b1: 16 unsound).
- **Truy hồi điều khoản (b2) giảm lỗi của Gemini** (unsound 16 → 5) nhưng cũng giảm Coverage (55,1% → 29,5%); với OpenAI, b2 kết luận nhiều hơn b1 một chút (3,8% → 10,3%) và thêm 1 ca sai (EL-09).
- **Đúng gold:** CPA² hơn cả 4 baseline ở 36–53 ca, kém ở 3–7 ca (p < 0,0001, qua ngưỡng Bonferroni).
- **Không unsound: CPA² chính thức THUA b1 OpenAI** (6 vs 0, p = 0,031 — chưa qua ngưỡng Bonferroni). b1 OpenAI gần như không kết luận gì, nên không sai; 6 ca sai của CPA² trên dev 20/10 là lỗi đã sửa sau đó (bản `_sau_A17`: 0 unsound) — nhưng dev đã nhiễm nên không dùng bản sau sửa để kết luận. Đây là lý do mục 1.4 không cho đọc Soundness một mình.
- **Ca CPA² chính thức sai mà baseline đúng:** NL-06, NL-10, NL-11 (parser, đã sửa sau 20/10) và HG-01 (chỉ so với b2 Gemini).
- **Công cụ (b3) kéo hai họ model về gần nhau.** OpenAI kết luận nhiều hơn hẳn (Coverage 3,8% ở b1 → 44,9%) nhưng sai nhiều hơn (0 → 8 unsound); Gemini sai ít hơn b1 (16 → 11) với Coverage gần như giữ nguyên (55,1% → 53,8%). Trung bình 3 lượt gọi/ca. Trên `[cau_hoi_ro]`, b3 OpenAI là baseline mạnh nhất: 2 unsound, Coverage 46,9%, Selective Acc 91,3% — so với CPA² chính thức 3 unsound, 77,6%, 92,1%.
- **Ca baseline sai lặp lại ở nhiều cấu hình:** đề xuất đăng ký (RC-02, RC-04, RC-05, RC-06) và OCR mức M4 (ON-05M4, ON-06M4, ON-10M4) — sẽ phân tích ở mục 4 trên test. Ở `[thiet_ke]`, b3 Gemini có 7/13 kết luận sai (những ca gold UNKNOWN theo nguyên tắc thiết kế).
- **Chi phí:** 7,37 USD cho 6 lần chạy dev (b1/b2: 2,83; b3: 4,54); thấp hơn ước lượng thô (~10,2 USD). Token ra rất ít (b1/b2: OpenAI ~100–130, Gemini ~200–220 token/ca): với cấu hình này, hai model gần như không sinh token nghĩ tính phí.

---

## 3. Kết quả test (số so sánh chính — chạy MỘT lần)

> **Chạy một lần, 19–20/11/2026**, sau khi chốt A20/A21 (`c146b69`). b1/b2 trên `c146b69`, b3 trên `04bc0b9`; mọi file khớp bản đóng băng `fad02fb2…/eff97ff7…`, 76/76 ca, 0 LOI trong kết quả cuối. b3 Gemini dừng hai lần và tiếp tục từ checkpoint: HTTP 402 hết credit ở 30/76, rồi 1 ca LOI tạm thời được thử lại bằng chính lệnh đó (không phải chạy test lần hai). Chi phí test 7,28 USD (tổng dev + test 14,65 USD). Số lấy từ `w23_so_sanh/bang_so_sanh_test.md`. Hai dòng CPA² là lần chạy Tuần 22 (02/11, `e880ee4`).

### 3.1 `tong` (76 ca)

| Hệ | n | Soundness | unsound | Coverage | Selective Acc | đúng gold | từ chối thừa | thiếu nhãn | LOI | USD |
|---|---|---|---|---|---|---|---|---|---|---|
| **CPA² (chính thức, Tuần 22)** | 76 | 93,4% | 5 | 63,2% | 89,6% | **58** | 13 | 0 | 0 | 0 |
| CPA² `_sau_A17` (không chính thức, test đã nhiễm) | 76 | 100,0% | 0 | 61,8% | 100,0% | 63 | 13 | 0 | 0 | 0 |
| b1 OpenAI (gpt-6.1-sol) | 76 | 100,0% | 0 | 3,9% | 100,0% | 19 | 57 | 0 | 0 | 0,54 |
| b1 Gemini (gemini-4-argon) | 76 | 80,3% | 15 | 47,4% | 58,3% | 36 | 25 | 0 | 0 | 0,67 |
| b2 OpenAI | 76 | 100,0% | 0 | 10,5% | 100,0% | 24 | 52 | 0 | 0 | 0,75 |
| b2 Gemini | 76 | 94,7% | 4 | 22,4% | 76,5% | 28 | 44 | 0 | 0 | 0,90 |
| b3 OpenAI | 76 | 94,7% | 4 | 30,3% | 82,6% | 34 | 38 | 6 | 0 | 1,99 |
| b3 Gemini | 76 | 89,5% | 8 | 52,6% | 80,0% | 44 | 24 | 7 | 0 | 2,44 |
| *mốc: luôn UNKNOWN* | 76 | 100% | 0 | 0% | — | 16 | 60 | | | |

Thiếu nhãn ở b3 đều là ca hết 6 lượt gọi công cụ mà chưa kết luận → UNKNOWN.

### 3.2 `[cau_hoi_ro]` (50 ca) — nhóm dùng để kết luận (A20)

| Hệ | n | Soundness | unsound | Coverage | Selective Acc | đúng gold | từ chối thừa |
|---|---|---|---|---|---|---|---|
| **CPA² (chính thức)** | 50 | 96,0% | **2** | **54,0%** | 92,6% | **36** | 12 |
| CPA² `_sau_A17` | 50 | 100,0% | 0 | 52,0% | 100,0% | 38 | 12 |
| b1 OpenAI | 50 | 100,0% | 0 | 2,0% | 100,0% | 13 | 37 |
| b1 Gemini | 50 | 78,0% | 11 | 56,0% | 60,7% | 28 | 11 |
| b2 OpenAI | 50 | 100,0% | 0 | 10,0% | 100,0% | 17 | 33 |
| b2 Gemini | 50 | 96,0% | 2 | 22,0% | 81,8% | 21 | 27 |
| b3 OpenAI | 50 | 100,0% | 0 | 28,0% | 100,0% | 26 | 24 |
| b3 Gemini | 50 | 92,0% | 4 | 62,0% | 87,1% | 35 | 11 |

### 3.3 `[quy_che]` (62 ca) · `[thiet_ke]` (14 ca) · `[theo errata]` (76 ca)

| Hệ | `[quy_che]` unsound · Coverage · đúng gold | `[thiet_ke]` unsound · Coverage · đúng gold | `[theo errata]` unsound · đúng gold · từ chối thừa |
|---|---|---|---|
| CPA² (chính thức) | 4 · 72,6% · 45 | 1 · 21,4% · 13 | 5 · 64 · 7 |
| CPA² `_sau_A17` | 0 · 72,6% · 49 | 0 · 14,3% · 14 | 0 · 69 · 7 |
| b1 OpenAI | 0 · 4,8% · 7 | 0 · 0% · 12 | 0 · 25 · 51 |
| b1 Gemini | 13 · 53,2% · 24 | 2 · 21,4% · 12 | 18 · 35 · 23 |
| b2 OpenAI | 0 · 12,9% · 12 | 0 · 0% · 12 | 0 · 30 · 46 |
| b2 Gemini | 2 · 24,2% · 17 | 2 · 14,3% · 11 | 5 · 31 · 40 |
| b3 OpenAI | 3 · 33,9% · 22 | 1 · 14,3% · 12 | 5 · 38 · 33 |
| b3 Gemini | 3 · 54,8% · 35 | 5 · 42,9% · 9 | 11 · 44 · 21 |

Errata (7 ca: HG-02/03/04/08, TN-01/03/08) đổi gold TRUE/FALSE → UNKNOWN, nên baseline nào kết luận ở các ca đó thì theo errata lại thành sai (b1 Gemini 15 → 18).

### 3.4 McNemar (CPA² chính thức vs baseline, 76 cặp, `tong`)

| Baseline | đúng gold: CPA² kém / CPA² hơn / p | không unsound: CPA² kém / CPA² hơn / p |
|---|---|---|
| b1 OpenAI | 1 / 40 / < 0,0001 | 5 / 0 / 0,063 |
| b1 Gemini | 6 / 28 / 0,0002 | 5 / 15 / 0,041 |
| b2 OpenAI | 1 / 35 / < 0,0001 | 5 / 0 / 0,063 |
| b2 Gemini | 3 / 33 / < 0,0001 | 5 / 4 / 1,000 |
| b3 OpenAI | 3 / 27 / < 0,0001 | 5 / 4 / 1,000 |
| b3 Gemini | 6 / 20 / **0,0094** | 5 / 8 / 0,581 |

Ngưỡng Bonferroni 0,05/6 ≈ 0,0083. **Đúng gold:** CPA² hơn 5/6 baseline qua ngưỡng; với b3 Gemini p = 0,0094 — **chưa qua**. **Không unsound:** không cặp nào qua ngưỡng (b1 Gemini p = 0,041 chỉ qua mức 0,05 thô).

### 3.5 Trả lời câu hỏi so sánh chính (đặt trước ở mục 1.4)

Trên test, `[cau_hoi_ro]`, CPA² chính thức so với baseline tốt nhất từng loại:

| Loại | (1) unsound: CPA² 2 vs | (2) Selective Acc: CPA² 92,6% vs | (3) Coverage: CPA² 54,0% vs |
|---|---|---|---|
| b1 | OpenAI 0 · Gemini 11 | OpenAI 100% (1 kết luận) · Gemini 60,7% | OpenAI 2,0% · Gemini 56,0% |
| b2 | OpenAI 0 · Gemini 2 | OpenAI 100% (5 kết luận) · Gemini 81,8% | OpenAI 10,0% · Gemini 22,0% |
| b3 | OpenAI 0 · Gemini 4 | OpenAI 100% (14 kết luận) · Gemini 87,1% | OpenAI 28,0% · Gemini 62,0% |

- **(1) Số kết luận sai: CPA² chính thức KHÔNG ít hơn baseline OpenAI.** Cả ba baseline OpenAI có 0 kết luận sai, đổi lại chúng kết luận rất ít (1–14/50 ca). 2 ca sai của CPA² trong nhóm này (DK-21, DK-22) là lỗi KB/thiết kế đã biết từ Tuần 22 và đã sửa sau (C20, C21), nhưng số chính thức giữ nguyên.
- **(2) Selective Accuracy:** CPA² (92,6%) cao hơn mọi baseline Gemini, thấp hơn ba baseline OpenAI (100% trên rất ít kết luận).
- **(3) Coverage:** CPA² (54,0%) cao hơn cả ba baseline OpenAI và b2 Gemini; **thấp hơn b1 Gemini (56,0%) và b3 Gemini (62,0%)** — hai hệ này đổi Coverage lấy nhiều kết luận sai hơn (11 và 4).
- **Không baseline nào vừa sai ít hơn vừa kết luận nhiều hơn CPA².** Trên `tong`, CPA² có nhiều ca đúng gold nhất (58; baseline cao nhất 44), nhưng trên `[cau_hoi_ro]` b3 Gemini gần ngang (35 vs 36).

---

## 4. Phân tích ca sai

> Trên test (số chính thức). Danh sách ca lấy từ `bang_so_sanh_test.md` (mục "Ca bất đồng") và file kết quả baseline; mỗi ca baseline sai được xếp loại bằng cách đọc câu trả lời thô (`tra_loi_tho`).

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

### 4.2 Kết luận sai của baseline (31 lượt trên 21 ca)

b1 OpenAI và b2 OpenAI không có kết luận sai nào. 31 lượt sai: b1 Gemini 15, b2 Gemini 4, b3 OpenAI 4, b3 Gemini 8.

| Loại | Lượt | Ca và cấu hình | Mô tả (từ câu trả lời thô) |
|---|---|---|---|
| **L7** câu hỏi benchmark gây lỗi | 14 | RC-01, RC-03, RC-07, RC-12 (b1G 3, b2G 1, b3O 3, b3G 4); EL-17 (b1G); ON-07M4 (b3O), ON-08M4 (b2G) | RC: câu hỏi "Hệ thống có thể đề xuất em đăng ký X ở HK1 không?" nhưng claim là `khong_de_xuat:X@1` (gold TRUE = *không* đề xuất) → trả lời "không" đúng nghĩa câu hỏi mà bị chấm sai. EL-17: hỏi "được công nhận" nhưng claim là "đủ điều kiện được xét" (QĐ5339 Đ2 k6). ON-07M4/08M4: hỏi bằng ký hiệu ASP `passed("…")?` (gold UNKNOWN, nên cũng là L4) |
| **L2** bịa hoặc dùng sai quy định | 8 | đều b1 Gemini: DK-11, EL-05 · DK-13, DK-17, DK-20 · DK-18, ON-04M1 · TN-12 | DK-11, EL-05: tự trừ 11 TC GDQP/GDTC khỏi số TC tích lũy trước khi so ngưỡng 120 TC. DK-13: coi XH024 là tiên quyết của XH025 (thực tế song hành). DK-17: bỏ ngưỡng ≥ 80 TC của CT466E. DK-20: tiên quyết của ML019 ghi nhầm thành ML021 (đúng là ML018). DK-18, ON-04M1: bịa nội dung CTĐT (CT518E là "tiểu luận tốt nghiệp"; "phải học kèm CT477"). TN-12: dùng "15 TC giảm 1 HK" (QĐ3266 Đ5 là 9 TC) và đếm `da_hoc_nam2` = 18 nửa năm thành 18 HK |
| **L4** kết luận khi gold UNKNOWN | 5 | ON-04M4 (b1G); ON-03M4, ON-04M3, ON-04M4, ON-10M3 (b3G) | OCR mức M3/M4: dòng học phần bị mất (tổng TC học kỳ lệch) hoặc điểm chữ F trái với điểm số. Model **có nhận ra** điểm lệch (vd. ON-10M3: "điểm chữ F không hợp lệ với điểm số 7.5") nhưng vẫn kết luận FALSE thay vì nêu dữ kiện không chắc |
| **L1** tính sai số | 4 | TN-13 (b1G, b2G), HG-04 (b1G, b2G) | TN-13: cộng TC ra 161 và 171 (đúng 159 < 161). HG-04: ĐTBCTL tính ra 3,18 (đúng 3,20, biên dưới hạng giỏi) |
| L3 · L6 · L8 | 0 | | Không có kết luận sai thuộc các loại này. L6 (thiếu nhãn: b3 OpenAI 6, b3 Gemini 7 — hết lượt gọi công cụ) và L8 (1 LOI tạm thời của b3 Gemini, đã thử lại) chỉ làm tăng từ chối, không thành kết luận sai |

- **Gần một nửa (14/31) lượt sai là do câu hỏi của benchmark (L7)**, không phải do model. Đây là lý do A20 chọn kết luận trên `[cau_hoi_ro]`: trong nhóm đó còn 17 lượt sai (b1G 11, b2G 2, b3G 4), gồm L2 8, L4 5, L1 4.
- **L2 chỉ xuất hiện ở b1 Gemini** (không có văn bản quy chế): thêm truy hồi điều khoản (b2) hay công cụ tra CTĐT (b3) đều loại được lỗi bịa quy định ở tập test.
- **L1 còn ở b2 Gemini:** có văn bản quy chế mà không có máy tính thì vẫn cộng sai TC và ĐTBCTL. b3 (có `may_tinh`) không sai ca L1 nào.
- **L4 tập trung ở b3 Gemini trên OCR nhiễu:** công cụ giúp kết luận nhiều hơn, nhưng model không có cơ chế "không chắc thì từ chối" như ba trị của CPA² (Tuần 16).
- **L5 (từ chối thừa) là lỗi lớn nhất về số lượng** nhưng không làm sai: b1 OpenAI 57, b2 OpenAI 52, b2 Gemini 44, b3 OpenAI 38, b1 Gemini 25, b3 Gemini 24 (CPA² 13). GPT-6.1-sol ở b1 nêu đúng lý do — "chưa có quy định … cần bổ sung" — nên hành vi này hợp lý khi không có văn bản, nhưng vẫn từ chối nhiều ở b2/b3 dù đã có điều khoản và công cụ.

### 4.3 Baseline đúng, CPA² chính thức sai

| Ca | Gold → CPA² | Baseline đúng | Nguyên nhân (Tuần 22 §3.1) | Đã sửa |
|---|---|---|---|---|
| DK-21 | FALSE → TRUE | b1 Gemini, b3 OpenAI, b3 Gemini | KB: ML018 coi là đã tích lũy vì công nhận LLCT tự động | C20, R-Formal v1.12 (`5535fa4`) |
| DK-22 | UNKNOWN → FALSE | cả 6 (đều trả UNKNOWN) | thiết kế: mã CT999 ngoài CTĐT, thế giới đóng cho FALSE | C21 (`a22e238`) |

MT-08, MT-09, MT-11 (cùng nguyên nhân C20) CPA² cũng sai, nhưng **không baseline nào trả đúng** (đều từ chối); ba ca này có câu hỏi rỗng (`cau_hoi_kem = rong`), nên chỉ nằm trong `tong`.

### 4.4 Cả hai cùng sai

Không có ca nào cả CPA² chính thức lẫn một baseline cùng kết luận sai. Các lỗi của CPA² (KB: công nhận tự động; thiết kế: thế giới đóng với mã ngoài CTĐT) và của baseline (câu hỏi, bịa quy định, tính số, OCR nhiễu) **không chồng nhau**.

### 4.5 CPA² đúng, baseline sai — những gì solver + chứng chỉ làm được mà baseline không

- **Ngưỡng TC và quan hệ học phần** (DK-11, DK-13, DK-17, DK-20, EL-05): CPA² đọc tiên quyết / song hành / ngưỡng TC từ CTĐT đã hình thức hoá, không tự suy ra quy định.
- **Số học** (TN-13): tổng TC tính bằng solver. Ở HG-04 (ĐTBCTL đúng biên 3,20) baseline Gemini tính sai, nhưng CPA² chính thức cũng không đúng gold — nó từ chối vì chưa khai báo dữ kiện hạ bậc (Đ34 k2; theo errata gold là UNKNOWN, nên theo errata CPA² đúng).
- **OCR không chắc** (ON-03M4, ON-04M3, ON-04M4, ON-10M3): kiểm chéo tổng TC / điểm (Tuần 15, C14) → UNKNOWN kèm dữ kiện cần xác minh, thay vì kết luận theo dòng đọc sai.
- Ở tập test này, CPA² **không** hơn baseline ở việc tránh kết luận sai so với baseline OpenAI (mục 3.5) — điểm mạnh của CPA² là kết luận **được nhiều hơn** mà vẫn ít sai, chứ không phải ít sai hơn một hệ gần như luôn từ chối.

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

- [x] **A19:** cấu hình `.env` (model, giá, trần), đóng băng (`256df16`), chạy dev b1/b2 × openai/gemini — 19/11/2026, 2,83 USD.
- [x] **A19 còn lại:** chạy dev b3 OpenAI, b3 Gemini — 19/11/2026, 4,54 USD.
- [x] **A20, A21:** chốt trước khi chạy test (mục 1.6) — 19/11/2026: hai dòng; errata (a).
- [x] Điền mục 1.5, chạy `so_sanh.py --split dev --ra`, điền mục 2 (6/6 cấu hình).
- [x] Chạy test một lần cho mỗi cấu hình, điền mục 3, phân tích mục 4 — 19–20/11/2026, 7,28 USD.
- [ ] Người thứ hai soát phân loại L1–L8 ở mục 4.2 (A7): phân loại do một người làm, đọc câu trả lời thô.
- [ ] Cập nhật checklist Excel: chỉ tích ô có bằng chứng.
