# TUẦN 2 — TAXONOMY HỌC VỤ v1.2

> **Cập nhật sau Tuần 6** (Curriculum KB v1 — khung CTĐT CNTT K49 chép đủ 78 dòng). Bốn thay đổi:
> 1. **T4 tách thành T4a / T4b / T4c.** T4b — *tiên quyết theo ngưỡng tín chỉ tích lũy*
>    ("≥80TC", "≥120TC", "≥125TC") — là dạng mới, không phải quan hệ giữa hai học phần.
> 2. **T3 có ba kiểu nhóm**, không chỉ "N môn": đếm môn, **đếm tín chỉ**, và **một nhánh**
>    ("10 TC AV hoặc PV", "6 TC CN1 hoặc CN2 hoặc CN3"). CTĐT K49 KHÔNG có nhóm đếm môn nào.
> 3. Ví dụ "10 chọn 2" và các mã CT203E, CT280, CT282E, CT299, CT291, CT295 **không có trong CTĐT
>    CNTT K49** (lấy nhầm từ dữ liệu AcademiQ) — đã thay bằng ví dụ thật.
> 4. **Luận văn không phải học phần bắt buộc**: CT550E (15 TC) nằm trong nhóm tự chọn 15 TC cùng
>    CT501E và 7 HP 3 TC. Ví dụ 1 của T6 thực chất là một nhóm T3 đếm tín chỉ.

> **Cập nhật sau Tuần 5** (R-Formal v1.2). Ba thay đổi, đều do đối chiếu toàn văn QĐ3266 và
> QĐ5339 phát hiện:
> 1. **Trục C: 6 → 7 trạng thái.** Ô `exempted` tách đôi thành `exempted_M` và `recognized`
>    (mục 3) — hai loại miễn có hệ quả kế toán khác nhau.
> 2. **Thêm Trục B′ — khả dụng dữ kiện** (mục 2.1): *hình thức hoá được* và *thi hành được*
>    là hai trục độc lập.
> 3. Bốn quyết định diễn giải treo ở mục 5 nay đã có nguồn — xem
>    `w5_rformal/PhuLuc_Quyet_dinh_dien_giai.md`.


**Sản phẩm:** Taxonomy v1 — phân loại các dạng ràng buộc học vụ
**Tiêu chí hoàn thành:** có ví dụ cho từng loại ✅
**Nguồn ví dụ:** CTĐT ngành CNTT ĐHCT (`academiq_ctdt_mysql.sql`), đồ thị tiên quyết (`core/constants.py: PREREQS`), hồ sơ sinh viên (`data/students/*.json`), QĐ3266/2024

---

## 0. Taxonomy này để làm gì

Mỗi loại ràng buộc dưới đây là **một khuôn hình thức hoá** (formalization pattern). Khi đọc một điều khoản trong quy chế hoặc một dòng trong CTĐT, ta phân nó vào một loại, rồi áp đúng khuôn đó để sinh quy tắc cho solver. Taxonomy chính là cầu nối giữa *văn bản hành chính tiếng Việt* và *chương trình logic chạy được*.

Ba trục phân loại:

- **Trục A — Loại ràng buộc:** 7 loại (T1–T7), phần chính của tài liệu này
- **Trục B — Khả năng hình thức hoá:** Formalizable / Partially-Formalizable / Not-Formalizable
- **Trục C — Trạng thái dữ kiện:** passed / failed / exempted / substituted / in_progress / unknown

---

## 1. TRỤC A — Bảy loại ràng buộc

### Bảng tổng quan

| Mã | Loại | Câu hỏi nó trả lời | Độ khó hình thức hoá | Rủi ro chính |
|---|---|---|---|---|
| **T1** | Mandatory | Môn này có bắt buộc không? | Thấp | Đồng nghĩa mã môn (CT190 vs CT190E) |
| **T2** | Elective | Môn tự chọn nào được tính? | Thấp | Ranh giới nhóm không rõ trong PDF |
| **T3** | N-of-M | Nhóm "15 TC" / "AV hoặc PV" đã đủ chưa? | Trung bình | Kiểu nhóm (môn / tín chỉ / một nhánh); một môn thuộc nhiều nhóm |
| **T4** | Prerequisite | Được đăng ký môn này chưa? | Trung bình | T4a tiên quyết · T4b ngưỡng tín chỉ · T4c song hành |
| **T5** | Exemption | Chứng chỉ này miễn được gì? | **Cao** | Miễn có tính vào CGPA không? |
| **T6** | Substitution | Môn A thay được môn B không? | **Cao** | Chênh lệch tín chỉ khi thay |
| **T7** | Graduation | Đủ điều kiện tốt nghiệp chưa? | **Cao** | Tổng hợp cả 6 loại trên + ngưỡng số |

---

### T1 — MANDATORY (học phần bắt buộc)

**Định nghĩa:** học phần mà sinh viên **buộc phải đạt** để hoàn thành CTĐT; không có phương án thay thế trong CTĐT.

**Khuôn hình thức:**
```
required(C).
violated_T1(C) :- required(C), not passed(C).
```

**Ví dụ thật (CTĐT CNTT K51):**

| Mã | Tên | TC | Ghi chú |
|---|---|---|---|
| CT101 | Lập trình căn bản A | 4 | Gốc của gần như mọi nhánh tiên quyết |
| CT177 | Cấu trúc dữ liệu | 3 | Nút thắt cổ chai của CTĐT |
| CT180 | Cơ sở dữ liệu | 3 | |
| ML014 | Triết học Mác – Lênin | 3 | Khối đại cương bắt buộc |

**Ca biên phải xử lý:** hồ sơ `sv_14w626u2.json` ghi `CT190` và `CT172` trong khi CTĐT ghi `CT190E`, `CT172E`. Bảng `CODE_ALIASES` đã có sẵn để chuẩn hoá — **nhưng đây chính là chỗ hệ thống dễ kết luận sai nhất**, và phải đưa vào bộ Adversarial.

---

### T2 — ELECTIVE (học phần tự chọn)

**Định nghĩa:** học phần được tính vào CTĐT nhưng sinh viên có quyền chọn học hay không. Chỉ ràng buộc ở cấp **nhóm** (xem T3), không ràng buộc ở cấp từng môn.

**Khuôn hình thức:**
```
elective(C).
{ take(C) } :- elective(C).       % chọn tự do
```

**Ví dụ thật (CTĐT CNTT K49, sửa ở Tuần 6):** CT478 Trung tâm dữ liệu (3), CT283 Hệ thống chịu lỗi (3), CT233 Điện toán đám mây (3), CT482 Xử lý dữ liệu lớn (3), CT210 Thị giác máy tính (3), CT219 Xử lý ngôn ngữ tự nhiên (3), CT312 Khai khoáng dữ liệu (3) — và cả **CT550E Luận văn tốt nghiệp (15)**, CT501E Tiểu luận tốt nghiệp (6), cùng một ô gộp "15 TC".

**Ca biên:** một học phần có thể là `elective` ở ngành này và `required` ở ngành khác. Ví dụ CT204E *An toàn và bảo mật thông tin* là `required` với CNTT nhưng nằm nhóm tự chọn của ngành khác → **loại ràng buộc phụ thuộc cặp (ngành, khoá)**, không phụ thuộc mã môn.

---

### T3 — N-OF-M (chọn N trong M)

**Định nghĩa:** trong một nhóm gồm M học phần, sinh viên phải đạt **ít nhất N** môn (hoặc ít nhất K tín chỉ).

**Khuôn hình thức (dạng đếm môn):**
```
group_ok(G) :- group_min(G,N), #count{ C : in_group(G,C), passed(C) } >= N.
```
**Khuôn hình thức (dạng đếm tín chỉ):**
```
group_ok(G) :- group_min_credits(G,K),
               #sum{ CR,C : in_group(G,C), passed(C), course(C,CR) } >= K.
```

**Khuôn hình thức (dạng MỘT NHÁNH — thêm ở Tuần 6):** ô CTĐT ghi "A hoặc B"; tín chỉ KHÔNG cộng dồn qua nhánh.
```
dat_nhanh(G,B) :- nhanh(G,B), nhom_min_tc(G,N),
                  #sum{ CR,C : thuoc_nhanh(G,B,C), passed(C), course(C,CR) } >= N.
dat_nhom(G)    :- nhom_kieu(G,mot_nhanh), dat_nhanh(G,_).
```

**Ví dụ thật (CTĐT CNTT K49 — sửa ở Tuần 6; bản trước dùng nhóm "10 chọn 2" không có thật):**

| Nhóm | Kiểu | Thành viên | Yêu cầu |
|---|---|---|---|
| GDTC | tín chỉ | TC100 (1+1+1) | 3 TC |
| Ngoại ngữ | **một nhánh** | AV: XH023–025, XH031–033 · PV: FL001–003, FL007–009 | 10 TC trong **một** ngoại ngữ |
| Xã hội | tín chỉ | ML007, XH028, XH011, XH012, XH014, KN001E, KN002E | 2 TC |
| Chuyên ngành | **một nhánh** | CN1: CT211+CT297 · CN2: CT449+CT484 · CN3: CT522+CT279 | 6 TC trong **một** cặp |
| Tốt nghiệp | tín chỉ | CT550E (15), CT501E (6), CT478, CT283, CT233, CT482, CT210, CT219, CT312 | 15 TC |

Không nhóm nào đếm theo số môn. Cài đặt và kiểm thử: `w6_curriculum/curriculum_schema.lp`,
`validate_curriculum.py` (I4, I5, I9).

**Ba ca biên bắt buộc đưa vào bộ test:**
1. **Chồng nhóm** — một môn thuộc hai nhóm tự chọn: có được tính hai lần không? (Mặc định: **không**, phải thêm ràng buộc phân hoạch.)
2. **Đếm môn vs đếm tín chỉ** — nhóm "chọn 2 môn" khác nhóm "tích luỹ 6 tín chỉ" khi các môn khác tín chỉ.
3. **Dư thừa** — sinh viên đạt 4/10 môn: 2 môn tính vào nhóm, 2 môn dư đi đâu? (vào tổng tín chỉ tự do, hay bỏ?)

---

### T4 — PREREQUISITE (tiên quyết)

**Định nghĩa:** ràng buộc **thứ tự thời gian** giữa hai học phần.

**Bốn biến thể phải phân biệt rõ — đây là chỗ CTĐT tiếng Việt hay nhập nhằng:**

| Biến thể | Nghĩa | Khuôn hình thức |
|---|---|---|
| **T4a Tiên quyết** (prerequisite) | Phải **tích lũy** P trước khi học C (QĐ3266 Đ.7 k.4) | `:- at(C,K1), prereq(C,P), at(P,K2), K2 >= K1.` |
| **T4b Ngưỡng tín chỉ** *(mới, Tuần 6)* | Phải **tích lũy ≥ N TC** trước khi học C — không gắn với học phần nào | `thieu_tc(C,D) :- tien_quyet_tc(C,N), tc_tich_luy(T), T < N, D = N-T.` |
| **T4c Song hành** (co-requisite) | Học P **trước hoặc cùng kỳ** với C (QĐ3266 Đ.7 k.5) | `K2 <= K1` thay vì `K2 < K1` |
| Học trước (pre-study) | Đã học P (kể cả rớt) | **QĐ3266 không định nghĩa** — không dùng |

**T4b — vì sao là loại riêng:** "≥120TC" không phải cạnh trong đồ thị học phần; nó là ngưỡng trên
*tiến độ tích lũy*, nên phụ thuộc toàn bộ bảng điểm chứ không phụ thuộc một môn. Hệ quả cho lập
kế hoạch (RQ3): T4b biến bài toán xếp lịch thành bài toán có **ràng buộc tích luỹ theo thời gian**,
không giải được chỉ bằng sắp xếp tô-pô. Trong CTĐT CNTT K49 có 4 học phần T4b:

| Mã | Tên | TC | Ngưỡng |
|---|---|---|---|
| CT466E | Niên luận - CNTT | 3 | ≥ 80 TC |
| CT550E | Luận văn tốt nghiệp - CNTT | 15 | ≥ 120 TC |
| CT501E | Tiểu luận tốt nghiệp - CNTT | 6 | ≥ 120 TC |
| CT518E | Thực tập doanh nghiệp - CNTT | 5 | ≥ 125 TC, **chỉ mở HK III** |

R-Formal v1.4 bỏ sót T4b khi xét quyền đăng ký (lỗi L3 của Tuần 6: kết luận CT550E "được đăng ký"
với SV có 30 TC) — đã sửa ở v1.5.

**T4c — ví dụ thật:** chuỗi ngoại ngữ XH023 → XH024 → … → XH033 nằm ở cột **song hành**, không phải
tiên quyết; CT182 có tiên quyết CT176 và song hành CT180.

**Ví dụ thật T4a (CTĐT CNTT K49, đối chiếu lại ở Tuần 6):**

```
CT177 ← CT101              Cấu trúc dữ liệu ← Lập trình căn bản A
CT174 ← CT177              Phân tích & thiết kế thuật toán ← Cấu trúc dữ liệu
CT175 ← CT177              Lý thuyết đồ thị ← Cấu trúc dữ liệu
CT180 ← CT177              Cơ sở dữ liệu ← Cấu trúc dữ liệu
CT271E ← CT174, CT176      Niên luận cơ sở ← TKTT VÀ OOP             (tiên quyết kép)
CT293 ← CT112 ← CT178 ← CT173   Mạng & TTDL ← Mạng ← HĐH ← KTMT      (chuỗi dài)
ML021 ← ML019 ← ML018 ← ML016 ← ML014   chuỗi lý luận chính trị — dài nhất CTĐT (5)
```
*(Bản trước ghi "CT182 ← CT176, CT180" và "CT282E ← CT294 ← CT190E" — sai: CT180 là song hành
của CT182; CT294 không có tiên quyết; CT282E không có trong CTĐT K49.)*

**Vì sao T4 là trái tim của truy vấn phản thực:** đồ thị tiên quyết biến câu hỏi *"rớt CT177 thì trễ mấy kỳ?"* thành bài toán **đường đi dài nhất trên DAG dưới ràng buộc trần tín chỉ** — không phải hỏi–đáp. CT177 có 3 môn kế thừa trực tiếp và kéo theo cả CT182, nên rớt nó tốn ít nhất 1 kỳ, thường là 2.

**Ca biên:** CTĐT thay đổi giữa các khoá → CT172 (K48) và CT172E (K51) có ràng buộc tiên quyết khác nhau. KB phải khoá theo `(ngành, khoá)`.

---

### T5 — EXEMPTION (miễn học phần)

**Định nghĩa:** sinh viên được **công nhận đạt** một học phần mà không cần học, do có chứng chỉ ngoài hoặc kết quả đã tích luỹ trước.

**Khuôn hình thức:**
```
exempted(C)  :- has_certificate(Cert), exempts(Cert,C), valid(Cert).
passed(C)    :- exempted(C).
% KHÁC BIỆT MẤU CHỐT: môn miễn KHÔNG có điểm số
:- exempted(C), grade(C,_).
```

**Ví dụ thật:** hồ sơ SV-C có `TN010 (Xác suất thống kê)` được miễn bằng chứng chỉ tương đương. Trong CTĐT ĐHCT dạng phổ biến nhất là **miễn học phần ngoại ngữ (FL...) bằng chứng chỉ IELTS/TOEIC** và **miễn tin học căn bản bằng chứng chỉ ứng dụng CNTT**.

**Vấn đề khó nhất — và là một đóng góp nhỏ nhưng thật của luận văn:**

> Học phần được miễn **có tính vào CGPA không**, và **có tính vào tổng tín chỉ tích luỹ không**?

Đây là hai câu hỏi độc lập, cho **bốn tổ hợp**, và câu trả lời quyết định trực tiếp con số CGPA in ra cho sinh viên. Quy chế thường chỉ nói *"được công nhận"* mà không nói rõ. Prototype hiện tại chọn: **tính vào tín chỉ, KHÔNG tính vào CGPA** — và điều này phải được **đối chiếu với QĐ3266 và xác nhận với Phòng Đào tạo**, không được đoán.

Đây chính là dạng điều khoản **Partially-Formalizable**: hình thức hoá được, nhưng cần một quyết định diễn giải phải ghi nhận công khai trong KB.

> **Cập nhật Tuần 5 — hai điều chỉnh quan trọng cho T5.**
> (1) Câu trả lời đã có: học phần miễn bằng chứng chỉ mang **điểm M** → vào tín chỉ tích luỹ,
> **không** vào ĐTBCTL; còn học phần **công nhận điểm** thì **có** vào ĐTBCTL (QĐ5339 Đ.3 k.11).
> (2) **Miễn không tự động.** QĐ5339 Điều 2 khoản 6: phải có đơn của SV → Tổ Xét miễn →
> Hội đồng cấp Trường. Nên câu *"Chứng chỉ IELTS của em miễn được môn nào?"* phải trả lời là
> *"em **đủ điều kiện nộp đơn xin miễn** các học phần …"*, không phải *"em đã được miễn …"*.
> Trả lời vế sau là **nói sai** — và là ca đối kháng mạnh nhất tìm được cho H2, vì nó là
> tình huống thường ngày chứ không phải dữ liệu khuyết bất thường.
> Bảng tra chứng chỉ ↔ bậc nằm ở Phụ lục 1 QĐ5339: **Khoá 45 trở về sau cần bậc 3**
> (IELTS 4.5 / TOEIC 450 / TOEFL iBT 45 / chứng chỉ C của ĐHCT).

---

### T6 — SUBSTITUTION (học phần thay thế)

**Định nghĩa:** học phần A được chấp nhận **thay cho** học phần B trong CTĐT.

**Khuôn hình thức:**
```
substitutes(A,B).
passed(B) :- passed(A), substitutes(A,B).
% ràng buộc dùng một lần
:- substitutes(A,B1), substitutes(A,B2), B1 != B2, used(A,B1), used(A,B2).
```

**Ba ví dụ thật cần xử lý:**

1. **Luận văn ↔ học phần thay thế.** Sinh viên không đủ điều kiện làm luận văn tốt nghiệp (**CT550E, 15 TC** — bản trước ghi nhầm CT466E 10 TC) thì học nhóm học phần thay thế. *Sửa ở Tuần 6:* trong CTĐT K49 đây **không phải T6** mà là một nhóm T3 đếm tín chỉ — CT550E, CT501E và 7 HP 3 TC nằm chung ô "15 TC"; ràng buộc là đủ 15 TC trong nhóm (khớp QĐ3266 Đ.31 k.3).
2. **Niên luận chuyển ngành.** CT271E (Niên luận cơ sở – CNTT) và CT201E (Niên luận cơ sở – KHMT) là hai mã khác nhau cho cùng vai trò; sinh viên chuyển ngành đã học một trong hai.
3. **Học phần đổi mã giữa các khoá.** CT172 → CT172E, CT190 → CT190E. Về mặt hành chính là "đổi mã", về mặt KB là quan hệ thay thế hai chiều.

**Ca biên khó:** **chênh lệch tín chỉ.** Nếu A có 3 TC thay cho B có 4 TC thì tổng tín chỉ tích luỹ tính theo A hay theo B? Và điểm của A có vào CGPA ở vị trí của B không? Cần một quyết định diễn giải, ghi rõ trong KB.

---

### T7 — GRADUATION (điều kiện tốt nghiệp)

**Định nghĩa:** ràng buộc **tổng hợp** — hợp của T1…T6 cộng thêm các ngưỡng số học.

**Khuôn hình thức:**
```
graduate :- cond_required, cond_elective, cond_credits, cond_cgpa,
            cond_thesis, cond_certificates, cond_discipline.
```

**Các điều kiện thành phần (bản làm việc — phải đối chiếu QĐ3266):**

| Điều kiện | Nội dung | Loại |
|---|---|---|
| `cond_required` | Đạt mọi học phần bắt buộc | T1 |
| `cond_elective` | Đủ mọi nhóm N-of-M | T2, T3 |
| `cond_credits` | Tổng tín chỉ tích luỹ ≥ yêu cầu CTĐT | ngưỡng số |
| `cond_cgpa` | CGPA ≥ 2,00 | ngưỡng số |
| `cond_thesis` | Hoàn thành luận văn **hoặc** nhóm học phần thay thế | T6 |
| `cond_certificates` | Đủ chứng chỉ ngoại ngữ, GDQP, GDTC | T5 |
| `cond_discipline` | Không đang trong thời gian kỷ luật | **Not-Formalizable** — dữ liệu không có trong bảng điểm |

**Kiểm chứng thật (prototype Tuần 4, đối chiếu chéo Z3 và clingo):**

| Hồ sơ | Tình huống | Kết luận | Đúng như mong đợi |
|---|---|---|---|
| SV-A | đủ mọi điều kiện | `TRUE` | ✅ |
| SV-B | thiếu điểm 2 môn tự chọn | `UNKNOWN` + chỉ ra thiếu CT312, CT282E *(Tuần 6: CT282E không có trong CTĐT K49, prototype đã đổi sang CT219)* | ✅ **đây là hành vi baseline không có** |
| SV-C | rớt CT177, mới học 6 môn | `FALSE` + hỏng 3 điều kiện: required, N-of-M, credits | ✅ |

**Vì sao `cond_discipline` quan trọng dù không hình thức hoá được:** nó buộc kết luận tốt nghiệp **luôn phải ở mức `UNKNOWN` trên trục kỷ luật**, trừ khi có dữ kiện xác nhận. Một hệ thống trung thực phải nói *"về mặt học vụ em đủ điều kiện; phần kỷ luật hệ thống không có dữ liệu"* thay vì nói gọn *"em đủ điều kiện tốt nghiệp"*. Đây là minh hoạ đẹp cho luận điểm ba trị.

---

## 2. TRỤC B — Khả năng hình thức hoá

Đây là trục sẽ trở thành **đóng góp RQ1**: một phân loại học về khả năng hình thức hoá của quy chế học vụ đại học Việt Nam.

| Nhãn | Định nghĩa | Xử lý trong CPA² | Ví dụ |
|---|---|---|---|
| **F — Formalizable** | Dịch trọn vẹn sang logic thực thi, không mất thông tin | Solver quyết định | *"Điểm trung bình tích luỹ đạt từ 2,00 trở lên"* |
| **P — Partially Formalizable** | Dịch được phần lõi, còn tham số/diễn giải phải chốt bằng quyết định của con người | Hình thức hoá + **ghi rõ quyết định diễn giải** trong KB, hiển thị cho người dùng | *"Học phần được miễn được công nhận"* (miễn có vào CGPA không?) |
| **N — Not Formalizable** | Chứa yếu tố thẩm quyền, dữ liệu không tồn tại, hoặc ngôn ngữ mở | Trả `UNKNOWN` + trích nguyên văn điều khoản + hướng dẫn liên hệ | *"Trường hợp đặc biệt do Hiệu trưởng quyết định"* |

**Ba nguyên nhân khiến một điều khoản rơi vào N** (giả thuyết cần kiểm bằng dữ liệu ở Tuần 5):

1. **Thẩm quyền mở** — kết quả phụ thuộc quyết định hành chính của một con người.
2. **Dữ kiện không tồn tại** — hệ thống không có và không thể có dữ liệu (kỷ luật, hoàn cảnh gia đình).
3. **Ngôn ngữ mơ hồ có chủ ý** — *"trong trường hợp cần thiết"*, *"theo quy định hiện hành"* (con trỏ tới văn bản khác).

**Chỉ số sẽ báo cáo (RQ1):** `Formalization Coverage = |F| / (|F|+|P|+|N|)`, kèm phân tích lý do cho từng điều khoản thuộc N.

### 2.1. TRỤC B′ — khả dụng dữ kiện *(bổ sung ở Tuần 5)*

Trục B trộn hai câu hỏi khác nhau. Phải tách:

| Câu hỏi | Về cái gì | Trục |
|---|---|---|
| *Điều khoản này có dịch được sang logic không?* | **văn bản** | B (F/P/N) |
| *Hệ thống có dữ liệu để chạy quy tắc đó không?* | **dữ liệu** | **B′ (có/không)** |

Ca buộc phải tách: QĐ3266 Điều 19 — *"phải tham dự tối thiểu 80% số tiết đối với các học
phần lý thuyết"*. Ngưỡng hoàn toàn rõ, không thẩm quyền mở, không ngôn ngữ mơ hồ → **F trên
trục B**. Nhưng dữ liệu điểm danh không có trong bảng điểm → **"không" trên trục B′**, nên
hệ thống buộc phải trả `UNKNOWN`. Xếp nó vào N là sai (nó không kháng lại việc hình thức
hoá); xếp F rồi im lặng cũng sai (hệ thống sẽ tưởng mình kết luận được).

Hệ quả: phải báo cáo **hai** chỉ số, không một.

- `Formalization Coverage` trả lời câu hỏi của RQ1: quy chế dịch được bao nhiêu sang logic.
- `Executable Coverage = |F ∧ có dữ liệu| / (|F|+|P|+|N|)` trả lời: hệ thống thật kết luận
  được bao nhiêu. Đây mới là con số quyết định trần Coverage ở đường cong
  Coverage–Selective Accuracy của Tuần 22.

Ở R-Formal v1.2: 81,7 % so với 59,2 %. Chênh lệch 22,5 điểm phần trăm chính là phần mà mọi
baseline sẽ trả lời tự tin còn CPA² sẽ từ chối — một dự đoán định lượng cho H2, lập **trước**
khi chạy thí nghiệm.

**Cảnh báo khi báo cáo con số.** Lớp P không phải lúc nào cũng là thuộc tính bền của điều
khoản. Có ba loại: P do **câu chữ** (thẩm quyền mở, ngôn ngữ mơ hồ) là bền; P do **kho văn
bản chưa đủ** và P do **xung đột chưa phân giải** là thuộc tính tạm thời của trạng thái
nghiên cứu, sẽ biến mất khi đọc thêm hoặc hỏi thêm. Cùng một quy chế đã cho ba con số khác
nhau trong một tuần (79,6 % → 78,9 % → 81,7 %); luận văn phải nói rõ con số được đo ở trạng
thái nào.

---

## 3. TRỤC C — Trạng thái dữ kiện

Không phải nhị phân đạt/không đạt. Sáu trạng thái, và mỗi trạng thái ảnh hưởng khác nhau đến ba đại lượng:

| Trạng thái | Tính là "đạt"? | Vào tổng tín chỉ? | Vào ĐTBCTL? | Nguồn |
|---|---|---|---|---|
| `passed` | ✅ | ✅ | ✅ | Bảng điểm, điểm ≥ D (QĐ3266 Đ.22 k.3) |
| `failed` | ❌ | ❌ | ❌ vào ĐTBCTL, ✅ vào ĐTBCHK | Bảng điểm, điểm F (QĐ3266 Đ.24 k.2 và k.4) |
| `exempted_M` | ✅ | ✅ | ❌ | Miễn học phần **điều kiện** bằng chứng chỉ → **điểm M** (QĐ3266 Đ.22 k.5 đ.a; QĐ5339 Đ.3 k.4) |
| `recognized` | ✅ | ✅ | ✅ | **Công nhận điểm** học phần từ CTĐT đã học — mang điểm số quy đổi (QĐ5339 Đ.3 k.11) |
| `substituted` | ✅ | ✅ theo học phần **được miễn** | ✅ theo điểm gộp có trọng số | Quyết định thay thế — T6 (QĐ5339 Đ.3 k.3) |
| `in_progress` | ⏳ | ❌ chưa | ❌ chưa | Đang học kỳ hiện tại |
| `unknown` | **❓** | **❓** | **❓** | Điểm chưa cập nhật, OCR hỏng, môn không nhận diện được, hoặc **điểm I chưa quá hạn** (QĐ3266 Đ.22 k.5 đ.b) |

**Vì sao phải tách `exempted` làm đôi** (sửa ở Tuần 5). Bản v1 giả định mọi học phần được
miễn đều nằm ngoài ĐTBCTL. Sai. QĐ5339 Điều 3 khoản 11 nói: *"**Trừ các học phần điều kiện
và học phần có điểm M**, kết quả điểm xét miễn học phần **được sử dụng để tính điểm trung
bình chung tích lũy**."* Hai loại miễn cho **hai giá trị ĐTBCTL khác nhau** trên cùng một
bảng điểm — mà ĐTBCTL quyết định cả điều kiện tốt nghiệp lẫn hạng tốt nghiệp. Đây không
phải chi tiết kế toán vụn vặt.

**Một trạng thái thứ tám cần cân nhắc — `du_dk_xin_mien`.** QĐ5339 Điều 2 khoản 6 cho thấy
miễn **không tự động**: có chứng chỉ chỉ tạo ra quyền nộp đơn, còn `exempted_M` chỉ phát
sinh sau quyết định phê duyệt của Tổ Xét miễn. Hiện KB mô hình hoá bằng một vị từ riêng
(`du_dk_xin_mien/1`) chứ chưa đưa vào Trục C, vì nó là trạng thái của **hồ sơ**, không phải
của **học phần**. Cần chốt ở Tuần 7 khi xây Student Fact Model.

**Đây là bảng làm phát sinh ngữ nghĩa ba trị.** Mỗi ô `❓` là một biến tự do trong bài toán suy diễn. Solver sinh mọi thế giới khả dĩ cho các biến này:

- Kết luận đúng trong **mọi** thế giới → `TRUE`
- Sai trong **mọi** thế giới → `FALSE`
- Khác nhau giữa các thế giới → `UNKNOWN`, và tập biến gây ra sự khác biệt **chính là danh sách dữ kiện còn thiếu** trả về cho sinh viên

Đã kiểm chứng chạy được với cả clingo (cautious/brave consequences) và Z3 (entailment hai chiều) — xem Tuần 4.

---

## 4. Ma trận độ phủ: taxonomy × truy vấn thật

| Câu hỏi sinh viên | T1 | T2 | T3 | T4 | T5 | T6 | T7 |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| "Em còn thiếu môn gì?" | ✔ | | ✔ | | ✔ | ✔ | |
| "Em còn thiếu bao nhiêu tín chỉ?" | ✔ | ✔ | ✔ | | ✔ | ✔ | ✔ |
| "Kỳ này em đăng ký CT180 được chưa?" | | | | ✔ | | | |
| "Em đủ điều kiện làm luận văn chưa?" | ✔ | | ✔ | | | ✔ | ✔ |
| "Chứng chỉ IELTS của em miễn được môn nào?" | | | | | ✔ | | |
| "Nếu em rớt CT177 thì trễ mấy kỳ?" | ✔ | | ✔ | ✔ | | | ✔ |
| "Em đủ điều kiện tốt nghiệp chưa?" | ✔ | ✔ | ✔ | | ✔ | ✔ | ✔ |

Bảy loại phủ hết bảy câu hỏi trọng tâm → **taxonomy v1 đủ dùng cho vòng đầu**.

---

## 5. Việc còn lại của Tuần 2 → chuyển sang Tuần 5

- [x] Đối chiếu từng loại T1–T7 với **số điều/khoản cụ thể** — xong ở Tuần 5: 71 đơn vị
      trong miền, mỗi đơn vị có con trỏ `(văn bản, điều, khoản, điểm)` và trích nguyên văn
- [x] Bổ sung **T8 — Academic Warning**: QĐ3266 Điều 18 quy định thành nhóm riêng, không
      phải hệ quả của ngưỡng GPA. Đã đưa vào danh mục (10 đơn vị)
- [x] Chốt 4 quyết định diễn giải treo: **miễn↔ĐTBCTL** và **miễn↔tín chỉ** đóng bằng
      QĐ3266 Đ.22 k.5 đ.a + QĐ5339 Đ.3 k.11 (QD-01, đã sửa); **thay thế↔tín chỉ** và
      **thay thế↔điểm** đóng bằng QĐ5339 Đ.3 k.3 (QD-10). Toàn bộ 11 quyết định nay nằm ở
      `w5_rformal/PhuLuc_Quyet_dinh_dien_giai.md`
- [x] **Tuần 6:** bổ sung T4b (tiên quyết theo ngưỡng tín chỉ) và T4c (song hành) vào T4;
      thay ví dụ "10 chọn 2" bằng 5 nhóm thật của CTĐT K49 (3 kiểu nhóm)
- [ ] Xây bộ test riêng cho T3 (N-of-M) — tiêu chí hoàn thành của Tuần 8
      *(đã có 3 ca ở `w6_curriculum/validate_curriculum.py`: I4 thiếu nhóm, I5 trộn nhánh, I9 chéo cặp)*
- [ ] **Mới:** chốt vị trí của `du_dk_xin_mien` (trạng thái hồ sơ hay trạng thái học phần)
      khi xây Student Fact Model ở Tuần 7
- [ ] **Mới:** nhãn F/P/N mới do một người gán — cần soát chéo, dùng
      `w5_rformal/make_review_kit.py`
