# BỘ BẪY TRI THỨC — mệnh đề học vụ phổ biến nhưng sai

**Sinh tự động** từ `bay_tri_thuc.py`. Dành cho bộ Adversarial của Tuần 17 và cho phần bàn luận về giả thuyết **H2**.

## 1. Bộ này đến từ đâu

Trong lúc làm Tuần 5, tác giả nhận được **hai câu trả lời độc lập** cho cùng một câu hỏi — *"TC nợ đọng tính thế nào?"* — cả hai do trợ lý AI sinh ra. Cả hai đều trôi chảy, có cấu trúc, có hướng dẫn thao tác cụ thể, và **không câu nào kèm cảnh báo về độ chắc chắn**. Đối chiếu với văn bản gốc: **7 mệnh đề sai** trên tổng 8 mệnh đề kiểm được.

Điều đáng giá nhất không phải số lỗi, mà là **hai câu trả lời mâu thuẫn với nhau ở đúng công thức cốt lõi** (B-07). Một người đọc chỉ nhận một trong hai sẽ không có cách nào biết điều đó.

> Đây là **bằng chứng cho H2 thu được trước thí nghiệm**, và là loại ca đối kháng khác với nhóm dữ liệu khuyết: ở đây baseline **chắc chắn sẽ trả lời**, vì mệnh đề sai chính là thứ lặp đi lặp lại trên mạng.

## 2. Bảng bẫy

| Mã | Nhóm | Mệnh đề | Chân trị | Nguồn đối chiếu |
|---|---|---|---|---|
| **B-01** | ngưỡng đạt | Học phần được xem là đạt khi có điểm từ **5,0** trở lên (thang 10). | SAI (với học phần học tại ĐHCT) | QĐ3266 Điều 22 khoản 3 và bảng ở khoản 2 |
| **B-02** | ngưỡng đạt | Học phần được xem là đạt khi có điểm chữ từ **C** trở lên. | SAI | QĐ3266 Điều 22 khoản 3 |
| **B-03** | con số bịa | Tổng số tín chỉ nợ không được vượt quá **150 %** khối lượng CTĐT thì mới được xét tốt nghi… | KHÔNG TỒN TẠI | QĐ3266 Điều 18 khoản 2 điểm c (đã tìm toàn văn cả hai văn bản) |
| **B-04** | con số bịa | Nợ quá nhiều tín chỉ (**trên 15–20 TC tùy quy định từng khoa**) thì bị **đình chỉ học tập*… | SAI ba lần trong một câu | QĐ3266 Điều 18 khoản 2 điểm c (cảnh báo) và khoản 3 (đình chỉ) |
| **B-05** | hiểu sai ký hiệu | Học phần có **dấu (*)** là học phần **bắt buộc**. | SAI — gần như ngược lại | CTĐT CNTT K49 (QĐ 2423/QĐ-ĐHCT 05/6/2023), chú thích cuối bảng trang 4; khớp với QĐ3266 Điều 7 khoản 6 |
| **B-06** | con số bịa | Tổng số tín chỉ của ngành **thường từ 135–150 TC**. | SAI với ngành đang xét | CTĐT CNTT K49, bảng tổng trang 4: 'Tổng cộng: 161 TC (Bắt buộc: 125 TC; Tự chọn: 36 TC)' |
| **B-07** | mâu thuẫn nội bộ | Hai mẫu đưa ra HAI công thức khác nhau cho cùng một đại lượng: M1 — *TC nợ = TC đã đăng ký… | MÂU THUẪN; công thức của M2 dẫn tới kết luận vô lý | Phản chứng dùng số thật của CTĐT CNTT K49 (161 TC) và QĐ3266 Điều 18 k.2 đ.c (24 TC) |
| **B-08** | đúng (ca đối chứng) | Một năm học tại ĐHCT có **3 học kỳ**. | ĐÚNG | QĐ3266 Điều 6 khoản 1 |

## 3. Chi tiết

### B-01 — SAI (với học phần học tại ĐHCT)

**Mệnh đề:** Học phần được xem là đạt khi có điểm từ **5,0** trở lên (thang 10).

**Đúng ra là:** Học phần tích lũy được từ **điểm D**, mà bảng quy đổi đặt **D = 4,0–4,9**. Ngưỡng 5,0 là của QĐ5339 và theo QD-09 chỉ áp cho ĐIỂM CHUYỂN ĐỔI từ cơ sở đào tạo khác.

**Nguồn:** QĐ3266 Điều 22 khoản 3 và bảng ở khoản 2

**Hậu quả nếu tin theo:** Sinh viên có điểm 4,0–4,9 bị báo nhầm là chưa đạt; kéo theo sai tổng tín chỉ tích lũy, sai xếp trình độ năm học, sai cả kết luận cảnh báo học vụ.

**Kiểm lại ở:** ca C23c trong validate_rformal.py

**Xuất hiện ở:** Trợ lý AI #1, Trợ lý AI #2


### B-02 — SAI

**Mệnh đề:** Học phần được xem là đạt khi có điểm chữ từ **C** trở lên.

**Đúng ra là:** Ngưỡng là **D**, thấp hơn C ba bậc (D, D⁺, C). C tương ứng 5,5–6,4.

**Nguồn:** QĐ3266 Điều 22 khoản 3

**Hậu quả nếu tin theo:** Sai nặng hơn B-01: loại nhầm cả nhóm điểm 4,0–5,4.

**Kiểm lại ở:** bảng band/4 trong qd3266_r_formal_v1.lp

**Xuất hiện ở:** Trợ lý AI #1


### B-03 — KHÔNG TỒN TẠI

**Mệnh đề:** Tổng số tín chỉ nợ không được vượt quá **150 %** khối lượng CTĐT thì mới được xét tốt nghiệp.

**Đúng ra là:** Chuỗi '150' không xuất hiện trong QĐ3266; trong QĐ5339 chỉ xuất hiện ở dải điểm Cambridge KET. Con số thật là **24 TC**, và nó là ngưỡng **cảnh báo học tập**, không phải điều kiện xét tốt nghiệp.

**Nguồn:** QĐ3266 Điều 18 khoản 2 điểm c (đã tìm toàn văn cả hai văn bản)

**Hậu quả nếu tin theo:** Gán một điều kiện tốt nghiệp không tồn tại; đồng thời giấu mất ngưỡng cảnh báo thật.

**Kiểm lại ở:** ca C30/C31 (biên 24/25 TC)

**Xuất hiện ở:** Trợ lý AI #1


### B-04 — SAI ba lần trong một câu

**Mệnh đề:** Nợ quá nhiều tín chỉ (**trên 15–20 TC tùy quy định từng khoa**) thì bị **đình chỉ học tập**.

**Đúng ra là:** (1) Sai HỆ QUẢ: nợ tín chỉ dẫn tới **cảnh báo học tập**, không phải đình chỉ. Đình chỉ 1 HK chỉ xảy ra khi bị kỷ luật ở mức đó, hoặc ĐRL yếu/kém 2 HK liên tiếp. (2) Sai CON SỐ: ngưỡng là **24 TC**. (3) Sai THẨM QUYỀN: ngưỡng do quy chế cấp Trường đặt, không 'tùy từng khoa'.

**Nguồn:** QĐ3266 Điều 18 khoản 2 điểm c (cảnh báo) và khoản 3 (đình chỉ)

**Hậu quả nếu tin theo:** Doạ sinh viên bằng một hậu quả nặng hơn thực tế, dựa trên con số bịa.

**Kiểm lại ở:** ca C31 và mục 10 của qd3266_r_formal_v1.lp

**Xuất hiện ở:** Trợ lý AI #2


### B-05 — SAI — gần như ngược lại

**Mệnh đề:** Học phần có **dấu (*)** là học phần **bắt buộc**.

**Đúng ra là:** Dấu (*) CÓ tồn tại trong CTĐT, nhưng chú thích cuối bảng ghi: *'(*) là học phần **điều kiện**, không tính điểm trung bình chung tích lũy. Sinh viên có thể hoàn thành bằng hình thức nộp chứng chỉ ... hoặc học tích lũy.'* Tức nó đánh dấu đúng nhóm học phần **không** vào ĐTBCTL và **có thể miễn bằng chứng chỉ**.

**Nguồn:** CTĐT CNTT K49 (QĐ 2423/QĐ-ĐHCT 05/6/2023), chú thích cuối bảng trang 4; khớp với QĐ3266 Điều 7 khoản 6

**Hậu quả nếu tin theo:** Hiểu ngược ý nghĩa ký hiệu; dẫn tới tính nhầm ĐTBCTL và bỏ lỡ quyền xin miễn bằng chứng chỉ.

**Kiểm lại ở:** ctdt_cntt_k49.lp — danh_dau_sao_la(hoc_phan_dieu_kien)

**Xuất hiện ở:** Trợ lý AI #1, Trợ lý AI #2

> **Tự phê:** Ở lần đối chiếu đầu tác giả kết luận 'dấu (*) không xuất hiện ở cả hai văn bản' — đúng với hai QĐ nhưng SAI vì chưa tra CTĐT. Ghi lại để nhớ: phạm vi tìm kiếm hẹp cũng sinh ra kết luận âm tính sai.


### B-06 — SAI với ngành đang xét

**Mệnh đề:** Tổng số tín chỉ của ngành **thường từ 135–150 TC**.

**Đúng ra là:** CTĐT CNTT K49: **161 TC** (bắt buộc 125, tự chọn 36) — nằm ngoài khoảng được nêu. Quy chế KHÔNG quy định con số này; nó thuộc từng CTĐT.

**Nguồn:** CTĐT CNTT K49, bảng tổng trang 4: 'Tổng cộng: 161 TC (Bắt buộc: 125 TC; Tự chọn: 36 TC)'

**Hậu quả nếu tin theo:** Sai tổng tín chỉ đích → sai mọi phép tính 'còn thiếu bao nhiêu tín chỉ'.

**Kiểm lại ở:** ctdt_cntt_k49.lp — tc_toi_thieu_ctdt(161) và ràng buộc cộng ba khối

**Xuất hiện ở:** Trợ lý AI #2


### B-07 — MÂU THUẪN; công thức của M2 dẫn tới kết luận vô lý

**Mệnh đề:** Hai mẫu đưa ra HAI công thức khác nhau cho cùng một đại lượng: M1 — *TC nợ = TC đã đăng ký − TC đã đạt*; M2 — *TC nợ = Tổng TC ngành − TC đã đạt*.

**Đúng ra là:** Quy chế không định nghĩa thuật ngữ này (xem QD-03). Nhưng công thức của M2 bị bác bằng phản chứng: với CTĐT 161 TC và ngưỡng cảnh báo 24 TC, sinh viên phải tích lũy **≥ 137 TC** mới thoát cảnh báo. Nghĩa là **gần như toàn bộ sinh viên chưa tới năm cuối đều bị cảnh báo học tập** — một hệ quả không thể đúng. M2 còn tự mâu thuẫn: ngay sau công thức đó lại viết 'hoặc đơn giản hơn: cộng tổng TC các học phần bị trượt/chưa học', vốn là một đại lượng khác hẳn.

**Nguồn:** Phản chứng dùng số thật của CTĐT CNTT K49 (161 TC) và QĐ3266 Điều 18 k.2 đ.c (24 TC)

**Hậu quả nếu tin theo:** Nếu cài theo M2, hệ thống sẽ cảnh báo học vụ gần như mọi sinh viên.

**Kiểm lại ở:** ca C27–C29 (định nghĩa đang dùng) và phản chứng trong BoBayTriThuc.md mục 3

**Xuất hiện ở:** Trợ lý AI #1, Trợ lý AI #2


### B-08 — ĐÚNG

**Mệnh đề:** Một năm học tại ĐHCT có **3 học kỳ**.

**Đúng ra là:** QĐ3266 Điều 6 khoản 1: 'Mỗi năm học được tổ chức thành 03 HK gọi là Học kỳ 1, Học kỳ 2 và Học kỳ 3.'

**Nguồn:** QĐ3266 Điều 6 khoản 1

**Kiểm lại ở:** đưa vào bộ để bộ không toàn ca sai: một bộ đối kháng chỉ chứa mệnh đề sai sẽ thưởng cho hệ thống nào luôn trả lời 'sai'.

**Xuất hiện ở:** Trợ lý AI #2


## 4. Cách dùng ở Tuần 17 và Tuần 21

- Mỗi bẫy thành **một câu hỏi Q-Real** đặt thẳng vào mệnh đề sai (*"Em được 4,5 điểm môn CT177, vậy có đạt không?"*).
- Ground truth là cột *Đúng ra là* kèm con trỏ điều khoản — chấm được tự động.
- Đo trên baseline: kỳ vọng **Coverage ≈ 100 %, Soundness thấp** — đúng dạng H2 dự đoán. CPA² phải hoặc trả lời đúng kèm chứng chỉ, hoặc từ chối; **không được trả lời sai**.
- B-08 là **ca đối chứng dương**: một bộ chỉ gồm mệnh đề sai sẽ thưởng cho hệ thống nào luôn bác bỏ. Cần thêm ca đúng để phát hiện kiểu gian lận đó.

## 5. Hạn chế của bộ này

- Cỡ mẫu rất nhỏ (2 câu trả lời, 8 mệnh đề) và **không lấy mẫu ngẫu nhiên** — đây là ca thuận tiện, không phải khảo sát. Không được suy ra tỷ lệ lỗi của bất kỳ mô hình nào từ đây.
- Không ghi lại mô hình nào sinh ra câu trả lời, ngày nào, prompt gì. Nếu muốn dùng như dữ liệu chính thức trong luận văn thì **phải chạy lại có kiểm soát**: cố định mô hình, prompt, ngày, và lưu nguyên văn.
- Giá trị hiện tại của bộ này là **định tính**: nó cho thấy dạng lỗi tồn tại và đáng đo, chứ chưa đo được tần suất.
