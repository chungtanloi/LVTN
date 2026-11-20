# TUẦN 24 — HAI Ý ĐỊNH TƯ VẤN MỚI + PHÁT HÀNH DEMO

**Giai đoạn:** Hoàn thiện (Tuần 24/24) · **Mục tiêu:** demo end-to-end chạy ổn định; bổ sung hai câu hỏi tư vấn sinh viên hay hỏi
**Sản phẩm:** `w24_muc_tieu/` (`8785ce0`), `w24_cuoi_khoa/` (`6afaa6a`), bản sửa đóng gói và gắn nguồn (`34aa001`), phát hành Render + Vercel (`069d5cf`, `db3e84f`)
**Phạm vi:** hai ý định nằm **ngoài benchmark** đã đóng băng. Số liệu đánh giá Tuần 20–23 **không đổi**: chạy lại G-Truth / Q-Noise / OCR-Noise × dev/test sau mỗi tính năng (`_sau_muc_tieu`, `_sau_cuoi_khoa`) → 0 ca đổi kết luận hay câu hỏi bổ sung.

> Báo cáo đa ngành cùng tuần (khảo sát 9 CTĐT) ở `Tuan24_Da_nganh.md`, do phiên khác thực hiện.

---

## 1. Mục tiêu hạng tốt nghiệp (`w24_muc_tieu/`)

**Câu hỏi:**
- "Em cần trung bình bao nhiêu để tốt nghiệp loại giỏi?"
- "Kỳ tới em học 18 tín chỉ thì cần trung bình bao nhiêu để tốt nghiệp loại giỏi?"

**Cách làm.** Đây là **phép tính chính xác** trên các định nghĩa đã hình thức hoá, không phải dự đoán, và không thêm quy định mới:
- ĐTBCTL = `tl_tu / tl_mau` (R-B10).
- Ngưỡng hạng so hữu tỉ theo cận dưới (R-F06, QD-14).
- Hạ một mức hạng xuất sắc/giỏi (R-F07, R-F07b).

Gọi N là tổng điểm hiện tại, D là số TC đang tính điểm, X là số TC sẽ học, L là cận dưới của hạng. Để đạt **từ hạng X trở lên** cần tổng điểm S trên X TC thoả `10·(N + S) ≥ L·(D + X)`, với S nằm trong [10X, 40X] (từ toàn D đến toàn A).

**X lấy từ đâu:**
- Câu hỏi nêu số TC → dùng đúng số đó, tối đa 20 TC/HK (QĐ3266 Điều 14 khoản 1).
- Không nêu → số TC **tối thiểu** còn phải học có tính điểm: 161 − 21 (học phần điều kiện, CQ-05) − số TC không điều kiện đã tích lũy.

**Ba trị theo khả thi trên mọi thế giới:**

| Kết quả | Khi nào |
|---|---|
| TRUE | đạt được ở mọi thế giới |
| FALSE | không thể ở mọi thế giới |
| UNKNOWN | tuỳ dữ kiện; nêu từng kịch bản, kèm dữ kiện quyết định (thường là TC từng bị F, kỷ luật cấp Trường — Đ34 k2) |

Riêng khi không nêu số TC, "không thể vì điểm" chỉ đúng với số TC tối thiểu, vì học thêm thì kết quả khác. Trường hợp này trả UNKNOWN và hỏi số TC dự định. Ngoại lệ: xuất sắc bị hạ bậc thì học thêm cũng không đổi, nên vẫn FALSE.

**Ví dụ (hồ sơ giả lập `sv_lvtn`, ĐTBCTL 3,13 trên 140 TC, học thêm 18 TC):**

| Mục tiêu | Kết quả |
|---|---|
| từ giỏi trở lên, đã khai báo không F / không kỷ luật | TRUE — cần trung bình tối thiểu 3,70, ví dụ toàn A |
| từ giỏi trở lên, chưa khai báo | UNKNOWN — không hạ: 3,70; bị hạ: không thể; hỏi hai dữ kiện |
| từ xuất sắc trở lên | FALSE — toàn A cũng chỉ tới 3,23 < 3,60 |
| từ khá trở lên | TRUE — chỉ cần đạt mọi học phần (từ D trở lên) |

**Kiểm thử:** `validate_muc_tieu.py`, **45 kiểm tra**, viết trước rồi mới viết code.
- **A — số học ASP:** 14 ca tính tay, gồm biên toàn A (7 TC cần 284 > 280; 8 TC cần 316), biên "chỉ cần qua" (S = 10X), học phần điều kiện, hạ bậc và D = 0.
- **B — parser:** 7 ca dương, 11 ca âm.
- **C — hồi quy:** 375 câu hỏi benchmark không câu nào bị bắt sang ý định mới.
- **D — tích hợp:** 12 ca; riêng D5 dùng oracle Python độc lập với file `.lp`.

**Review ECC:** 2 lỗi cao, 3 trung bình, 4 thấp; đã sửa mọi lỗi cao và trung bình, mỗi lỗi có ca hồi quy fail trước khi sửa.
- **H1:** "không thể ở mọi thế giới" từng trả UNKNOWN và hỏi dữ kiện vô ích → nay ba trị theo khả thi.
- **H2:** FALSE dựa trên số TC tối thiểu → như mô tả ở trên.
- **M1:** D = 0 từng được kết luận "đã đạt".
- **M2:** nhãn kịch bản.
- **M3:** ghi rõ "từ … trở lên", khác QD-15 (đúng hạng).

## 2. So sánh ba phương án nhóm tốt nghiệp (`w24_cuoi_khoa/`)

**Câu hỏi:**
- "Em nên làm luận văn hay tiểu luận?"
- "Em có nên làm luận văn không?"
- "So sánh luận văn và tiểu luận"
- "… khác nhau gì?"

**Cách làm.** Không thêm luật mới; dữ kiện lấy từ KB và từ module điều kiện w18. Nhóm tốt nghiệp của CTĐT cần **tổng ≥ 15 TC** trong các học phần của nhóm. Có ba phương án:
1. **Luận văn:** CT550E (15 TC).
2. **Tiểu luận:** CT501E (6 TC) + học phần thay thế trong nhóm cho đủ 15 TC.
3. **Không làm luận văn hay tiểu luận:** chỉ học học phần thay thế (QĐ3266 Điều 31 khoản 3, R-F05; khớp test I3 của w6).

Với từng hồ sơ, câu trả lời nêu:
- **Điều kiện nhận đề tài:** chỉ là ngưỡng TC của CTĐT (QD-12), hoặc đã khai báo hình thức khác.
- **Đã đạt:** lấy từ chính học phần. Đã đạt hình thức kia → "không áp dụng" (Điều 31: một trong ba hình thức); nhóm đã đủ → "không còn cần".
- **Số TC còn thiếu** theo từng phương án.
- **Học phần đủ điều kiện tiên quyết/song hành**, có ghi chú "chưa xét học kỳ mở và thời gian đăng ký".
- **Học phần chưa chắc** (điểm chưa chắc) không bị liệt kê là đăng ký được.

Hệ thống **không khuyên chọn** phương án nào: "lựa chọn là của bạn" (bài học P19-1: đủ điều kiện ≠ nên làm).

**Kiểm thử:** `validate_cuoi_khoa.py`, **33 kiểm tra**. Oracle **độc lập với KB**: CTĐT JSON + hồ sơ.
- **B — parser:** 6 ca dương, 10 ca âm.
- **C — hồi quy:** benchmark không bị ảnh hưởng.
- **D — hồ sơ thử:** đã làm luận văn; 146 TC; đã có 2 học phần thay thế; 119 TC; chỉ đạt tiểu luận; chỉ học học phần thay thế; đã khai báo tiểu luận.
- **E — đi qua lớp gắn nguồn của API** (mục 3).

**Review ECC:** 2 lỗi cao, 4 trung bình, 4 thấp.
- **H1:** bỏ sót phương án (3), đã sửa.
- **H2:** khẳng định sai "luận văn đã hoàn thành" khi mới đạt tiểu luận, đã sửa.
- M1, M2, M3 và L3 đã sửa.
- **Lỗi tự phát hiện khi đọc câu trả lời mẫu** (test bản đầu không bắt): hồ sơ chỉ đạt tiểu luận (6/15 TC) bị báo "nhóm tốt nghiệp đã đủ". Đã siết test cho đỏ rồi mới sửa.
- **Chưa sửa (ghi nhận):**
  - **M4:** câu so sánh mang verdict TRUE (thông tin, không phải mệnh đề).
  - **L2:** giao diện web chưa hiện con trỏ trang/dòng của CTĐT.

## 3. Phát hành demo và hai lỗi phát hiện trước khi deploy

Chạy thử qua **đúng đường của API** (`w14 grounded_answer.tra_loi`) trước khi deploy phát hiện hai lỗi, đã sửa trong `34aa001`:
1. **Dockerfile chỉ chép các file được liệt kê, nên thiếu `w24_*`.** Deploy nguyên trạng thì hai ý định mới lỗi ImportError trên Render.
2. **Lỗi có sẵn từ Tuần 18:** các bước chứng chỉ của w18 ghi `source.van_ban` là chuỗi tự do. Lớp gắn nguồn không khớp được passage, nên câu **"Em đủ điều kiện làm luận văn chưa?" bị BLOCKED mỗi khi sinh viên đủ điều kiện**, đúng trường hợp phổ biến nhất. Test w18 và w24 không đi qua lớp này nên không bắt được.
   - Đã sửa: nguồn chuẩn theo catalog.
   - Thành viên nhóm chuyển thành **dữ kiện CTĐT** (`du_kien_ctdt`, passage `ctdt_k49:<mã>`), không còn là bước luật.

**Kết quả phát hành (chi tiết ở `CPA2_App/VALIDATION.md`):**
- **Render:** health `status=ok`, KB `57ab3bec24c3a961`, khớp runtime đóng gói.
- **`cloud_smoke.py` 9/9:** Clerk → Convex → Render, gồm ca Tuần 24 (mục tiêu giỏi 18 TC → TRUE 3,54; so sánh → TRUE; đủ điều kiện làm luận văn → TRUE; cả ba có trích nguồn).
- **Vercel production** `cpa2-gut7dk4uv`: bundle có nhãn A17 mới.
- **Trước phát hành:** 22/22 `validate_*.py`; API unittest 59 đạt (1 bỏ qua).
- **Kiểm tra bảo mật chạy SAU khi deploy** (bỏ sót trước, đã ghi nhận): OSV 0 cảnh báo; AgentShield B (80/100), giống lần trước.

## 4. Hạn chế

- **Ngoài benchmark:** hai ý định chỉ được kiểm bằng ca do em viết. Chưa có câu hỏi thật của sinh viên (Q-Real còn 0 câu, A16), nên độ phủ parser trên câu tự nhiên chưa đo được.
- **Giả định của phép tính mục tiêu:**
  - đạt mọi học phần sắp học;
  - không tính học cải thiện điểm D;
  - X mặc định là số TC tối thiểu. Học phần học vượt có tính vào ĐTBCTL hay không chưa được hình thức hoá, nên câu trả lời mới hỏi lại số TC dự định thay vì tự giả định.
- **Câu giả định "nếu rớt X thì trễ mấy kỳ"** vẫn chưa hỗ trợ (UNKNOWN "chưa hỗ trợ").
- **"Đủ điều kiện tiên quyết/song hành" ≠ được đăng ký** trong một học kỳ cụ thể: chưa xét lịch mở và thời gian đăng ký.
- **Chưa có người thứ hai soát (A7).**

## 5. Việc còn lại

- [x] Hai ý định mới + kiểm thử + review + hồi quy benchmark (0 ca đổi).
- [x] Phát hành demo: Render + Vercel, cloud smoke 9/9.
- [ ] **Phối hợp với phiên đa ngành** (`Tuan24_Da_nganh.md` bước 2–3 chờ thống nhất về w12/w18/app): w12 `prototype.py` và app đã thay đổi trong tuần này (`8785ce0`, `6afaa6a`, `34aa001`). Phiên đó cần rebase hoặc đọc lại các thay đổi trước khi luồn `ctdt` qua các module. Hai ý định mới hiện **gắn cứng CTĐT CNTT K49** (nhóm `g_tot_nghiep`, mã CT550E/CT501E đọc từ `hinh_thuc_cuoi_khoa`, ngưỡng từ KB).
- [ ] **QD-16:** ghi số hiệu, ngày và nơi ban hành văn bản xác nhận (cột nguồn vẫn "CHƯA GHI").
- [ ] **Người thứ hai soát (A7):** phân loại L1–L8 Tuần 23 và một mẫu gold.
- [ ] Viết chương luận văn: kết quả Tuần 22–23 và hai tính năng này (phần hệ thống, không phải phần đánh giá).
