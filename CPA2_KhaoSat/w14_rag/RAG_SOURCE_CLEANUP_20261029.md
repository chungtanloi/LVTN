# Nguồn sạch, hỏi lại và thử nghiệm hybrid — 29/10/2026

## Phần triển khai

Giữ mô hình xếp hạng v3. Corpus cũ là chỉ mục tìm kiếm, có các tín hiệu và ghi
chú cũ; nội dung đó không còn được đưa trực tiếp ra làm đoạn trích quy chế.
Nguồn hiển thị lấy từ `corpus_source_v1.jsonl`: 228 passage, giữ toàn bộ mã
nguồn/quy tắc/ASP cũ và bổ sung Điều 22 khoản 4. Cả đoạn trích tra cứu và phần
trích dẫn certificate đều dùng nội dung nguồn đã tách. Solver và bảng ánh xạ
chứng minh không đổi.

`build_clean_corpus.py` dựng lại thân nguồn từ OCR/chép tay, không nối thêm
ghi chú R-Formal vào nguyên văn. 144 bản ghi văn bản cũ được giữ riêng trong
`corpus_notes_v1.jsonl` để kiểm toán. Không coi toàn bộ OCR đã chính xác:
passage chưa kiểm tra được gắn `ocr_unreviewed` và website nhắc đối chiếu PDF.

10 passage được chép/đối chiếu ảnh PDF trong đợt này: QĐ3266 Điều 14 khoản
0/1/2 (PDF trang 8), Điều 22 khoản 3/4/5 (trang 14), Điều 24 khoản 3/4/5
(trang 15), QĐ5339 Điều 3 khoản 8 (trang 7). Đây là trợ lý đối chiếu bằng mắt,
chưa phải chuyên gia kiểm tra độc lập. Bảng ở Điều 24 khoản 5 được chuyển
sang văn bản, không giữ bố cục bảng. Bản chép nằm trong `source_corrections_v1.json`.

Sửa hai lỗi cụ thể: ghi chú phân tích không còn hiện như nguyên văn Điều 14;
Điều 22 khoản 4 bị OCR ghép vào khoản 3 được tách ra. `source_bindings_v1.json`
ghi lại quan hệ tách này; câu hỏi tự do về công bố điểm được đưa về khoản 4.
Yêu cầu rõ điều/khoản tra trực tiếp địa chỉ nguồn; tham chiếu không tồn tại
không được đổi sang khoản gần giống.

Website có liên kết PDF gốc theo trang. Hai PDF quy chế được sao chép nguyên
byte từ thư mục `ctu` vào `web/public/quy-che`; hash và kích thước nằm trong
`source_pdf_manifest_v1.json`. Không đưa bảng điểm cá nhân lên website/repository.

Nếu câu hỏi dùng “môn này/học phần đó” mà thiếu mã môn, hệ thống yêu cầu bổ
sung. Nếu người dùng yêu cầu kết luận cá nhân trong Kho quy chế, hệ thống
hướng dẫn sang Tư vấn học vụ với hồ sơ đã xác nhận. Không dùng điểm xếp hạng
như xác suất đúng.

## Thử nghiệm, không triển khai

V4: cùng bộ đặc trưng từ vựng, chọn lại trên nguồn sạch. V5: lấy top 30 mỗi
kênh từ vựng/ngữ nghĩa, ghép RRF, rồi dùng reranker tuyến tính 15 đặc trưng.
Đây là reranker nhẹ, chưa phải cross-encoder đọc cặp câu hỏi–đoạn văn.

Embedding dùng `intfloat/multilingual-e5-small`, revision cố định trong
`semantic_assets_v1.json`, ONNX int8; query/passage có prefix riêng, masked
mean pooling và chuẩn hóa L2 theo [model card](https://huggingface.co/intfloat/multilingual-e5-small).
Tổ chức lấy ứng viên rồi xếp hạng lại theo [hướng dẫn Sentence Transformers](https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html).
Mô hình/index được kiểm hash, không tải qua mạng khi xử lý câu hỏi.

Index 431 cửa sổ trên 228 nguồn, đóng băng trong `semantic_index_v1.npz`.
Trọng số chọn bằng DEV + TRAIN bỏ ví dụ cùng nhóm người trả lời, không dùng
nhãn TEST chọn trọng số. V5 đạt DEV 20/24 và 23/24; TRAIN MRR nhóm là số dùng
chọn mô hình, không phải kết quả kiểm tra độc lập.

| Chẩn đoán đã biết | V3 R@1 / R@5 | V4 R@1 / R@5 | V5 R@1 / R@5 |
|---|---|---|---|
| 29 câu khảo sát tổng hợp | 15 / 26 | 15 / 26 | 15 / 25 |
| 24 câu TEST thủ công | 18 / 23 | 17 / 22 | 18 / 23 |

V5 giảm một câu top 5 ở bộ khảo sát; V4 giảm ở bộ thủ công. Không đưa cả hai
mô hình lên production. Không chỉnh lại trọng số để khớp TEST sau các số đo
này. Giữ v3, chỉ thay phần phân giải/hiển thị nguồn và xử lý câu thiếu thông tin.

Đo trên Windows: encoder với tokenizer đầy đủ khoảng 450 MB RSS; tokenizer
SentencePiece với cùng bảng mã giảm xuống khoảng 234 MB cho một truy vấn.
Đây chưa phải kiểm tra tải Linux/Render; không suy ra giới hạn production từ
số đo này. Production không cài thêm ONNX/SentencePiece hay tải model.

## Kiểm tra mới và giới hạn

`rag_source_checks_v1.json`: 16 câu tổng hợp mới, gán nguồn trước lượt dự đoán
đầu trên tệp. Câu hỏi tập trung các đoạn vừa đối chiếu, một lượt gán nhãn có
AI hỗ trợ; không đại diện sinh viên thật và không phải benchmark nghiệm thu.
Kết quả thực tế: nguồn đúng trong top 3 ở 5/12 câu, đúng hạng đầu 4/12; cả
4/4 ca hỏi lại/tham chiếu không tồn tại xử lý đúng, tổng 9/16. Giữ nguyên các
ca trượt, không đổi nhãn hay tinh chỉnh theo chúng. File báo cáo đầy đủ:
`evaluation_source_delivery_20261029.json`.

Nguồn sạch giúp tránh trích sai loại nội dung; không tự giải quyết được các
cách hỏi khác từ ngữ quy chế. Bước tiếp theo cần câu hỏi thực được ẩn danh và
gán nguồn độc lập, cùng thử cross-encoder tiếng Việt/đa ngôn ngữ. Không tuyên
bố đã đạt mục tiêu RAG 80%/95%.

## Tái lập

```powershell
python build_clean_corpus.py --output <corpus_moi>.jsonl --notes <ghi_chu_moi>.jsonl
python -m pip install -r requirements-semantic.txt
python prepare_semantic.py --directory semantic_assets
$env:CPA2_SEMANTIC_MODEL_DIR=(Resolve-Path semantic_assets)
python train_grouped_retrieval.py --reviewed --corpus corpus_source_v1.jsonl --output <model_v4_tai_lap>.json
python train_hybrid.py --assets semantic_assets --output <model_v5_tai_lap>.json
python evaluate_retrieval.py --dataset survey-holdout --split test --model retrieval_model_v5.json --report <bao_cao_moi>.json
```

Để dựng lại index phải dùng thư mục làm việc mới không có hai tệp index,
thêm `--index` vào `prepare_semantic.py`. Không ghi đè artifact đã đóng băng.
