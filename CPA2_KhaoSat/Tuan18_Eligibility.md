# TUẦN 18 — ELIGIBILITY ENGINE

**Giai đoạn:** Recommendation (Tuần 18/24) · **Mục tiêu:** Kiểm tra luận văn / niên luận / học phần thay thế
**Sản phẩm:** Eligibility module v1 (`w18_eligibility/`)
**Tiêu chí hoàn thành:** Eligible / Not Eligible / Unknown ✅
- `validate_eligibility.py` đạt **36/36** kiểm tra (gold viết tay trước khi cài đặt; bộ test tự soạn)
- Test mọi tuần 5–18 ĐẠT; bộ đối kháng Tuần 17 trả lời không đổi
- ⚠️ Điều kiện nhận đề tài LVTN/TLTN **do đơn vị đào tạo quy định** — chưa có văn bản → chỉ nhận kết quả xét, chưa hình thức hoá nội dung (Viec_ton_dong A12)

---

## 0. Kết luận trước

> **Đủ 120 TC chưa phải là đủ điều kiện làm luận văn.** QĐ3266 Điều 31 (tr.19): *"Để được nhận đề tài LVTN hoặc TLTN, SV phải thỏa mãn các điều kiện do đơn vị đào tạo quy định. Cuối mỗi HK, đơn vị đào tạo xét và công bố hình thức thực hiện cuối khóa."* Quy chế không nêu các điều kiện đó, nên hệ thống không bịa: nó kiểm phần có nguồn (ngưỡng TC/tiên quyết của CTĐT) và coi **kết quả xét của đơn vị** là dữ kiện ngoài. Thiếu dữ kiện → **UNKNOWN + hỏi "đơn vị đã công bố hình thức LVTN cho bạn chưa?"**, không phải ELIGIBLE. Thiếu TC thì NOT_ELIGIBLE dù chưa biết kết quả xét (TC quyết định).

---

## 1. Thiết kế

| Đối tượng | Học phần | Điều kiện | Nguồn |
|---|---|---|---|
| `lvtn` | CT550E | ≥ 120 TC **và** đơn vị đã công bố hình thức LVTN | CTĐT K49 tr.4 (R-A03) + QĐ3266 Đ31 (R-F04) |
| `tltn` | CT501E | ≥ 120 TC **và** đơn vị đã công bố hình thức TLTN | như trên |
| `nien_luan` | CT466E | ≥ 80 TC | CTĐT (R-A03) |
| `nien_luan_co_so` | CT271E | đã tích lũy CT174, CT176 | CTĐT (R-A03 — tiên quyết là ĐÃ TÍCH LŨY) |
| `thuc_tap` | CT518E | ≥ 125 TC | CTĐT (R-A03) |
| `tich_luy_tc` | nhóm tốt nghiệp | SV tự chọn; LVTN/TLTN bị F → làm lại hoặc HP thay thế | QĐ3266 Đ31 k3 (R-F05) |
| `thay_the:<MÃ>` | HP trong CTĐT | đã đạt HP cũ tương ứng (ML009→ML014, ML010→ML016+ML018 …) | QĐ5339 Đ3 k9 (R-M13) |

- **Kết quả:** `ELIGIBLE` / `NOT_ELIGIBLE` / `UNKNOWN` (ba trị trên mọi thế giới như Tuần 16) / `DA_HOAN_THANH` (HP đã tích lũy; đã xong hình thức cuối khóa khác — Đ31 "một trong ba hình thức"; HP thay thế đã đạt bằng điểm chính nó) / `MAU_THUAN`.
- **Lý do** (`ly_do`): `thieu_tc(C,n)`, `thieu_tien_quyet(C,P)`, `dv_cong_bo_khac(X)` — chỉ nêu khi đúng trong mọi thế giới.
- **Chứng chỉ:** why/2 → catalog (văn bản, điều, khoản). R-F04 có thêm `rule_src(r_f04, qd3266, 31, …)` để trích dẫn; **vẫn lớp N** (nội dung điều kiện do đơn vị quyết — KB chỉ mô hình kết quả xét).
- **Hồ sơ:** trường mới `hinh_thuc_cuoi_khoa ∈ {lvtn, tltn, tich_luy_tc, null}` (schema + loader chung). Giá trị sai (vd. `"LVTN"`) → mâu thuẫn, coi như chưa khai báo.
- **Nhánh mở chỉ cho hình thức đang hỏi** (`dang_xet/1`): hỏi LVTN thì chỉ hỏi về LVTN, và nhóm niên luận/thực tập không nhân mô hình.

---

## 2. Kết quả (`validate_eligibility.py`, 36/36)

| Nhóm | n | Nội dung |
|---|---|---|
| A. LVTN/TLTN | 10 | 146 TC chưa biết đơn vị xét → UNKNOWN + hỏi; công bố LVTN → ELIGIBLE (chứng chỉ R-A03 + R-F04); công bố TLTN → LVTN NOT / TLTN ELIGIBLE; **biên 120 / 119 TC**; 119 TC chưa biết xét → vẫn NOT (TC quyết định); đã đạt → DA_HOAN_THANH; LVTN bị F → được làm lại |
| B. Tích lũy TC | 3 | chưa làm LVTN → ELIGIBLE không cần đơn vị; LVTN F → ELIGIBLE; nhóm đủ → DA_HOAN_THANH |
| C. Niên luận / thực tập | 4 | biên 80/79 và 125/124 TC |
| D. Niên luận cơ sở | 5 | thiếu CT176 (nêu tiên quyết thiếu); CT176 F; CT176 điểm chưa rõ → UNKNOWN + hỏi; bản ghi CT174 mâu thuẫn → UNKNOWN |
| E. Thay thế | 3 | ML009 → ML014; ML009 F → NOT; ML010 → ML018 (một → nhiều) |
| F. Prototype | 2 | "đủ điều kiện làm luận văn" → UNKNOWN / TRUE |
| H. Hồi quy review | 8 | đã xong TLTN → LVTN DA_HOAN_THANH; đã xong LVTN → TLTN DA_HOAN_THANH; HP thay thế đã đạt; mã ngoài CTĐT → lỗi; chỉ hỏi đúng hình thức; giá trị sai; câu "tiểu luận" → nhánh TLTN; không hồ sơ → UNKNOWN |
| G. Schema | 1 | trường `hinh_thuc_cuoi_khoa` |

---

## 3. Phát hiện

### P18-1 · Prototype luôn trả FALSE cho "đủ điều kiện làm luận văn"
Parser stub (w12) và parser Tuần 13 ánh xạ ý định này sang claim `du_dk_tc` **không có đối số** — atom không bao giờ có trong answer set → ba trị luôn FALSE. Ca hồi quy F1 fail với code cũ. Nay câu hỏi này đi qua Eligibility module (`prototype.answer_eligibility`, có hậu kiểm mã HP trong lời giải thích; không có hồ sơ → UNKNOWN).

### P18-2 · Đủ TC ≠ đủ điều kiện (R-F04)
Ghi chú catalog từ Tuần 5 đã nói "điều kiện khác của đơn vị đào tạo vẫn UNKNOWN", nhưng trước Tuần 18 không có đường nào trả UNKNOWN cho câu hỏi này: `du_dk_dang_ky("CT550E")` chỉ xét TC.

### P18-3 · Đã xong hình thức khác (review)
Bản đầu báo ELIGIBLE LVTN cho SV đã đạt TLTN, và hỏi đơn vị về TLTN cho SV đã đạt LVTN. Đ31 cho SV thực hiện **một trong ba** hình thức → nay DA_HOAN_THANH.

---

## 4. Hạn chế

- Nội dung điều kiện nhận đề tài của Trường CNTT&TT chưa có văn bản (A12). Khi có: thêm quy tắc với nguồn, ca hồi quy.
- `hinh_thuc_cuoi_khoa` là một giá trị cho toàn khóa; chưa mô hình học kỳ công bố / đổi hình thức sau khi bị F.
- Chưa xét lịch mở học phần theo học kỳ (`mo_hk`) và song hành khi trả lời "đủ điều kiện".
- Parser Tuần 13 vẫn sinh claim `du_dk_tc`; tích hợp mới chỉ ở prototype (bắt claim đó và chuyển sang module).
- Bộ test tự soạn; chưa có câu hỏi thật.
- Không có phần đọc tài liệu mới.

## 5. Việc còn lại → Tuần 19+

- [ ] Tuần 19 (Recommendation): chỉ đề xuất phương án mà Eligibility trả ELIGIBLE — không đề xuất NOT_ELIGIBLE/UNKNOWN như thể chắc
- [ ] A12: văn bản điều kiện nhận đề tài LVTN/TLTN của đơn vị
- [ ] Đưa ca eligibility vào bộ test mới của Tuần 20

### Ghi chú kiểm chứng

- [x] Eligible / Not Eligible / Unknown cho LVTN, TLTN, niên luận, niên luận cơ sở, thực tập, tích lũy TC, thay thế
- [x] Mỗi kết luận có chứng chỉ trỏ về điều/khoản; Unknown kèm câu hỏi đúng dữ kiện quyết định
- [x] Mọi tuần 5–18 ĐẠT
- [ ] Điều kiện của đơn vị đào tạo chưa hình thức hoá (thiếu văn bản)
