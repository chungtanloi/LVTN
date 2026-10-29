# Cải tiến truy hồi ngày 29/10/2026

Mô hình v3 dùng cùng 13 đặc trưng từ vựng và cùng corpus như v1. Không thêm
embedding, LLM, dịch vụ tính phí hoặc nhãn mới. Trọng số được chọn bằng 10.000
ứng viên với seed 29, trên 24 câu DEV và 60 câu TRAIN có nguồn, thuộc 22 nhóm
người trả lời khảo sát tổng hợp. Khi tính đặc trưng ví dụ cho mỗi câu TRAIN,
loại tất cả ví dụ cùng nhóm. Mỗi nhóm đóng góp ngang nhau. Thứ tự mục tiêu:
đạt ngưỡng DEV, tối đa MRR trung bình nhóm TRAIN, Recall@5 nhóm, rồi MRR DEV.
Các nhóm này dùng để chọn mô hình; điểm TRAIN không phải kiểm tra độc lập.

Áp dụng bản rà soát nguồn có sẵn `rag_soat_gold_errata_v1.json` cho 41 câu TRAIN:
sửa/giữ/mở rộng nguồn theo kết quả soát; loại 7 câu không có mã nguồn đã xác nhận
khỏi ví dụ dương (67 → 60). Không thay nhãn DEV/TEST. Rà soát này một phần và
sau khi thấy dự đoán của thử nghiệm cũ, không phải nhãn kiểm tra độc lập.

Trọng số v3 đóng băng trước khi chạy lại hai bộ TEST. Các bộ này đã biết từ v1
và bản thử v2 trong cùng đợt làm việc, nên chỉ là chẩn đoán. Không chọn lại trọng
số sau khi xem TEST của v3. Bản thử v2 dùng nhãn cũ được giữ riêng để kiểm toán;
không triển khai v2 vì còn các nhãn TRAIN đã được xác nhận sai.

| Bộ câu hỏi | v1 R@1 | v3 R@1 | v1 R@5 | v3 R@5 |
|---|---:|---:|---:|---:|
| Khảo sát tổng hợp, 29 câu đã biết | 14/29 | 15/29 | 23/29 | 26/29 |
| Câu hỏi thủ công, 24 câu TEST đã biết | 17/24 | 18/24 | 23/24 | 23/24 |
| DEV, dùng chọn mô hình | 23/24 | 20/24 | 24/24 | 23/24 |

Chọn v3 cho độ phủ top 5 tốt hơn và áp dụng sửa nhãn đã có. Tổng hai bộ TEST,
R@1 tăng 31/53 → 33/53; R@5 tăng 46/53 → 49/53. Chưa đạt tiêu chí 80%/95%
trên bộ khảo sát, chưa thể
coi RAG đã nghiệm thu. Đây là truy hồi nguồn liên quan, không phải độ đúng của
câu trả lời hay kết luận học vụ. Dữ liệu tổng hợp và nhãn nguồn do một lượt
gán nhãn có AI hỗ trợ; nhãn TEST chưa được chuyên gia rà soát độc lập.

Các cải tiến đi kèm:

- Khi người dùng nêu số quyết định hoặc số điều, giữ đúng tham chiếu đầy đủ;
  không lấy Điều 14 cho yêu cầu Điều 140.
- Tra tiên quyết/số tín chỉ của mã môn cụ thể giữ đúng học phần; mã không có
  trong corpus không trả tiên quyết của môn khác. Câu hỏi học lại điểm F vẫn
  được tìm quy chế chung.
- Đoạn trích tra cứu được chọn theo từ/cụm từ câu hỏi ở toàn passage, tối đa
  300 ký tự. Lưu chỉ số đầu/cuối và nguyên văn passage; website có nút mở toàn
  bộ đoạn nguồn. Không sinh lại nội dung quy chế bằng mô hình ngôn ngữ.
- Grounding của kết luận cá nhân vẫn đi từ từng bước chứng minh đến nguồn.

Tái lập từ thư mục này:

```powershell
python build_reviewed_training.py --output <ban_train_tai_lap>.json
python train_grouped_retrieval.py --reviewed --output <duong_dan_chua_ton_tai>.json
python validate_retrieval_ranker.py
python evaluate_retrieval.py --dataset survey-holdout --split test --model retrieval_model_v3.json --report <bao_cao_moi>.json
```

NumPy chỉ cần cho huấn luyện offline. Runtime dùng thư viện chuẩn Python.
Không sửa các báo cáo/nhãn v1 để làm đẹp số liệu. Bước đánh giá kế tiếp cần
câu hỏi mới được gán nguồn trước khi chạy và chuyên gia kiểm tra nguồn.
