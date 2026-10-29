# Nguồn RAG và thử nghiệm hybrid — 29/10/2026

Giữ ranker v3; thay nguồn hiển thị/trích dẫn bằng `corpus_source_v1.jsonl` (228 passage), tách 144 văn bản cũ sang tệp kiểm toán và không nối ghi chú R-Formal vào đoạn trích. Đối chiếu ảnh PDF và chép/sửa 10 passage; thêm Điều 22 khoản 4 bị OCR ghép vào khoản 3, có phân giải câu hỏi tự do và tra địa chỉ điều/khoản chính xác. Phần OCR chưa đối chiếu được gắn nhãn; có hai PDF gốc theo trang tại `web/public/quy-che`, đối chiếu SHA-256 trong `source_pdf_manifest_v1.json`. Chỉ là quy chế công khai, không phải bảng điểm sinh viên. Không đổi solver/ánh xạ chứng minh.

Kho quy chế yêu cầu bổ sung khi nói “môn này/học phần đó” mà thiếu mã; câu hỏi cần kết luận cá nhân được hướng dẫn sang Tư vấn học vụ với hồ sơ. Có nút chọn cách hỏi mẫu. Không chuyển điểm xếp hạng thành xác suất đúng.

Đã thử v4 (nguồn sạch + từ vựng) và v5 (từ vựng + E5 ONNX int8, RRF, reranker tuyến tính 15 đặc trưng). Hai thử nghiệm không được triển khai: trên 29 câu đã biết, v3/v4/v5 lần lượt R@1=15/15/15 và R@5=26/26/25; trên 24 câu đã biết, lần lượt 18/17/18 và 23/22/23. Giữ nguyên nhãn/báo cáo và không chọn lại trọng số sau TEST. Không cài thêm model, ONNX hoặc SentencePiece trên Render.

Bộ kiểm tra mới tập trung các nguồn vừa sửa: 12 câu tìm nguồn + 4 ca xử lý thiếu thông tin/tham chiếu không có. Kết quả thật 5/12 tìm đúng trong top 3, 4/12 đúng hạng đầu; 4/4 ca kiểm soát đúng, tổng 9/16. Đây là câu tổng hợp, nguồn do AI gán trước dự đoán, một người gán; chưa phải tập nghiệm thu độc lập. Các ca trượt giữ nguyên. Xem `RAG_SOURCE_CLEANUP_20261029.md` để biết phương pháp, tái lập và giới hạn.

Kiểm tra cục bộ: API 50 ca (49 đạt, 1 bỏ qua do thiếu pypdf tạo fixture mật khẩu), gồm 6 ca nguồn sạch/phân giải/hỏi lại; ranker/grounding 21/21. Web 18/18, TypeScript và build đạt. Runtime đóng gói đạt, KB `ca4c5987580ad591`. Không chạy lại benchmark OCR toàn bộ.

Production code `f4e19243c5d3ea2acb5e5e673bf36ad57d702376`: Render `dep-dbhh6mo8v5cc738g0lg0` live; Vercel `dpl_DZwANGM37edLGifg6JEF3Eb3f4hs` READY, main domain đã gắn; health xác nhận `ca4c5987580ad591`. Không thay Convex. Kiểm tra bằng tài khoản tổng hợp: đăng nhập, kết luận/proof, lịch sử và sửa hồ sơ vẫn đạt; tra nguồn giữ CT177, lọc Điều 14; tra khoản 4 Điều 22 trả đúng nội dung công bố điểm và liên kết PDF trang 14; câu thiếu mã hiện yêu cầu bổ sung và nút điền câu mẫu. Tải lại hai PDF production và kiểm tra kích thước/SHA-256 khớp bản gốc. Đã xem ảnh `cloud-source-corrected.png` và `cloud-source-clarification.png` trong `web/.vercel`; desktop/mobile đạt, không có lỗi JavaScript.

Hai lượt browser đầu dừng do selector của kịch bản cũ: Điều 14 sau làm sạch không còn dài để mở rộng; selector đoạn trích cũng khớp thêm đoạn chứa link PDF. Đã sửa selector, chuyển kiểm tra mở rộng sang điểm W, chạy lại riêng luồng nguồn và đạt (exit 0). Không tính hai lượt đầu là đạt. Đã xóa cả hai tài khoản thử và dữ liệu Convex của chúng; không dùng bảng điểm thật trên cloud.

# Cải tiến RAG ngày 29/10/2026

Runtime tra cứu chuyển sang `retrieval_model_v3.json` với `rag_survey_train_sources_v2.json`, áp dụng bản soát nguồn TRAIN đã có: 41 câu được đối chiếu với errata, bỏ 7 ví dụ chưa có nguồn xác nhận khỏi 67 ví dụ dương, còn 60 câu thuộc 22 nhóm. Chọn trọng số bằng DEV và TRAIN loại toàn bộ ví dụ cùng nhóm; không dùng nhãn TEST để chọn trọng số. Bản thử v2 dùng nhãn cũ được giữ riêng và không triển khai. Hai bộ TEST đều đã biết, chỉ là chẩn đoán, chưa phải đánh giá độc lập mới.

Trên 29 câu tổng hợp: R@1 14/29 → 15/29, R@5 23/29 → 26/29. Trên 24 câu TEST thủ công: 17/24 → 18/24 và 23/24 giữ nguyên. Tổng 53 câu: R@1 31 → 33, R@5 46 → 49. DEV của v3 đạt 20/24 và 23/24. Chưa đạt tiêu chí 80%/95% trên tập khảo sát; không tuyên bố RAG đã nghiệm thu hay dùng số này làm độ đúng câu trả lời. Nhãn TEST chưa có chuyên gia kiểm tra độc lập. Chi tiết ở `CPA2_KhaoSat/w14_rag/RETRIEVAL_V3.md` và các báo cáo JSON ngày 20261029; giữ nguyên số liệu và nhãn gốc v1.

Thêm ràng buộc số điều chính xác, giữ mã môn khi tra CTĐT, mã không có không lấy tiên quyết của môn khác. Đoạn trích tra cứu là một lát cắt nguyên văn theo từ/cụm từ câu hỏi, tối đa 300 ký tự; trả chỉ số đầu/cuối và toàn passage, giao diện có Xem toàn bộ đoạn nguồn. Nguồn chứng minh cá nhân vẫn lấy từ certificate và hậu kiểm.

Kiểm tra cục bộ: 21/21 ca ranker/grounding; tái lập dữ liệu TRAIN từ errata trùng khớp; huấn luyện lại tái lập đúng hash mô hình `b27cde64fa4b06c5ac1bd77238a71c50e33c2343cbeac28be11e0fe04426a66c`. API 44 ca (43 đạt, 1 bỏ qua do thiếu pypdf dựng fixture mật khẩu) với bản thử v2; runtime đóng gói v3 đạt, KB `fd34e20b8fbf5fad`. Web 18/18, TypeScript và build đạt. Không chạy lại benchmark OCR toàn bộ.

Production commit `333b59841d9bf44d2298bd6c3597897a623ff509`: Render `dep-dbhgmiu1egvs73fhb420` live; Vercel `dpl_128J5gucd5a5NEAJ1TqWUR15XDTy` READY và gắn https://cpa2-web.vercel.app. Health xác nhận KB `fd34e20b8fbf5fad`. Chạy lại 4 ca API tra cứu với v3 đạt. Không đổi Convex trong lần này.

Browser production bằng hồ sơ tổng hợp: đăng nhập Clerk, Convex gọi Render, trả kết luận có chứng minh và lưu lịch sử; tra CT177 giữ đúng tiên quyết CT101; yêu cầu QĐ3266 Điều 14 chỉ trả các passage Điều 14; mở toàn bộ đoạn nguồn và kiểm tra đoạn trích là chuỗi con nguyên văn, không quá 300 ký tự. Đã xem ảnh `web/.vercel/cloud-rag-v3.png`; bố cục desktop/mobile đạt, không có lỗi JavaScript. Đã xóa cả hai tài khoản thử và toàn bộ dữ liệu Convex của chúng. Không đưa bảng điểm thật lên cloud.

# Trạng thái triển khai CPA² — cập nhật 28/10/2026

## Sửa, duyệt và lưu tiến trình rà soát OCR — 28/10/2026

Đã phát hành `d2c3a7b17b67dc4f5b7ea3017e30ae63ee705b04`: Render `dep-dbgsjaec6qcc73chq9p0` live; Convex production cập nhật; Vercel `dpl_ApSGgPwRbGE3CqTC2PvbZwEJhh96` READY tại https://cpa2-web.vercel.app. Health và runtime đóng gói xác nhận KB `541d234241cb14f6`. Hash runtime nay gồm bộ đọc PDF, worker và bộ kiểm tra rà soát OCR để phản ánh đường nhập dữ kiện đã sửa.

Từng dòng có Sửa & duyệt: sửa mã học phần, tín chỉ, điểm thang 10 và điểm chữ, rồi bấm Duyệt dòng này. Server kiểm tra mã/TC theo CTĐT, miền điểm và đối chiếu điểm chữ, sau đó dựng lại hồ sơ và chạy lại kiểm chéo học kỳ/tích lũy. Dòng đạt được đánh dấu Đã duyệt; nếu vẫn có lỗi học kỳ hoặc một lần học khác chưa chắc, cảnh báo liên quan còn giữ. Có bổ sung môn thiếu vào học kỳ được chọn, loại dòng nhận nhầm (giữ bản trước trong lịch sử), sửa/duyệt số tổng theo bảng điểm gốc và xác nhận cuối cùng trước khi lưu hồ sơ. Dòng miễn CC004 cần xác nhận Phòng Đào tạo; mã ngoài CTĐT chưa được duyệt như một môn đã ánh xạ.

Điểm đã duyệt ghi source=manual_review và reviewed_by_user; độ tin cậy OCR gốc không bị nâng giả lên 100%. Dữ liệu nhận diện gốc và các lần sửa được giữ trong ngữ cảnh rà soát. Nút đối chiếu toàn bảng không thay thế kiểm tra các dòng còn lỗi. Các hồ sơ OCR cũ thiếu ngữ cảnh cần chạy OCR lại một lần. Không suy lại điểm số từ chuỗi raw.

Tiến trình trên tác vụ OCR được lưu theo tài khoản, tiếp tục sau reload; kiểm tra phiên bản ngăn hai tab ghi đè âm thầm và ngăn tác vụ đang chạy khôi phục dữ liệu đã xóa. Với bản OCR có uploadId, review và save dùng báo cáo server đang lưu, không tin việc client xóa cờ cảnh báo. Muốn lưu điểm đã chỉnh phải qua Sửa & duyệt; không thể đổi metadata để bỏ qua các dòng chưa giải quyết. Hồ sơ sau lưu vẫn có phiên bản riêng.

Kiểm tra: 44 ca API (43 đạt, 1 bỏ qua fixture mật khẩu thiếu pypdf), gồm 9 ca sửa/duyệt; chạy lại 9 ca sau kiểm tra cuối đạt. Web 18/18, TypeScript và build đạt; runtime đóng gói đạt. Các nhóm lỗi OCR C/E/F/G đạt, gồm đọc sai GDQP/GDTC, thiếu dòng, miễn tín chỉ và sai số tổng. Không chạy lại toàn bộ benchmark nghiên cứu. Checklist React được áp dụng cho hooks, lỗi inline, nhãn biểu mẫu và chỉ dựng danh sách chọn môn khi mở editor.

Browser production bằng dữ liệu tổng hợp:

- Hồ sơ một dòng CT101 có OCR confidence thấp: sửa 9,7/B → server từ chối và hiển thị lỗi ngay trong editor; đổi thành 9,7/A → được duyệt, hết cảnh báo, xác nhận cuối bảng → lưu → reload giữ đúng điểm và nguồn manual_review. Đã xem ảnh `web/.vercel/cloud-approval-edit.png` và `cloud-approved-saved.png`.
- Tài khoản chưa có hồ sơ tải PDF tổng hợp, nhận 17 dòng/7 cảnh báo; sửa và duyệt một dòng theo gold, reload tự mở bản rà soát còn dang dở, giữ dấu đã duyệt và lịch sử sửa. Các cảnh báo khác vẫn tồn tại. Lượt kiểm tra đầu dừng vì selector summary khớp cả cảnh báo và editor; đã sửa selector, kiểm tra lại trên cùng tác vụ OCR thành công, không tính lượt đầu là đạt.
- Truy vấn lại xác nhận hồ sơ đã lưu có CT101=97/A, ocr_pending=false, reviewed_by_user=true; tác vụ chưa hoàn tất của tài khoản kia có lịch sử một lần duyệt và thời điểm cập nhật để tiếp tục. Không có lỗi JavaScript. Đã xóa cả hai tài khoản kiểm thử và dữ liệu Convex, kiểm tra state rỗng. Chỉ dùng hồ sơ tổng hợp trên cloud.

## Hiển thị dòng OCR chưa chắc trong danh sách — 28/10/2026

Đã phát hành `20b257598d734187b822ef3146c3c423d26e775b` tại https://cpa2-web.vercel.app: Render `dep-dbgs15vlk1mc739bp21g` live; Vercel `dpl_GcA9JGBqfae6LTwhpMz9gCwdFPYn` READY, KB `3ba129435078c712`. Không thay schema Convex hoặc thuật toán chấp nhận điểm.

Các dòng OCR quan sát được nhưng chưa vào grades nay vẫn hiện cùng danh sách: tô vàng, xếp lên đầu, có mục Cần xem lại để mở học kỳ, lý do và OCR gốc. Điểm/tín chỉ đọc được hiện dưới dạng giá trị tạm để đối chiếu; ô không đọc được để trống, không đổi thành 0/F. Bao gồm mã ngoài CTĐT, dòng miễn CC004, mã chưa rõ và các lần học lại chưa chắc; không tạo môn mới chỉ từ mã thay thế suy đoán. Phần bảng dùng hàm ghép dữ liệu hiển thị, không chèn các giá trị tạm vào profile.grades. Các dòng này chưa có thao tác tự xác nhận thành điểm tin cậy; cảnh báo và điều kiện chặn lưu/tư vấn vẫn được giữ.

Backend thêm `report.dong_can_ra_soat`, tách biệt facts; worker và giao diện lưu hồ sơ cũng kiểm tra cờ này, nên đánh dấu reviewed không vượt qua bước rà soát. Báo cáo cũ vẫn hiển thị được các dòng từ chi_tiet, nhưng không suy điểm số bằng cách phân tích OCR raw. Ca PDF thật cục bộ có 29 môn trong grades và 9 dòng rà soát, tổng 38 dòng quan sát; không tải PDF thật lên cloud.

Kiểm tra: API 35 ca (34 đạt, 1 bỏ qua fixture PDF mật khẩu thiếu pypdf); web 15/15 (10 Convex, 5 kiểm tra ghép dòng). Có ca điểm chưa chắc không thành fact, điểm thiếu không thành 0, học lại giữ các lần quan sát, JSON metadata lỗi không làm hỏng bảng và chỉnh tay không tự xóa cảnh báo. TypeScript, build và runtime đóng gói đạt. Phần thay đổi này bổ sung báo cáo/giao diện; không chạy lại toàn bộ benchmark nghiên cứu đã ghi ở mục trước.

Browser production bằng tài khoản mới: mở hộp chọn PDF, tải một trang tổng hợp, nhận bản nháp → 17 dòng hiện trong bảng gồm 10 môn qua kiểm chéo và 7 dòng cảnh báo. Kiểm tra cảnh báo ở đầu bảng, mở details, điểm tạm không nằm trong input sửa facts và không nằm trong profile.grades; không có lỗi JavaScript. Đã xem ảnh `web/.vercel/cloud-first-upload.png`. Lượt khởi động browser đầu bị lỗi tiến trình máy cục bộ, không tính là đạt; lượt sau hoàn tất. Đã xóa tài khoản cùng dữ liệu kiểm thử. Cần tải lại trang và OCR lại PDF để nhận đầy đủ trường điểm tạm từ báo cáo mới.

## Sửa chặn dây chuyền khi thiếu dòng học kỳ cuối — 28/10/2026

Người dùng báo chỉ thấy 5 môn học kỳ đầu dù báo cáo có `tong_dong=37`, `nhan=6`, và nghi ngờ TC tích lũy từ HK2 23–24 đến HK1 25–26. Đã tái hiện cục bộ đúng mẫu này: từ tài liệu OCR của PDF 4 trang, bỏ một dòng 3 TC ở học kỳ cuối nhưng giữ số tổng in trên giấy → 37 dòng, 5 môn vào grades, tất cả các học kỳ sau HK1 bị gắn cờ TC tích lũy. Đây là ca tiêm lỗi tái hiện cơ chế, không khẳng định đã biết chính xác dòng bị bỏ sót trong lượt OCR cloud của người dùng.

Nguyên nhân: `_tich_luy` so sánh tổng tính từ các dòng không đầy đủ với tổng in đầy đủ. Khi CC004 còn hai khả năng tính tín chỉ, không có mốc chắc chắn sau học kỳ đầu, nên sai lệch cuối kỳ bị quy ngược cho mọi học kỳ từ HK2. Bản sửa chỉ tính/so tổng tích lũy khi từng học kỳ trong prefix có đủ tín chỉ theo tổng đăng ký; nếu thiếu tổng, thiếu TC dòng hoặc lệch tổng đăng ký, trả trạng thái chưa đủ dữ liệu tính tích lũy. Học kỳ thiếu dòng vẫn có `dong_an`/`hoc_ky_lech`, vẫn UNKNOWN; các kiểm tra điểm/GDTC/GDQP và ngưỡng confidence giữ nguyên.

Ca tái hiện sau sửa nhận 28 môn thay vì 5, vẫn 37 dòng và còn cờ HK1 25–26. Giao diện bổ sung tổng số dòng nhận diện, số môn qua kiểm chéo và học kỳ cần đối chiếu. Báo cáo thêm `doi_chieu_hoc_ky` với số tổng OCR, tổng từ các dòng và khả năng tính tổng tích lũy để khoanh vùng lỗi. Kết quả cũ không tự chạy lại; cần tải PDF lên để tạo bản OCR mới.

Mã phát hành `7d2ec0d05a06b27c3bc70014ded7a98855ef84f0`: Render `dep-dbgrnh8ae00c73d8ea2g` live, Vercel `dpl_BnxWr9oCXzRHBWSdAd93ASJTRPPF` READY và domain chính. HTTP health và kết quả OCR cloud đều xác nhận KB `4514b749ea5b5243`. Không đổi schema Convex hoặc cấu hình dịch vụ.

Đã kiểm tra: API 30 ca cũ đạt 29 / bỏ qua 1 fixture mật khẩu thiếu pypdf, thêm 1 ca hồi quy mới với hai biến thể tổng đã biết/mất; CI API và web cho mã này success. Convex 10/10, TypeScript và build đạt. Các nhóm OCR C/E/F/G, gồm lỗi GDTC/GDQP, miễn tín chỉ và đọc sai điểm, đạt. Hồi quy OCR đầy đủ trên bản sao riêng hoàn tất 361,6 giây, đạt cổng 833/834 fact được chấp nhận đúng và độ phủ kết luận 1/18; còn lỗi điểm ở ảnh nghiêng như trước. Log: `C:/Users/ASUSPC~1/AppData/Local/Temp/cpa2-partial-cumulative-final-of79r2zc/ocr.log`. Lượt thử ban đầu thất bại vì thiếu bộ nhớ khi chạy song song, không tính là đạt; lượt build sau giới hạn Go threads và lượt OCR chạy riêng mới là kết quả hoàn tất.

Browser production: tài khoản mới chưa có hồ sơ → consent → bấm mở hộp chọn tệp → PDF tổng hợp một trang → OCR → hiển thị rõ 17 dòng / 10 môn, ba học kỳ trong báo cáo và dữ kiện từng học kỳ. `needs_review`/`ocr_pending` vẫn true, không có lỗi JavaScript; đã xem ảnh `web/.vercel/cloud-first-upload.png`. Kiểm tra này xác nhận luồng cloud và phần chẩn đoán; ca mất dòng cuối có miễn tín chỉ được kiểm tra ở mức dữ liệu tài liệu bằng fixture cục bộ và kiểm thử tự động. Đã xóa cả hai tài khoản giả lập và dữ liệu Convex. PDF thật vẫn chỉ xử lý cục bộ.

## Sửa nút chọn PDF cho tài khoản mới — 28/10/2026

Đã tái hiện trên website bằng tài khoản giả lập chưa lưu hồ sơ: input PDF bị disabled do điều kiện `!profile`, khiến bấm nút không mở hộp chọn tệp. Các lượt kiểm tra trước dùng tài khoản đã lưu hồ sơ nên bỏ sót trường hợp này; việc gọi setInputFiles cũng không chứng minh thao tác bấm mở hộp chọn tệp hoạt động.

Bản sửa `0224f12f041e5873fb9e2b93644a1c336df79811` bỏ điều kiện phải có hồ sơ khỏi nút tải tệp, thêm ô đồng ý xử lý dữ liệu ngay cạnh nút và gửi consent đến startOcr. Backend cho phép tài khoản mới OCR khi đồng ý rõ ràng, vẫn từ chối khi thiếu consent hoặc khai báo từ chối; các client cũ có hồ sơ đã consent tiếp tục dùng được. Không tự tạo hồ sơ giả để mở khóa OCR.

Convex production đã cập nhật; Vercel production `dpl_7NdKEjtsAoGr81hPE1hSFAPZ6Xun` READY, domain https://cpa2-web.vercel.app. API Render giữ bản 69be40f đã kiểm tra ở mục dưới. Kiểm thử Convex 10/10, TypeScript và build đạt.

Đã kiểm tra luồng người dùng mới trên website bằng script `scripts/cloud-first-upload.cjs`: đăng nhập tài khoản chưa có hồ sơ → tích consent → bấm nút và bắt sự kiện filechooser thật → chọn PDF tổng hợp một trang → Convex Storage → OCR → hiển thị bản nháp 17 dòng. Truy vấn lại xác nhận profile vẫn null, tác vụ done, `needs_review` và `ocr_pending` true; không có lỗi JavaScript. Đã xem ảnh `web/.vercel/cloud-first-upload.png`. Tài khoản và dữ liệu kiểm thử đã xóa, state rỗng. Cần tải lại trang đã mở để nhận giao diện mới.

## Đã phát hành PDF/OCR — 28/10/2026

Website production: https://cpa2-web.vercel.app. Mã phát hành `69be40fe79aa261d6f0bf241c7d04adbbb45fc27`, nhánh `codex/cpa2-web-deploy`. Render deploy `dep-dbgr2vei0phs738p9t5g` live; Vercel `dpl_5S6xnPnYFBr6rQco6rGEJbgDBiD7` READY và gắn domain chính. Convex production `exciting-cheetah-606` đã cập nhật. Health và kết quả OCR xác nhận KB `6b0e182eb2c27f5c`.

Lượt cloud đầu trên mã `b9cd336` trả HTTP 504 vì PDF 4 trang vượt giới hạn 120 giây; không tính là đạt. Bản sửa tăng riêng thời hạn OCR lên 240 giây, thời gian chờ Convex/API demo lên 250 giây; giới hạn 4 trang, 10 MB/tệp, tổng 20 MB và chặn dữ kiện chưa chắc giữ nguyên. Không nâng gói Render hoặc thay nguồn/quy tắc học vụ.

Đã kiểm tra trên trình duyệt website công khai bằng hai tài khoản Clerk giả lập: đăng nhập, tư vấn và chứng chỉ, lịch sử sau reload, sửa/lưu hồ sơ có consent, chọn PDF tổng hợp 4 trang → Convex Storage → scheduled action → Render → bản nháp OCR hiển thị. Tác vụ hoàn tất sau khoảng 142,7 giây tính từ lúc đăng ký đến log HTTP 200; nhận diện 51 dòng và đưa 30 điểm học phần vào hồ sơ, cả 30 khớp gold tổng hợp. Các dòng còn lại vẫn cần rà soát; đây là một ca kiểm thử, không phải độ đúng 100% cho mọi bảng điểm. `needs_review` và `ocr_pending` đều true. Đã xem ảnh `web/.vercel/cloud-pdf-review.png` để xác nhận giao diện thực tế.

Browser còn kiểm tra tra cứu CT177/CT101, desktop/mobile, không có lỗi JavaScript. Vercel không ghi nhận runtime error trong cửa sổ 15 phút sau phát hành; chưa cấu hình log drain riêng. Đã xóa dữ liệu Convex của tài khoản kiểm thử, kiểm tra state rỗng và xóa cả hai tài khoản Clerk. Chỉ PDF tổng hợp được tải lên cloud; PDF thật do người dùng cung cấp chỉ được xử lý cục bộ.

Kiểm tra nhánh đã ghép giữ bản sửa C19: API 29 đạt / 1 bỏ qua (thiếu pypdf cho fixture PDF có mật khẩu); Convex 9/9; TypeScript và build đạt; runtime đóng gói đạt; hồi quy OCR đầy đủ trên bản sao độc lập đạt trong 383,5 giây (833/834 fact được chấp nhận đúng, còn một lỗi điểm ở ảnh nghiêng, độ phủ kết luận 1/18). Log tại `C:/Users/ASUSPC~1/AppData/Local/Temp/cpa2-deploy-ocr-regression-tg9tdcg4/ocr.log`. Sau thay thời hạn, 5 kiểm thử biên PDF, Convex 9/9 và TypeScript tiếp tục đạt. GitHub Actions cho mã 69be40f: API và web đã success; job nghiên cứu toàn bộ tuần còn chạy lúc ghi nhận này, không báo toàn bộ CI đã hoàn tất.

Người dùng vào **Hồ sơ & bảng điểm → Nhận diện PDF / ảnh (OCR)** để tải tệp. Render free có thể cần vài phút; kết quả vẫn là bản nháp cần rà soát. Chưa tự đồng bộ điểm từ cổng trường. Các giới hạn nghiệm thu RAG ở dưới giữ nguyên.

## PDF bảng điểm và cải thiện OCR — kiểm tra cục bộ trước phát hành 28/10/2026

Đã thêm PDF vào giao diện tải bảng điểm, kiểm tra Convex Storage và API OCR. PDF được nhận diện bằng chữ ký tệp, dựng ảnh bằng pypdfium2 5.9.0 trong tiến trình worker có thời hạn 120 giây. Tổng PDF và ảnh không quá 4 trang; mỗi tệp tối đa 10 MB, tổng 20 MB; trang PDF dựng rộng 2448 px, tối đa 20 triệu điểm ảnh. PDF hỏng, cần mật khẩu hoặc quá giới hạn bị từ chối. Kiểm tra dung lượng và ảnh hiện có được giữ nguyên.

OCR bổ sung đọc riêng ô tổng tín chỉ đăng ký theo vị trí nhãn (kể cả tổng ở trang tiếp theo), đọc lại ô tín chỉ/điểm chưa chắc bằng crop một dòng và chuẩn hóa ký tự I/l thành 1 trong số học kỳ. Lượt đọc lại không thay một giá trị hợp lệ bằng giá trị khác chỉ để khớp điểm trung bình; bất đồng và dữ kiện chưa chắc vẫn bị giữ lại để rà soát. Không đổi ngưỡng confidence, luật ASP, CTĐT, gold hoặc ánh xạ CC004/GDTC. Khi ghép sang nhánh phát hành, giữ bản sửa C19 đã có: điểm chữ không được nâng độ tin cậy của điểm số chính xác GDQP.

Thử cục bộ trên PDF 4 trang do người dùng cung cấp, chỉ lưu kết quả trong `_rieng/` bị Git bỏ qua: HTTP 200 sau khoảng 19,1 giây; nhận diện 38 dòng học phần (gồm dòng miễn), đưa 29 điểm học phần vào hồ sơ; không còn cờ học kỳ lệch tổng tín chỉ hoặc dòng ẩn. Đối chiếu điểm thang 10 của cả 29 môn được nhận với bốn trang render không thấy sai. Đây là đối chiếu một tệp, chưa phải đánh giá độc lập. Còn 5 mã có confidence thấp (QP013, KL001E, ML014, ML018, ML021), TC025–027 ngoài CTĐT và CC004 chờ xác minh. Hồ sơ tiếp tục có `needs_review`, `ocr_pending`; không dùng kết quả này kết luận tốt nghiệp.

Kiểm tra đã hoàn tất:

- API nhánh triển khai: 29 kiểm thử đạt, 1 bỏ qua vì thiếu pypdf để dựng tệp có mật khẩu (30 ca tổng cộng); gồm PDF hỏng, quá 4 trang, PDF trộn ảnh vượt số trang, trang có hình học quá lớn và nhận diện theo chữ ký thay vì tên tệp.
- Convex 9/9, gồm tải PDF → scheduled action → multipart giữ nguyên nội dung/MIME → lưu bản nháp chờ rà soát (môi trường giả lập).
- TypeScript và production build đạt; runtime đóng gói đạt, KB `6b0e182eb2c27f5c`.
- HTTP OCR tổng hợp đủ 4 trang: PNG nhận đúng 50/50 fact được chấp nhận; PDF nhận đúng 35/35. Số dòng nhận diện đều 55. PDF vẫn có độ phủ thấp hơn ảnh gốc trong ca này.
- Hồi quy OCR đầy đủ trên bản sao tạm đạt: 833/834 fact được chấp nhận đúng (99,88%, cổng ≥99%). Vẫn có một sai lệch CT179 ở ảnh nghiêng tổng hợp (7,3 thay vì 7,5); không coi đạt ngưỡng là hoàn toàn không có lỗi. Chỉ 1/18 ca có kết luận xác định, còn lại UNKNOWN. Không thay báo cáo/gold khảo sát gốc. Log: `C:/Users/ASUSPC~1/AppData/Local/Temp/cpa2-pdf-ocr-regression-rx4dlfcs/ocr.log`.
- OSV: 30 gói trong môi trường Python, không ghi nhận advisory tại lượt kiểm tra.

Các số ở mục này ghi nhận trước phát hành. Kết quả cloud và kiểm tra trình duyệt sau phát hành nằm ở mục đầu; RAG giữ nguyên và chưa đạt các điều kiện nghiệm thu nghiên cứu ở mục dưới.

## Rà soát nguồn và chứng chỉ — 26/10/2026

Đã tái hiện và sửa: số quyết định không có trong corpus (`QĐ326`, `QĐ53390`) bị ghép nhầm sang văn bản khác; câu không có bằng chứng vẫn nhận ba nguồn điểm 0; chứng chỉ thiếu ánh xạ nguồn vẫn qua hậu kiểm; giới hạn 20 bước bỏ mất kết luận cần giải thích; và annotation `why` có thể được hiển thị dù atom tương ứng không đúng trong mô hình.

Tra cứu nay khớp nguyên số quyết định, bỏ nguồn điểm 0. Grounding kiểm tra passage thực sự có trong corpus, đúng rule và địa chỉ văn bản; xóa dữ liệu grounding cũ khi chạy lại. Thiếu nguồn trả `BLOCKED/GROUNDING_SOURCE_INVALID`. Chứng chỉ giữ toàn bộ source trace, đưa kết luận TRUE lên đầu, chỉ giữ atom đúng trong cautious model (TRUE) hoặc mô hình đại diện (verdict khác). Đây là trace nguồn, chưa phải bộ kiểm chứng chứng minh độc lập.

Trích đoạn lặp được dẫn về bước đầu cùng rule, vẫn giữ địa chỉ nguồn cho từng bước. Hồ sơ tổng hợp `sv_lvtn` có 350 bước, khoảng 81,8 KB; ca giả lập gồm 78 môn có 389 bước, khoảng 90,1 KB. Kiểm thử đặt ngân sách 96 KiB/chứng chỉ; 100 chứng chỉ mẫu lớn khoảng 8,59 MiB, dưới giới hạn đọc/trả 16 MiB của Convex ([tài liệu chính thức](https://docs.convex.dev/production/state/limits)). Không cắt ngầm trace để đạt giới hạn.

Kiểm thử riêng source/ranker: 15/15; API: 18/18; runtime đóng gói đạt, KB `bc22650d280a402b`; OSV kiểm 29 gói, không ghi nhận advisory. Huấn luyện lại trên train/dev vẫn tái tạo hash model `7a3f1d7e195e511141873c69710d76ce7d49ddbdaac07662d243059e05cf08ec`. Không thay trọng số, luật ASP, nhãn nguồn, gold hoặc split; không dùng lại holdout để điều chỉnh. Các số Recall ở mục tiếp theo vẫn giữ nguyên và chưa đạt điều kiện nghiệm thu đầy đủ.

Hồi quy cuối trên bản sao độc lập: **19/19 bộ đạt**, gồm OCR đầy đủ 558,8 giây và đề xuất 155,1 giây; log ở `web/.vercel/rag-source-final-20261026/` (không commit). Lượt đang chạy trước khi hoàn tất bản sửa đã dừng, không tính vào kết quả này. Các giới hạn kiểm thử và điều kiện nghiệm thu nghiên cứu giữ nguyên.

Đã phát hành API: commit `c88891be841a6775b7c39752a32f9e60f093717d`, Render deploy `dep-dbfa59ks728c73elpsug`, live. Docker build và HTTP `/health` đều xác nhận KB `bc22650d280a402b`. HTTP cloud kiểm qua QĐ326/QĐ53390/câu vô nghĩa → không nguồn; CT177 → CT101; QĐ5339 chỉ trả đúng văn bản; tốt nghiệp TRUE có 350 bước được grounding đầy đủ, kết luận ở đầu; ranh giới TC công nhận null/0/27 → UNKNOWN/TRUE/FALSE.

Luồng Clerk → Convex → Render đạt với hai tài khoản giả lập: từ chối truy cập ẩn danh/lưu không consent; giữ đủ source trace trong câu trả lời đã lưu; cách ly tài khoản; giữ phiên bản lịch sử; câu ngoài phạm vi UNKNOWN. Browser trên website công khai kiểm qua dashboard, hỏi đáp, hơn 20 bước chứng chỉ với `tot_nghiep` ở đầu, lịch sử sau reload, sửa/lưu điểm, CT177/CT101, desktop/mobile; không có lỗi JavaScript. Đã xem ảnh chứng chỉ và mobile. Lượt browser đầu timeout khi chờ sự kiện `load`; script nay chờ DOM rồi kiểm các điều khiển ứng dụng, lượt chạy đầy đủ sau đó đạt. Không tính lượt timeout là pass. Ảnh `cloud-proof.png`, `cloud-rag.png`, `cloud-dashboard.png`, `cloud-mobile.png` được cập nhật. Đã xóa dữ liệu Convex, xác nhận state rỗng, xóa cả hai tài khoản Clerk và tệp QA riêng. Frontend không thay đổi trong lần sửa backend này.

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
