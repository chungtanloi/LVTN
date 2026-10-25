# CPA² — Website tư vấn học vụ có chứng minh

Ứng dụng luận văn **CPA²**. Kế thừa luồng hồ sơ, nhập bảng điểm và trải nghiệm tư vấn từ niên luận AcademiQ; các kết luận học vụ sử dụng lõi CPA² trong `CPA2_KhaoSat`.

## Chạy thử trên Windows

Yêu cầu: Python 3.12 trở lên, Node.js 20.9 trở lên, pnpm. OCR cần Tesseract với ngôn ngữ `vie` và `eng`; có thể đặt `TESSERACT_EXE` nếu dùng đường dẫn khác.

Từ thư mục gốc `D:\LVTN`:

```powershell
python -m venv CPA2_App/api/.venv
./CPA2_App/api/.venv/Scripts/python.exe -m pip install -r CPA2_App/api/requirements-dev.txt
cd CPA2_App/web
pnpm install --frozen-lockfile
cd ../..
powershell -NoProfile -ExecutionPolicy Bypass -File CPA2_App/scripts/dev.ps1
```

Mở **http://127.0.0.1:3000**. Script tạo khóa dịch vụ ngẫu nhiên trong môi trường tiến trình, chạy API ở `127.0.0.1:8000`, chỉ mở Next.js trên loopback. Ctrl+C dừng phiên chạy. Nếu cổng bận, dùng `-WebPort 3001 -ApiPort 8001`.

Sau khi cài phụ thuộc một lần, có thể nhấp đúp `CPA2_App/Start-CPA2.cmd` để khởi động. Launcher cũng nhận diện Node.js đi kèm Codex desktop nếu Node chưa có trong PATH.

Chế độ cục bộ dùng hồ sơ giả lập. Hồ sơ và lịch sử trên giao diện chỉ ở bộ nhớ phiên; tải lại trang sẽ trở về hồ sơ mẫu. Không dùng dữ liệu thật trong bản demo chưa đăng nhập. `.env` gốc của luận văn và secret của niên luận không được đọc hoặc sao chép.

## Chức năng

- Dashboard thống kê mô tả, hồ sơ và bảng điểm có chỉnh sửa từng học phần.
- Nhập JSON CPA² hoặc bản xuất hồ sơ AcademiQ; kiểm tra rõ ngành và khóa, không đổi K51 thành K49.
- Chat xét tốt nghiệp, đăng ký học phần, điều kiện LVTN/TLTN, miễn học phần và xếp loại trong phạm vi parser hiện có.
- Chứng chỉ, bước chứng minh, nguồn quy chế, dữ kiện thiếu và xuất kết quả JSON.
- Đề xuất đăng ký một học kỳ, tra cứu đoạn quy chế và lịch sử gắn với phiên bản hồ sơ.
- OCR 1–4 ảnh PNG/JPEG theo thứ tự trang; mỗi ảnh tối đa 10 MB, tổng tối đa 20 MB và 20 triệu điểm ảnh/ảnh. Dữ kiện không chắc tiếp tục bị chặn.
- Backend Convex cho lưu hồ sơ có đồng ý, phiên bản bất biến, hội thoại riêng từng tài khoản, tác vụ OCR và xóa dữ liệu.

Điểm chữ từ niên luận không được đổi thành một điểm số tùy ý. Nếu thiếu điểm thang 10, CPA² yêu cầu bổ sung trước khi suy luận. Số GPA/tín chỉ trên dashboard là thống kê mô tả, không thay thế kết luận tốt nghiệp của solver.

## Kiến trúc và API

```text
Next.js + Tailwind (Vercel)
  └─ Clerk → Convex (hồ sơ, phiên bản, lịch sử, ảnh, tác vụ OCR)
                └─ action → FastAPI (Docker / Render)
                              └─ loader chung → clingo → proof → grounding
```

Python dùng một tiến trình con cho mỗi tác vụ để cách ly các import cũ và cưỡng chế thời gian xử lý. Tối đa hai tác vụ đang xử lý trong một tiến trình API; suy luận/tra cứu tối đa 30 giây, OCR tối đa 120 giây. Lỗi kỹ thuật, quá thời gian, `BLOCKED` và hồ sơ mâu thuẫn được giữ riêng với kết luận ba trị.

Các endpoint `/v1/*` yêu cầu `Authorization: Bearer <CPA2_SERVICE_KEY>`. `/health` không chứa dữ liệu sinh viên.

| Endpoint | Đầu vào / mục đích |
|---|---|
| `GET /health` | Tình trạng API và hash phiên bản KB |
| `GET /v1/catalog` | Danh mục CTĐT CNTT K49 |
| `GET /v1/demo-profiles` | Hồ sơ giả lập có sẵn |
| `POST /v1/profiles/validate` | `{ profile }` → hồ sơ chuẩn hóa, kiểm schema |
| `POST /v1/advice` | `{ profile, question }` → verdict, certificate, nguồn, missing facts |
| `POST /v1/recommendations` | `{ profile, semester: 1..3 }` → học phần hợp lệ, chứng chỉ, mục cần xác minh |
| `POST /v1/lookup` | `{ question }` → đoạn nguồn, không kết luận về sinh viên |
| `POST /v1/ocr` | Multipart `files` → hồ sơ nháp và báo cáo kiểm chéo |

## Đưa lên Vercel + Convex + Clerk + Render

1. **Render:** tạo Docker Web Service từ repo, build context là gốc repo, Dockerfile `CPA2_App/Dockerfile`; health check `/health`. Có Blueprint ở `CPA2_App/render.yaml`. Tạo secret `CPA2_SERVICE_KEY`. Không đưa secret vào Dockerfile. `.dockerignore` chỉ cho phép mã và KB cần thiết, loại dữ liệu niên luận, bảng điểm thật và `.env` khỏi build context.
2. **Clerk:** tạo application, bật phương thức đăng nhập mong muốn và cấu hình tích hợp Convex theo [hướng dẫn chính thức](https://docs.convex.dev/auth/clerk). Khi dùng JWT template, template phải có tên `convex`.
3. **Convex:** từ `CPA2_App/web`, chạy `pnpm convex:dev` để liên kết deployment; đặt `CLERK_JWT_ISSUER_DOMAIN`, `CPA2_API_URL` (URL Render) và cùng `CPA2_SERVICE_KEY` trong dashboard Convex. `convex/auth.config.ts` dùng audience `convex`. Khi phát hành chạy `pnpm convex:deploy`.
4. **Vercel:** chọn Root Directory `CPA2_App/web`, framework Next.js, Node.js 24, Install Command `pnpm install --frozen-lockfile`, Build Command `pnpm build`. Cấu hình `NEXT_PUBLIC_CONVEX_URL`, `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`. Không cần đưa khóa Python sang trình duyệt hoặc Vercel khi dùng Convex.
5. Thêm domain Vercel vào cấu hình Clerk và kiểm tra đăng nhập bằng hai tài khoản. Mỗi tài khoản chỉ thấy dữ liệu của mình; thử xóa dữ liệu và kiểm tra không còn file/hội thoại/phiên bản của tài khoản đó.

Chế độ demo luôn bị vô hiệu hóa trong `NODE_ENV=production`, kể cả khi vô tình đặt `CPA2_DEMO_MODE=true`. Khi chưa có Clerk/Convex, production hiển thị trang chờ cấu hình, không mở quyền truy cập tạm.

Không commit/push hoặc tạo dịch vụ trả phí tự động trong phiên triển khai này. Việc publish cloud cần tài khoản/dự án và cấu hình môi trường tương ứng.

## Kiểm tra

```powershell
cd CPA2_App/api
./.venv/Scripts/python.exe -m unittest discover -s tests -v
cd ../web
pnpm test
pnpm typecheck
pnpm build
cd ../..
./CPA2_App/api/.venv/Scripts/python.exe CPA2_App/scripts/verify_runtime.py
./CPA2_App/api/.venv/Scripts/python.exe CPA2_App/scripts/verify_ocr.py
python CPA2_App/scripts/verify_research.py
./CPA2_App/api/.venv/Scripts/python.exe CPA2_App/scripts/security_check.py
```

`verify_research.py` chạy các bộ validate trên bản sao tạm để không thay báo cáo, corpus, gold hoặc dữ liệu khảo sát đang chỉnh trong repo. Log ghi ở thư mục tạm được in ở cuối; mỗi bộ có thời hạn 10 phút. Timeout cần được báo riêng, không tính là đạt.

Ứng dụng dùng môi trường Python riêng và `api/requirements.lock` để khóa cả phụ thuộc gián tiếp. `security_check.py` đối chiếu các gói trong môi trường chạy với OSV; phía web dùng `pnpm audit --prod`.

`scripts/browser-check.cjs` kiểm tra dashboard → hỏi đáp → chứng chỉ → sửa/lưu bảng điểm → đề xuất → tra cứu → lịch sử → mobile → xóa, gồm kiểm tra CSRF. Cần sẵn Playwright và trình duyệt; đặt `CPA2_RUNTIME_MODULES` nếu dùng thư viện từ runtime bên ngoài, `CPA2_BROWSER_EXE` nếu dùng Edge/Chrome có sẵn. Chạy trong khi phiên demo đang mở.

## Giới hạn và giai đoạn tiếp theo

- Phạm vi CNTT K49; không tích hợp hệ thống Phòng Đào tạo, không nhập SQL dump hoặc hồ sơ thật từ niên luận.
- OCR có độ phủ giới hạn; mẫu sai hoặc dữ kiện chưa chắc cần được bổ sung thủ công từ bảng điểm gốc. Xác nhận của người dùng không tự làm các dòng thiếu trở thành chắc chắn.
- Các ảnh tải thành công nhưng chưa đăng ký tác vụ có thể còn trong Convex Storage nếu mạng gián đoạn; cần rà soát Storage khi vận hành thử nghiệm. Chức năng xóa dữ liệu xử lý các ảnh đã đăng ký dưới tài khoản.
- Chưa tích hợp dự báo điểm, AI API, Stripe, Resend hoặc Supabase. Terra/Sol/Gemini Flash là định hướng sau khi luồng cơ bản ổn định; cần xác minh model API trước khi thêm. LLM chỉ tham gia parser/verbalizer, kết luận vẫn do solver và hậu kiểm.
- Docker và đăng nhập cloud cần kiểm thử thực tế trên tài khoản triển khai trước khi coi là nghiệm thu online.
