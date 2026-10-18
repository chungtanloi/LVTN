# TUẦN 17 — ADVERSARIAL SET

**Giai đoạn:** Uncertainty (Tuần 17/24) · **Mục tiêu:** Tạo ca thiếu dữ liệu, sát ngưỡng, OCR sai
**Sản phẩm:** Adversarial set v1 (`w17_adversarial/`)
**Tiêu chí hoàn thành:** ≥ 60 case đối kháng ✅. Bộ có **80 ca chấm điểm** và 5 ca không chấm.

Kết quả CPA² trên **test**, chạy một lần, không tinh chỉnh (37 ca, đã bỏ 2 ca "không phát hiện được"):

| Số đo | Kết quả |
|---|---|
| Soundness | **91,9%** (3 ca sai, đều thuộc nhóm hồ sơ lỗi) |
| Coverage | 78,4% |
| Selective Accuracy | 89,7% |
| Từ chối thừa | 0 |
| Hỏi lại đúng dữ kiện | 2/2 |

- ⚠️ **Hồ sơ mâu thuẫn: 0/6 sound** (dev + test). Loader không kiểm tính nhất quán của bản ghi.
- ⚠️ **Lỗi OCR nhất quán mà kiểm chéo không thấy: 2/2 ca kết luận trái sự thật.**

---

## 0. Kết luận trước

> Ngoài nhóm hồ sơ lỗi, CPA² **không sai ca nào trong 72 ca** (dev + test). Các ca gồm thiếu dữ liệu, sát ngưỡng, bẫy quy chế và OCR có lỗi phát hiện được.
>
> Bộ đối kháng cũng chỉ ra hai lỗ hổng thật:
> 1. **Hệ thống tin mọi bản ghi điểm.** Điểm 8,0 nhưng ghi F, 3,0 nhưng ghi đạt, 15,0 ngoài thang, sai số TC, đã học 0 nửa năm mà có 161 TC: cả 6 ca đều được kết luận TRUE/FALSE thay vì từ chối.
> 2. **Lỗi OCR nhất quán thì không kiểm chéo nào bắt được.** Ví dụ mã đọc nhầm thành một mã hợp lệ khác cùng số TC, hoặc điểm F đọc thành D khi ĐTBCHK không đọc được. Đây là rủi ro tồn dư của đầu vào OCR.

---

## 1. Thiết kế bộ ca

### 1.1. Năm nhóm (80 ca chấm điểm)

| Nhóm | n | Gold T/F/U | Nội dung |
|---|---|---|---|
| Thiếu dữ liệu | 17 | 3/7/7 | Thiếu kỷ luật / số nửa năm đã học / QĐ miễn; điểm không chắc (kể cả F/D/A). **Bẫy ngược:** HP bắt buộc chưa học → FALSE, không phải UNKNOWN. **Bẫy từ chối thừa:** dữ kiện thiếu không liên quan hoặc điểm không chắc nhưng không quyết định → vẫn phải trả lời |
| Sát ngưỡng | 24 | 13/11/0 | ĐTBCTL đúng 2,00 / C 5,5 vs D+ 5,4 · điểm 4,0 vs 3,9 · TB GDQP 5,0 vs 4,975 · 120 vs 119 TC (tiên quyết LVTN) · 161 vs 159 TC · 18 vs 19 nửa năm · 8 vs 9 TC công nhận · IELTS 4.5/4.0, TOEIC 450/445, TOEFL iBT 45/44 |
| Bẫy quy chế | 15 | 9/6/0 | QD-11 (đủ ĐK xin miễn ≠ đã miễn), B-01 (đạt từ 5,0), F/HP điều kiện không vào ĐTBCTL, điểm M vào tổng TC, trộn AV/PV, LVTN là tự chọn, B-03 (nợ TC chặn tốt nghiệp), chứng chỉ Anh ≠ Pháp văn, trần 9 năm, đăng ký ≠ tích lũy |
| Hồ sơ lỗi | 6 | 0/0/6 | Điểm số ↔ chữ ↔ trạng thái mâu thuẫn, điểm ngoài thang, TC ≠ CTĐT, thời gian học không thể |
| OCR sai (mức tài liệu) | 18 | 3/2/13 | Sai điểm chữ, mất dòng, mã không đọc được, hai lần đọc mã khác nhau, sai TC, confidence thấp, đọc sai nhất quán (có/không có ĐTBCHK để bắt), sai tổng TC/ĐTBCHK, học lại, thiếu khai báo |

**Không chấm (5 ca):**
- KX-01: sinh viên chưa khai báo lựa chọn tích lũy (CQ-06).
- KX-02: GDQP điểm D mà TB ≥ 5,0 (phạm vi áp dụng ngưỡng D+ của QĐ5339 Đ3 k2 chưa chốt).
- KX-03: GDTC ghi TC025–027.
- KX-04, KX-05: mức ảnh, phụ thuộc môi trường.

### 1.2. Gold độc lập với hệ thống

- **Viết tay** trong `build_adversarial.py`. Mỗi ca có lý do và nguồn (văn bản, điều, khoản, trang của bản OCR).
- Gold mang nghĩa **câu trả lời đúng với thông tin có trong đầu vào**. Ca OCR có thêm `su_that` là tình trạng thật của sinh viên.
- **Oracle** `oracle.py` là Python thuần, không clingo, không đọc `.lp`. Nó cài lại Đ22, Đ24, Đ32 k1 b và Đ5 từ câu chữ, rồi kiểm **29 tiền đề số học** của gold (ví dụ ĐTBCTL đúng 2, TB GDQP = 199/40), cộng với tiền đề bẫy của BQ-05 (tính cả F thì 280/143 ≈ 1,958 < 2).
- **Đóng băng:** gold được commit ở `200b860` **trước** lần chạy CPA² đầu tiên. `gold_dong_bang.json` trích từ chính commit đó. Validate G1/G2 chặn mọi sửa đổi về sau.
- **Tách dev/test:** phân tầng theo nhóm, seed 17, mỗi nhóm lệch ≤ 1 ca. Tuần này **không tinh chỉnh hệ thống** (theo kế hoạch đã duyệt: chỉ ghi nhận lỗi).

### 1.3. Đầu vào trung lập với hệ thống

Mỗi ca gồm hồ sơ gốc (6 hồ sơ giả lập Tuần 7) và các phép biến đổi. Từ đó:
- CPA² nhận hồ sơ cộng lựa chọn ASP cho dữ kiện mở.
- Baseline Tuần 21 nhận `dau_vao_baseline()`: hồ sơ **đã bỏ** điểm chưa rõ, kèm mô tả tiếng Việt. Không nêu tên hồ sơ gốc, vì hồ sơ gốc còn giữ điểm thật.

Ca OCR được dựng ở **mức tài liệu**, theo định dạng đầu ra nhận dạng của Tuần 15. Không cần Tesseract, kết quả tất định.

---

## 2. Kết quả CPA²

### 2.1. Số đo chính (bỏ 2 ca không phát hiện được)

| Split | n | Soundness | Coverage | Sel. Acc | Đúng gold | Unsound | Từ chối thừa | Hỏi đúng |
|---|---|---|---|---|---|---|---|---|
| dev | 41 | 92,7% | 70,7% | 89,7% | 38 | 3 (HL) | 0 | 5/5 |
| **test** | **37** | **91,9%** | **78,4%** | **89,7%** | **34** | **3 (HL)** | **0** | **2/2** |
| dev + test | 78 | 92,3% | 74,4% | 89,7% | 72 | 6 (HL) | 0 | 7/7 |

Theo nhóm (dev + test):
- Thiếu dữ liệu 17/17, sát ngưỡng 24/24, bẫy quy chế 15/15, OCR (có thể phát hiện) 16/16 đều đúng gold.
- Hồ sơ lỗi **0/6**.
- Coverage của nhóm OCR thấp (dev 22%, test 14%). Đây là chủ đích: OCR không chắc thì từ chối.

Nếu tính cả 2 ca không phát hiện được (theo cách chấm của lần chạy đầu), Soundness trên test là **87,2%** (34/39).

### 2.2. Rủi ro OCR ẩn (2 ca, cả hai ở test)

| Ca | Sự thật | OCR đọc ra | CPA² |
|---|---|---|---|
| OC-07 | Đủ ĐK | CT178 (bắt buộc) đọc nhất quán thành CT478 (tự chọn, cùng 3 TC) | FALSE — "thiếu CT178" |
| OC-11 | CT177 = F | Đọc nhất quán 4,5/D, ĐTBCHK không đọc được | TRUE |

Thời gian chạy: tổng 23,7 giây cho 80 ca, ca lâu nhất 4,5 giây (OCR có 6 HP không chắc).

---

## 3. Phát hiện

### P17-1 · Hệ thống tin mọi bản ghi điểm (6/6 ca hồ sơ lỗi unsound) — ĐÃ SỬA (mục 7)
Loader (`load_facts` w7) chỉ đọc `thang10`, bỏ qua `letter`, `status`, `credits` và cận 0–10. Hệ quả:
- HL-01: 8,0 ghi F → TRUE.
- HL-02: 3,0 ghi passed → FALSE.
- HL-03: điểm 15,0 → FALSE (không có band).
- HL-04: 4 TC thay vì 3 → TRUE.
- HL-05: 8,0 ghi B → TRUE.
- HL-06: 0 nửa năm mà có 161 TC → TRUE.

**Hướng sửa (chưa làm):** kiểm nhất quán trước khi giải (điểm ↔ chữ theo Đ22 k2, trạng thái, TC ↔ CTĐT, TC/HK ≤ 20). Gặp mâu thuẫn thì trả UNKNOWN và nêu bản ghi cần xác minh.

### P17-2 · Lỗi OCR nhất quán không phát hiện được (OC-07, OC-11) — ĐÃ GIẢM THIỂU (mục 7)
Mọi kiểm chéo của Tuần 15 đều qua. **Hướng giảm thiểu (chưa làm):**
- Coi ĐTBCHK không đọc được là học kỳ nghi ngờ.
- Với đầu vào OCR, kết luận "thiếu HP bắt buộc" thì hỏi lại sinh viên thay vì trả FALSE.
- Ưu tiên hai lần đọc mã độc lập.

### P17-3 · Đơn vị "học kỳ" trong trần thời gian (R-E02) — ĐÃ SỬA, R-Formal v1.8 (mục 7)
QĐ3266 Đ6 k1 (tr.5) quy định **mỗi năm học có 03 HK × 15 tuần**, nên "giảm 1 HK" trong Đ5 là 1/3 năm. R-Formal lại trừ `giam_hk` theo **nửa năm**. Ví dụ sai: 27 TC công nhận và đã học 16 nửa năm (8 năm).
- Đọc đúng: trần 9 − 1 = 8 năm, chưa quá hạn.
- R-Formal: trần 18 − 3 = 15 nửa năm, kết luận quá hạn.

Gold NG-17/NG-18 vẫn đúng theo cả hai cách đọc. Oracle dùng chung giả định nửa năm nên không kiểm độc lập được điểm này. **Cần sửa R-Formal (lập kế hoạch riêng), có thể phải đổi đơn vị `da_hoc_nam2`.**

### P17-4 · Câu hỏi bổ sung của OCR còn thô
Khi ĐTBCHK hoặc tổng TC lệch, cả học kỳ (6 HP) thành không chắc, nên hệ thống hỏi lại cả 6 HP. Với hồ sơ, missing evidence hỏi đúng 7/7 dữ kiện quyết định.

---

## 4. Errata (phát hiện sau khi đóng băng gold — không sửa gold)

| Mã | Nội dung | Xử lý |
|---|---|---|
| E17-1 | OC-07, OC-11 có gold = sự thật, trái định nghĩa "gold đúng với thông tin đầu vào" (review tìm ra) | Sửa **công thức chấm**: tách khỏi số đo chính, báo riêng thành "rủi ro OCR ẩn". Câu trả lời của CPA² giữ nguyên (đã đối chiếu với lần chạy 1). Báo cả hai con số |
| E17-2 | NG-10 (TB GDQP 4,975 → FALSE) dựa vào việc **không làm tròn** TB GDQP. Đ22 k1–2 chỉ nói làm tròn điểm học phần, không có nguồn về làm tròn trung bình | Giữ gold. Nếu làm tròn thì gold là TRUE. NG-10 ở dev, CPA² trả FALSE. Bỏ NG-10 thì dev 40 ca, Soundness 92,5% |
| E17-3 | Trần thời gian dùng "1 HK = nửa năm" (P17-3) | Gold NG-15…18, BQ-14 đúng theo cả hai cách đọc. Oracle ghi rõ giả định |
| E17-4 | OC-15/16: lần học thêm (F) đặt ở học kỳ sau lần học đạt | Không đổi gold (điểm HP là điểm cao nhất, Đ17 k2, không phụ thuộc thứ tự). Sửa mô tả phép `hoc_lai` |
| E17-6 | Sau khi sửa P17-3: `ly_do` và tiền đề oracle (`tran_nam2` → `tran_hk`) của NG-17/NG-18 (và tiền đề NG-15, BQ-14) được viết lại theo đơn vị HK | Không phải gold (G2 vẫn khớp `200b860`); kết quả chính thức Tuần 17 chạy với lý do cũ — ghi lại ở đây |
| E17-5 | Nguồn dùng chung thiếu số trang (trái quy tắc CLAUDE.md) | Bổ sung trang. `adversarial_set.json` chỉ đổi các dòng `nguon` (đã kiểm: 0 dòng gold/su_that thay đổi) |

---

## 5. Hạn chế

- Bộ ca **tự soạn** bởi tác giả hệ thống, dựa trên 6 hồ sơ giả lập. Chưa có người thứ hai gán gold độc lập (κ).
- Ca OCR ở mức tài liệu mô phỏng các lỗi đã gặp ở Tuần 15, chưa phải phân bố lỗi thật.
- Claim tập trung vào tốt nghiệp: 59/80 ca hỏi `tot_nghiep`, còn lại là xin miễn (8), tiên quyết LVTN (4), đạt HP (4), đủ TC (3), ĐTBCTL (2). Chưa có ca cảnh báo học vụ, xếp hạng tốt nghiệp hay phản thực.
- Không có phần đọc tài liệu mới về adversarial evaluation.

## 6. Việc còn lại → Tuần 18+

- [x] P17-1: kiểm nhất quán hồ sơ trước khi giải (mục 7)
- [x] P17-3: đơn vị học kỳ trong trần thời gian — R-Formal v1.8 (mục 7)
- [x] P17-2: giảm rủi ro OCR ẩn (mục 7)
- [ ] **Tuần 20: bộ test MỚI, chưa từng thấy** — test của bộ v1 đã nhiễm sau khi sửa P17-1/P17-2
- [ ] Gộp 3 bản loader hồ sơ (w7/w11/w12) — hiện ra_soat được gọi ở từng nơi
- [ ] Tuần 21: chạy baseline LLM/RAG trên cùng bộ ca bằng `dau_vao_baseline()`
- [ ] Mời người thứ hai gán gold một mẫu để đo κ

### Ghi chú kiểm chứng

- [x] ≥ 60 ca (80), đủ 5 nhóm, có gold + nguồn + dev/test
- [x] Gold đóng băng trước khi chạy (commit `200b860`), oracle khớp 29 tiền đề
- [x] Chạy CPA² trên dev và test, báo cáo cả ca thất bại
- [ ] CPA² chưa sound trên hồ sơ mâu thuẫn (0/6) và lỗi OCR nhất quán (0/2) — **ở lần chạy chính thức Tuần 17**; sau sửa xem mục 7

---

## 7. Sửa sau Tuần 17 (18/10/2026)

Thực hiện theo kế hoạch đã duyệt: Plan → TDD → Implement → Review → Verify. **Số liệu ở mục 2 là kết quả chính thức của Tuần 17 và giữ nguyên.** Số dưới đây chạy lại sau khi sửa, ghi ra file `*_sau_P17`.

### 7.1. Các sửa đổi

| Mã | Sửa | Ca kiểm thử (viết trước, fail với code cũ) |
|---|---|---|
| P17-1 | `abstention.ra_soat()` chạy trước khi giải. Bản ghi điểm **tự mâu thuẫn** (ngoài thang 0–10 hoặc không phải số nguyên; chữ ≠ quy đổi Đ22 k2; trạng thái ≠ ngưỡng D Đ22 k3; TC ≠ CTĐT; M/W/I kèm điểm số) bị bỏ ra, điểm HP mở thành F/D/A cùng điểm số ghi trên hồ sơ (và M/W/I nếu bản ghi nhận như vậy). Số nửa năm đã học không thể có (TC đã đăng ký > 20 TC/HK × số HK, Đ14 k1 + Đ6 k1) được coi như chưa khai báo. Kết quả có thêm trường `mau_thuan`. Rà soát được gọi ở w16 `tra_loi`, w12 prototype, w11 certificate và w15 `ket_luan` | w16 E1–E12: 6 loại mâu thuẫn bản ghi, thời gian không thể, mâu thuẫn không quyết định vẫn TRUE, 6 hồ sơ sạch không bị báo nhầm, prototype, điểm số thực không làm crash |
| P17-3 | R-Formal **v1.8**: `thoi_gian_toi_da_hk(M)`, M = trần (nửa năm) × 3/2 − `giam_hk`; `qua_thoi_gian_toi_da :- 3·da_hoc_nam2 > 2·M`. Nguồn: QĐ3266 **Điều 6 khoản 1 (tr.5)**, mỗi năm học có 03 HK. Theo người dùng xác nhận (18/10/2026), một HK gồm 11 tuần học, 1 tuần thi, 1 tuần dự phòng; bản OCR Đ6 k2 ghi 15 tuần (11 dạy-học + 1 dự trữ/thi riêng + 1 thi riêng + 2 thi chung). Số tuần không ảnh hưởng phép tính, chỉ cần "3 HK/năm" | w5 C16b, w10 B7e: 27 TC công nhận, đã học 8 năm → chưa quá hạn (luật cũ: quá hạn). C15/C16/C32 đổi đơn vị atom |
| P17-2 | w15 `sang_ho_so`: (a) học kỳ **không đọc được ĐTBCHK** bị coi là lệch (không tin điểm); (b) HP **bắt buộc vắng mặt** mà có HP lệch đúng 1 ký tự, cùng TC, đã được nhận (là HP không bắt buộc, hoặc HP bắt buộc xuất hiện ≥ 2 dòng) → cả hai không chắc | w15 F1 (F đọc thành D + mất ĐTBCHK), F2 (CT178 → CT478), F4 (CT178 → CT177), F3 (bảng điểm hoàn hảo không bị nghi) |

Review tìm ra 10 điểm. Đã sửa: rà soát chưa phủ w11/w15; prototype bỏ qua danh sách mâu thuẫn; heuristic (b) bỏ sót trường hợp bắt buộc → bắt buộc; điểm dạng số thực làm crash; M/W/I không được mở; oracle mất ghi chú "không kiểm độc lập"; câu hỏi thời gian gọi nhầm "học kỳ chính". Ghi nhận, chưa làm: gộp 3 bản loader (đổi kiến trúc).

### 7.2. Chạy lại bộ đối kháng — ⚠️ test ĐÃ NHIỄM

| Split | n | Soundness | Coverage | Sel. Acc | Unsound | Rủi ro OCR ẩn |
|---|---|---|---|---|---|---|
| dev (chính thức T17 → sau sửa) | 41 | 92,7% → **100%** | 70,7% → 63,4% | 89,7% → 100% | 3 → 0 | — |
| test (chính thức T17 → sau sửa) | 37 | 91,9% → **100%** | 78,4% → 70,3% | 89,7% → 100% | 3 → 0 | 2/2 → 0/2 |

- Coverage giảm vì 6 ca hồ sơ lỗi nay trả UNKNOWN (đúng gold), không phải từ chối thừa (từ chối thừa vẫn 0).
- **Test đã nhiễm:** P17-1 và P17-2 được thiết kế sau khi đã thấy các ca test thất bại (HL-02/03/06, OC-07, OC-11). Con số 100% trên test **không phải đánh giá trên dữ liệu chưa thấy** và không dùng để báo cáo H1. Cần một bộ test mới ở Tuần 20.
- Độ phủ OCR trên ảnh tổng hợp (w15 B, Linux) không đổi: 7/18.
