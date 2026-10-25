# TUẦN 15 — OCR BẢNG ĐIỂM

**Giai đoạn:** Uncertainty (Tuần 15/24) · **Mục tiêu:** OCR + lưu confidence cho từng dữ kiện
**Sản phẩm:** OCR pipeline v1 (`w15_ocr/`)
**Tiêu chí hoàn thành:** Có fact + confidence ✅
- Fact được nhận đúng **783/784 = 0,999** (cổng ≥ 0,99) trên 6 hồ sơ × 3 biến thể nhiễu
- **0/18** kết luận sai (TRUE/FALSE ngược đáp án)
- ⚠️ Độ phủ thấp: **1/18** ca ra TRUE/FALSE, còn lại UNKNOWN

---

## 0. Kết luận trước

> OCR không đủ tốt để tin từng con số, nhưng **đủ tốt để biết khi nào không tin**. Pipeline nhận một fact chỉ khi các lần đọc độc lập khớp nhau dưới ràng buộc của quy chế: điểm chữ phải khớp T.Hợp theo R-B02, TC phải khớp CTĐT, tổng TC và ĐTBCHK của học kỳ phải khớp số in. Chưa đủ chắc thì solver xét mọi khả năng. Kết quả là pipeline **không sinh kết luận sai nào**, đổi lại là rất hay trả UNKNOWN. Đây đúng là đánh đổi Coverage ↔ Selective Accuracy mà luận văn cần đo. UNKNOWN ở đây kèm **danh sách học phần cần sinh viên xác nhận**, không phải lời từ chối chung chung.

---

## 1. Kiến trúc

```
ảnh trang ─► dựng thẳng (projection profile, chỉ xoay khi |góc| ≥ 0,15°)
          ─► OCR lượt chính (vie, psm 6): học kỳ · dòng tiêu đề cột · dòng HP · dòng tổng
          ─► OCR từng dải cột (eng + whitelist): Mã HP · TC · Thi · T.Hợp · Q/Đổi
          ─► chuẩn hoá ─► kiểm chéo ─► hồ sơ (student_fact_schema + confidence + ocr_raw) + báo cáo
```

| Bước | Vì sao |
|---|---|
| OCR theo dải cột có whitelist | OCR cả dòng cho ra `97A` (9.7 dính với A), `§0` (8.0), `CTI00` (CT100) |
| Điểm thang 10 luôn có 1 chữ số thập phân | `97` → 9.7, `100` → 10.0; `975` → loại |
| Sửa mã theo vị trí | 2 chữ + 3 số + `E`: `CTI00` → CT100, `QP0IIE` → QP011E, `KL00IE` → KL001E |
| Mã có 2 lần đọc (dải cột + token đầu dòng) | Khớp → gộp confidence; ra 2 mã hợp lệ khác nhau (CT518E/CT515E) → cả hai không chắc |
| Điểm có tới 3 lần đọc (T.Hợp, Thi, điểm chữ) | Khớp dưới R-B02 → confidence 1 − Π(1 − cᵢ) |

**Confidence của một bản ghi** = min(mã, TC, điểm). Ngưỡng τ = 0,70 chốt trước khi đo.

---

## 2. Kiểm chéo và xử lý "không chắc"

| Kiểm tra | Nếu không qua |
|---|---|
| Mã ∈ CTĐT K49; TC = TC trong CTĐT; điểm chữ = R-B02(T.Hợp) | HP vào danh sách **không chắc** |
| Σ TC các dòng = "Tổng Số Tín Chỉ Đăng Ký" (chấp nhận có/không tính dòng miễn) | Có thể có dòng bị ẩn → **UNKNOWN** |
| ĐTBCHK tính lại (R-B08: kể cả F và HP điều kiện, trừ GDTC) = số in | Mọi HP của học kỳ → không chắc |
| Dòng không đọc được mã | Có thể ẩn HP → **UNKNOWN** |

**HP không chắc** → luật chọn `1 { g10(C,0); g10(C,40); g10(C,100) } 1.`, tức xét F, D (đạt thấp nhất) và A. Kết luận chỉ là TRUE/FALSE khi đúng trong mọi nhánh. Quá 6 HP không chắc (3⁶ = 729 mô hình) → UNKNOWN.

**Dữ kiện không có trên bảng điểm** (xác nhận kỷ luật R-F03, lựa chọn tích lũy CQ-06) lấy từ `khai_bao`. Thiếu khai báo thì để mở cả hai nhánh.

---

## 3. Kết quả

### 3.1. Bảng điểm tổng hợp (đáp án tuyệt đối)

Vẽ từ 6 hồ sơ Tuần 7 theo bố cục Mẫu In D5050A0 (chép từ bảng điểm thật; tên và mã số là giả), với 3 biến thể: sạch · mờ + JPEG q = 35 · nghiêng 0,8°.

| Chỉ số | Kết quả |
|---|---|
| Fact được nhận đúng | **783/784 = 0,999** |
| Kết luận sai | **0/18** |
| Độ phủ (TRUE/FALSE) | **1/18** (`sv_tron_ngoai_ngu`/sạch → FALSE đúng) |
| Hồ sơ OCR hợp lệ theo `student_fact_schema` | 18/18 |

Fact sai duy nhất: CT179 (biến thể nghiêng) đọc thành 7,3 thay vì 7,5. Cả hai đều là B nên R-B02 không bắt được, nhưng sai này **không đổi suy luận**: KB tính GPA theo điểm chữ, nên không quy tắc nào phân biệt 7,3 với 7,5.

### 3.2. Tiêm lỗi

| Lỗi tiêm | Kết quả |
|---|---|
| Đọc nhầm điểm chữ B+ → F | Bị R-B02 bắt → không chắc; kết luận không thành FALSE sai |
| Mất hẳn một dòng HP | Học kỳ lệch tổng TC → UNKNOWN, **không** thành "thiếu môn" |
| Không khai báo kỷ luật | UNKNOWN |

### 3.3. Bảng điểm thật (chỉ chạy ở máy, kết quả không commit)

4 trang bảng điểm in từ dkmh.ctu.edu.vn: đọc 37 dòng HP, nhận 32, không chắc 2, không dòng nào bị loại, 1 học kỳ lệch (dòng tổng kết không đọc được). **Đối chiếu tay trang 1: nhận 10/11, đúng 10/10**, còn lại 1 không chắc (QP010E).

---

## 4. Phát hiện

### P15-1 · Hai lỗi soundness do review tìm ra, đã sửa (test E)

- **Không đơn điệu theo GPA.** Bản đầu chỉ xét F/A cho HP không chắc. Nhưng điểm D *đạt* vẫn vào ĐTBCTL và kéo nó xuống: với `sv_du_hp`, nhánh F → TRUE, nhánh A → TRUE, trong khi nhánh D (đúng) → FALSE. Bản đầu sẽ trả **TRUE sai**. Đã thêm mốc D = 40.
- **Học lại.** Lần 1 đọc chắc là F, lần 2 đọc không ra thì bản đầu giữ F và bỏ cờ không chắc, có thể trả **FALSE sai**. Đã sửa: mã có dù chỉ một dòng không chắc thì cả mã là không chắc.

Cả hai đều có test hồi quy; với code cũ, test cho ra TRUE sai.

### P15-2 · KB Tuần 10 dùng giả định thế giới đóng cho dữ kiện ngoài

Chú thích trong `graduation_solver.lp` ghi "dk_ky_luat … luôn UNKNOWN nếu thiếu", nhưng `prototype.solve_verdict` trả **FALSE** khi thiếu `xac_nhan_ky_luat_sach`, vì không có dữ kiện thì `not` đúng. Pipeline OCR tự mở nhánh cho dữ kiện này. **Sửa cho toàn KB thuộc Tuần 16.**

### P15-3 · Bảng điểm thật khác mô hình CTĐT/miễn của Tuần 6–9

| Bảng điểm thật | Mô hình hiện tại | Xử lý |
|---|---|---|
| Miễn ngoại ngữ in thành dòng **CC004** "Chứng chỉ trình độ Tiếng Anh - Bậc 3 (B1)", 10 TC, Miễn M | Điểm M trên XH023–025 | Giả định CC004 = miễn trọn nhánh Anh văn (XH023–025), **gắn cờ chờ Phòng Đào tạo xác nhận** |
| GDTC ghi thành **TC025, TC026, TC027** | Curriculum KB chỉ có **TC100** "GDTC 1+2+3" | **Chưa xử lý.** KB sẽ không nhận GDTC thật → kết luận "thiếu nhóm GDTC" sai. Cần xem lại CTĐT K49 |
| "Tổng Số Tín Chỉ Đăng Ký" không tính dòng CC004 | — | Kiểm tổng TC chấp nhận cả hai cách |
| ĐTBCHK in 3.85 = 50/13: tính cả HP quốc phòng | R-B08 "kể cả HP điều kiện trừ GDTC" | Khớp quy chế — xác nhận R-B08 trên dữ liệu thật |

### P15-4 · Lỗi OCR đặc thù

- Dựng thẳng một trang vốn thẳng (−0,05°) làm "ML018" thành "ML01§" → chỉ xoay khi |góc| ≥ 0,15°.
- Tiêu đề lặp ở trang sau ("Bảng Ghi Điểm…", "Loại…") bị nhận là dòng HP → nhận dòng chỉ với token ASCII.
- Confidence của Tesseract cho "B+" thấp có hệ thống (0,4–0,6) → gộp với các lần đọc khớp nhau.

---

## 5. Hạn chế

- **Độ phủ 1/18.** Ca nào cũng còn vài HP không chắc, mà mỗi HP không chắc có thể đổi kết luận. Hướng cải thiện: hỏi lại sinh viên đúng các HP này (đây là "missing evidence" của Tuần 16), OCR lại riêng ô bị nghi ngờ ở DPI cao hơn, và dùng điểm đọc được làm ưu tiên thay vì mọi khả năng.
- **Đánh giá trên ảnh tổng hợp** do chính pipeline này định nghĩa bố cục. Bảng điểm thật mới đối chiếu tay được 1 trang.
- **Thiết kế có chỉnh sau khi xem kết quả tổng hợp:** gộp confidence, ngưỡng xoay, regex nhận dòng. Không có tập tổng hợp giữ riêng; bảng điểm thật là tập kiểm tra ngoài duy nhất.
- **Giả định đơn điệu:** trong miền đạt, điểm cao hơn không làm điều kiện tốt nghiệp xấu đi. Đúng với các quy tắc hiện có (ĐTBCTL, TB GDQP); cần kiểm lại khi thêm quy tắc mới.
- Gộp confidence giả định lỗi giữa các cột gần độc lập, trong khi chúng cùng một ảnh.

---

## 6. Việc còn lại → Tuần 16+

- [x] **Tuần 16:** sửa giả định thế giới đóng cho dữ kiện ngoài trong KB (P15-2); "missing evidence" = danh sách HP không chắc + khai báo thiếu — ✅ đã xong: Tuần 16 (graduation_solver.lp mục 0 + w16_abstention)
- [ ] Xác minh với CTĐT/Phòng Đào tạo: GDTC TC025–027 ↔ TC100; CC004 ↔ nhánh Anh văn
- [x] Đưa các ca OCR (mất dòng, đọc nhầm, nghiêng) vào bộ Adversarial ở Tuần 17 — ✅ đã xong: Tuần 17 nhóm ocr_sai (18 ca mức tài liệu + 2 ca mức ảnh)
- [ ] Đối chiếu tay 3 trang còn lại của bảng điểm thật

### Ghi chú kiểm chứng

- [x] Mỗi fact có `confidence` và `ocr_raw`; hồ sơ hợp lệ theo schema
- [x] Fact nhận đúng ≥ 99% trên ảnh tổng hợp có nhiễu
- [x] Không kết luận sai trên 18 ca + 3 ca tiêm lỗi + 2 ca hồi quy
- [x] Đã chạy trên bảng điểm thật (không commit dữ liệu)
- [ ] Độ phủ còn thấp (1/18)
