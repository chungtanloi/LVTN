# Biểu mẫu thu câu hỏi học vụ — nội dung để dán vào Google Form

<!-- SINH TỰ ĐỘNG bởi build_bieu_mau.py từ qreal/kich_ban_q_elicit.json — sửa kịch bản rồi chạy lại, không sửa tay. -->

> **Cho người tạo form.** Mỗi tiêu đề `###` bên dưới là MỘT câu hỏi trên Google Form: chép NGUYÊN tiêu đề, kể cả mã trong ngoặc vuông, vì bộ nhập đọc CSV theo các mã này.
>
> **Trước khi mở form:** thay mọi chỗ `<<ĐIỀN: …>>` bằng thông tin thật.
>
> **Cài đặt Google Form:**
> - Tắt *Thu thập địa chỉ email*.
> - Không bật *Giới hạn 1 câu trả lời*, vì tuỳ chọn này bắt đăng nhập.
> - Tắt *Cho phép chỉnh sửa sau khi gửi*.
>
> Dùng *Chuyển đến phần dựa trên câu trả lời* cho `[DONG_Y]` và `[BO]`. Google Form luôn có nút *Quay lại*, nên câu tự do vẫn có thể bị sửa sau khi đọc kịch bản (đã nhắc người trả lời; ghi là hạn chế).
>
> **Sau khi đóng form:**
> 1. Tải CSV từ Trang tính.
> 2. Đặt file vào `w20_benchmark/qreal/_tho/` (gitignore).
> 3. Chạy `python nhap_qreal.py`.
> 4. Rà tay `qreal.json` và `qelicit.json` trước khi commit.
> 5. Xoá bản thô (Trang tính + CSV) đúng hạn đã ghi ở phần đồng ý.
>
> Người trả lời muốn rút lại thì chạy `python nhap_qreal.py --rut <mã>`.

## Tiêu đề và mô tả form

**Tiêu đề:** Bạn thường hỏi gì về chuyện học ở trường? (khảo sát khoảng 5 phút)

**Mô tả:** Mình là sinh viên ĐH Cần Thơ, đang làm đề tài nghiên cứu cuối khoá về một trợ lý trả lời câu hỏi học vụ. Mình cần biết sinh viên THẬT SỰ hỏi như thế nào, vì vậy bạn cứ viết đúng như khi nhắn cho bạn bè hay cố vấn học tập: không dấu, viết tắt, sai chính tả đều ổn.

## Phần 0 — Đồng ý tham gia

### [DONG_Y] Bạn có đồng ý cho dùng câu hỏi bạn viết cho đề tài này không?

*Trắc nghiệm, bắt buộc.* Nội dung giải thích (đặt trong phần mô tả của câu hỏi):

- **Người thu dữ liệu:** <<ĐIỀN: họ tên>>, sinh viên ĐH Cần Thơ. Liên hệ: <<ĐIỀN: email liên hệ>>.
- **Mục đích:** đánh giá trợ lý trả lời câu hỏi học vụ trong đề tài nghiên cứu cuối khoá. Một số câu có thể được trích nguyên văn trong báo cáo.
- **Ẩn danh:** biểu mẫu không hỏi tên, mã số sinh viên, email, số điện thoại hay ngày sinh. Xin đừng ghi các thông tin này vào câu trả lời. Lỡ ghi thì mình sẽ xoá khi rà tay.
- **Nơi lưu:** câu trả lời đã ẩn danh và rà tay được lưu trong kho mã nguồn của đề tài trên GitHub (có thể công khai). Câu trả lời cũng có thể được gửi tới dịch vụ AI (OpenAI, Google Gemini) để so sánh với trợ lý. Dữ liệu không dùng cho mục đích khác.
- **Thời hạn:** bản thô (Trang tính, file CSV, cùng mã rút) được xoá ngay sau khi nhập và rà, chậm nhất <<ĐIỀN: ngày>>.
- **Rút lại:** bạn có thể tự đặt một mã rút ở câu tiếp theo. Muốn rút, gửi mã đó qua liên hệ ở trên trước <<ĐIỀN: ngày>> (ngày xoá bản thô); mình sẽ xoá các câu đi kèm mã khỏi dữ liệu và các lần cập nhật sau. Không đặt mã, hoặc sau ngày đó, thì mình không thể biết câu nào là của bạn.
- **Giới hạn của việc rút lại:** phần đã nằm trong lịch sử kho mã (các phiên bản cũ trên GitHub), đã đưa vào báo cáo, hoặc đã gửi tới dịch vụ AI thì mình không thể thu hồi.
- **Tự nguyện:** tham gia là tự nguyện. Ngoài câu đồng ý và câu chọn bộ, mọi câu đều không bắt buộc.

Lựa chọn:
- `Tôi đồng ý` → chuyển đến câu tiếp theo
- `Không đồng ý` → *Gửi biểu mẫu* (kết thúc)

### [MA_RUT] Mã rút lại do bạn tự đặt (không bắt buộc)

*Trả lời ngắn.* Tối thiểu 6 ký tự ngẫu nhiên, phân biệt hoa/thường, ví dụ `k7Mq2x`. Đừng dùng ngày sinh, mã số sinh viên, số điện thoại hay mật khẩu. Mã chỉ dùng để tìm câu của bạn khi bạn muốn rút, không đưa lên kho mã và được xoá cùng bản thô.

## Phần 1 — Câu hỏi của chính bạn

*Mô tả phần:* Bạn đã từng thật sự muốn hỏi gì về chuyện học ở trường? Mỗi ô một câu, viết đúng như bạn đã hỏi hoặc định hỏi. Không nghĩ ra thì bỏ trống.

### [TU_DO-1] Câu hỏi 1

*Đoạn văn, không bắt buộc.*

### [TU_DO-2] Câu hỏi 2

*Đoạn văn, không bắt buộc.*

### [TU_DO-3] Câu hỏi 3

*Đoạn văn, không bắt buộc.*

## Phần 2 — Chọn bộ tình huống

### [BO] Chọn một số bất kỳ từ 1 đến 4

*Trắc nghiệm, bắt buộc. Chỉ dùng để chia bạn vào một bộ tình huống.* Mô tả phần: sau bước này, xin đừng quay lại sửa câu ở Phần 1.

- `1` → chuyển đến *Bộ tình huống 1*
- `2` → chuyển đến *Bộ tình huống 2*
- `3` → chuyển đến *Bộ tình huống 3*
- `4` → chuyển đến *Bộ tình huống 4*

## Bộ tình huống 1

*Mô tả phần:* Đọc từng tình huống, rồi viết câu bạn sẽ hỏi (nhắn cho bạn bè, cố vấn học tập hay trợ lý ảo) trong tình huống đó. Viết bằng lời của bạn, không cần giống tình huống. Không biết hỏi gì thì bỏ trống. Cuối phần → *Gửi biểu mẫu*.

### [KB-01] Học kỳ tới bạn muốn học môn CT177, nhưng không chắc mình đã học đủ các môn bắt buộc phải học trước nó hay chưa. Bạn muốn hỏi xem mình có thể ghi danh môn này không.

*Đoạn văn (trả lời dài), không bắt buộc.*

### [KB-02] Bạn đã học gần hết chương trình, chỉ còn chờ điểm một môn. Bạn muốn biết cuối học kỳ này mình có nhận bằng hay không.

*Đoạn văn (trả lời dài), không bắt buộc.*

### [KB-03] Bạn có chứng chỉ IELTS 6.0 còn hạn. Bạn muốn biết với chứng chỉ này, mình có phải học các học phần tiếng Anh căn bản nữa không.

*Đoạn văn (trả lời dài), không bắt buộc.*

### [KB-04] Bạn muốn biết học kỳ hè năm nay mỗi tín chỉ phải đóng bao nhiêu tiền.

*Đoạn văn (trả lời dài), không bắt buộc.*

### [KB-05] Điểm trung bình tích lũy của bạn hiện khoảng 3,1. Bạn muốn biết với mức điểm này, tấm bằng bạn nhận được sẽ ghi mức nào.

*Đoạn văn (trả lời dài), không bắt buộc.*


## Bộ tình huống 2

*Mô tả phần:* Đọc từng tình huống, rồi viết câu bạn sẽ hỏi (nhắn cho bạn bè, cố vấn học tập hay trợ lý ảo) trong tình huống đó. Viết bằng lời của bạn, không cần giống tình huống. Không biết hỏi gì thì bỏ trống. Cuối phần → *Gửi biểu mẫu*.

### [KB-06] Bạn định học học phần CT182 ở học kỳ tới, nhưng nhớ là học kỳ trước mình bị điểm F một môn liên quan. Bạn muốn hỏi xem mình có thể chọn học phần này không.

*Đoạn văn (trả lời dài), không bắt buộc.*

### [KB-07] Bạn đang học năm 4 và muốn làm một đề tài nghiên cứu cuối khoá với giảng viên thay vì học thêm các môn khác. Bạn muốn biết số tín chỉ hiện có của mình đã đủ để bắt đầu hay chưa.

*Đoạn văn (trả lời dài), không bắt buộc.*

### [KB-08] Bạn muốn rà lại xem trong chương trình đào tạo, những môn bắt buộc nào mình vẫn chưa học xong.

*Đoạn văn (trả lời dài), không bắt buộc.*

### [KB-09] Bạn lo môn CT296 học kỳ này có thể bị điểm F. Bạn muốn biết chuyện đó sẽ làm mình nhận bằng chậm thêm bao lâu.

*Đoạn văn (trả lời dài), không bắt buộc.*

### [KB-10] Bạn muốn chuyển sang học một ngành khác trong trường và muốn biết thủ tục cần làm.

*Đoạn văn (trả lời dài), không bắt buộc.*


## Bộ tình huống 3

*Mô tả phần:* Đọc từng tình huống, rồi viết câu bạn sẽ hỏi (nhắn cho bạn bè, cố vấn học tập hay trợ lý ảo) trong tình huống đó. Viết bằng lời của bạn, không cần giống tình huống. Không biết hỏi gì thì bỏ trống. Cuối phần → *Gửi biểu mẫu*.

### [KB-11] Bạn muốn được gợi ý danh sách môn phù hợp để học trong học kỳ 2 sắp tới, dựa trên những môn mình đã học.

*Đoạn văn (trả lời dài), không bắt buộc.*

### [KB-12] Bạn muốn biết tổng số tín chỉ mình đang có so với số tín chỉ của cả chương trình còn chênh bao nhiêu.

*Đoạn văn (trả lời dài), không bắt buộc.*

### [KB-13] Bạn có chứng chỉ TOEIC 600. Bạn muốn biết chứng chỉ này giúp mình khỏi phải học những học phần ngoại ngữ nào.

*Đoạn văn (trả lời dài), không bắt buộc.*

### [KB-14] Bạn vừa có điểm môn cuối cùng của chương trình. Bạn muốn biết đợt xét cấp bằng sắp tới mình đã đủ tiêu chuẩn hay chưa.

*Đoạn văn (trả lời dài), không bắt buộc.*

### [KB-15] Bạn muốn biết học kỳ này mình có nhận được học bổng khuyến khích học tập hay không.

*Đoạn văn (trả lời dài), không bắt buộc.*


## Bộ tình huống 4

*Mô tả phần:* Đọc từng tình huống, rồi viết câu bạn sẽ hỏi (nhắn cho bạn bè, cố vấn học tập hay trợ lý ảo) trong tình huống đó. Viết bằng lời của bạn, không cần giống tình huống. Không biết hỏi gì thì bỏ trống. Cuối phần → *Gửi biểu mẫu*.

### [KB-16] Bạn muốn làm niên luận CT466E trong học kỳ tới và muốn hỏi xem với kết quả học tập hiện tại, mình có thể ghi danh học phần này không.

*Đoạn văn (trả lời dài), không bắt buộc.*

### [KB-17] Bạn nghe nói có hình thức làm một bài nghiên cứu cuối khoá ngắn hơn, kết hợp học thêm vài môn. Bạn muốn biết với kết quả học tập hiện tại, mình có thể chọn hình thức này không.

*Đoạn văn (trả lời dài), không bắt buộc.*

### [KB-18] Bạn có hai môn từng bị điểm F rồi học lại. Bạn muốn biết điều đó có làm bằng của mình bị hạ một bậc không.

*Đoạn văn (trả lời dài), không bắt buộc.*

### [KB-19] Bạn muốn biết quy chế của trường giới hạn số tín chỉ được học trong một học kỳ chính như thế nào.

*Đoạn văn (trả lời dài), không bắt buộc.*

### [KB-20] Bạn muốn có một kế hoạch chọn môn cho học kỳ hè để kịp tiến độ, và cần gợi ý những môn phù hợp.

*Đoạn văn (trả lời dài), không bắt buộc.*

## Lời cảm ơn (thông báo xác nhận)

Cảm ơn bạn đã giúp! Câu hỏi của bạn giúp trợ lý hiểu sinh viên hỏi thật như thế nào.
