# Trạng thái triển khai CPA² — cập nhật 26/10/2026

## Rà soát nguồn và chứng chỉ — 26/10/2026

Đã tái hiện và sửa: số quyết định không có trong corpus (`QĐ326`, `QĐ53390`) bị ghép nhầm sang văn bản khác; câu không có bằng chứng vẫn nhận ba nguồn điểm 0; chứng chỉ thiếu ánh xạ nguồn vẫn qua hậu kiểm; giới hạn 20 bước bỏ mất kết luận cần giải thích; và annotation `why` có thể được hiển thị dù atom tương ứng không đúng trong mô hình.

Tra cứu nay khớp nguyên số quyết định, bỏ nguồn điểm 0. Grounding kiểm tra passage thực sự có trong corpus, đúng rule và địa chỉ văn bản; xóa dữ liệu grounding cũ khi chạy lại. Thiếu nguồn trả `BLOCKED/GROUNDING_SOURCE_INVALID`. Chứng chỉ giữ toàn bộ source trace, đưa kết luận TRUE lên đầu, chỉ giữ atom đúng trong cautious model (TRUE) hoặc mô hình đại diện (verdict khác). Đây là trace nguồn, chưa phải bộ kiểm chứng chứng minh độc lập.

Trích đoạn lặp được dẫn về bước đầu cùng rule, vẫn giữ địa chỉ nguồn cho từng bước. Hồ sơ tổng hợp `sv_lvtn` có 350 bước, khoảng 81,8 KB; ca giả lập gồm 78 môn có 389 bước, khoảng 90,1 KB. Kiểm thử đặt ngân sách 96 KiB/chứng chỉ; 100 chứng chỉ mẫu lớn khoảng 8,59 MiB, dưới giới hạn đọc/trả 16 MiB của Convex ([tài liệu chính thức](https://docs.convex.dev/production/state/limits)). Không cắt ngầm trace để đạt giới hạn.

Kiểm thử riêng source/ranker: 15/15; API: 18/18; runtime đóng gói đạt, KB `bc22650d280a402b`; OSV kiểm 29 gói, không ghi nhận advisory. Huấn luyện lại trên train/dev vẫn tái tạo hash model `7a3f1d7e195e511141873c69710d76ce7d49ddbdaac07662d243059e05cf08ec`. Không thay trọng số, luật ASP, nhãn nguồn, gold hoặc split; không dùng lại holdout để điều chỉnh. Các số Recall ở mục tiếp theo vẫn giữ nguyên và chưa đạt điều kiện nghiệm thu đầy đủ.

Hồi quy cuối trên bản sao độc lập: **19/19 bộ đạt**, gồm OCR đầy đủ 558,8 giây và đề xuất 155,1 giây; log ở `web/.vercel/rag-source-final-20261026/` (không commit). Lượt đang chạy trước khi hoàn tất bản sửa đã dừng, không tính vào kết quả này. Các giới hạn kiểm thử và điều kiện nghiệm thu nghiên cứu giữ nguyên.

## Cải thiện RAG theo kế hoạch — 26/10/2026

Chỉ tiêu giữ nguyên theo `Ke_hoach_nghien_cuu_CPA2_24_tuan.xlsx`, sheet `Kế hoạch 24 tuần`, F15:H15: truy hồi đúng nguồn; Recall@1 ≥ 0,80, Recall@5 ≥ 0,95 trên test. **Chưa đủ điều kiện ghi hoàn tất nghiệm thu.**

| Bộ đánh giá | BM25 cũ R@1 / R@5 | RAG mới R@1 / R@5 | Diễn giải |
|---|---|---|---|
| Dev RAG 24 câu | 19/24 / 21/24 | 23/24 / 24/24 | Dùng để chọn trọng số, không phải kết quả test |
| Test cũ 24 câu | 16/24 / 22/24 | 17/24 / 23/24 | 70,8% / 95,8%; chỉ R@5 đạt ngưỡng; tập đã được xem, chỉ dùng đối chiếu |
| 29 câu survey giữ lại | 10/29 / 17/29 | 14/29 / 23/29 | 48,3% / 79,3%; cả hai chỉ tiêu còn chưa đạt |

RAG mới kết hợp BM25 toàn đoạn, phần nội dung bỏ tiêu đề lặp, phần mở đầu, cửa sổ từ, độ phủ từ theo IDF và thực thể mã học phần. 67/77 câu **train tổng hợp** được gán đoạn nguồn liên quan để làm ví dụ truy hồi; 10 câu ngoài phạm vi/thiếu ngữ cảnh không được dùng ép nguồn. Trọng số chọn trên 24 dev (10.000 cấu hình không âm, seed 21). Lệnh huấn luyện lại tái tạo đúng hash model `7a3f1d7e195e511141873c69710d76ce7d49ddbdaac07662d243059e05cf08ec`.

Production chỉ dùng thư viện chuẩn Python; không thêm API AI hoặc encoder nặng. Đo cục bộ: lượng cấp phát Python tăng tối đa khoảng 19,6 MiB khi dựng chỉ mục, trung bình khoảng 6,8 ms/lượt tìm của ba câu mẫu (không phải cam kết độ trễ/RAM toàn dịch vụ). Câu ví dụ tổng hợp chỉ phục vụ xếp hạng, không được trả ra như văn bản quy chế. Grounding chứng chỉ dùng `Retriever(ranked=False)`, độc lập hoàn toàn với trọng số tìm kiếm.

Các câu/nguồn tham chiếu của holdout được lưu và đóng băng trước dự đoán; có một errata gán nguồn học lực học kỳ (Điều 24 khoản 5 thay Điều 26 khoản 1), cũng được ghi trước dự đoán. Nhãn nguồn do trợ lý gán từ corpus, chưa được người thứ hai kiểm tra; dữ liệu survey đều tự khai SYNTHETIC. Không coi các số này là kết quả Q-Real thật hoặc độ đúng của kết luận học vụ. Tệp `retrieval_acceptance_v1.json` ghi rõ `acceptance_complete=false`; không sửa ô nghiệm thu trong Excel.

Đã kiểm tra: 19/19 bộ hồi quy nghiên cứu, 6/6 kiểm thử riêng cho ranker, API 15/15. Có kiểm tra đúng mã CT177, ràng buộc nguồn QĐ5339, nguồn trả ra chỉ lấy từ corpus, tách train/holdout theo nhóm và grounding không đổi. Runtime đóng gói đạt, KB `909ea81282ee3339`; OSV 29 gói Python không ghi nhận advisory. Bằng chứng số đo và tập dữ liệu nằm ở `CPA2_KhaoSat/w14_rag/evaluation_ranked_v1_*.json`, `rag_survey_*_v1.json`, `retrieval_model_v1.json`.

Đã phát hành API trên Render: commit `ca3c7285c622b037fa2a58905ee3ae33532f093d`, deploy `dep-dbf3je0473hc73bnp8tg`, live; HTTP health và từng kết quả thử đều xác nhận KB `909ea81282ee3339`. Endpoint lookup trả đúng `ctdt_k49:CT177` với tiên quyết CT101; câu chỉ định QĐ5339 chỉ trả passage QĐ5339. Kiểm lại ca TC công nhận thiếu/0/27 cho UNKNOWN/TRUE/FALSE như trước. Browser trên website công khai kiểm qua Clerk → Convex → Render, chứng chỉ, lịch sử, lưu hồ sơ và tra cứu CT177 đạt; ảnh `cloud-rag.png` đã được xem để xác minh. Đã xóa dữ liệu cùng hai tài khoản Clerk thử nghiệm và kiểm tra state rỗng. Frontend không cần thay đổi cho lần phát hành backend này.

## Bản sửa sau rà soát

- Đã sửa cơ chế dữ kiện thiếu: thời gian học chỉ được coi là đã khai báo khi có cả `da_hoc_nam2` và `tc_cong_nhan`. Ca 8,5 năm: thiếu/null TC công nhận → UNKNOWN kèm câu hỏi bổ sung; 0 → TRUE; 27 → FALSE. API có ca hồi quy tương ứng. Giao diện thêm ô TC công nhận/chuyển đổi, phân biệt để trống và số 0. Chỉ hồ sơ demo giả lập mới khai báo sẵn 0, không áp mặc định cho hồ sơ nhập của người dùng.
- OCR chỉ cần verdict nay dùng hai phép kiểm tra tồn tại answer set thay vì liệt kê/lưu mọi answer set. Đã kiểm tra tương đương TRUE/FALSE/UNKNOWN/UNSAT và ca 2^25 thế giới tiềm năng. Đường tạo chứng chỉ và missing evidence vẫn giữ nguyên.
- Sửa đọc ô TC tích lũy: dùng crop theo nhãn trên ảnh và một lượt OCR chữ số, có ngưỡng confidence, không suy số in từ tổng điểm/môn. Ca sạch đã đọc lại đúng các giá trị 111/161 bị lỗi trước đây; kiểm tra G11 cả hai hồ sơ đạt.
- RAG bổ sung các viết tắt CBHV/CBHT/KHHT/đk/dk từ ngôn ngữ của tập train tổng hợp. Các thử nghiệm BM25 chỉ dùng dev; chưa có bằng chứng đạt mục tiêu Recall, chưa thay chỉ tiêu bằng số của tập train.
- `Q-real.csv` do người dùng cung cấp có 40 dòng, 138 câu; cả 40 dòng ghi rõ nguồn SYNTHETIC. Bộ đã ẩn danh, khử trùng và chia theo nhóm người trả lời/câu trùng: train 77, dev 32, test 29. Không nhập vào Q-Real thật, không cộng vào chỉ tiêu 400; nhãn ý định giữ từ CSV trước khi chạy mô hình.
- Đã huấn luyện baseline ý định Naive Bayes cục bộ: 77 train, chọn alpha trên 32 dev; đúng 10/32 (31,25%). Chưa chạy test, chưa tích hợp mô hình yếu này vào production. Không fine-tune LLM, không gọi API, không để mô hình tự kết luận học vụ. Tệp dữ liệu, manifest và trọng số ở `CPA2_KhaoSat/w20_benchmark/qreal/synthetic_survey/`.
- API 13/13, Convex 7/7, TypeScript và production build đạt; audit web không ghi nhận lỗ hổng, OSV 29 gói Python không có advisory. Runtime đóng gói đạt, KB `ec1200bb64cca6b6`.
- Hồi quy đầy đủ trên bản sao ổn định: **18/18 bộ đạt**; OCR đầy đủ hoàn tất trong 202,6 giây, giữ nguyên cổng đúng fact ≥99% và không kết luận sai. Log riêng từng script ở `CPA2_App/web/.vercel/research-fix-final/` (không commit). Sau đó kiểm thêm toàn bộ 4 test xử lý survey/không rò tập, đều đạt. 18/18 không có nghĩa Recall RAG đã đạt: dev vẫn 19/24 và 21/24.
- Đã triển khai: Vercel production `dpl_2NkMmoD6fanoXHGTge7FSGhSEeKY`, mã giao diện `b5e2d48`; Render `dep-dbf2jk7b9u1s73bdd3t0`, mã container `0ca6d1f`, live. Sau lượt build đầu API còn phục vụ hash cũ; đã build lại có xóa cache và in hash KB ngay trong Docker build, rồi xác minh HTTP thực tế trả `ec1200bb64cca6b6`.
- Nghiệm thu cloud sau bản sửa: ca 8,5 năm thiếu/null TC → UNKNOWN và `missing_facts=[qua_thoi_gian_toi_da]`; 0 → TRUE; 27 → FALSE. OCR qua Convex Storage/scheduled action → Render → bản nháp 17 dòng đạt. Trình duyệt kiểm lại đăng nhập, chứng chỉ, lịch sử sau tải lại, sửa điểm + khai báo TC=0 + lưu, tra cứu và mobile; không có lỗi JavaScript. Đã xóa dữ liệu Convex và hai tài khoản Clerk thử nghiệm, kiểm tra state rỗng.
- Thử nghiệm bổ sung **không được phát hành**: định tuyến RAG theo quy tắc nguồn đạt dev 23/24, 24/24 nhưng test báo cáo một lần chỉ đạt 14/24, 22/24, chưa đạt 0,80/0,95. Đã loại toàn bộ thay đổi định tuyến và giữ retriever đã kiểm thử; không sửa tiếp theo câu test. Số dev cao của phương án bị loại không được dùng làm kết quả production. Thử baseline ý định embedding cục bộ trên cùng train/dev cũng thấp (7/32 dev), nên giữ baseline Naive Bayes 10/32 ở mức nghiên cứu; test survey vẫn chưa chạy.

Gold, split benchmark và sáu hồ sơ gốc đã đóng băng được giữ nguyên. Các ca dương tính cần biết TC chuyển đổi dùng bản sao khai báo rõ 0 trong helper kiểm thử; không sửa gold để ép kết quả. Vì nguồn hồ sơ benchmark cũ thiếu trường này, kết quả benchmark sau bản sửa có thể từ chối nhiều hơn và phải được báo đúng theo dữ liệu gốc.

## Rà soát lại lõi CPA² — 25/10/2026

**Chưa đủ điều kiện kết luận lõi đã hoàn tất.** Các bộ kiểm thử hiện có đạt không có nghĩa đã bao phủ mọi tình huống thiếu dữ kiện.

- Phát hiện đã tái hiện: `tc_cong_nhan` bị bỏ trống được KB xem như 0 (`qd3266_r_formal_v1.lp`, quy tắc `giam_hk(0) :- not tc_cong_nhan(_).`). Trên bản sao hồ sơ giả lập `sv_lvtn`, đặt `da_hoc_nam2=17` (8,5 năm): bỏ trường `tc_cong_nhan` cho TRUE và không yêu cầu bổ sung; khai báo 0 cho TRUE; khai báo 27 cho FALSE. Thiếu thông tin có khả năng đổi kết luận nhưng hệ thống không trả UNKNOWN. Lỗi có ở cả mã khảo sát và mã đóng gói; hai trường hợp thiếu/27 đã được tái hiện thêm trên API Render live với cùng kết quả. Lượt rà soát này chưa sửa luật hoặc phát hành bản vá.
- RAG chạy lại trên dev: Recall@1 = 19/24 (0,79), Recall@5 = 21/24 (0,88); chưa đạt mục tiêu 0,80 / 0,95 dù bộ kiểm tra grounding kết thúc với exit 0. Hậu kiểm nguồn đạt và chất lượng truy hồi tự do là hai tiêu chí khác nhau.
- Benchmark G-Truth dev chạy lại, không chỉnh gold/test: 58 ca, không có TRUE/FALSE sai, coverage 91,4%; đúng gold đóng băng 57/58, đúng theo errata có sẵn 58/58. Đây là số dev, không phải kết quả test độc lập.
- Kiểm tra mới: API 12/12, Convex 7/7, TypeScript đạt; runtime đóng gói chạy được tốt nghiệp, điều kiện luận văn, đăng ký, đề xuất và tra cứu, hash KB `2e7757765cfa09ae`. Các file lõi Python được đối chiếu giữa thư mục làm việc và nhánh triển khai đều trùng.
- Website trả HTTP 200; API cloud trả TRUE với 20 bước chứng minh cho hồ sơ giả lập và UNKNOWN cho câu học phí; API demo production bị chặn 403.
- Bộ hồi quy mới chạy trên bản sao tạm, đặt `OMP_THREAD_LIMIT=1`: 16/17 bộ đạt (tuần 5–14 và 16–21); tuần 15 OCR vẫn timeout sau 600 giây. Tiến trình OCR có thời điểm dùng khoảng 4,8 GB RAM; chưa khoanh vùng được hàm gây chậm, nên chưa quy nguyên nhân chỉ cho Tesseract. Log lượt chạy: `C:/Users/ASUSPC~1/AppData/Local/Temp/cpa2-research-check-s3azdacq`. Không sửa dữ liệu/gold/báo cáo khảo sát gốc.

Các việc nghiên cứu còn mở nằm trong `CPA2_KhaoSat/Viec_ton_dong.md`: đối chiếu bảng điểm thật/mã miễn, xác nhận nguồn và cách hiểu quy chế, nhãn độc lập, đánh giá test/benchmark, parser LLM và kế hoạch nhiều học kỳ. Không đồng nhất việc website chạy được với việc toàn bộ luận văn đã nghiệm thu.

## Đã kiểm tra

| Hạng mục | Kết quả |
|---|---|
| API Python trong môi trường riêng | 13/13 kiểm thử đạt sau bản sửa |
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
| Hồi quy khảo sát | 18/18 bộ validate đạt sau bản sửa; OCR đầy đủ 202,6 giây |

Các bộ khảo sát chạy trên bản sao riêng. Không sửa gold hoặc báo cáo khảo sát gốc để làm cho kiểm tra đạt. Các lượt trước bản sửa đã timeout và không được tính là pass; lượt mới hoàn tất đầy đủ sau khi sửa đường giải ba trị và đọc ô TC tích lũy.

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
