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

## Đã triển khai và kiểm tra online

- Mã ứng dụng trên nhánh `codex/cpa2-web-deploy`. Vercel production đã READY tại **https://cpa2-web.vercel.app**, deployment `dpl_2x9UHaUd8eyeBijhuWFuJXeHS5WR`, mã ứng dụng `5954726`. Trang đăng nhập công khai trả 200, API demo production trả 403.
- Render: `cpa2-api` live tại https://cpa2-api.onrender.com, workspace My Workspace, gói free. Container Docker build/chạy trên Linux; `/health` trả 200 và KB `2e7757765cfa09ae`. Câu xét tốt nghiệp trên hồ sơ giả lập trả TRUE với 20 bước chứng minh; câu học phí trả UNKNOWN/khong_ro; yêu cầu không có khóa trả 401.
- Convex: dự án `cpa2`, team PandaCore (`loiphat123456`), dev `nautical-fox-575`, prod `exciting-cheetah-606`; schema, indexes, functions, URL API, khóa dịch vụ và Clerk issuer đã đồng bộ ở cả hai deployment.
- Clerk: đã provisioning qua Vercel Marketplace, gói Hobby miễn phí; JWT template `convex` có audience `convex`. Bản demo dùng Clerk test instance, chưa phải cấu hình Clerk production/domain riêng.
- Hai tài khoản Clerk giả lập được tạo riêng để thử JWT thật: truy cập ẩn danh bị chặn; lưu cần consent; mỗi tài khoản không đọc/xóa được dữ liệu tài khoản kia; cập nhật hồ sơ tạo phiên bản mới, không đổi phiên bản của câu trả lời cũ. Luồng JWT → Convex → Render → chứng chỉ → lịch sử đạt; câu ngoài phạm vi giữ UNKNOWN.
- Kiểm tra Edge/Playwright trên URL công khai: đăng nhập → dashboard có dữ liệu → hỏi tốt nghiệp → mở chứng chỉ và nguồn → tải lại vẫn có phiên/lịch sử → sửa điểm và lưu → tra cứu quy chế đạt. Không có lỗi JavaScript; desktop 1440 px và mobile 390 px không tràn ngang. Đã xem ảnh chụp để xác nhận bố cục.
- OCR cloud lần đầu vượt giới hạn 120 giây. Sau khi đặt `OMP_THREAD_LIMIT=1` trên Render để tránh Tesseract tạo nhiều luồng trên máy chủ ít CPU, lượt thử lại đạt: upload một trang bảng điểm giả lập → Convex Storage → scheduled action → Render → bản nháp 17 dòng, giữ `needs_review` và `ocr_pending`. Docker/Blueprint cũng lưu cấu hình này cho các lần triển khai tiếp theo. Kết quả một ảnh không bảo đảm mọi bộ ảnh 4 trang hoàn tất trên gói free.
- Tài khoản/dữ liệu kiểm tra chỉ dùng hồ sơ tổng hợp; cleanup được chạy sau khi hoàn tất các lượt thử.

Các ảnh `cloud-login.png`, `cloud-dashboard.png`, `cloud-proof.png`, `cloud-mobile.png` là bằng chứng giao diện của lượt kiểm tra cloud. Các kiểm thử cloud này bổ sung cho bộ giả lập Convex, không thay kết quả hồi quy khảo sát 16/17 ở trên.

Chưa tích hợp AI API, thanh toán hoặc email, theo phạm vi bản đầu đã chốt. Website và tài liệu sản phẩm sử dụng tên CPA²; AcademiQ chỉ là nguồn kế thừa của niên luận.
