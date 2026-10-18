# TUẦN 19 — RECOMMENDATION ENGINE

**Giai đoạn:** Recommendation (Tuần 19/24) · **Mục tiêu:** Chỉ recommend phương án đã chứng minh hợp lệ
**Sản phẩm:** Recommendation v1 (`w19_recommendation/`)
**Tiêu chí hoàn thành:** Không recommend Not Eligible ✅
- `validate_recommendation.py` đạt **34/34** kiểm tra (gold viết tay trước khi cài đặt; bộ test tự soạn)
- Bất biến G1: 21 lần đề xuất (6 hồ sơ × 3 HK + SV năm 2 × 3 HK) — mọi HP đề xuất được kiểm lại **độc lập** qua engine w16: `du_dk_dang_ky` TRUE, `tich_luy` FALSE, mở đúng HK; mọi hình thức tốt nghiệp đề xuất được Eligibility trả ELIGIBLE; không phương án nào vượt 20 TC
- Test mọi tuần 5–19 ĐẠT

---

## 0. Kết luận trước

> Hệ thống **không đề xuất điều nó không chứng minh được**. Một HP chỉ vào phương án khi hợp lệ trong **mọi** thế giới (ba trị Tuần 16). Nếu điểm tiên quyết chưa rõ (OCR), nhóm tự chọn chưa xác định được còn thiếu bao nhiêu, hay Eligibility trả UNKNOWN, thì HP đó vào danh sách **cần xác minh** kèm lý do, không vào phương án. Thứ tự ưu tiên giữa các HP hợp lệ là **chính sách tư vấn** do tác giả đặt, không phải quy chế, và được ghi rõ như vậy.

---

## 1. Thiết kế

**Đầu vào:** hồ sơ (loader chung w7) và học kỳ `hk` ∈ {1, 2, 3}. HK3 là học kỳ hè; QĐ3266 Đ6 k1 quy định một năm có 3 HK.

**Bước 1: ứng viên.** Python tính trên các answer set của KB:

| Điều kiện | Nguồn |
|---|---|
| chưa tích lũy (FALSE mọi thế giới) | R-B (Đ22) |
| `du_dk_dang_ky` TRUE mọi thế giới: tiên quyết đã tích lũy, ngưỡng TC | R-A03 · QĐ3266 Đ7 k4 + CTĐT |
| mở ở HK `hk`; không phải GDQP (trường bố trí riêng) | CTĐT K49 |
| cần cho CTĐT: bắt buộc, hoặc thuộc nhóm tự chọn còn thiếu | R-A02, CTĐT |
| nhóm một nhánh (AV/PV; CN1–3): đã bắt đầu nhánh nào thì chỉ nhánh đó | CTĐT ("10 AV hoặc PV") |
| CT550E/CT501E: Eligibility (Tuần 18) trả ELIGIBLE; khai báo hình thức thì chỉ HP của hình thức đó | QĐ3266 Đ31, QD-12 |

HP thuộc một trong các trường hợp sau được tách khỏi danh sách học:
- đủ điều kiện **nộp đơn** xin miễn (R-M06/R-M16, QD-11 — chưa phải đã miễn), chỉ tính HP còn cần;
- được công nhận thay thế (R-M13, Eligibility ELIGIBLE);
- đã có quyết định miễn.

**Bước 2: chọn phương án** (`recommendation.lp`, clingo tối ưu).

| | Nội dung | Loại |
|---|---|---|
| ràng buộc | ≤ 20 TC | quy chế R-C01 · Đ14 k1 |
| ràng buộc | một nhánh/nhóm; không cùng lúc LVTN + TLTN | CTĐT; Đ31 |
| ràng buộc | không chọn HP thừa trong nhóm (bỏ HP đó vẫn đủ thiếu hụt → cấm) | Tuần 8 "không gợi ý thừa" |
| ưu tiên @5 | TC bắt buộc | **chính sách** |
| ưu tiên @4 | số HP sau mà HP này mở khóa | **chính sách** |
| ưu tiên @3 | tránh chọn HP có HP song hành chưa học và không cùng kỳ | **chính sách** (QD-13) |
| ưu tiên @2 / @1 | TC lấp nhóm tự chọn / tổng TC | **chính sách** |

**Bước 3: kiểm lại tường minh.** Mọi HP được chọn phải hợp lệ trên mọi thế giới, chưa tích lũy và mở đúng HK, đồng thời tổng TC ≤ 20. Không qua kiểm lại → bỏ cả phương án và ghi vào `can_xac_minh`. Bước này không dùng `assert`, vì `python -O` bỏ các lệnh assert.

**Đầu ra:** `dang_ky` (mỗi HP có chứng chỉ, ví dụ `du_dk_dang_ky("CT176")` ← r_a03 ← QĐ3266 Điều 7 khoản 4), `can_xac_minh`, `ung_vien_khong_chon`, `hinh_thuc_tot_nghiep`, `xin_mien`, `thay_the`, `loi_khuyen`, `mau_thuan`.

**Prototype (w12):** "kỳ này em (có) nên đăng ký gì" → `claim = de_xuat`. Học kỳ được đọc từ câu hỏi ("học kì 2", "kỳ 3", "HK III", "học hè"). "Học kỳ 4" → hỏi lại, không lặng lẽ dùng HK1. Câu hỏi về **một** HP hoặc về luận văn/tiểu luận không bị nhánh này chiếm. Câu hỏi được chuẩn hoá NFC trước khi khớp.

### Ví dụ — SV năm 2 (đã học AV1, CT101, CT173, TN001, ML014 …)

| HK | Phương án | TC |
|---|---|---|
| 1 | CT176, CT177 (mỗi HP mở khóa 3 HP), CT178, CT188, CT223, CT273, ML016 | 20 |
| 3 (hè) | ML016, TN002, KN002E (nhóm xã hội), XH024, XH025 (nhóm AV) — CT1xx không mở HK3 | 15 |

---

## 2. QD-13 — song hành (xác nhận ngoài văn bản)

**Loi, 18/10/2026:** "song hành nghĩa là có thể học trước tín chỉ đó hoặc học sau 2 tín chỉ cũng được, kết quả học 2 cái không ảnh hưởng nhau, chỉ có nội dung học bổ trợ nhau."

⚠️ **Khác câu chữ** QĐ3266 Đ7 k5 (tr.5): *"Học phần song hành … là học phần mà SV phải học trước hoặc học cùng lúc với học phần HPxxx."*

Cách xử lý:
- **KB giữ R-A04 đúng văn bản** (`vi_pham_song_hanh`, lớp F, không đổi).
- QD-13 được ghi vào catalog (`quyet_dinh` của R-A04) và phụ lục (sinh lại bằng `gen_quyet_dinh.py`), nằm cùng nhóm "xác nhận ngoài văn bản" với QD-09 và QD-12. Nên có email/biên bản.
- Recommendation **không** dùng song hành làm ràng buộc. Nó chỉ (a) ưu tiên tránh @3 và (b) đưa lời khuyên "nên học P trước hoặc cùng kỳ".
- Nếu sau này văn bản được xác nhận theo câu chữ, chỉ cần đổi mức @3 thành ràng buộc cứng.

---

## 3. Kết quả (`validate_recommendation.py`)

| Nhóm | n | Nội dung |
|---|---|---|
| A. SV năm 2, HK1 | 9 | ≤ 20 TC; không HP thiếu tiên quyết (CT174/175/180, CT112, ML018, CT271E); không HP đã tích lũy; không Pháp văn khi đã học AV; không GDQP; chỉ bắt buộc khi đủ lấp 20 TC; CT177, CT176 được ưu tiên; mở HK1; có chứng chỉ |
| B. HK3 | 2 | chỉ HP mở HK3; AV căn bản 2–3 trước AV tăng cường |
| C. Không chắc | 1 | điểm CT101 chưa rõ → CT177, CT176 vào cần xác minh |
| D. Giai đoạn cuối | 4 | 146 TC: chỉ nhóm tốt nghiệp, không LVTN + TLTN; ba hình thức ELIGIBLE; đã công bố TLTN → không LVTN; đã đủ CTĐT → không đề xuất |
| E. Miễn / thay thế | 5 | IELTS 6.0 → nộp đơn xin miễn AV; HP xin miễn không bị đề xuất học; diễn đạt "nộp đơn"; đã có QĐ miễn → không đề xuất xin miễn; ML009 → ML014 thay thế |
| F. Song hành | 1 | CT182 không bị chặn vì CT180 chưa học |
| G. Bất biến | 1 | 21 lần đề xuất kiểm lại độc lập |
| H. Prototype | 9 | ý định; học kỳ trong câu hỏi (kì/kỳ/HK III/hè); HK4 → hỏi lại; câu về một HP; "có nên"; NFD |
| I. Hồi quy review | 2 | học cả AV lẫn PV → lý do "cả hai nhánh"; không dùng assert |

**TDD:**
- Bản đầu fail vì thiếu module. Sau khi cài đặt, E4, E5 và H1 còn fail; đã sửa:
  - E4: nhóm AV đã đủ nhờ miễn mà vẫn gợi ý xin miễn XH031–033.
  - E5: KB coi ML014 đã tích lũy (substituted), nên bước thay thế bị bỏ qua.
- Review sinh 8 ca H2–H6 và I1–I2. Cả 8 fail với code trước review.
- Ca B2 (AV tăng cường trước căn bản) fail trước khi thêm mức ưu tiên @3.

---

## 4. Phát hiện

### P19-1 · Đủ điều kiện xin miễn ≠ cần xin miễn
Bản đầu gợi ý "nộp đơn xin miễn XH031–033" cho SV đã được miễn đủ 10 TC nhóm AV. Đúng điều kiện (R-M06) nhưng vô ích. Nay chỉ gợi ý HP còn cần cho CTĐT.

### P19-2 · Ưu tiên theo tổng TC chọn AV tăng cường trước AV căn bản
Thuần tối ưu TC, solver chọn XH031 (4 TC) + XH032 thay cho XH024 + XH025 khi chưa học XH024. Hợp lệ theo QD-13, nhưng là lời tư vấn kém. Đã thêm mức ưu tiên song hành @3, vẫn không chặn.

### P19-3 · Parser: ý định và học kỳ (review)
Các lỗi review tìm ra:
- "học **kì** 2" (cách viết phổ biến) và "kỳ 3" rơi về HK1 im lặng.
- "học kỳ 4" bị chấp nhận thành HK1.
- "em nên đăng ký CT180 được chưa" bị nhánh đề xuất chiếm.
- "em **có** nên đăng ký" rơi về `tot_nghiep` mặc định. Đây cùng họ với P18-1: ý định sai mà không báo lỗi.
- Chuỗi NFD không khớp.

Tất cả đã có ca hồi quy.

---

## 5. Hạn chế

- Kế hoạch **một học kỳ**: chưa xếp nhiều học kỳ hay lộ trình tới tốt nghiệp. Counterfactual Optimality Gap (RQ3, B8) để Tuần 22.
- Chưa có lịch học/trùng giờ, sĩ số, học phí (A4). Không có dữ liệu HP nào thực sự mở trong một học kỳ cụ thể; `mo_hk` là kế hoạch CTĐT.
- Thứ tự ưu tiên là chính sách của tác giả, chưa được GVHD/cố vấn học tập xác nhận.
- Chưa xét HP đang học (chưa có điểm) và học cải thiện điểm. Đ14 k2 (HK đầu do trường xếp) chưa mô hình.
- `mo_khoa` chỉ đếm HP mở khóa trực tiếp, chưa tính bắc cầu.
- Parser Tuần 13 (regex) chưa có ý định `de_xuat`; mới tích hợp ở prototype.
- Bộ test tự soạn; chưa có câu hỏi thật. Không có phần đọc tài liệu mới.

## 6. Việc còn lại → Tuần 20+

- [ ] Đưa ca recommendation vào bộ test mới của Tuần 20 (B1)
- [ ] Văn bản/email xác nhận QD-13 (song hành)
- [ ] GVHD xác nhận thứ tự ưu tiên tư vấn
- [ ] Kế hoạch nhiều học kỳ + Optimality Gap (B8, Tuần 22)

### Ghi chú kiểm chứng

- [x] Không recommend Not Eligible: bất biến G1 kiểm lại độc lập 21 lần đề xuất
- [x] UNKNOWN → cần xác minh, không đề xuất (C1, I1)
- [x] Mỗi HP đề xuất có chứng chỉ trỏ về điều/khoản
- [x] Mọi tuần 5–19 ĐẠT
