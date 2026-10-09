# TUẦN 5 — PHỤ LỤC: R-FORMAL v1.1 → v1.3

> **Cập nhật v1.2 — đã có xác nhận cho hai câu hỏi treo.**
> **QD-09 đóng:** điểm quy đổi 4,0–4,9 từ cơ sở đào tạo khác **KHÔNG được tích lũy**.
> **QĐ5339 (2019) vẫn còn hiệu lực** → nhóm R-M không phải làm lại.
> Hệ quả số liệu: Formalization Coverage **78,9 % → 81,7 %** (R-M02 và R-M03b chuyển từ
> lớp P sang lớp F); ca kiểm thử 27 → **29/29 đạt**. Chi tiết ở mục 4 và mục 9.


**Bối cảnh:** sau khi bản v1.0 kết luận rằng *"toàn bộ loại T5 nằm ngoài QĐ3266"* (phát hiện
P-3), văn bản đích đã được bổ sung vào kho: **QĐ 5339/QĐ-ĐHCT ngày 05/11/2019** — *Quy định
xét miễn và công nhận điểm học phần trong CTĐT trình độ đại học hệ chính quy* (19 trang,
4 điều, cũng là bản quét không có lớp văn bản).

**Kết quả:** T5 được mở khoá hoàn toàn, **và v1.1 sửa một kết luận sai của v1.0.**

---

## 0. Kết luận trước

> Thêm 19 bản ghi từ QĐ5339 (16 trong miền). **Formalization Coverage gần như không đổi:
> 79,6 % → 78,9 %.** Nhưng **Executable Coverage tụt từ 66,7 % xuống 56,3 %.**

Đây là kết quả đáng chú ý và ngược trực giác: bổ sung một văn bản để *lấp một lỗ hổng* lại
làm hệ thống *kết luận được ít hơn* theo tỷ lệ. Lý do là toàn bộ nhóm T5 phụ thuộc dữ kiện
chứng chỉ — thứ không có trong bảng điểm. Nói cách khác, v1.0 không hề "tốt hơn"; nó chỉ
**chưa nhìn thấy phần việc mà nó không làm được**.

Đây chính là luận điểm nên đưa vào luận văn: coverage đo trên một kho văn bản chưa đầy đủ
là **ước lượng chệch lên**, và độ chệch chỉ lộ ra khi kho được bổ sung.

---

## 1. Số liệu v1.0 → v1.1

| Chỉ số | v1.0 (chỉ QĐ3266) | v1.1 (+ QĐ5339) |
|---|:-:|:-:|
| Bản ghi trong danh mục | 73 | **93** |
| Đơn vị trong miền (F+P+N) | 54 | **71** |
| F — Formalizable | 43 (79,6 %) | **56 (78,9 %)** |
| P — Partially formalizable | 7 (13,0 %) | **10 (14,1 %)** |
| N — Not formalizable | 4 (7,4 %) | **5 (7,0 %)** |
| **Formalization Coverage** | **79,6 %** | **78,9 %** |
| **Executable Coverage** | **66,7 %** | **56,3 %** |
| Buộc trả UNKNOWN vì thiếu dữ kiện | 11 (20,4 %) | **21 (29,6 %)** |
| Quy tắc ASP có con trỏ nguồn | 41 | **52** |
| Ca kiểm thử ngữ nghĩa | 17/17 | **27/27** |

Nhóm *"miễn & thay thế"* từ 7 đơn vị (F = 3) thành **21 đơn vị (F = 15)** — từ nhóm yếu nhất
thành nhóm lớn nhất trong danh mục.

---

## 2. SỬA MỘT KẾT LUẬN SAI CỦA v1.0 — QD-01

v1.0 đóng QD-01 như sau, dựa trên QĐ3266 Điều 22 khoản 5 điểm a:

> *"Học phần được miễn TÍNH vào tổng TC tích lũy, KHÔNG tính vào ĐTBCTL."*

**Phát biểu này quá rộng.** QĐ5339 Điều 3 khoản 11 nói:

> *"Kết quả điểm xét miễn được ghi nhận trong bảng kết quả học tập toàn khóa của SV. **Trừ
> các học phần điều kiện và học phần có điểm M**, kết quả điểm xét miễn học phần **được sử
> dụng để tính điểm trung bình chung tích lũy**."*

Nghĩa là có **hai loại miễn khác nhau về hệ quả kế toán**:

| Loại | Cơ chế | Điểm | Vào TC tích lũy | Vào ĐTBCTL |
|---|---|---|:-:|:-:|
| `exempted_M` | miễn học phần **điều kiện** bằng chứng chỉ (ngoại ngữ, tin học, GDQP, GDTC) | điểm **M**, không có điểm số | ✅ | ❌ |
| `recognized` | **công nhận điểm** học phần từ CTĐT đã học | mang **điểm số quy đổi** | ✅ | ✅ |

v1.0 chỉ nhìn thấy loại thứ nhất vì QĐ3266 chỉ nói về điểm M.

**Hệ quả cho taxonomy Tuần 2:** Trục C hiện có 6 trạng thái với một ô `exempted` duy nhất.
Ô đó **phải tách đôi** — 6 trạng thái thành 7. Đây không phải chi tiết kế toán vụn vặt: hai
trạng thái cho ra **hai giá trị ĐTBCTL khác nhau** trên cùng một bảng điểm, và ĐTBCTL quyết
định cả điều kiện tốt nghiệp lẫn hạng tốt nghiệp.

Ca C5 (điểm M bị loại khỏi mẫu số) và ca C20 (điểm công nhận nằm trong mẫu số) khoá cả hai
nhánh, đặt cạnh nhau để so sánh trực tiếp.

---

## 3. Phát hiện mới quan trọng nhất: miễn KHÔNG tự động (QD-11)

QĐ5339 Điều 2 khoản 6 quy định quy trình: SV **làm đơn** → **Tổ Xét miễn** của đơn vị đào tạo
xét → Trưởng Khoa phê duyệt → Phòng Đào tạo kiểm tra → **Hội đồng Xét miễn cấp Trường** phê
duyệt → nhập điểm.

Vậy **có chứng chỉ không đồng nghĩa với được miễn.** Có hai vị từ khác nhau:

```prolog
du_dk_xin_mien(C)   % suy ra được từ chứng chỉ  — CPA² tính được
duoc_mien(C)        % chỉ đến từ quyết định phê duyệt — dữ kiện ngoài
```

Và **không có luật nào suy `passed(C)` từ `du_dk_xin_mien(C)`**. KB phát thêm `mien_treo(C)`
để nói *"đủ điều kiện nhưng chưa có quyết định"*.

**Hệ quả trực tiếp cho bộ Q-Real.** Câu *"Chứng chỉ IELTS của em miễn được môn nào?"* trong
ma trận độ phủ Tuần 2 phải được trả lời là:

> *"Với IELTS 5.0, em **đủ điều kiện nộp đơn xin miễn** các học phần Anh văn căn bản (QĐ5339
> Điều 3 khoản 5 điểm a — Khóa 45 trở về sau cần bậc 3, tương đương IELTS 4.5). Hệ thống
> **không có** dữ liệu về quyết định xét miễn của em, nên chưa thể kết luận em đã được miễn."*

chứ **không** phải *"IELTS của em miễn được Anh văn căn bản 1, 2, 3"*. Câu sau là **nói sai**,
và là kiểu sai mà mọi baseline gần như chắc chắn sẽ mắc — vì nó là câu trả lời "hữu ích" nhất
về mặt ngôn ngữ. Ca C17/C18 khoá hành vi này: cùng một hồ sơ, thêm đúng dữ kiện `duoc_mien`
thì chân trị mới đổi.

Đây là **ca đối kháng mạnh nhất tìm được cho tới nay** cho giả thuyết H2 (baseline tự tin một
cách sai lầm), vì nó không đòi hỏi dữ liệu khuyết bất thường — nó là tình huống thường ngày.

---

## 4. XUNG ĐỘT GIỮA HAI VĂN BẢN CÙNG HIỆU LỰC (QD-09)

Đây là phát hiện phương pháp luận của phụ lục này.

Bảng quy đổi điểm của **hai văn bản không trùng nhau**:

| Thang 10 | QĐ3266 (2024) | QĐ5339 (2019) |
|---|---|---|
| 5,0 – 5,4 | D+ = 1,5 | D+ = 1,5 |
| **4,0 – 4,9** | **D = 1,0** | **không có ô** |
| dưới 4,0 | F = 0,0 | **không có dòng F** |
| Ngưỡng tích lũy (thang 10) | **4,0** | **5,0** |

QĐ5339 Điều 3 khoản 2 nói rõ: *"Học phần chỉ được xem là tích lũy khi đạt từ điểm D trở lên
theo thang điểm chữ **(trừ học phần Giáo dục quốc phòng và an ninh phải đạt từ điểm D+ trở
lên)** hoặc **đạt từ điểm 5,0 trở lên theo thang điểm 10**."*

Một sinh viên có điểm **4,5** là **ĐẠT** theo QĐ3266 và **KHÔNG ĐẠT** theo QĐ5339.

**Vì sao đây không phải xung đột liên phiên bản.** Giả định số 3 mục 5.3 của Tuần 1 viết:
*"Quy chế áp dụng theo phiên bản có hiệu lực tại thời điểm hỏi; không xử lý xung đột liên
phiên bản."* Giả định đó **không bao được ca này**, vì QĐ5339 không phải phiên bản cũ của
QĐ3266 — hai văn bản **cùng hiệu lực, khác phạm vi**, và QĐ3266 Điều 5 **chủ động trỏ sang**
QĐ5339. Không thể bỏ một trong hai.

**Cách CPA² chốt (QD-09) — ĐÃ XÁC NHẬN ở v1.2:** phân giải theo **phạm vi áp dụng**, không
theo thời điểm ban hành — điểm học tại ĐHCT dùng bảng QĐ3266 (ngưỡng 4,0); điểm quy đổi từ
cơ sở đào tạo khác dùng bảng QĐ5339 (ngưỡng 5,0). **Điểm chuyển đổi 4,0–4,9 KHÔNG được tích
lũy.** Xem mục 9 về hệ quả và về nghĩa vụ ghi nguồn.

Ca C22 vẫn để `passed(qp)` và `khong_dat_gdqp(qp)` **cùng đúng** trong một mô hình — mâu thuẫn
hiện ra chứ không bị che.

**Hệ quả cho giả định của Tuần 1:** phải sửa giả định số 3 thành hai mệnh đề tách bạch:

- *(giữ)* không xử lý xung đột **liên phiên bản** của cùng một văn bản;
- *(mới)* xung đột **liên văn bản** giữa các quy định cùng hiệu lực **là có thật, được phát
  hiện, và được phân giải bằng quy tắc phạm vi có ghi nhận công khai**.

Bổ sung mã lý do mới vào trục B: **`xung_dot_van_ban`** — nguyên nhân thứ bảy khiến một điều
khoản không thi hành được trọn vẹn, và là nguyên nhân duy nhất **không tồn tại khi chỉ đọc
một văn bản**.

---

## 5. Lược đồ con trỏ nguồn phải mở rộng: `rule_src/4` → `rule_src/5`

Lược đồ chốt ở v1.0 giả định ngầm rằng KB có **một** văn bản nguồn:

```prolog
rule_src(RuleId, Dieu, Khoan, Diem).
```

Với hai văn bản, `rule_src(r_b03, 22, 3, none)` và một quy tắc ở Điều 22 của QĐ5339 sẽ trỏ
tới cùng một địa chỉ mà nghĩa khác hẳn. v1.1 thêm tham số văn bản:

```prolog
rule_src(RuleId, VanBan, Dieu, Khoan, Diem).
rule_src(r_b03,  qd3266, 22, 3, none).
rule_src(r_m15,  qd5339,  3, 11, none).
```

Bất biến A3 nay kiểm cả mã văn bản, và bất biến mới **A7** kiểm mọi mã văn bản dùng trong
`.lp` đều được khai báo ở `meta.van_ban` của danh mục.

Bài học đáng ghi vào luận văn: **địa chỉ của một quy tắc pháp lý không phải (điều, khoản) mà
là (văn bản, điều, khoản)** — điều hiển nhiên khi nhìn lại, nhưng chỉ lộ ra khi có văn bản
thứ hai. Chi phí sửa ở tuần 5 là một lệnh thay thế; nếu để tới tuần 12, khi chứng chỉ đã nối
với proof engine, chi phí sẽ khác hẳn.

---

## 6. Các quyết định diễn giải sau v1.1

| Mã | Nội dung | Trạng thái |
|---|---|---|
| QD-01 | Miễn ↔ TC ↔ ĐTBCTL | 🔄 **SỬA** — tách hai loại miễn (mục 2) |
| QD-02 | TC tự chọn dư | 🟡 đóng một phần |
| QD-03 | Định nghĩa *"TC nợ đọng"* | 🔴 mở — cần Phòng Đào tạo |
| QD-04 | Ngoại lệ thẩm quyền hạ trần chân trị | ✅ đóng (thận trọng) |
| QD-05 | Thời hạn điểm I | 🔴 mở |
| QD-06 | Điều kiện công nhận TC | ✅ **đóng** — chính là QĐ5339 |
| QD-07 | Thay thế luận văn theo TC | ✅ đóng |
| QD-08 | Tiêu chí *"tương đương"* | 🔄 **sửa lý do** — thẩm quyền mở, không phải ngôn ngữ mơ hồ; người quyết định là Tổ Xét miễn |
| **QD-09** | Xung đột bảng quy đổi giữa hai văn bản | ✅ **mới, ĐÓNG ở v1.2** — điểm chuyển đổi 4,0–4,9 không tích lũy |
| **QD-10** | Gộp điểm khi miễn nhiều↔một | ✅ **mới, đóng** — QĐ5339 Điều 3 k.3 |
| **QD-11** | Miễn không tự động | ✅ **mới, đóng** — QĐ5339 Điều 2 k.6 |

Đáng chú ý ở **QD-08**: v1.0 xếp lý do là *"ngôn ngữ mơ hồ"*, v1.1 sửa thành *"thẩm quyền
mở"*. Bản thân câu chữ không đổi — cái đổi là **em đã đọc thêm một văn bản**. Nghĩa là
**phân loại lý do phụ thuộc độ đầy đủ của kho văn bản**, và đây phải được nêu như một hạn
chế phương pháp của RQ1, không được giấu.

---

## 7. Ba câu hỏi cũ nay đã có câu trả lời

| Câu hỏi treo từ Tuần 2 | Trả lời từ QĐ5339 |
|---|---|
| *"Chứng chỉ nào miễn được học phần nào?"* | Phụ lục 1 — bảng quy đổi IELTS/TOEIC/TOEFL/Cambridge ↔ 6 bậc. K45+ cần **bậc 3** (IELTS 4.5 / TOEIC 450 / iBT 45) |
| *"Chênh lệch tín chỉ khi thay thế thì tính sao?"* (T6 ca biên) | Điều 3 k.3 — điểm theo **trung bình có trọng số** của các học phần đã học; TC theo học phần **được miễn** |
| *"Có bảng thay thế học phần thật nào không?"* | Điều 3 k.9 — bảng chuyển đổi Lý luận chính trị ML009→ML014, ML010→ML016+ML018, ML011→ML019, ML006→ML021 |

Một chi tiết nhỏ nhưng đáng ghi (ca C21): quy tắc trung bình có trọng số **sinh ra điểm không
nằm trên thang 8 bậc**. Miễn 1 học phần từ hai học phần 4,0 (2 TC) và 3,0 (3 TC) cho 3,4 —
không phải A, B+, B hay bất kỳ bậc nào. Vậy `g4` **không đóng** trên tập giá trị của bảng quy
đổi, và mọi mã giả định "điểm luôn thuộc 8 giá trị" sẽ sai. Đây là ràng buộc thiết kế cho
Tuần 6.

---

## 8. Việc phải làm, cập nhật sau v1.1

**Đã gỡ chặn:** T5 không còn thiếu nguồn. Tuần 6 chạy đúng kế hoạch.

**Còn chặn:** điều kiện nhận đề tài LVTN/TLTN vẫn *"do đơn vị đào tạo quy định"* (QĐ3266
Điều 31) — vẫn cần quy định của Trường CNTT&TT, hoặc rút câu hỏi *"em đủ điều kiện làm luận
văn chưa?"* khỏi bộ Q-Real.

**Ba câu hỏi mới cho GVHD / Phòng Đào tạo** — hai đã có trả lời ở v1.2:

1. ✅ **QD-09** — điểm 4,0–4,9 quy đổi từ trường khác: **KHÔNG đạt**. Đã đưa vào KB.
2. 🔴 **QD-03** — *"TC nợ đọng"* tính thế nào? **Vẫn mở.** Ảnh hưởng tới cảnh báo học vụ
   (R-D03, ngưỡng 24 TC). Đây là câu hỏi treo cuối cùng có ảnh hưởng tới một ngưỡng số.
3. ✅ **QĐ5339 vẫn còn hiệu lực**, chưa bị văn bản nào thay thế → nhóm R-M giữ nguyên,
   rủi ro phải làm lại đã được loại bỏ.

---

### Ghi chú kiểm chứng — trạng thái tại v1.2

- [x] **29/29** ca kiểm thử đạt (17 ca của v1.0 và 10 ca T5 của v1.1 vẫn xanh sau khi
      phân giải QD-09)
- [x] 7/7 bất biến con trỏ nguồn đạt, gồm bất biến A7 về mã văn bản
- [x] Mọi bảng của QĐ5339 (quy đổi điểm, thành tích Olympic, quy đổi chứng chỉ ngoại ngữ)
      đã đối chiếu thủ công trên ảnh trang — OCR làm nát cả ba
- [x] **QD-09 đã xác nhận**: điểm chuyển đổi 4,0–4,9 không tích luỹ. Nhưng **chưa ghi rõ
      ai xác nhận và ngày nào** — xem `w5_rformal/PhuLuc_Quyet_dinh_dien_giai.md`
- [x] **QĐ5339 đã xác nhận còn hiệu lực**, chưa bị văn bản nào thay thế
- [x] **Trục C của Tuần 2 đã sửa 6 → 7 trạng thái** — `Tuan2_Taxonomy_Hoc_Vu_v1.md`
      nay là v1.1, có thêm `exempted_M` / `recognized` và Trục B′
- [x] Bộ kiểm chứng **chạy lại được trên máy trắng**: `requirements.txt` ghim `clingo`;
      phần A và B chạy được cả khi thiếu `clingo` (mã thoát 2 để phân biệt)
- [ ] **QD-03** (*"TC nợ đọng"*) vẫn mở — câu hỏi treo cuối cùng ảnh hưởng tới một ngưỡng số
- [ ] Nhãn F/P/N vẫn do **một người** gán — bộ soát chéo đã sẵn sàng
      (`make_review_kit.py` + `tinh_kappa.py`), chưa có người thứ hai chạy
- [ ] Chưa kiểm thử trên **bảng điểm thật** — 29 ca hiện dùng hồ sơ tổng hợp (Tuần 7)


---

## 9. CẬP NHẬT v1.2 — sau khi có xác nhận

### 9.1. Số liệu

| Chỉ số | v1.1 | **v1.2** |
|---|:-:|:-:|
| F — Formalizable | 56 (78,9 %) | **58 (81,7 %)** |
| P — Partially formalizable | 10 (14,1 %) | **8 (11,3 %)** |
| N — Not formalizable | 5 (7,0 %) | 5 (7,0 %) |
| **Formalization Coverage** | 78,9 % | **81,7 %** |
| **Executable Coverage** | 56,3 % | **59,2 %** |
| Ca kiểm thử | 27/27 | **29/29** |

R-M02 (bảng quy đổi) và R-M03b (ngưỡng 5,0) chuyển từ **P → F**: câu chữ của chúng vốn đã rõ
ràng; chúng bị xếp P chỉ vì **xung đột với văn bản kia**. Xung đột được phân giải thì lý do
xếp P biến mất.

Đây là điểm đáng chú ý về mặt phương pháp: **lớp P không phải lúc nào cũng là thuộc tính của
điều khoản.** Có ba loại P khác nhau về bản chất — P do câu chữ (ngôn ngữ mơ hồ, thẩm quyền
mở) là thuộc tính bền của điều khoản; P do **kho văn bản chưa đủ** (QD-08) và P do **xung đột
chưa phân giải** (QD-09) là thuộc tính **tạm thời của trạng thái nghiên cứu**, sẽ biến mất khi
đọc thêm hoặc hỏi thêm. Khi báo cáo Formalization Coverage trong luận văn, phải nói rõ con số
được đo ở trạng thái nào — nếu không, cùng một quy chế sẽ cho ba con số khác nhau (79,6 % →
78,9 % → 81,7 %) mà không ai biết vì sao.

### 9.2. Hệ quả của QD-09: một bất đối xứng phải nói ra

Cùng con số **4,5**:

- học tại ĐHCT → điểm **D**, **tích lũy được** (QĐ3266 Điều 22 khoản 3);
- chuyển từ trường khác → **không tích lũy** (QĐ5339 Điều 3 khoản 2).

Ba ca kiểm thử khoá bất đối xứng này cạnh nhau — C23 (chuyển đổi 4,5 → không tích lũy),
C23b (chuyển đổi 5,0 → tích lũy, quy đổi thành D+ = 1,5), C23c (học tại ĐHCT 4,5 → tích lũy).
Đây là ca đối kháng tốt cho Tuần 17: một hệ thống chỉ nhớ "D là đạt" sẽ trả lời sai với sinh
viên chuyển trường, và sai theo hướng **có lợi giả** — nói với sinh viên rằng họ đã tích lũy
một học phần mà thực tế chưa.

### 9.3. Nghĩa vụ ghi nguồn — phần quan trọng nhất của cập nhật này

QD-09 **không nằm trong câu chữ của bất kỳ văn bản nào**. Nó là một quyết định diễn giải do
con người xác nhận. Nếu chứng chỉ trình bày kết luận *"học phần này của em không được tích
lũy"* như thể suy trực tiếp từ quy chế, thì chứng chỉ **nói quá** — và đó đúng là kiểu lỗi
mà toàn bộ đề tài này tồn tại để chống lại.

Vì vậy KB phát thêm vị từ `dien_giai(qd09)` mỗi khi một kết luận dựa vào phân giải này, để
tầng chứng chỉ (Tuần 11–12) buộc phải nêu rõ:

> *"Kết luận này dựa trên một **quyết định diễn giải** (QD-09) về cách áp dụng đồng thời
> QĐ3266 và QĐ5339, không phải trên câu chữ trực tiếp của một điều khoản."*

Ba việc phải làm cho luận văn, không được bỏ:

1. **Ghi rõ ai xác nhận QD-09 và ngày nào.** Hiện KB mới ghi "xác nhận ngoài văn bản" —
   thiếu chủ thể và thời điểm. Nếu là xác nhận miệng thì nên xin một email hoặc ghi biên bản
   trao đổi với GVHD, vì đây là chỗ hội đồng có thể hỏi.
2. **Đưa danh sách quyết định diễn giải vào một phụ lục của luận văn**, mỗi mục có: nội dung,
   lý do phải quyết, phương án đã chọn, nguồn xác nhận. Đây chính là phần *"ghi rõ quyết định
   diễn giải trong KB"* mà taxonomy Tuần 2 yêu cầu cho lớp P — nay có 11 mục thật để trưng ra.
3. **Không gộp QD-09 vào phần "kết quả hình thức hoá".** Nó thuộc phần *hạn chế và giả định*,
   vì nó là điều tác giả quyết chứ không phải điều tìm thấy.

### 9.4. Còn lại gì

- 🔴 **QD-03** (*"TC nợ đọng"*) — câu hỏi treo cuối cùng còn ảnh hưởng tới một ngưỡng số.
- 🔴 QD-05 (thời hạn điểm I do GV quy định) và QD-08 (tiêu chí *"tương đương"*) — cả hai đều
  là **thẩm quyền mở thật sự**, không phải thiếu thông tin; chúng sẽ **không** đóng được bằng
  cách đọc thêm văn bản, và nên được báo cáo như kết quả của RQ1 chứ không như việc còn dang dở.
- Điều kiện nhận đề tài LVTN/TLTN (QĐ3266 Điều 31) vẫn cần quy định của Trường CNTT&TT.
- Trục C của Tuần 2 vẫn cần sửa 6 → 7 trạng thái (chưa cập nhật vào file Tuần 2).


---

## 10. CẬP NHẬT v1.3 — định nghĩa vận hành cho "TC nợ đọng" (QD-03)

### 10.1. Ba khẳng định phổ biến KHÔNG có trong văn bản

Khi đi tìm cách hiểu *"TC nợ đọng"*, ba mệnh đề sau xuất hiện rất thường xuyên trong các
nguồn giải thích không chính thức. Đã kiểm bằng cách **tìm toàn văn cả hai QĐ** — không có
mệnh đề nào trong số đó:

| Khẳng định thường gặp | Đối chiếu văn bản |
|---|---|
| *"Học phần đạt khi có điểm **từ 5,0 trở lên**"* | **Sai** với điểm học tại ĐHCT. QĐ3266 Điều 22 khoản 3: tích lũy **từ điểm D**, mà bảng Điều 22 khoản 2 đặt **D = 4,0–4,9**. Ngưỡng 5,0 là của QĐ5339 và theo QD-09 chỉ áp cho **điểm chuyển đổi** |
| *"Học phần đạt khi có điểm chữ **C trở lên**"* | **Sai**. C = 5,5–6,4. Ngưỡng tích lũy là **D**, thấp hơn ba bậc (D, D⁺, C) |
| *"Tổng TC nợ không được vượt quá **150 %** khối lượng CTĐT"* | **Không tồn tại.** Chuỗi "150" không xuất hiện ở QĐ3266; ở QĐ5339 chỉ xuất hiện trong dải điểm Cambridge KET. Con số thật trong quy chế là **24 TC** — và nó là ngưỡng **cảnh báo học tập** (Điều 18 k.2 đ.c), không phải điều kiện xét tốt nghiệp |
| *"Học phần có **dấu \***  là bắt buộc"* | Không xuất hiện ở cả hai văn bản. Có thể là quy ước hiển thị của phần mềm, không phải quy phạm |

Ba mệnh đề này đáng đưa vào **bộ Adversarial của Tuần 17** như một nhóm riêng: *bẫy tri
thức phổ biến nhưng sai*. Chúng khác với ca thiếu dữ liệu ở chỗ baseline sẽ trả lời **rất
tự tin**, vì đây đúng là thứ lặp đi lặp lại trên mạng.

### 10.2. Định nghĩa vận hành đã cài đặt

QĐ3266 dùng cụm *"TC nợ đọng"* **đúng một lần** (Điều 18 khoản 2 điểm c) và không định nghĩa
ở đâu. Định nghĩa đang dùng:

> **TC nợ đọng = tổng TC của các học phần ĐÃ ĐĂNG KÝ từ đầu khoá mà đến thời điểm xét vẫn
> CHƯA TÍCH LŨY.**

Định nghĩa này **không tự trả lời hai câu hỏi con**, nên cả hai được cài thành **chính sách
bật/tắt** thay vì chôn cứng vào mã:

| Mã | Câu hỏi | Mặc định | Lý do chọn |
|---|---|---|---|
| **QD-03a** | Học phần **đang học**, chưa có điểm — có tính là nợ không? | **CÓ** | Theo cách hiểu thông dụng; nhưng xem cảnh báo dưới |
| **QD-03b** | Học phần đã **rút hợp lệ** (điểm W) — có tính là nợ không? | **KHÔNG** | Điều 15 cho phép rút và Điều 22 k.5 đ.c loại điểm W khỏi mọi trung bình. Coi môn đã rút là "nợ" là phạt sinh viên vì một **quyền** mà quy chế trao cho họ |

Năm ca kiểm thử mới khoá hành vi này (34/34 đạt):

- **C27** hồ sơ mẫu → nợ đọng 7 TC (4 TC môn rớt + 3 TC môn đang học), môn điểm W không tính
- **C28** tắt QD-03a → **cùng bảng điểm cho 4 TC**
- **C29** bật QD-03b → **9 TC**
- **C30 / C31** ca biên ngưỡng: **24 TC không cảnh báo, 25 TC có** (*"vượt quá 24"* nghĩa là > 24)

Cặp C27/C28 là điểm đáng lưu ý: **cùng một bảng điểm cho 7 TC hoặc 4 TC tuỳ chính sách**.
Với ngưỡng 24 TC, chênh lệch này hoàn toàn có thể lật kết luận cảnh báo học vụ ở một hồ sơ
thật. Đây không phải chi tiết kế toán — nên nó phải là một **quyết định được ghi công khai**,
và mọi kết luận dùng nó đều phát kèm `dien_giai(qd03)`.

### 10.3. Trạng thái QD-03 và việc còn phải làm

QD-03 nay ở trạng thái **🟠 đóng tạm** — có định nghĩa chạy được, **chưa có nguồn xác nhận**.
Đây là trạng thái khác hẳn với ✅ đóng, và phụ lục quyết định diễn giải nay tự cảnh báo nếu
một mục ghi *đóng* mà không có nguồn.

Hai câu cần hỏi Phòng Đào tạo, nên hỏi **cùng lúc**:

1. *"TC nợ đọng"* tính theo học phần **đã đăng ký** hay theo **kế hoạch học tập toàn khoá**?
   Hai cách cho con số rất khác nhau với sinh viên chậm tiến độ.
2. Học phần **đang học chưa có điểm** và học phần **đã rút (điểm W)** có nằm trong số đó không?

Và một điểm mà thông tin về hệ thống `hqtl.ctu.edu.vn` gợi ra, có thể quan trọng hơn cả hai
câu trên: **nếu con số "TC nợ đọng" đọc thẳng được từ hệ thống quản lý trực tuyến của
Trường**, thì CPA² không nên tự tính nó nữa. Khi đó R-D03 đổi từ *tự suy từ bảng điểm* sang
*nhập từ hệ thống*, hai chính sách QD-03a/b trở nên vô hiệu, và độ tin cậy của kết luận cảnh
báo học vụ tăng hẳn. Cần xác nhận **hệ thống tính con số đó theo công thức nào** — vì nếu
công thức của hệ thống khác định nghĩa trong KB, đó lại là một xung đột kiểu QD-09, lần này
giữa **văn bản** và **phần mềm đang vận hành**.
