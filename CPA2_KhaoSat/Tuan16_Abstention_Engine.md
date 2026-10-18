# TUẦN 16 — THREE-VALUED LOGIC / ABSTENTION ENGINE

**Giai đoạn:** Uncertainty (Tuần 16/24) · **Mục tiêu:** Cài TRUE/FALSE/UNKNOWN + missing evidence
**Sản phẩm:** Abstention engine v1 (`w16_abstention/`)
**Tiêu chí hoàn thành:** Không đoán khi thiếu dữ liệu ✅
- `validate_abstention.py` đạt **30/30** kiểm tra (A 11 · B 10 · C 5 · D 4), bộ test tự soạn
- Bổ sung sau Tuần 17 (P17-1, rà soát hồ sơ mâu thuẫn): nhóm E 12 kiểm tra → **42/42** (xem `Tuan17_Adversarial_Set.md` mục 7)
- Đã viết test trước: bản đầu có 27 kiểm tra, **14** kiểm tra fail với KB/loader cũ, trong đó có ca hồi quy A2, A3, A6, A9 (luật cũ cho FALSE thay vì UNKNOWN)
- Test của mọi tuần 5–16 đều ĐẠT, 6 hồ sơ giả lập giữ nguyên kết luận Tuần 12
- P16-2 đã sửa (17/10/2026, sau khi chọn cách đọc (b)): quá thời gian tối đa thì không tốt nghiệp. R-Formal lên v1.7, có 5 ca hồi quy fail với luật cũ

---

## 0. Kết luận trước

> Trước Tuần 16, KB coi **thiếu dữ kiện là sai** (giả định thế giới đóng). Hệ quả:
> - Thiếu xác nhận kỷ luật thì `tot_nghiep` = FALSE, trong khi schema w7 ghi `null → UNKNOWN`.
> - Thiếu số học kỳ đã học thì hệ thống coi như "chưa quá hạn".
>
> Cả hai đều là đoán. Tuần 16 sửa như sau:
> - Dữ kiện ngoài chưa khai báo được **mở cả hai nhánh** ngay trong KB, nên ba trị tự cho UNKNOWN.
> - Engine chỉ kết luận khi claim cố định trên **mọi** thế giới.
> - Khi UNKNOWN, engine trả về **đúng các dữ kiện làm kết luận thay đổi**, kèm câu hỏi tiếng Việt, nguồn quy tắc, và kết luận ứng với từng giá trị.

---

## 1. Thiết kế

### 1.1. Thế giới mở có kiểm soát (KB, `graduation_solver.lp` mục 0)

```prolog
khai_bao(thoi_gian) :- da_hoc_nam2(_).
{ xac_nhan_ky_luat_sach } :- not khai_bao(ky_luat).
{ qua_thoi_gian_toi_da }  :- not khai_bao(thoi_gian).
```

| Hồ sơ | Loader phát | Kết quả `tot_nghiep` (hồ sơ đủ học vụ) |
|---|---|---|
| `xac_nhan_ky_luat_sach: true` | `xac_nhan_ky_luat_sach.` | TRUE |
| `false` | `khai_bao(ky_luat).` | FALSE (khai báo thật) |
| `null` / không có trường | (không) | **UNKNOWN** (trước: FALSE) |

Đây là quy tắc **meta**: nó quy định cách xử lý dữ kiện thiếu, không phải nội dung quy chế. Vì vậy nó không gắn `why/2` vào điều khoản nào. Nguồn của các biến bị ảnh hưởng: `xac_nhan_ky_luat_sach` ← R-F03 (QĐ3266 Đ32 k1); `qua_thoi_gian_toi_da` ← R-E01/R-E02 (QĐ3266 Đ5).

### 1.2. Missing evidence (`abstention.bang_chung_thieu`)

Mỗi answer set là một thế giới, tức một cách gán các dữ kiện mở. Với mỗi biến mở, engine chia các thế giới theo giá trị của biến rồi tính ba trị trong từng phần. Cách này **tương đương giải lại với ràng buộc biến = giá trị** mà không phải giải lại. Biến được coi là **quyết định** khi kết luận đổi theo giá trị của nó, và chỉ biến quyết định mới được hỏi.

Có 4 loại biến:
- `xac_nhan_ky_luat_sach`
- `qua_thoi_gian_toi_da`
- `g10("C")`: điểm không chắc, gồm F/D/A của OCR Tuần 15
- `duoc_mien("C")`: quyết định miễn chưa rõ (bẫy QD-11)

Ví dụ B8 (thiếu kỷ luật, CT550E không chắc): `xac_nhan_ky_luat_sach` cho {true → UNKNOWN, false → FALSE}. Nghĩa là xác nhận kỷ luật một mình chưa đủ, còn phải biết điểm CT550E.

### 1.3. Chính sách từ chối

| Verdict | `ket_luan` | Hành vi |
|---|---|---|
| TRUE / FALSE | True / False | Kết luận, không hỏi thêm |
| UNKNOWN | **None** | Không kết luận, liệt kê câu hỏi. **Không chọn theo đa số thế giới** (C3: 3/4 thế giới TRUE vẫn UNKNOWN), vì số thế giới không phải xác suất |
| MAU_THUAN (vô nghiệm) | None | Báo hồ sơ mâu thuẫn với quy chế |

`prototype.answer` (Tuần 12) dùng engine này thay cho cách lọc chuỗi `brave \ cautious` theo `"g10"`/`"duoc_mien"`.

---

## 2. Kết quả

| Nhóm | Kiểm tra | Nội dung |
|---|---|---|
| A. Thế giới mở | 11 | kỷ luật true/false/null/thiếu; trộn AV/PV + null vẫn FALSE; `thieu_dk(thoi_gian)` thiếu/9/20; `bi_xoa_ten`; thiếu `da_hoc_nam2` → `tot_nghiep` UNKNOWN + câu hỏi thời gian |
| B. Missing evidence | 10 | chỉ hỏi biến quyết định (B5: CT478 80/90 không hỏi); kết luận theo giá trị; F/D/A; QĐ miễn chưa rõ |
| C. Chính sách | 5 | `ket_luan` None; câu hỏi tiếng Việt không lộ tên atom; đa số ≠ chắc; vô nghiệm |
| D. Tích hợp | 4 | prototype null → UNKNOWN + `missing_facts`; 6 hồ sơ giữ kết luận; thời gian xác định khi có `da_hoc_nam2` |

**Verify toàn bộ** (Linux, cloud): w5–w16 đều `KẾT LUẬN: ĐẠT`, exit 0.

w15 cần wrapper vì code đang cố định đường dẫn Windows:
- Font: dùng Liberation Serif thay `C:/Windows/Fonts/times.ttf`.
- Tesseract: đặt `TESSERACT_EXE=tesseract`.

Trên Linux, độ phủ w15 là **7/18**, khác con số 1/18 của báo cáo Tuần 15 (Windows). Tôi đã chạy w15 trên **code trước và sau Tuần 16** trong cùng môi trường Linux, và đầu ra giống hệt nhau. Vậy chênh lệch đến từ môi trường (font, phiên bản Tesseract 5.3.4), **không phải do Tuần 16**. Không nên dùng con số 7/18 để báo cáo.

---

## 3. Phát hiện

### P16-1 · Định nghĩa "đã khai báo" theo chính atom bị mở thì thế giới tự đóng lại
Bản đầu viết `khai_bao(ky_luat) :- xac_nhan_ky_luat_sach.` Khi nhánh chọn "true", atom này làm `khai_bao(ky_luat)` đúng, từ đó triệt tiêu điều kiện `not khai_bao(ky_luat)` của chính lựa chọn. Mô hình đó không ổn định, nên chỉ còn 1 mô hình (FALSE). Test A2/A3 bắt được lỗi này. **Quy tắc:** `khai_bao/1` chỉ được suy từ dữ kiện đầu vào.

### P16-2 · `tot_nghiep` bỏ qua điều kiện thời gian — ĐÃ SỬA theo cách đọc (b)
- `graduation_solver.lp` đưa `dk_thoi_gian` vào `du_dk_hoc_vu`.
- R-Formal (qd3266 dòng 360–362) **cũng** định nghĩa `du_dk_hoc_vu` và `tot_nghiep` theo Đ32 k1 a/b/c mà không có thời gian.
- Hai định nghĩa hợp lại, nên sinh viên `da_hoc_nam2(20)` (trần 18) có cùng lúc `tot_nghiep` và `thieu_dk(thoi_gian)`. Lỗi này đã có từ trước Tuần 16.

Có hai cách đọc quy chế, và tôi **không tự chọn**:
- (a) Đ32 k1 không nêu thời gian. Khi quá hạn mà chưa đủ điều kiện thì bị xoá tên (Đ33 k1 / R-F09, R-D08), tức là chỉ dẫn tới `bi_xoa_ten`.
- (b) Đ5 "thời gian tối đa để hoàn thành CTĐT" là điều kiện ngầm của tốt nghiệp.

**Quyết định (17/10/2026): chọn (b).** Nguồn: QĐ3266 Đ5, tr.4: "thời gian học tập tối đa cho phép để SV hoàn thành CTĐT" (CTĐT 4,5 năm → tối đa 9 năm, R-E01; trần giảm theo TC công nhận, R-E02).

Cách sửa: thêm điều kiện thời gian vào **cả hai** định nghĩa `tot_nghiep`. Nếu chỉ sửa một nơi thì định nghĩa còn lại vẫn suy ra `tot_nghiep`.
- R-Formal v1.7: `tot_nghiep :- du_dk_hoc_vu, xac_nhan_ky_luat_sach, not qua_thoi_gian_toi_da.`
- `graduation_solver.lp`: `tot_nghiep :- du_dk_hoc_vu, dk_ky_luat, dk_thoi_gian.`
- Cả hai đều thêm `why(tot_nghiep, r_e01)`.

Ca hồi quy, tất cả fail với luật cũ:
- w5 C9b: quá hạn 19 > 18 → không `tot_nghiep`. Ca biên C9c: 18 = trần → vẫn tốt nghiệp.
- w10 B7b: quá hạn → FALSE. B7d: thiếu `da_hoc_nam2` → UNKNOWN. Ca biên B7c: 18 → TRUE.
- w16 A10/A11: thiếu `da_hoc_nam2` → UNKNOWN, kèm câu hỏi "đã học bao nhiêu nửa năm" (quá hạn → FALSE, chưa quá hạn → TRUE).

Fixture `KY_LUAT` của w10/w11 thêm `da_hoc_nam2(9).` (hồ sơ khai báo đủ). Kết luận của 6 hồ sơ giả lập không đổi.

Học phí ×1,5 sau thời gian thiết kế: **không có trong QĐ3266/QĐ5339**. Đ10 k1 chỉ ghi "mức học phí do Hiệu trưởng quyết định". Chưa hình thức hoá, cần văn bản quy định mức học phí làm nguồn.

### P16-3 · `tc_cong_nhan` vẫn dùng giả định thế giới đóng
`giam_hk(0) :- not tc_cong_nhan(_)` (R-E02). Hồ sơ có `da_hoc_nam2` nhưng không ghi `tc_cong_nhan` sẽ được coi là không có tín chỉ công nhận. Tôi chưa mở nhánh này, vì đa số sinh viên không có tín chỉ chuyển đổi, và mở nhánh sẽ làm mọi kết luận thời gian thành UNKNOWN. Câu hỏi bổ sung về thời gian đã hỏi luôn cả tín chỉ công nhận.

### P16-4 · Đường dẫn Windows cố định làm test không chạy trên máy khác
- w12 dùng `D:/LVTN/...`: đã sửa sang đường dẫn tương đối.
- w15 dùng `C:/Windows/Fonts/times.ttf`: chưa sửa, chạy bằng wrapper.

### P16-5 · Giá trị `g10` không duy nhất trong một mô hình
`g10/2` vừa là dữ kiện vừa có thể được suy ra (qd5339: miễn thi, điểm học cao hơn). Vì vậy giá trị của biến được lấy là **tập** điểm, sắp xếp cố định, chứ không lấy một điểm ngẫu nhiên. Lỗi này do review tìm ra.

---

## 4. Hạn chế

- **Số mô hình tăng tới ×4** khi hồ sơ thiếu cả hai trường. Với OCR có k học phần không chắc, số mô hình là 4·3ᵏ (k ≤ 6 → ≤ 2916). w15 nay chuyển tiếp `da_hoc_nam2`/`tc_cong_nhan` nên giảm còn 2·3ᵏ.
- **Missing evidence chỉ xét từng biến một.** Engine báo một biến có tự đủ để kết luận không (`du_ket_luan`), nhưng chưa tìm tập câu hỏi nhỏ nhất.
- Loader hồ sơ → ASP vẫn bị **chép ở 3 nơi** (w7/w11/w12). `abstention.KB_FILES` cũng chép danh sách file của `prototype.kb`. Cần gộp lại, nhưng đó là thay đổi kiến trúc nên chưa làm.
- Bộ test tự soạn, có 28 kiểm tra. Bộ đối kháng ≥ 60 ca thuộc Tuần 17.
- Không có phần đọc tài liệu mới về ba trị hoặc abstention.

## 5. Việc còn lại → Tuần 17+

- [x] Quyết định P16-2: chọn (b), đã sửa `tot_nghiep` và thêm ca hồi quy
- [ ] Tìm văn bản quy định học phí (hệ số ×1,5 sau thời gian thiết kế) trước khi hình thức hoá
- [ ] Đưa các ca dữ kiện thiếu / đa số ≠ chắc / QĐ miễn chưa rõ vào bộ Adversarial (Tuần 17)
- [ ] Đo Coverage ↔ Selective Accuracy trên bộ đối kháng
- [ ] Bỏ đường dẫn font Windows ở `render_transcript.py`; gộp loader

### Ghi chú kiểm chứng

- [x] Thiếu dữ kiện ngoài → UNKNOWN (không FALSE/TRUE)
- [x] UNKNOWN → `ket_luan = None` + câu hỏi cho dữ kiện quyết định, kèm nguồn
- [x] Test của mọi tuần đều đạt; 6 hồ sơ giữ kết luận
- [x] `tot_nghiep` phụ thuộc điều kiện thời gian (P16-2)
