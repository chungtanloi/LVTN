# Trạng thái triển khai CPA² — 25/10/2026

## Đã kiểm tra

| Hạng mục | Kết quả |
|---|---|
| API Python trong môi trường riêng | 12/12 kiểm thử đạt |
| Convex: phân quyền, phiên bản, consent, xóa và giới hạn yêu cầu | 7/7 kiểm thử trong môi trường giả lập đạt |
| TypeScript và Next.js production build | Đạt |
| Trình duyệt Edge/Playwright | Dashboard → hỏi đáp thật → chứng chỉ → sửa/lưu điểm → đề xuất → tra cứu → lịch sử → xóa đạt; không có lỗi JavaScript trong lượt kiểm tra |
| Responsive | Desktop 1440 px, mobile 390 px; bảng điểm cuộn trong vùng riêng, không tràn ngang trang |
| CSRF của API demo | Yêu cầu khác origin bị từ chối |
| Chặn demo trong production | Chạy `next start` với `CPA2_DEMO_MODE=true`: trang chờ cấu hình trả 200 và API demo trả 403 |
| Đóng gói runtime | 5 luồng advice/recommendation/lookup chạy từ bản sao chỉ có các file Docker COPY; hash KB trùng checkout |
| OCR qua HTTP trong môi trường riêng | Đọc bảng điểm giả lập 4 trang, 55 dòng; giữ trạng thái chờ rà soát |
| Audit phụ thuộc web production | `pnpm audit --prod`: không ghi nhận cảnh báo |
| Audit Python, gồm phụ thuộc gián tiếp/dev | OSV: 29 gói được kiểm tra, không ghi nhận cảnh báo sau khi cập nhật Pillow và python-multipart |
| Hồi quy khảo sát | 16/17 bộ validate đạt; bộ w15 OCR đầy đủ vượt giới hạn 600 giây, chưa đạt điều kiện hoàn tất kiểm tra toàn bộ |

Các bộ khảo sát chạy trên bản sao tạm. Không sửa quy tắc, gold hoặc báo cáo khảo sát gốc để làm cho kiểm tra đạt. Timeout không được tính là pass. Chế độ OCR nhanh được chạy bổ sung: các ca sạch và các ca đã in kết quả qua F8 đều đạt, nhưng tiến trình tiếp tục xử lý quá 10 phút nên đã dừng; chưa có kết luận cuối cho lượt này. Kết quả từng phần không thay cho bộ OCR đầy đủ.

## Chưa nghiệm thu online

- Đã push mã ứng dụng lên nhánh `codex/cpa2-web-deploy`, commit `49d37f5`.
- Render: `cpa2-api` đã live tại https://cpa2-api.onrender.com; `/health` trả 200 và KB `2e7757765cfa09ae`. Đã cấu hình khóa dịch vụ: câu xét tốt nghiệp trên hồ sơ giả lập trả TRUE với 20 bước chứng minh; câu học phí trả UNKNOWN/khong_ro; yêu cầu không có khóa trả 401.
- Vercel: đã tạo dự án `cpa2-web` trong workspace `loi5`, chưa phát hành giao diện có đăng nhập.
- Convex: đã tạo dự án `cpa2` trong team PandaCore (`loiphat123456`), dev `nautical-fox-575`, prod `exciting-cheetah-606`; đã đặt URL API và khóa dịch vụ ở cả hai deployment. Backend chưa đồng bộ vì thiếu Clerk issuer.
- Clerk: đã chọn gói Hobby miễn phí, nhưng Vercel yêu cầu người dùng chấp thuận điều khoản Marketplace trước khi provisioning. Đây là bước hiện đang chờ người dùng.
- Kiểm thử Convex là kiểm thử chức năng backend trong bộ nhớ, chưa thay cho kiểm tra hai tài khoản Clerk thật trên cloud.
- Container Docker đã build và khởi động thành công trên Render Linux. Chưa kiểm thử suy luận/OCR có xác thực qua cloud.
- Trước khi công bố demo online: tạo/kết nối các dự án, cấu hình môi trường theo README, build Docker, thử đăng nhập hai tài khoản, upload/OCR, xóa dữ liệu và kiểm tra lại health.

Chưa tích hợp AI API, thanh toán hoặc email, theo phạm vi bản đầu đã chốt. Website và tài liệu sản phẩm sử dụng tên CPA²; AcademiQ chỉ là nguồn kế thừa của niên luận.
