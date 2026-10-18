# Q-Real — câu hỏi THẬT của sinh viên (mục tiêu 400–600 câu)

Nguồn do Loi cung cấp (Tuần 20, phương án 1a): nhóm/diễn đàn sinh viên ĐHCT, câu bạn bè hỏi, log hỏi đáp.

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
