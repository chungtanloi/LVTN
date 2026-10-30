# Cross-encoder RAG v6 — 30/10/2026

V6 đạt ngưỡng số học **R@1 ≥80%, R@5 ≥95% trên bộ 40 câu tổng hợp mới**:
33/40 (82,5%) và 38/40 (95%). Cả 6 tình huống kiểm soát đạt. Cùng câu hỏi,
bản v3 đạt 25/40 (62,5%) và 38/40 (95%). Mức tăng ở kết quả đầu tiên là 20
điểm phần trăm; không có tăng R@5 trên bộ này.

Đây **không phải nghiệm thu trên sinh viên thật**. Bộ câu hỏi do AI soạn/gán
nguồn, một người gán, bao phủ các quy chế/CTĐT đã có; chưa có chuyên gia đánh
giá độc lập. Bộ khảo sát cũ vẫn dưới mục tiêu, không được giấu kết quả này.

## Cấu hình và tách dữ liệu

- Lấy tối đa 20 ứng viên từ ranker v3 và 20 từ BM25 trên nguồn sạch; hợp nhất
  theo mã nguồn. Tách khoản OCR trước khi dùng điểm ưu tiên.
- Cross-encoder `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` đọc cặp câu hỏi–
  đoạn văn, ONNX int8, revision và SHA-256 cố định trong manifest. Dữ liệu
  model tải lúc build, không tải hoặc gọi API ngoài khi xử lý câu hỏi.
- Trộn điểm cross-encoder chuẩn hóa theo tập ứng viên (0,5) và điểm từ vựng
  chuẩn hóa (0,5). Các số này là điểm xếp hạng, không phải xác suất đúng.
- Cấu hình chọn trên DEV: thử 101 tỷ trọng và pool 20/30/40 bằng dự đoán DEV
  đã lưu. Ưu tiên cấu hình nhỏ trong nhóm đồng hạng. Không chọn theo TEST.
- Bảng cache dùng để chọn tham số đạt 23/24 và 24/24. Khi tích hợp phân giải
  khoản nguồn và chạy lại toàn luồng, DEV thực tế đạt **22/24 và 24/24**.
  Không lấy số cache 23/24 thay cho số toàn luồng.

Lưu ý mô tả selection_method trong JSON viết gọn: bước thử trọng số trên cache
dùng điểm ưu tiên legacy theo mã cũ; phân giải khoản áp dụng trong pipeline
v6 đã đóng băng, sau bước cache. Số DEV toàn luồng ở trên phản ánh khác biệt này.

`rag_acceptance_holdout_v2_20261030.json` và protocol được commit `c8d57a8`
trước dự đoán. Cấu hình/model code được commit `5729718` trước lượt chấm cuối.
Hash cấu hình: `63e529a2cdf398307a3015b52275e08a2b2b04ee25dcd8a47caf39c6d62bc572`.
Không đổi câu hỏi, nhãn hay trọng số sau lượt này. Hai ca không tìm thấy trong
top 5 là A202 và A209, giữ nguyên trong báo cáo.

## Các kết quả, giữ riêng phạm vi đo

| Bộ đo | R@1 | R@5 | Vai trò |
|---|---:|---:|---|
| DEV 24 câu, toàn luồng | 22/24 | 24/24 | Đã dùng phát triển |
| 40 câu tổng hợp mới | 33/40 | 38/40 | Bộ kiểm tra cuối v6, nhãn AI, một người |
| TEST thủ công cũ, chỉ tìm nguồn | 20/24 | 24/24 | Chẩn đoán đã biết |
| Khảo sát tổng hợp cũ, chỉ tìm nguồn | 15/29 | 26/29 | Chưa đạt mục tiêu |
| Hai bộ cũ gộp, chỉ tìm nguồn | 35/53 | 50/53 | Không coi là kiểm tra mới |

So với v3 trên hai bộ cũ: từ 33/53 và 49/53 lên 35/53 và 50/53. Riêng 29 câu
khảo sát không cải thiện R@1/R@5, còn nhiều cách hỏi cần xử lý. Vì vậy chưa
tuyên bố RAG đạt mục tiêu trên mọi tập hay đã nghiệm thu độc lập.

`evaluation_cross_v6_diagnostic_20261030.json` đo cả việc hỏi lại, có 8 câu
dương bị chuyển sang yêu cầu ngữ cảnh nên số tìm nguồn là 30/53, 42/53.
Để so đúng với các báo cáo retriever cũ, báo cáo
`evaluation_cross_v6_retrieval_diagnostic_20261030.json` chạy lại toàn bộ 8
câu đó ở chế độ chỉ tìm nguồn; các dự đoán khác được giữ nguyên. Không sửa
gold hoặc chọn riêng các ca thành công. Hai phạm vi đo không được trộn.

## Runtime và bảo vệ dữ liệu

Đồ thị ONNX tối ưu được tạo trên **máy đang phục vụ**, mỗi lần container
khởi động, vì tối ưu CPU có thể phụ thuộc phần cứng. Không mang đồ thị tối ưu
Windows sang Linux. Mẫu so sánh local trước/sau tối ưu có độ lệch logit bằng 0;
không thay trọng số hay nội dung nguồn. Tạo mô hình theo nhu cầu; tra duy nhất
một mã môn và tham chiếu không có không cần chạy neural.

Sửa nhận diện “tối đa/tối thiểu” bị nhầm thành đại từ “tôi”; câu hỏi quy tắc
điểm F/đình chỉ thi không bắt buộc mã môn. Đã so sánh trước/sau: nhánh xử lý
của toàn bộ 46 câu cuối không đổi. Đây là sửa định tuyến ngoài bộ cuối, không
chỉnh kết quả kiểm tra sau dự đoán.

Giữ dịch vụ miễn phí hiện có. Giới hạn một tác vụ để khống chế RAM khi neural
và OCR dùng cùng máy. Timeout tra cứu 120 giây, caller 125 giây; không thay
timeout solver. Câu hỏi phức tạp có thể mất nhiều thời gian hơn bản từ vựng.
Nếu thiếu/sai model thì trả lỗi rõ, không âm thầm chạy ranker cũ rồi coi là v6.
Nguồn vẫn là nguyên văn đã tách ghi chú; kết luận cá nhân vẫn do solver và
chứng minh quyết định. Không thay điểm hoặc dữ kiện sinh viên để khớp kết quả.

## Tái lập

```powershell
python -m pip install -r ../../CPA2_App/api/requirements.lock
python prepare_cross_encoder.py --optimize <thu_muc_cache_cua_may_hien_tai>
$env:CPA2_CROSS_ENCODER_CACHE="<thu_muc_cache_cua_may_hien_tai>"
python evaluate_cross_encoder.py --assets cross_encoder_assets --dataset final --report <bao_cao_moi>.json
```

Model card và cách sử dụng: [Sentence Transformers cross-encoder](https://huggingface.co/cross-encoder/mmarco-mMiniLMv2-L12-H384-v1).
Model theo Apache-2.0. Cần câu hỏi sinh viên thực đã ẩn danh và người kiểm
nguồn độc lập cho đợt nghiệm thu tiếp theo; không tái dùng tập cuối này như
một holdout mới sau khi đã xem kết quả.
