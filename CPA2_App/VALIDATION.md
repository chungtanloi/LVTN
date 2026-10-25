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

- Chưa có deployment Vercel/Convex/Clerk/Render được cấu hình trong phiên làm việc.
- Kiểm thử Convex là kiểm thử chức năng backend trong bộ nhớ, chưa thay cho kiểm tra hai tài khoản Clerk thật trên cloud.
- Chưa build container Docker trên máy này vì không có Docker CLI; kiểm tra runtime chỉ xác nhận tập file và luồng Python, không xác nhận image Linux.
- Trước khi công bố demo online: tạo/kết nối các dự án, cấu hình môi trường theo README, build Docker, thử đăng nhập hai tài khoản, upload/OCR, xóa dữ liệu và kiểm tra lại health.

Chưa tích hợp AI API, thanh toán hoặc email, theo phạm vi bản đầu đã chốt. Website và tài liệu sản phẩm sử dụng tên CPA²; AcademiQ chỉ là nguồn kế thừa của niên luận.
