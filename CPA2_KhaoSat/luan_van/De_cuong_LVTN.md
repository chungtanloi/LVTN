---
loai: ĐỀ CƯƠNG LUẬN VĂN TỐT NGHIỆP ĐẠI HỌC
nganh: NGÀNH CÔNG NGHỆ THÔNG TIN
ten_vi: TƯ VẤN HỌC VỤ CÁ NHÂN HÓA CÓ CHỨNG CHỈ HÌNH THỨC: KIẾN TRÚC NEURO-SYMBOLIC VỚI CƠ CHẾ TỪ CHỐI KẾT LUẬN DƯỚI DỮ LIỆU KHÔNG CHẮC CHẮN
ten_en: CERTIFIED PERSONALIZED ACADEMIC ADVISING (CPA²): A NEURO-SYMBOLIC ARCHITECTURE WITH PRINCIPLED ABSTENTION UNDER PERCEPTUAL UNCERTAINTY
sinh_vien: <<HỌ VÀ TÊN>>
mssv: <<MSSV>>
khoa: <<KHÓA>>
gvhd: <<HỌC VỊ. HỌ TÊN GVHD>>
thoi_gian: Cần Thơ, 12/2026
---

# MỤC LỤC

[[MUC_LUC]]

# TÓM LƯỢC

Tư vấn học vụ cá nhân hóa đòi hỏi những kết luận không thể truy hồi từ văn bản, chẳng hạn "sinh viên này còn thiếu bao nhiêu tín chỉ để tốt nghiệp". Kết luận đó phải được suy dẫn từ quy chế đào tạo, chương trình đào tạo và bảng điểm cá nhân. Đề tài xây dựng CPA², một kiến trúc neuro-symbolic trong đó mọi kết luận về một sinh viên đều do bộ giải lập trình tập trả lời (clingo) chứng minh và kèm chứng chỉ truy về điều, khoản của Quyết định 3266 và Quyết định 5339 của Trường Đại học Cần Thơ. Mô hình ngôn ngữ chỉ được dùng để phân tích câu hỏi và diễn đạt kết quả. Hệ thống dùng ngữ nghĩa ba trị (ĐÚNG / SAI / CHƯA ĐỦ DỮ LIỆU): khi dữ kiện thiếu hoặc bảng điểm OCR đọc không chắc, hệ thống từ chối kết luận và chỉ ra đúng dữ kiện cần bổ sung. Đến tháng 11/2026, quy chế đã được hình thức hóa với độ phủ 83,3% số điều khoản trong miền. Trên tập kiểm tra 76 ca, CPA² đúng đáp án chuẩn ở 58 ca, cao hơn sáu cấu hình đối chứng dùng mô hình ngôn ngữ lớn (nhiều nhất 44 ca). Chỉ tiêu Soundness 100% chưa đạt (91,1% trên G-Truth). Giai đoạn còn lại mở rộng sang 9 ngành của Trường Công nghệ Thông tin và Truyền thông, bổ sung lập kế hoạch học tập có bảo đảm tối ưu, và đánh giá lại trên bộ dữ liệu mới.

**Abstract.** Personalized academic advising requires conclusions that cannot be retrieved from documents, such as how many credits a given student still needs to graduate; they must be derived from regulations, curricula and the student's transcript. This thesis builds CPA², a neuro-symbolic architecture in which every statement about a student is proved by an answer set programming solver (clingo) and carries a certificate tracing back to articles and clauses of Can Tho University's Decisions 3266 and 5339. Language models are confined to parsing questions and verbalizing results. A three-valued semantics (TRUE / FALSE / UNKNOWN) lets the system abstain when facts are missing or OCR readings of the transcript are uncertain, and name exactly which facts are needed. As of November 2026, 83.3% of in-scope regulation units are formalized. On a 76-case test set, CPA² matched the gold label in 58 cases, more than any of six LLM-based baseline configurations (at most 44). The 100% soundness target is not yet met (91.1% on G-Truth). The remaining work extends the knowledge base to nine programs of the College of Information and Communication Technology, adds optimal study planning, and re-evaluates on a new test set.

# PHẦN GIỚI THIỆU

## 1. Đặt vấn đề

Tư vấn học vụ tại các trường đại học đang thiếu nhân lực; ở nhiều nơi một cố vấn phụ trách hơn 300 sinh viên, khiến sinh viên khó được tư vấn kịp thời và dễ tốt nghiệp trễ hạn [1]. Các trợ lý tư vấn tự động hiện nay, kể cả niên luận AcademiQ của chính tác giả, đều dựa trên kiến trúc truy hồi kết hợp sinh văn bản (RAG), vốn giả định đáp án đã nằm sẵn trong tài liệu.

Giả định này sai với câu hỏi cá nhân hóa. Không văn bản nào chứa câu "sinh viên X còn thiếu 34 tín chỉ để tốt nghiệp"; mệnh đề đó phải được suy dẫn từ ba nguồn: quy chế đào tạo, chương trình đào tạo (kèm đồ thị tiên quyết) và bảng điểm. Sai sót ở đây có chi phí cao và bất đối xứng: khẳng định nhầm "em đã đủ điều kiện tốt nghiệp" có thể khiến sinh viên trễ một học kỳ. Vì vậy đây là miền mà chi phí của phương pháp hình thức được biện minh.

Đề tài đảo ngược vai trò của mô hình ngôn ngữ: mô hình ngôn ngữ không được suy luận về sinh viên; việc suy luận thuộc về bộ giải ràng buộc, và mô hình ngôn ngữ chỉ diễn đạt kết quả đã được chứng minh.

## 2. Những nghiên cứu liên quan

### 2.1. Hỏi–đáp quy chế học vụ bằng RAG

REBot/CatRAG (Trường Đại học Cần Thơ) kết hợp RAG, GraphRAG và định tuyến truy vấn để trả lời câu hỏi quy chế [2]. Thử thách EXACT 2026 (ĐH Bách Khoa TP.HCM) xây dựng bộ hỏi–đáp giáo dục có giải thích và suy luận logic bậc nhất [3]. Cả hai trả lời được "quy định nói gì" nhưng không truy cập hồ sơ sinh viên, không tính toán trên bảng điểm, nên không trả lời được "trường hợp của em thì sao".

### 2.2. Neuro-symbolic cho tư vấn học vụ

Aurora [1] là công trình gần nhất: kết hợp RAG, suy luận ký hiệu (Prolog) và cơ sở dữ liệu chương trình đào tạo; Prolog cưỡng chế ràng buộc cứng, mô hình ngôn ngữ chỉ giải thích sau đó. Aurora để hở bốn điểm mà đề tài nhắm tới: (1) Prolog lọc ứng viên nhưng không sinh chứng chỉ dẫn xuất cho bên thứ ba kiểm tra; (2) lập lộ trình bằng thuật toán tham lam, không có bảo đảm tối ưu; (3) tri thức là lược đồ CTĐT đã chuẩn hóa sẵn, không phải văn bản quy chế ngôn ngữ tự nhiên; (4) đánh giá nhỏ, không có bộ đối kháng, không xét dữ liệu đầu vào không chắc chắn.

### 2.3. Hình thức hóa quy định và kiểm chứng bằng bộ giải

Hướng Rules as Code hình thức hóa văn bản luật thành mã chạy được [4]. Các khung dùng mô hình ngôn ngữ sinh ràng buộc SMT rồi để bộ giải kiểm tra đã được áp dụng cho pháp lý tài chính, đạt khoảng 86% độ chính xác ở khâu sinh mã [5], và cho tác tử dùng công cụ [6]. Chưa nhánh nào áp dụng cho quy chế đào tạo đại học và suy luận cá nhân hóa.

### 2.4. Từ chối trả lời (abstention)

Abstention giúp giảm ảo giác [7], [8], nhưng các phương pháp hiện có dựa trên độ tin cậy thống kê của chính mô hình, không dựa trên bằng chứng hình thức rằng dữ kiện thực sự thiếu, và không chỉ ra được dữ kiện nào cần bổ sung. Nghiên cứu về năng lực lập kế hoạch cho thấy mô hình ngôn ngữ tuân thủ ràng buộc kém trên chính miền xếp lịch học [9].

### 2.5. Định vị đề tài

Đề tài không tuyên bố là hệ neuro-symbolic đầu tiên cho tư vấn học vụ. Ba điểm khác biệt kiểm chứng được: (i) từ lọc bằng ký hiệu sang chứng minh có chứng chỉ, mọi con số và mã học phần trong câu trả lời phải truy được về một dẫn xuất; (ii) hình thức hóa văn bản quy chế tiếng Việt thật (QĐ3266, QĐ5339) kèm phân loại khả năng hình thức hóa; (iii) ngữ nghĩa ba trị lan truyền độ bất định từ OCR bảng điểm vào tận kết luận.

## 3. Mục tiêu đề tài

Mục tiêu tổng quát: xây dựng và đánh giá một kiến trúc tư vấn học vụ trong đó mọi mệnh đề về một sinh viên cụ thể đều được bộ giải chứng minh trước khi phát biểu; khi dữ liệu không đủ hoặc không đáng tin, hệ thống từ chối kết luận và chỉ ra dữ kiện còn thiếu.

Mục tiêu cụ thể, gắn với các câu hỏi nghiên cứu:

- **RQ1 – Hình thức hóa:** dịch các nhóm điều khoản trọng yếu của QĐ3266 và QĐ5339 (cảnh báo học vụ, tốt nghiệp, đăng ký, miễn và công nhận) sang logic thực thi; đo tỉ lệ hình thức hóa được và phân loại cơ chế kháng hình thức hóa.
- **RQ2 – Ba trị và từ chối có căn cứ:** thiết kế ngữ nghĩa ba trị nhận độ tin cậy OCR làm một nguồn bất định và sinh câu hỏi bổ sung có định hướng.
- **RQ3 – Lập kế hoạch tối ưu:** tìm số học kỳ nhỏ nhất để tốt nghiệp thỏa mọi ràng buộc, kèm chứng minh không tồn tại phương án tốt hơn; mức nguyên mẫu.
- **RQ4 – Diễn đạt trung thực:** đo mức bảo toàn chân trị khi mô hình ngôn ngữ diễn đạt chứng chỉ, có bộ hậu kiểm.
- Xây dựng bộ dữ liệu đánh giá có đáp án chuẩn đóng băng trước khi chạy và so sánh với các hệ đối chứng dùng mô hình ngôn ngữ lớn.

## 4. Đối tượng và phạm vi nghiên cứu

Đối tượng: hệ thống hỏi–đáp tư vấn học vụ tiếng Việt có suy luận cá nhân hóa trên hồ sơ sinh viên.

Phạm vi:

- Văn bản quy chế: QĐ3266 (quy định công tác học vụ trình độ đại học chính quy) và QĐ5339 (xét miễn và công nhận điểm học phần) của Trường Đại học Cần Thơ.
- Chương trình đào tạo: 9 ngành khóa 49 của Trường Công nghệ Thông tin và Truyền thông (Khoa học máy tính, Mạng máy tính và truyền thông dữ liệu, Kỹ thuật phần mềm, Kỹ thuật phần mềm chất lượng cao, Hệ thống thông tin, Công nghệ thông tin, Công nghệ thông tin chất lượng cao, Truyền thông đa phương tiện, An toàn thông tin). Đến tháng 11/2026 mới hoàn thành ngành Công nghệ thông tin; 8 ngành còn lại thực hiện trong tháng 12/2026.
- Ngôn ngữ: tiếng Việt. Hồ sơ dùng trong đánh giá là hồ sơ giả lập; không đưa dữ liệu sinh viên thật vào kho mã.
- Ngoài phạm vi: khóa K48, K50, K51; các quy định không có trong hai văn bản trên (ví dụ hệ số học phí).

## 5. Phương pháp nghiên cứu

- **Phân tích văn bản và hình thức hóa thủ công có con trỏ nguồn:** mỗi quy tắc gắn văn bản, điều, khoản, trang; chỗ văn bản mơ hồ hoặc giao cho đơn vị đào tạo được mở nhánh (CHƯA ĐỦ DỮ LIỆU) thay vì tự chọn cách hiểu; quyết định diễn giải được ghi thành danh mục riêng.
- **Lập trình tập trả lời (ASP, clingo):** suy diễn trên quy chế, CTĐT và hồ sơ; giá trị ba trị lấy theo hệ quả thận trọng và hệ quả dũng cảm trên mọi "thế giới" có thể của dữ kiện chưa biết.
- **Tối ưu ràng buộc (OR-Tools CP-SAT):** cho bài toán lập kế hoạch nhiều học kỳ (RQ3).
- **Phát triển hướng kiểm thử:** mỗi quy tắc có ca kiểm thử; mỗi lỗi tìm thấy có ca hồi quy thất bại với quy tắc cũ.
- **Thực nghiệm đăng ký trước:** đáp án chuẩn viết tay, soát độc lập, đóng băng (băm và lưu phiên bản) trước lần chạy đầu; tách tập phát triển và tập kiểm tra; tập kiểm tra chạy một lần; so sánh cặp bằng kiểm định McNemar với hiệu chỉnh Bonferroni.

## 6. Nội dung nghiên cứu

Đề tài thực hiện cá nhân, gồm các công việc:

- Khảo sát bài toán, phân loại câu hỏi học vụ, tổng quan tài liệu, chọn bộ giải.
- Hình thức hóa QĐ3266, QĐ5339 (R-Formal) và chương trình đào tạo (Curriculum KB).
- Mô hình hồ sơ sinh viên; các bộ giải nhóm tự chọn, miễn và thay thế, tốt nghiệp, đủ điều kiện, đề xuất đăng ký.
- Chứng chỉ chứng minh, tích hợp nguyên mẫu, bộ phân tích câu hỏi, truy hồi điều khoản.
- OCR bảng điểm có độ tin cậy, ngữ nghĩa ba trị và từ chối kết luận.
- Xây dựng bộ đánh giá, chạy hệ đối chứng, so sánh và phân tích lỗi.
- Ứng dụng web minh họa.
- Giai đoạn còn lại: mở rộng 9 ngành, lập kế hoạch tối ưu (RQ3), diễn đạt bằng mô hình ngôn ngữ (RQ4), đánh giá lần hai.

## 7. Bố cục của quyển luận văn

Ngoài phần giới thiệu và kết luận, luận văn gồm bốn chương: Chương 1 đặc tả bài toán và yêu cầu; Chương 2 trình bày thiết kế, gồm hình thức hóa quy chế, ngữ nghĩa ba trị, chứng chỉ và lập kế hoạch; Chương 3 mô tả cài đặt và ứng dụng web; Chương 4 trình bày thiết kế đánh giá, kết quả và phân tích lỗi. Phụ lục gồm danh mục quy tắc, danh mục quyết định diễn giải và hướng dẫn cài đặt.

# PHẦN NỘI DUNG (DỰ KIẾN)

Mỗi mục dưới đây ghi nội dung dự kiến và trạng thái hiện tại (đã có / đang làm / dự kiến).

# CHƯƠNG 1. ĐẶC TẢ YÊU CẦU

## 1.1. Bài toán tư vấn học vụ cá nhân hóa

Nguồn tri thức (quy chế, CTĐT, bảng điểm) và đặc điểm của câu hỏi cá nhân hóa: kết luận phải suy dẫn, không truy hồi được. Trạng thái: đã có (báo cáo Tuần 1).

## 1.2. Phân loại câu hỏi học vụ

Bảy loại ràng buộc: học phần bắt buộc, tự chọn, nhóm chọn N trong M, tiên quyết (tiên quyết, ngưỡng tín chỉ, song hành), miễn, thay thế, tốt nghiệp; kèm mức khó và điểm dễ sai. Trạng thái: đã có (Tuần 2).

## 1.3. Yêu cầu chức năng

Trả lời các nhóm câu hỏi: tốt nghiệp và xếp hạng, đủ điều kiện đăng ký học phần và làm luận văn, miễn và công nhận, cảnh báo học vụ, đề xuất đăng ký một học kỳ, mục tiêu hạng tốt nghiệp; nhập bảng điểm bằng ảnh hoặc PDF; hiển thị chứng chỉ và nguồn điều khoản. Dự kiến bổ sung: câu hỏi phản thực ("nếu rớt học phần X thì tốt nghiệp trễ mấy kỳ").

## 1.4. Yêu cầu phi chức năng

Mọi kết luận có chứng chỉ; không bịa nội dung quy chế; từ chối khi thiếu hoặc không chắc dữ kiện và nêu dữ kiện cần bổ sung; mô hình ngôn ngữ không tự kết luận học vụ; bảo vệ dữ liệu sinh viên (chỉ lưu khi có đồng ý).

## 1.5. Ca sử dụng

Sinh viên đăng nhập, chọn ngành, nhập bảng điểm, xác nhận dòng OCR không chắc, đặt câu hỏi, xem chứng chỉ và lịch sử.

# CHƯƠNG 2. THIẾT KẾ GIẢI PHÁP

## 2.1. Kiến trúc tổng thể

Bốn tầng: phân tích câu hỏi → cơ sở tri thức (quy chế, CTĐT, hồ sơ) → bộ giải ba trị và chứng chỉ → diễn đạt và hậu kiểm. Hậu kiểm quét mọi con số và mã học phần trong câu trả lời; không khớp chứng chỉ thì chặn. Trạng thái: đã có.

## 2.2. Hình thức hóa quy chế (RQ1)

### 2.2.1. Đơn vị điều khoản và ba trục phân loại

Mỗi đơn vị gắn loại ràng buộc, lớp khả năng hình thức hóa (F: hình thức hóa được, P: một phần, N: không) và trục dữ liệu (có hay không có dữ kiện trong hồ sơ).

### 2.2.2. Kết quả hình thức hóa

Danh mục hiện hành (R-Formal v1.14) có 96 đơn vị, trong đó 72 đơn vị thuộc miền suy diễn học vụ cá nhân hóa: F = 60, P = 8, N = 4; 24 đơn vị ngoài miền (thủ tục, tổ chức, tài chính). Formalization Coverage = 60/72 = 83,3%; Executable Coverage (lớp F và có dữ liệu) = 44/72 = 61,1%.

### 2.2.3. Cơ chế kháng hình thức hóa

Ủy quyền quyết định ("do Hiệu trưởng quyết định", giao đơn vị đào tạo), mơ hồ ngữ nghĩa, thiếu dữ kiện trong hồ sơ, xung đột liên văn bản giữa QĐ3266 và QĐ5339; cách xử lý: mở nhánh, ghi quyết định diễn giải có nguồn.

### 2.2.4. Thí nghiệm dịch quy chế bằng mô hình ngôn ngữ (dự kiến)

Cho mô hình ngôn ngữ dịch từng điều khoản sang ASP, chấm bằng chính bộ ca kiểm thử của R-Formal, so với mức khoảng 86% của [5]. Thực hiện nếu đủ thời gian và ngân sách.

## 2.3. Cơ sở tri thức chương trình đào tạo đa ngành

Sinh tự động từ bảng chép có con trỏ trang, kiểm tra chéo với dòng "Cộng" của từng khối kiến thức. Dự kiến: sổ đăng ký CTĐT theo mã ngành; hồ sơ khai báo CTĐT; mã học phần đặc thù (luận văn, tiểu luận, niên luận) lấy từ dữ kiện CTĐT thay vì viết cứng. Trạng thái: đã có ngành CNTT; 8 ngành dự kiến tháng 12/2026.

## 2.4. Mô hình hồ sơ sinh viên

Lược đồ hồ sơ; quy ước điểm chứng chỉ ngoại ngữ; rà soát mâu thuẫn; một bộ chuyển đổi duy nhất từ hồ sơ sang dữ kiện ASP. Trạng thái: đã có.

## 2.5. Chọn bộ giải

So sánh clingo, CP-SAT và Z3 trên cùng bài toán. Chọn clingo cho suy diễn ba trị và chứng chỉ; CP-SAT cho lập kế hoạch; Z3 làm đối chứng mô hình hóa. Trạng thái: đã có (Tuần 4, có đính chính sau Tuần 6).

## 2.6. Chứng chỉ chứng minh

Vết dẫn xuất từ kết luận về quy tắc và điều khoản nguồn; nguồn của kết luận lấy từ chứng minh, không lấy từ kết quả truy hồi. Trạng thái: đã có.

## 2.7. Ngữ nghĩa ba trị và từ chối kết luận (RQ2)

### 2.7.1. Ba trị theo các thế giới khả dĩ

ĐÚNG nếu đúng trên mọi thế giới, SAI nếu sai trên mọi thế giới, CHƯA ĐỦ DỮ LIỆU nếu khác nhau; số thế giới không được hiểu như xác suất.

### 2.7.2. Hai nguồn bất định

Dữ kiện thiếu (chưa có kết quả, chưa khai báo) và dữ kiện không đáng tin (OCR đọc không chắc); cả hai được mở nhánh trên cùng cơ chế.

### 2.7.3. OCR bảng điểm có kiểm chéo

Chỉ nhận một dòng khi các lần đọc độc lập khớp nhau dưới ràng buộc quy chế (điểm chữ khớp điểm số, tín chỉ khớp CTĐT, tổng tín chỉ và điểm trung bình học kỳ khớp số in). Trạng thái: đã có.

### 2.7.4. Câu hỏi bổ sung có định hướng

Nêu đúng học phần hoặc con số cần sinh viên xác nhận. Hạn chế hiện tại: mới xét từng biến, chưa tìm tập câu hỏi nhỏ nhất.

## 2.8. Đủ điều kiện và đề xuất đăng ký

Chỉ đề xuất điều hợp lệ trên mọi thế giới; thứ tự ưu tiên là chính sách tư vấn, không phải quy chế. Trạng thái: đã có cho một học kỳ.

## 2.9. Lập kế hoạch nhiều học kỳ có bảo đảm tối ưu (RQ3, dự kiến)

Tìm số học kỳ nhỏ nhất k sao cho tồn tại phân bổ học phần vào các kỳ 1..k thỏa tiên quyết theo thời gian, trần tín chỉ mỗi kỳ, học phần mở theo kỳ và ngưỡng tín chỉ; chứng minh k−1 kỳ là không khả thi. So với bộ lập kế hoạch tham lam (kiểu Aurora) bằng Counterfactual Optimality Gap.

## 2.10. Diễn đạt và hậu kiểm (RQ4)

Hiện dùng mẫu câu cố định. Dự kiến: mô hình ngôn ngữ diễn đạt chứng chỉ, giữ hậu kiểm, đo tỉ lệ câu bị chặn và câu đổi chân trị.

## 2.11. Truy hồi điều khoản

Truy hồi để trích dẫn và giải thích, không dùng để kết luận. Trạng thái: đã có (BM25 và cross-encoder).

# CHƯƠNG 3. CÀI ĐẶT GIẢI PHÁP

## 3.1. Môi trường và công cụ

Python, clingo, OR-Tools CP-SAT, Tesseract (tiếng Việt), jsonschema.

## 3.2. Tổ chức mã nguồn

Mỗi thành phần một thư mục có bộ kiểm thử riêng; các tệp sinh tự động (CTĐT, corpus) chỉ sửa qua bộ sinh. Trạng thái: 19/19 bộ kiểm thử đạt ở thời điểm Tuần 22.

## 3.3. Cài đặt các thành phần chính

R-Formal, Curriculum KB, bộ chuyển hồ sơ, các bộ giải, chứng chỉ, OCR, ba trị, đề xuất; trích đoạn quy tắc tiêu biểu.

## 3.4. Ứng dụng web

Next.js trên Vercel, xác thực Clerk, dữ liệu Convex, dịch vụ bộ giải Python trên Render; luồng nhập bảng điểm, xác nhận dòng không chắc, hỏi đáp, chứng chỉ, lịch sử. Dự kiến: chọn ngành.

# CHƯƠNG 4. ĐÁNH GIÁ KIỂM THỬ

## 4.1. Mục tiêu và độ đo

Soundness (tỉ lệ không có kết luận sai), Coverage (tỉ lệ có kết luận), Selective Accuracy, số ca đúng đáp án chuẩn, từ chối thừa. Soundness cao chưa đủ: hệ chỉ biết từ chối cũng đạt 100%, nên luôn báo kèm Coverage.

## 4.2. Bộ dữ liệu

G-Truth (hồ sơ có đáp án chuẩn), OCR-Noise (bảng điểm nhiễu bốn mức), bộ đối kháng 80 ca, Q-Noise (240 câu biến thể cách gõ, tổng hợp). Q-Real (câu hỏi thật của sinh viên, chỉ tiêu 400 câu) đang thu qua biểu mẫu có đồng ý: hiện 0/400.

## 4.3. Kiểm thử đơn vị và hồi quy

Bộ kiểm thử theo từng thành phần; mỗi lỗi có ca hồi quy.

## 4.4. Kết quả đánh giá lần 1 (đã có)

- Bộ đối kháng: Soundness 91,9%, Coverage 78,4%.
- G-Truth, tập kiểm tra: Soundness 91,1% (5 kết luận sai trên 56 ca): **chưa đạt** chỉ tiêu 100%. 4 trong 5 lỗi cùng một nguyên nhân (công nhận học phần lý luận chính trị tự động), đã sửa sau đó nhưng tập kiểm tra đã nhiễm nên số chính thức giữ nguyên.
- OCR-Noise, tập kiểm tra: Soundness 100%, Coverage 25%: an toàn nhưng từ chối nhiều.
- Truy hồi điều khoản (Tuần 14): Recall@1 = 0,67, Recall@5 = 0,92: **chưa đạt** mục tiêu 0,80 / 0,95.

## 4.5. So sánh với hệ đối chứng (đã có)

Ba loại hệ đối chứng (mô hình ngôn ngữ thuần, RAG, gọi công cụ) trên hai họ mô hình, cùng bộ ca và cách chấm. Trên 76 ca kiểm tra, CPA² đúng đáp án chuẩn 58 ca, hệ đối chứng tốt nhất 44 ca; hơn 5/6 hệ có ý nghĩa thống kê sau hiệu chỉnh Bonferroni. Trên 50 ca có câu hỏi rõ, CPA² có 2 kết luận sai với Coverage 54,0%; các hệ đối chứng họ OpenAI không sai nhưng gần như luôn từ chối (Coverage 2–28%). Kết luận: CPA² kết luận được nhiều hơn mà vẫn ít sai, nhưng **không** ít kết luận sai hơn mọi hệ đối chứng.

## 4.6. Đánh giá lần 2 (dự kiến tháng 1/2027)

Bộ G-Truth v2 phân tầng theo 9 ngành và có ca phản thực, đóng băng trước khi chạy; chạy một lần cho CPA², sáu hệ đối chứng và bộ lập kế hoạch tham lam. Đo thêm: đường cong Coverage – Selective Accuracy (quét ngưỡng tin cậy OCR), đường cong chất lượng ảnh – Coverage (ảnh tổng hợp), Counterfactual Optimality Gap, độ trung thực diễn đạt. Ngân sách gọi API cho đợt này: 20 USD.

## 4.7. Phân tích lỗi và hạn chế

Phân loại lỗi của hệ đối chứng (tính sai số, bịa quy định, bỏ sót dữ kiện, kết luận khi phải từ chối) và của CPA² (cơ sở tri thức, phân tích câu hỏi, OCR). Hạn chế: bộ ca và đáp án do một người viết; tập nhỏ; mỗi họ mô hình một mô hình; OCR mới đánh giá trên ảnh tổng hợp.

# PHẦN KẾT LUẬN (DỰ KIẾN)

## 1. Kết quả đạt được

Tổng kết theo RQ1–RQ4, ghi rõ chỉ tiêu nào đạt và chưa đạt kèm số liệu.

## 2. Hướng phát triển

Mở rộng sang các khóa khác; thu câu hỏi thật quy mô lớn; người thứ hai gán nhãn để đo độ đồng thuận; đánh giá OCR trên ảnh thật có đồng ý.

# KẾ HOẠCH THỰC HIỆN

| Thời gian | Công việc | Sản phẩm |
|---|---|---|
| 21/11 – 11/12/2026 | Mở rộng 9 ngành: sổ đăng ký CTĐT, chép và kiểm tra chéo 8 CTĐT, hồ sơ giả lập | Curriculum KB 9 ngành |
| 12/12 – 18/12/2026 | Hoàn thiện và nộp đề cương | Đề cương (PDF) |
| 19/12/2026 – 01/01/2027 | Lập kế hoạch tối ưu (RQ3); đóng băng G-Truth v2 | Bộ lập kế hoạch, bảng gap |
| 02/01 – 08/01/2027 | Hai đường cong (RQ2), diễn đạt bằng mô hình ngôn ngữ (RQ4) | Hình, bảng độ trung thực |
| 09/01 – 15/01/2027 | Đánh giá lần 2, chạy một lần | Báo cáo kết quả |
| 16/01 – 29/01/2027 | Viết luận văn, gửi giáo viên hướng dẫn | Bản thảo |
| Sau Tết – trước hạn nộp | Chỉnh sửa, demo, slide, tập dượt bảo vệ | Quyển luận văn, demo |

# TÀI LIỆU THAM KHẢO

[1] L. A. Quincoso Lugones et al., "Aurora: Neuro-Symbolic AI Driven Advising Agent," arXiv:2602.17999, 2026.

[2] T. Ma et al., "REBot: From RAG to CatRAG with Semantic Enrichment and Graph Routing," in Proc. MIWAI, Springer, 2025.

[3] Nhóm URA, Trường ĐH Bách Khoa TP.HCM, "EXACT 2026 — 2nd International XAI Challenge for Transparent Educational Question Answering," IJCNN 2026.

[4] M. Waddington, "Research Note: Representing legislative Rules as Code," Computer Law & Security Review, 2022.

[5] Y.-S. Hsia, F. Yu, J.-H. R. Jiang, "Neuro-Symbolic Compliance: Integrating LLMs and SMT Solvers for Automated Financial Legal Analysis," arXiv:2601.06181, 2026.

[6] "Solver-Aided Verification of Policy Compliance in Tool-Augmented LLM Agents," arXiv:2603.20449, University of Washington, 2026.

[7] "Knowing when to quit: A principled framework for dynamic abstention in LLM reasoning," Amazon Science, 2026.

[8] E. Hecks, "What is LLM Abstention and Why it Matters for Reliable AI," Open Data Science, 2026.

[9] "Systematic Analysis of LLM Contributions to Planning: Solver, Verifier, Heuristic," arXiv:2412.09666, 2024.

[10] "LLM-Solve 2026: 2nd Workshop on LLMs meet Constraint Solving," Lisbon, 2026.

[11] "Neuro-symbolic synergy in education: a survey of LLM–knowledge graph integration for explainable reasoning and emotion-aware student support," Smart Learning Environments, Springer, 2026.

[12] Đại học Cần Thơ, Quyết định số 3266 về Quy định công tác học vụ dành cho sinh viên trình độ đại học hình thức chính quy, 2024.

[13] Northwestern University, "Generating Degree What-If Reports."

[14] Đại học Cần Thơ, Quyết định số 5339 về Quy định xét miễn và công nhận điểm học phần, 2019.

[15] Đại học Cần Thơ, Chương trình đào tạo trình độ đại học ngành Công nghệ thông tin (7480201), ban hành theo QĐ 2423/QĐ-ĐHCT ngày 05/6/2023.
