# TUẦN 5 — R-FORMAL v1.0  *(bản gốc — một số kết luận đã bị thay thế)*

> ### ⚠️ Tài liệu này là bản v1.0, giữ lại để đối chiếu lịch sử. Không dùng số liệu ở đây.
>
> Bản hiện hành: **R-Formal v1.2** — xem `Tuan5_R_Formal_v1_2_PhuLuc_QD5339.md`.
>
> | | v1.0 (tài liệu này) | **v1.2 (hiện hành)** |
> |---|:-:|:-:|
> | Văn bản nguồn | chỉ QĐ3266 | QĐ3266 **+ QĐ5339** |
> | Đơn vị trong miền | 54 | **71** |
> | Formalization Coverage | 79,6 % | **81,7 %** |
> | Executable Coverage | 66,7 % | **59,2 %** |
> | Ca kiểm thử | 17/17 | **29/29** |
>
> **Hai kết luận của v1.0 đã bị bác:**
> 1. **QD-01 phát biểu quá rộng.** v1.0 viết *"học phần được miễn không tính vào ĐTBCTL"* —
>    chỉ đúng cho học phần mang **điểm M**. Học phần **công nhận điểm** thì **có** tính
>    (QĐ5339 Điều 3 khoản 11).
> 2. **Phát hiện P-3 đã hết hiệu lực.** v1.0 kết luận *"toàn bộ loại T5 nằm ngoài QĐ3266"*
>    và coi đó là chặn. Văn bản đích (QĐ5339) nay đã có trong kho và T5 đã được hình thức hoá.
>
> Ngoài hai điểm trên, phần phương pháp và bốn phát hiện P-1, P-2, P-4 của tài liệu này
> vẫn còn giá trị.

---

## (nội dung bản gốc v1.0)


**Giai đoạn:** Formalization (Tuần 5/24) · **Mục tiêu:** Formalize quy chế
**Sản phẩm:** R-Formal v1
**Tiêu chí hoàn thành:** mỗi rule có nguồn ✅ — *kiểm tự động, không phụ thuộc người đọc*
**Bằng chứng kèm theo:** `w5_rformal/` — danh mục 73 bản ghi, 41 quy tắc ASP, 17/17 ca kiểm thử đạt

---

## 0. Kết luận trước

> **Trên 54 đơn vị quy phạm thuộc miền tư vấn học vụ của QĐ3266:**
> **Formalization Coverage = 79,6 %** (F = 43, P = 7, N = 4).
> **Executable Coverage = 66,7 %** — và khoảng cách **13 điểm phần trăm** giữa hai con số
> này là phát hiện phương pháp luận chính của tuần: *hình thức hoá được* và *thi hành được*
> là **hai trục độc lập**, không phải một.

Toàn bộ 41 quy tắc đã mã hoá đều mang con trỏ `rule_src(RuleId, Điều, Khoản, Điểm)`, và
tính bất biến "mọi kết luận đều truy được về một khoản của QĐ3266" được kiểm bằng máy
(`validate_rformal.py`, mục A) chứ không bằng lời hứa trong báo cáo.

Ngoài ra tuần này **sửa được một lỗi tham số thật trong prototype Tuần 4**, **đóng được 3
trong 4 quyết định diễn giải treo từ Tuần 2**, và **phát hiện 3 chỗ phải sửa phạm vi đề tài**.

---

## 1. Phương pháp

### 1.1. Nguồn và cách trích

Văn bản: **Quyết định số 3266/QĐ-ĐHCT ngày 15/8/2024** của Hiệu trưởng Trường Đại học Cần
Thơ ban hành *Quy định công tác học vụ dành cho sinh viên trình độ đại học hình thức chính
quy* — 36 điều, 4 chương, 21 trang, hiệu lực từ Học kỳ 2 năm học 2024–2025, thay thế
QĐ 1813/QĐ-ĐHCT (18/6/2021).

Bản PDF là **bản quét** (máy quét TOSHIBA e-STUDIO857), **không có lớp văn bản** —
`pdftotext` trên toàn file trả về đúng 21 byte. Quy trình đã dùng:

1. `pdftoppm -r 300 -gray` → 21 ảnh trang;
2. `tesseract -l vie --psm 6` → văn bản thô (`source/QD3266_ocr_raw.txt`, 60 KB);
3. **đối chiếu thủ công trên ảnh** cho mọi trang chứa số hoặc bảng: trang 4 (Điều 5),
   10 (Điều 18), 14 (Điều 22), 15 (Điều 24), 18 (Điều 30), 19 (Điều 32), 20 (Điều 33–35).

Bước 3 không phải thủ tục thừa — xem mục 5.

### 1.2. Đơn vị phân tích

Đơn vị không phải "điều" mà là **mệnh đề quy phạm nhỏ nhất có thể quy về một phát biểu về
trạng thái học vụ của một sinh viên**. Một điều có thể sinh nhiều đơn vị (Điều 18 sinh 8),
và một khoản có thể tách đôi khi hai vế thuộc hai lớp khác nhau (Điều 32 khoản 1 điểm a
tách thành R-F01a lớp F và R-F01b lớp N).

Điều nào **không** sinh mệnh đề nào về một sinh viên cụ thể — thủ tục hành chính, tổ chức
đào tạo, học phí, bảo hiểm, kỷ luật phòng thi, quản lý bằng — được gán lớp **X (ngoài miền)**
và **không tính vào mẫu số coverage**. Có 19 điều như vậy. Việc loại chúng phải công khai,
vì nếu tính cả thì coverage bị thổi phồng bằng những điều dễ.

### 1.3. Ba trục phân loại

| Trục | Giá trị | Nguồn |
|---|---|---|
| **A — loại ràng buộc** | T1…T8 | Taxonomy Tuần 2 |
| **B — khả năng hình thức hoá** | F / P / N | Taxonomy Tuần 2 |
| **B′ — khả dụng dữ kiện** | có / không | **MỚI ở Tuần 5** |

Trục B′ là bổ sung của tuần này, và mục 3 giải thích vì sao nó cần thiết.

---

## 2. Kết quả định lượng (đầu ra cho RQ1)

```
Tổng số điều của QĐ3266                        36
Số bản ghi trong danh mục                      73
  – ngoài miền tư vấn học vụ (X)               19
  – trong miền (F + P + N)                     54

F  Formalizable                                43   (79,6 %)
P  Partially formalizable                       7   (13,0 %)
N  Not formalizable                             4   ( 7,4 %)

>>> Formalization Coverage = F/(F+P+N)       = 79,6 %
>>> Executable Coverage    = (F ∧ có dữ liệu) = 66,7 %
Điều khoản buộc trả UNKNOWN vì thiếu dữ kiện   11   (20,4 %)
```

### 2.1. Vì sao một điều khoản rời khỏi lớp "thi hành được trọn vẹn"

| Nguyên nhân | Số đơn vị | Ví dụ |
|---|:-:|---|
| Dữ kiện không tồn tại trong phạm vi CPA² | 7 | Điều 32 k.1 đ.c — kỷ luật, truy cứu hình sự |
| Con trỏ tới văn bản khác | 5 | Điều 5 — *"theo Quy định xét miễn và công nhận điểm học phần"* |
| Thẩm quyền mở | 2 | Điều 18 k.5 đ.b — *"trường hợp đặc biệt do Hiệu trưởng quyết định"* |
| Thuật ngữ không được định nghĩa | 2 | Điều 18 k.2 đ.c — *"TC nợ đọng"* |
| Tham số do người quy định | 1 | Điều 22 k.5 đ.b — thời hạn bổ sung điểm I *"do GV quy định"* |
| Quy chế trao quyền chọn cho SV | 1 | Điều 17 k.3 — SV chọn học phần tự chọn nào tính vào ĐTBCTL |

Ba nguyên nhân đầu là đúng giả thuyết Tuần 2. **Hai nguyên nhân cuối là mới** và không có
trong khung phân loại ban đầu — chúng đáng được nêu như đóng góp nhỏ của RQ1, vì cả hai đều
sinh ra `UNKNOWN` theo cơ chế khác hẳn: *"tham số do người quy định"* làm KB thiếu một hằng
số, còn *"quyền chọn của SV"* làm bài toán **không đơn trị** — cùng một bảng điểm cho nhiều
ĐTBCTL hợp lệ. Loại sau không giải được bằng cách thu thập thêm dữ liệu; nó phải giải bằng
tối ưu hoá cộng một tuyên bố diễn giải công khai.

### 2.2. Độ phủ theo nhóm điều khoản ưu tiên (đối chiếu phạm vi Tuần 1)

| Nhóm | Số đơn vị | F | P | N |
|---|:-:|:-:|:-:|:-:|
| Điều kiện tốt nghiệp | 12 | 10 | 0 | 2 |
| Cảnh báo học vụ | 10 | 8 | 2 | 0 |
| Miễn & thay thế học phần | 7 | 3 | 3 | 1 |
| Đăng ký học phần | 6 | 5 | 0 | 1 |
| Điểm & tích lũy | 6 | 5 | 1 | 0 |
| Xếp loại / xếp hạng | 5 | 5 | 0 | 0 |
| Trần tín chỉ đăng ký | 3 | 3 | 0 | 0 |
| Học cùng lúc hai chương trình | 3 | 2 | 1 | 0 |
| Định nghĩa học phần | 2 | 2 | 0 | 0 |

**Nhóm "miễn & thay thế" là nhóm yếu nhất** (F chỉ 3/7) và đó không phải ngẫu nhiên —
xem phát hiện P-3 ở mục 4.

---

## 3. Phát hiện phương pháp luận: hai trục, không phải một

Taxonomy Tuần 2 trộn hai câu hỏi khác nhau vào một nhãn N:

- *"Điều khoản này có dịch được sang logic không?"* — câu hỏi về **văn bản**;
- *"Hệ thống có dữ liệu để chạy quy tắc đó không?"* — câu hỏi về **dữ liệu**.

Điều 19 là ca mẫu buộc phải tách hai câu hỏi này:

> *"Sinh viên phải dự 100% số tiết đối với các học phần thực hành... phải tham dự tối thiểu
> 80% số tiết đối với các học phần lý thuyết. SV vắng tham gia lớp nhiều hơn thời gian quy
> định sẽ bị cấm thi."*

Điều khoản này **hình thức hoá được trọn vẹn** — hai ngưỡng 100 % và 80 % hoàn toàn rõ,
không có thẩm quyền mở, không có ngôn ngữ mơ hồ. Nhưng CPA² **không bao giờ chạy được nó**,
vì dữ liệu điểm danh không nằm trong bảng điểm. Xếp nó vào N là sai (nó không kháng lại
việc hình thức hoá); xếp vào F rồi im lặng cũng sai (hệ thống sẽ tưởng mình kết luận được).

Cách xử lý đã chốt: **giữ lớp F trên trục B, gắn `du_lieu = "không"` trên trục B′**, và
tầng suy diễn coi mọi vị từ thuộc nhóm này là biến tự do → kết luận rơi về `UNKNOWN`.

Hệ quả đo lường: phải báo cáo **hai** chỉ số chứ không một.

- `Formalization Coverage` = 79,6 % trả lời câu hỏi *"quy chế đại học Việt Nam dịch được
  bao nhiêu sang logic?"* — đây là câu hỏi của RQ1.
- `Executable Coverage` = 66,7 % trả lời câu hỏi *"hệ thống thật kết luận được bao nhiêu?"* —
  đây là con số quyết định trần Coverage trong đường cong Coverage–Selective Accuracy ở Tuần 22.

Chênh lệch 13 điểm phần trăm chính là phần mà **mọi baseline sẽ trả lời tự tin còn CPA²
sẽ từ chối** — nói cách khác, đây là *dự đoán định lượng có thể kiểm chứng* cho giả thuyết
H2, lập trước khi chạy thí nghiệm. Điều này mạnh hơn nhiều so với việc quan sát hậu nghiệm.

---

## 4. Bốn phát hiện buộc phải sửa tài liệu tuần trước

### P-1 · SAI THAM SỐ trong prototype Tuần 4 — ngưỡng cảnh báo học vụ

`w4_solver_probe/kb.py` đặt `WARNING_TERM_GPA = 1.20`. Đối chiếu Điều 18 khoản 2:

- điểm a: cảnh báo khi **ĐTBCHK** dưới **0,80** (HK đầu khóa) hoặc dưới **1,00** (các HK sau);
- điểm c: cảnh báo khi **ĐTBCTL** dưới **1,2 / 1,4 / 1,6 / 1,8** theo trình độ năm thứ 1/2/3/4+.

Số 1,20 có thật trong quy chế nhưng nó là ngưỡng của **ĐTBCTL năm thứ nhất**, không phải
ngưỡng ĐTBCHK. Prototype đã gán sai đại lượng. Hệ quả cụ thể: một SV có ĐTBCHK = 0,90 ở học
kỳ đầu **không** bị cảnh báo theo điểm a, nhưng prototype cũ báo cảnh báo. Ca C2 trong bộ
kiểm thử khoá vĩnh viễn lỗi này; ca C2b cho thấy đúng bảng điểm đó ở học kỳ **không phải**
đầu khóa lại **có** cảnh báo — hai kết luận trái ngược từ cùng một điểm số.

Ngoài ra, xét cảnh báo theo điểm c cần biết **trình độ năm học**, mà Điều 30 xác định trình
độ năm học theo **tổng tín chỉ tích lũy, không theo niên khóa**. Một sai số 1 TC ở ranh giới
70/71 làm đổi ngưỡng cảnh báo từ 1,4 sang 1,6 (ca C3, C4). Đây là ca đối kháng bắt buộc cho
Tuần 17.

### P-2 · SAI PHẠM VI trong Tuần 1 — không tồn tại "sàn tín chỉ"

Tuần 1 mục 5.1 liệt kê nhóm điều khoản ưu tiên số (3) là *"trần/sàn tín chỉ đăng ký"*.
Toàn văn QĐ3266 **chỉ có trần** (Điều 14 khoản 1: tối đa 20 TC/HK) và **không có sàn tín chỉ
đăng ký bắt buộc**. Mốc 12 TC mà nhiều người tưởng là sàn thực ra chỉ là **điều kiện xét học
bổng** (Điều 9 khoản 1 điểm c) và **điều kiện xếp loại/khen thưởng** (Điều 26 khoản 1).

Đây là một **phát hiện âm tính** và nó có giá trị: một trợ lý học vụ trả lời *"em phải đăng
ký tối thiểu 12 tín chỉ"* là **nói sai quy chế**. Vì đây là niềm tin phổ biến, khả năng cao
LLM baseline sẽ mắc — nên câu hỏi này phải vào bộ Adversarial như một ca **bẫy tri thức
tiên nghiệm**, khác loại với các ca thiếu dữ liệu. Ca kiểm thử C13 khoá hành vi đúng.

Việc cần làm: sửa tên nhóm ưu tiên (3) trong Tuần 1 thành *"trần tín chỉ đăng ký"*.

### P-3 · THIẾU VĂN BẢN NGUỒN — toàn bộ loại T5 nằm ngoài QĐ3266

Taxonomy Tuần 2 dành hẳn một loại **T5 — Exemption** với ví dụ *"miễn học phần ngoại ngữ
bằng chứng chỉ IELTS/TOEIC"*. Đối chiếu toàn văn: **QĐ3266 không chứa bất kỳ quy tắc miễn
học phần cụ thể nào** — không có bảng chứng chỉ ↔ học phần được miễn, không có điều kiện
hiệu lực chứng chỉ. Quy chế chỉ nói *"được xem xét công nhận, chuyển đổi… **theo Quy định
xét miễn và công nhận điểm học phần trong CTĐT trình độ đại học hình thức chính quy của
Trường ĐHCT**"* (Điều 5).

QĐ3266 chỉ đóng góp **hệ quả kế toán** của việc miễn — Điều 22 khoản 5 điểm a về điểm M —
chứ không đóng góp **điều kiện** được miễn.

**Việc phải làm ngay ở Tuần 6:** xin hoặc tải *"Quy định xét miễn và công nhận điểm học phần"*
của ĐHCT. Nếu không lấy được, T5 phải bị rút khỏi phạm vi và điều đó phải nói rõ trong luận
văn, không được để lửng.

Cùng loại: **Điều 31 không quy định điều kiện nhận đề tài luận văn** — quy chế nói *"SV phải
thỏa mãn các điều kiện **do đơn vị đào tạo quy định**"*. Nghĩa là câu hỏi *"em đủ điều kiện
làm luận văn chưa?"* trong ma trận độ phủ Tuần 2 **không trả lời được từ QĐ3266**. Cần quy
định của Trường CNTT&TT, hoặc rút câu hỏi khỏi bộ Q-Real.

### P-4 · LỖI PIPELINE OCR — trang 20 trắng hoàn toàn

Tesseract trả về **chuỗi rỗng** cho trang 20, đúng trang chứa Điều 33 (xử lý SV quá hạn),
Điều 34 (**bảng hạng tốt nghiệp** + điều khoản giảm một mức) và Điều 35. Không có cảnh báo,
không có lỗi — chỉ là một trang trắng lặng lẽ giữa 21 trang. Nếu tin OCR, R-Formal sẽ **thiếu
toàn bộ quy tắc xếp hạng tốt nghiệp mà không ai biết**.

Ba trang khác mất bảng hoặc mất dòng: bảng Điều 5 (thời gian tối đa) mất sạch; bảng quy đổi
điểm Điều 22 **mất đúng hai dòng C⁺ và C** — nghĩa là mọi điểm 5,5–6,9 sẽ không quy đổi được;
bảng xếp loại Điều 24 mất toàn bộ nhãn hàng.

**Đây là bằng chứng thực nghiệm sớm cho Tuần 15–16**, và đáng đưa vào luận văn: lỗi OCR nguy
hiểm nhất không phải lỗi *sai ký tự* (dễ phát hiện) mà lỗi **mất im lặng** — một vùng nội
dung biến mất mà không để lại dấu vết. Hệ quả thiết kế: pipeline OCR **bắt buộc** phải có
kiểm tra tính đầy đủ ở mức cấu trúc (số điều liên tục 1→36, mỗi trang có ≥ N ký tự) chứ
không chỉ có `confidence` ở mức token — vì độ tin cậy trung bình của một trang trắng là
*không xác định*, không phải *thấp*.

---

## 5. Bốn quyết định diễn giải: trạng thái sau Tuần 5

Tuần 2 để treo 4 quyết định. Đối chiếu toàn văn đóng được 3.

| Mã | Câu hỏi | Trạng thái | Nguồn |
|---|---|---|---|
| **QD-01** | Học phần **miễn** có tính vào tín chỉ tích lũy / ĐTBCTL không? | ✅ **ĐÓNG** — tính vào **tín chỉ**, **không** tính vào ĐTBCTL và ĐTBCHK | Điều 22 k.5 đ.a (điểm M) |
| **QD-02** | Tín chỉ tự chọn **dư** đi đâu? | 🟡 **ĐÓNG MỘT PHẦN** — không bị bỏ; SV **được quyền chọn** môn điểm cao tính vào ĐTBCTL | Điều 17 k.3 |
| **QD-07** | **Thay thế** luận văn ràng buộc theo môn hay theo tín chỉ? | ✅ **ĐÓNG** — theo **đủ số TC** yêu cầu của CTĐT, không cần tương đương từng môn | Điều 31 k.3 |
| **QD-08** | Học phần A thay được B khi nào? | 🔴 **MỞ** — *"nội dung và khối lượng kiến thức tương đương"* không có tiêu chí định lượng | Điều 20 k.6 |

**QD-01 xác nhận đúng giả định của prototype Tuần 4** — nhưng khác biệt quan trọng: nay nó
có nguồn, không còn là phỏng đoán. Ca kiểm thử C5 kiểm trực tiếp **mẫu số** của ĐTBCTL để
bảo đảm học phần điểm M không lọt vào.

**QD-02 lộ ra một tính chất bất ngờ:** quy chế trao quyền chọn cho SV, nên **ĐTBCTL không
đơn trị** — cùng một bảng điểm có nhiều giá trị ĐTBCTL hợp lệ. CPA² chốt: báo cáo theo phương
án tối ưu (chọn tổ hợp cho ĐTBCTL cao nhất) và **ghi rõ trong chứng chỉ rằng đây là quyền
chọn của SV, không phải một sự thật khách quan**. Đây đúng là chỗ chứng chỉ tỏ ra hơn hẳn
một con số trần trụi.

Bốn quyết định mới phát sinh trong tuần: **QD-03** (định nghĩa *"TC nợ đọng"* — MỞ, phải hỏi
Phòng Đào tạo), **QD-04** (ngoại lệ thẩm quyền hạ trần chân trị của buộc thôi học — đóng theo
hướng thận trọng), **QD-05** (thời hạn điểm I do GV quy định — MỞ), **QD-06** (điều kiện công
nhận TC trỏ ra văn bản khác — MỞ).

**QD-04 đáng chú ý về mặt kiến trúc.** Điều 18 khoản 5 điểm b nói: *"Đã bị cảnh báo học tập
và HK kế tiếp có ĐTBCHK dưới 1,00. Những trường hợp đặc biệt sẽ do Hiệu trưởng quyết định."*
Phần lõi hình thức hoá được hoàn hảo. Nhưng **một mệnh đề ngoại lệ đủ để hạ trần chân trị của
cả điều khoản**: hệ thống không bao giờ được kết luận *"em sẽ bị buộc thôi học"* ở mức `TRUE`.
CPA² chỉ kết luận `thuộc diện xem xét buộc thôi học` và trả `UNKNOWN` cho quyết định cuối
cùng (ca C14). Đây là nguyên tắc chung, không phải xử lý riêng lẻ: **ngoại lệ thẩm quyền lan
truyền lên toàn bộ kết luận, không chỉ lên nhánh ngoại lệ.**

---

## 6. Lược đồ con trỏ nguồn — chốt câu hỏi thiết kế số 2 của Tuần 4

Tuần 4 để treo ba câu hỏi thiết kế. Câu số 2 (*"mỗi rule ASP phải mang theo
`source(RuleID, Điều, Khoản)` — thiết kế lược đồ này trước khi viết rule đầu tiên"*) nay đã
chốt:

```prolog
rule_src(RuleId, Dieu, Khoan, Diem).      % con trỏ tĩnh: quy tắc ↔ điều khoản
why(Atom, RuleId).                        % vết động: vì sao Atom được suy ra
```

Ví dụ cụ thể — Điều 22 khoản 3:

```prolog
rule_src(r_b03, 22, 3, none).
passed(C)            :- g4(C,P), P >= 10.
why(passed(C), r_b03) :- g4(C,P), P >= 10.
```

Mỗi quy tắc suy diễn đi kèm **một quy tắc `why/2` cùng thân**. Cách này tốn công gấp đôi khi
viết, nhưng đổi lại chứng chỉ dựng được bằng **một truy vấn duy nhất** trên `why/2`, và tính
đầy đủ của con trỏ nguồn **kiểm được bằng máy** — đây chính là điều biến "mỗi rule có nguồn"
từ một lời hứa thành một bất biến.

Ba bất biến được `validate_rformal.py` kiểm ở mỗi lần chạy:

1. mọi `RuleId` xuất hiện trong `why/2` đều có `rule_src/4` — **không có kết luận mồ côi**;
2. mọi `rule_src/4` đều có bản ghi trong `r_formal_v1.json` kèm **trích nguyên văn** —
   truy được tới câu chữ, không chỉ tới số điều;
3. con trỏ (điều, khoản, điểm) trong `.lp` **trùng khớp** với JSON — hai bản ghi độc lập
   phải nhất quán, nên sửa một chỗ mà quên chỗ kia sẽ gãy ngay.

Kết quả hiện tại: 41 `rule_src`, 31 `RuleId` được dùng trong `why/2`, **6/6 kiểm tra đạt**.
(41 > 31 vì một số quy tắc đã khai báo nguồn nhưng phần suy diễn để lại cho Tuần 6–10.)

**Câu hỏi thiết kế số 1 của Tuần 4** (biểu diễn điểm nhị phân hay thang đầy đủ) cũng được
Tuần 5 trả lời một phần: Điều 24 buộc phải giữ **thang điểm đầy đủ** cho mọi học phần tham
gia ĐTBCTL/ĐTBCHK, nên tối ưu hoá "chỉ dùng passed/failed" chỉ áp dụng được cho các ràng
buộc T1–T4. Chi tiết ở mục 8.

---

## 7. Hồ sơ sản phẩm

```
CPA2_KhaoSat/
├── Tuan5_R_Formal_v1.md              tài liệu này
└── w5_rformal/
    ├── r_formal_v1.json              DANH MỤC CHÍNH — 73 bản ghi, mỗi bản ghi có
    │                                 trích nguyên văn + con trỏ điều/khoản/điểm +
    │                                 lớp F/P/N + trục dữ liệu + ánh xạ T1–T8
    ├── build_catalog.py              sinh JSON (danh mục là mã nguồn, không phải bảng tay)
    ├── qd3266_r_formal_v1.lp         41 quy tắc ASP + con trỏ nguồn + why/2
    ├── validate_rformal.py           kiểm bất biến nguồn · thống kê coverage · 17 ca kiểm thử
    ├── coverage_report.txt           kết quả chạy thật
    └── source/QD3266_ocr_raw.txt     văn bản OCR thô (để đối chiếu, KHÔNG dùng trực tiếp)
```

Chạy: `python3 validate_rformal.py` (cần `pip install clingo`).

### Bộ kiểm thử ngữ nghĩa — 17/17 đạt

Bộ kiểm thử cố ý tập trung vào **ngưỡng số và ca biên**, vì đó là chỗ Tuần 4 đã sai một lần.

| Ca | Nội dung | Vì sao quan trọng |
|---|---|---|
| C1, C2, C2b | ngưỡng cảnh báo 0,80 / 1,00 | khoá lỗi P-1 |
| C3, C4 | biên xếp trình độ 70 / 71 TC | lệch 1 TC đổi ngưỡng cảnh báo |
| C5 | điểm M vào TC nhưng không vào ĐTBCTL | khoá QD-01 ở mức mẫu số |
| C6, C7 | GDQP ≥ 5,0 **thang 10** — biên 4,9 / 5,0 | dễ nhầm với ngưỡng 2,00 thang 4 |
| C8, C9 | tốt nghiệp: đủ học vụ nhưng thiếu dữ kiện kỷ luật | xác nhận thiết kế ba trị |
| C10, C11 | giảm hạng khi điểm F > 5 % — biên đúng 5 % | *"vượt quá"* nghĩa là > chứ không ≥ |
| C12, C13 | trần 20 TC; **không có sàn** | khoá phát hiện P-2 |
| C14 | buộc thôi học chỉ ở mức "thuộc diện xem xét" | khoá QD-04 |
| C15, C16 | trần thời gian 8 năm; giảm 2 HK khi công nhận 18 TC | bảng mà OCR đánh mất |

Cặp C8/C9 đáng nói riêng: **cùng một hồ sơ, thêm đúng một dữ kiện** (`xac_nhan_ky_luat_sach`)
thì chân trị chuyển từ `UNKNOWN` sang `TRUE`. Đây là minh chứng nhỏ nhất và sạch nhất cho
luận điểm trung tâm của đề tài — hệ thống không đoán chỗ nó không biết, và biết chính xác nó
đang thiếu gì.

---

## 8. Đầu vào cho Tuần 6

Tuần 6 phải xây **Curriculum KB v1** với tiêu chí *"solver đọc được curriculum"*. Việc đã
được Tuần 5 dọn sẵn hoặc chặn lại:

1. **Thay mọi số thu nhỏ bằng số thật.** `kb.py` Tuần 4 dùng `MIN_CREDITS_TO_GRADUATE = 120`
   là số minh hoạ. QĐ3266 **không** quy định số này — nó thuộc CTĐT. Phải trích từ
   `ctdt/K49/69_7480201_CongNgheThongTin.pdf`. Đã xác nhận đúng: `MAX_CREDITS_PER_TERM = 20`
   (Điều 14 k.1) và `MIN_CGPA_TO_GRADUATE = 2,00` (Điều 32 k.1 đ.a). Đã bác bỏ:
   `WARNING_TERM_GPA = 1,20`.

2. **Bổ sung lớp `hp_dieu_kien`.** CTĐT phải đánh dấu GDQP&AN, GDTC, Ngoại ngữ căn bản, Tin
   học căn bản — vì bốn nhóm này có quy tắc kế toán riêng (Điều 7 k.6) và là điều kiện tốt
   nghiệp độc lập (Điều 32 k.1 đ.b). Lược đồ CTĐT hiện tại của niên luận **chưa có** trường
   này.

3. **Thu thập hai văn bản còn thiếu** (chặn T5 và một phần T6/T7):
   *Quy định xét miễn và công nhận điểm học phần* của ĐHCT; quy định điều kiện nhận đề tài
   LVTN/TLTN của Trường CNTT&TT.

4. **Biểu diễn điểm — quyết định đã rõ một nửa.** Điều 24 buộc giữ thang điểm đầy đủ cho mọi
   học phần vào ĐTBCTL/ĐTBCHK, nên rút gọn `passed/failed` chỉ dùng được cho T1–T4. Rủi ro
   bùng nổ tổ hợp nêu ở Tuần 4 mục 6 vẫn còn nguyên và phải đo lại ở n = 5, 10, 20 dữ kiện
   khuyết trên KB thật.

5. **Bất đối xứng ĐTBCHK / ĐTBCTL** (Điều 24 k.2 vs k.4) là bẫy tính toán nguy hiểm nhất đã
   gặp: ĐTBCHK **tính cả** điểm F và học phần điều kiện (trừ GDTC); ĐTBCTL **không tính** cả
   hai. Hai công thức gần giống nhau nhưng cho kết quả khác hẳn. Cần ca đối chứng bằng Z3 với
   số thực gốc, vì đây đúng là chỗ thủ thuật nhân-10 của ASP dễ lệch ở ca sát ngưỡng.

---

### Ghi chú kiểm chứng

- [x] Mọi quy tắc đã mã hoá đều có con trỏ tới điều/khoản — **kiểm tự động**, 6/6 bất biến đạt
- [x] 17/17 ca kiểm thử ngữ nghĩa đạt, tập trung vào ngưỡng số và ca biên
- [x] Mọi điều khoản có số hoặc bảng đã được **đối chiếu thủ công trên ảnh trang**, không tin OCR
- [x] Formalization Coverage và Executable Coverage được tính từ danh mục bằng mã, không đếm tay
- [ ] **Chưa đối chiếu với con người.** QD-03 (*"TC nợ đọng"*) và QD-08 (*"tương đương"*) là
      suy đoán của tác giả, phải xác nhận với Phòng Đào tạo hoặc GVHD trước khi vào luận văn
- [ ] Chưa thu thập *Quy định xét miễn và công nhận điểm học phần* — **chặn toàn bộ loại T5**
- [ ] Chưa kiểm quy tắc trên bảng điểm thật (mới chỉ hồ sơ thử tổng hợp); dự kiến Tuần 7
- [ ] Danh mục chưa được người thứ hai soát độc lập — phân loại F/P/N hiện là **đánh giá đơn
      người**, cần nêu như hạn chế của RQ1 hoặc bổ sung một vòng soát chéo với GVHD
