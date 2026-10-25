# Q-Real — câu hỏi THẬT của sinh viên (mục tiêu 400–600 câu)

Nguồn do Loi cung cấp (Tuần 20, phương án 1a): nhóm/diễn đàn sinh viên ĐHCT, câu bạn bè hỏi, log hỏi đáp.

## Cách thu chính: Google Form (từ 19/10/2026)

Nội dung form nằm ở `bieu_mau.md`. File này sinh tự động bằng `python build_bieu_mau.py` từ `kich_ban_q_elicit.json`; đừng sửa tay.

1. **Trước khi mở form:**
   - điền mọi chỗ `<<ĐIỀN: …>>` (họ tên, email liên hệ, ngày xoá bản thô);
   - tạo form đúng như `bieu_mau.md`, chép nguyên tiêu đề kèm mã `[..]`;
   - tắt *Thu thập email*.
2. **Phát form.** Ghi lại kênh phát (nhóm lớp, bạn bè…) để báo cáo thiên lệch mẫu.
3. **Đóng form:**
   - xuất CSV vào `_tho/`;
   - chạy `python nhap_qreal.py` và đọc mọi dòng **CẢNH BÁO**;
   - rà tay `qreal.json` (câu tự do = **Q-Real**) và `qelicit.json` (câu theo kịch bản = **Q-Elicit**, báo riêng, KHÔNG tính vào 400);
   - tách các ô `nhieu_cau`.
4. **Rút lại.** Người trả lời gửi mã thì chạy `python nhap_qreal.py --rut <mã>`.
5. **Đúng hạn đã hứa:** xoá bản thô (Trang tính, CSV, `_tho/_noi_bo/ma_rut.json`). Sau đó không rút lại được nữa.

Kịch bản đã **đóng băng** (`kich_ban_dong_bang.json`). Muốn đổi kịch bản thì làm v2, không sửa v1.

## Quy trình

1. **Thu thập.** Chép nguyên câu hỏi về học vụ (đăng ký, tốt nghiệp, luận văn, miễn, chứng chỉ, điểm, cảnh báo…). Không sửa câu chữ, giữ cả lỗi chính tả hay không dấu, vì đó chính là dữ liệu cần đo. Không chép câu trả lời.
2. **Đặt file thô** vào `qreal/_tho/` (đã có trong `.gitignore`, KHÔNG commit). Có ba dạng:
   - `.txt`: mỗi dòng một câu;
   - `.csv`: cột `cau_hoi`, thêm cột `nguon` nếu có;
   - `.json`: danh sách chuỗi hoặc danh sách `{cau_hoi, nguon}`.

   Trường `nguon` chỉ ghi loại nguồn, ví dụ `nhom_fb_cntt` hay `ban_be`. Không ghi tên người, không ghi link.
3. **Chạy `python nhap_qreal.py`.** Script sẽ:
   - chuẩn hoá NFC;
   - ẩn danh MSSV, email, số điện thoại;
   - khử trùng và bỏ câu quá ngắn;
   - gán id ổn định và chia dev/test theo hash.

   Kết quả ghi vào `qreal/qreal.json`.
4. **Rà tay `qreal.json`** trước khi commit. Xoá tên người, mã lớp, link Facebook và mọi chi tiết nhận diện được, vì script chỉ bắt được các mẫu cố định. Chỉ commit bản đã rà.
5. **Gán nhãn** (tay, TRƯỚC khi chạy hệ thống):
   - `y_dinh`: một nhãn trong `meta.y_dinh_hop_le`;
   - `can_ho_so`: câu hỏi có cần hồ sơ cá nhân không;
   - `ma_hp`: mã học phần, nếu câu có nhắc.

   Nhãn này dùng để đánh giá parser (độ chính xác ý định) và độ phủ (Tuần 22).

Nhập lại lần sau vẫn **giữ nhãn đã gán**, vì id được tính từ nội dung câu đã chuẩn hoá.
