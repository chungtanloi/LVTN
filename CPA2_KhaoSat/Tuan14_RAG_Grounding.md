# TUẦN 14 — RAG GROUNDING

**Giai đoạn:** LLM (Tuần 14/24) · **Mục tiêu:** Kết nối retrieval với quy chế/CTĐT
**Sản phẩm:** RAG prototype (`w14_rag/`)
**Tiêu chí hoàn thành:** Truy hồi đúng nguồn
- ✅ **Grounding cho kết luận:** 100% bước chứng minh có passage đúng văn bản + điều; hậu kiểm chặn trích sai
- ⚠️ **Truy hồi tự do (tập test):** Recall@1 = 0,67, Recall@5 = 0,92. **Chưa đạt** mục tiêu 0,80 / 0,95

---

## 0. Kết luận trước

> Tuần này tách hai việc mà RAG thông thường gộp làm một. **Grounding** là trả lời câu hỏi "kết luận này dựa trên điều khoản nào?". Đây là tra cứu tất định: bước chứng minh `why(atom, r_xxx)` → bản ghi R-Formal → passage (văn bản, điều, khoản), và đạt 100%. **Truy hồi** là trả lời câu hỏi "văn bản nào nói về chuyện này?". Việc này dựa vào độ giống văn bản và sai khoảng 1/3 ở top-1. Câu trượt quan trọng nhất của tập test **đúng là bẫy mà luận văn dự đoán**: hỏi về điểm 4,5 *chuyển từ trường khác* thì truy hồi trả về QĐ3266 (ngưỡng 4,0) thay vì QĐ5339 (ngưỡng 5,0). Nếu để truy hồi chọn nguồn cho kết luận, hệ thống sẽ trích sai văn bản với độ tự tin cao. CPA² không để truy hồi làm việc đó.

---

## 1. Corpus (`build_corpus.py`)

| Thành phần | Số passage | Nguồn |
|---|---|---|
| QĐ3266 + QĐ5339, theo điều/khoản | 138 | 130 từ OCR, 8 dựng từ trích R-Formal |
| CTĐT CNTT K49: học phần + nhóm tự chọn | 83 | Curriculum KB v1 |

- Đơn vị = **(văn bản, điều, khoản)**, trùng mức trích dẫn của `rule_src` (Tuần 11). Mỗi passage mang danh sách quy tắc R-Formal và `asp` của nó.
- **OCR làm hỏng số khoản** theo nhiều kiểu: `5,` · `2 Điểm` · `10.SV` · `+,` (thay cho `4.`) · `s6`. Bộ tách chấp nhận dấu `.`/`,` tuỳ chọn và chữ hoa theo sau, cho phép nhảy cóc 1 khoản; số điều và số khoản phải tăng đơn điệu để tham chiếu chéo kiểu "xem Điều 24" không mở passage mới.
- **8 passage dựng từ trích R-Formal**, vì OCR hỏng hoặc trắng: QĐ3266 Đ24 k3–5 · Đ33 k1–2 · Đ34 k2 · Đ35 (trang 20 OCR trắng) · QĐ5339 Đ3 k8. Đây là lỗi "OCR trang trắng im lặng" đã gặp ở Tuần 5; ở đây nó bị phát hiện và được bù chứ không bị bỏ qua im lặng.
- Điều 33, 34 không có tiêu đề ở bất kỳ nguồn nào. **Không tự đặt tiêu đề.**
- ✅ **Đã lấp 18/10/2026 (sau Tuần 19):** Loi gửi PDF gốc QĐ3266; trang 20 được chép tay đúng chữ vào `w5_rformal/source/QD3266_tr20_chep_tay.txt` (Điều 32 k4–6, Điều 33 k1–4, Điều 34 k1–2, Điều 35). Đối chiếu: các trích R-Formal đọc từ ảnh ở Tuần 5 (R-F06…F10) **đúng nội dung** (R-F07–F09 nguyên văn; R-F06, R-F10 diễn đạt lại/rút gọn — nguyên văn ở bản chép tay); thêm R-X20, R-X21 (Đ33 k3, k4 — thủ tục, lớp X). Tiêu đề: Điều 33 "Xử lý sinh viên quá hạn thời gian học tập", Điều 34 "Bằng tốt nghiệp và hạng tốt nghiệp".
  Corpus nay: 144 passage quy chế (OCR 130, **chép tay 10**, dựng từ trích 4). Truy hồi (cùng bộ câu hỏi, không tinh chỉnh): dev Recall@1 19/24 → 19/24, **Recall@5 22/24 → 21/24** (dev08 "điều kiện tốt nghiệp" → Đ32 k1 tụt hạng 6, bị Đ32 k4 và Đ33 k2 mới vượt), MRR 0,849 → 0,845; test không đổi (16/24 · 22/24 · 0,788). Mục tiêu Recall vẫn **chưa đạt** (B6).

---

## 2. Truy hồi (`retriever.py`)

BM25 trên âm tiết + bigram âm tiết, có dấu và không dấu, mở rộng viết tắt học vụ (TC, HK, ĐTBCTL, LVTN, CNTT, ...). Không cần mạng hay model embedding (máy không có model nào trong cache).

### 2.1. Chọn cấu hình trên tập dev, không nhìn tập test

| Cấu hình | R@1 dev | R@5 dev |
|---|---|---|
| unigram, b = 0,75, + TF-IDF ký tự (RRF) | 11/24 | 17/24 |
| unigram, b = 0,75, BM25 thuần | 15/24 | 20/24 |
| **bigram, b = 0,4, BM25 thuần (chọn)** | 18/24 | 21/24 |
| + sửa corpus: tên nhóm tự chọn bằng tiếng Việt, nhãn "CTĐT CNTT K49" | **19/24** | **22/24** |

TF-IDF n-gram ký tự làm giảm kết quả ở mọi cấu hình nên đã bỏ. Hai sửa đổi cuối là sửa **corpus** (passage CTĐT chỉ có mã `g_ngoai_ngu`, không có chữ "ngoại ngữ" hay "CNTT K49"), không phải chỉnh theo từng câu hỏi.

### 2.2. Kết quả — chạy tập test đúng một lần

| Tập | Recall@1 | Recall@5 | MRR | Top-1 sai văn bản |
|---|---|---|---|---|
| dev (đã dùng để chỉnh) | 19/24 = 0,79 | 22/24 = 0,92 | 0,849 | 0/24 |
| **test** | **16/24 = 0,67** | **22/24 = 0,92** | **0,788** | **2/24** |

Recall@1 trên test theo loại: không dấu 2/2 · số liệu 4/4 · trực tiếp 6/9 · diễn đạt khác 3/6 · CTĐT 1/2 · **nhầm văn bản 0/1**.

Khoảng cách dev → test (0,79 → 0,67) cho thấy cấu hình đã khớp một phần vào dev, dù chỉ thử 16 cấu hình. Con số để báo cáo trong luận văn là **con số test**.

### 2.3. Các câu trượt đáng giữ làm ca phân tích

| Câu | Top-1 | Vì sao đáng chú ý |
|---|---|---|
| test10 "Điểm 4,5 học ở trường khác chuyển về có được tích lũy không?" | QĐ3266 Đ17 k1 (đáp án QĐ5339 Đ3 k2 ở hạng 3) | **Bẫy liên văn bản (QD-09).** Văn bản giống hơn nhưng sai phạm vi áp dụng; câu trả lời dựa trên top-1 sẽ là "được" trong khi đúng là "không". Bằng chứng cho H2 |
| test13 "Môn CT177 có tiên quyết là gì?" | CT188 | Passage CT188 *nhắc* CT177 trong mục tiên quyết. Truy hồi từ vựng không phân biệt "tiên quyết **của** X" với "X **là** tiên quyết của Y". Câu này phải hỏi KB (`tien_quyet/2`), không hỏi văn bản |
| test02 "Rớt môn bắt buộc thì phải làm sao?" | Đ27 k4 (hạng 9) | "Rớt" không có trong văn bản (văn bản viết "điểm F"); cần từ điển đồng nghĩa hoặc embedding |
| test06 "Sinh viên được học tối đa mấy năm?" | Đ14 k1 "tối đa 20 TC" | Trùng từ "tối đa"; đúng ở hạng 2 |

---

## 3. Grounding certificate và hậu kiểm

`ground_certificate(cert)`: với mỗi bước `why(atom, r_xxx)` → passage có `asp = r_xxx`. Bước nào không có passage thì ghi vào `khong_nguon`, không bỏ qua im lặng.

| Kiểm tra | Kết quả |
|---|---|
| A. 93/93 quy tắc R-Formal có passage; 53/53 `asp` có passage; passage cùng văn bản + điều với bản ghi | ✅ |
| C. `sv_lvtn` (TRUE), `sv_tron_ngoai_ngu` (FALSE), `sv_mien_ielts` (TRUE): 20/20 bước có passage, đúng văn bản + điều | ✅ |
| D. Trích từ nguồn certificate → cho qua | ✅ |
| D. Chèn passage **truy hồi xếp hạng cao nhất** cho câu hỏi tín chỉ (Đ14 k1) nhưng không thuộc chứng minh → **chặn** | ✅ |
| D. Passage không tồn tại → chặn | ✅ |

---

## 4. Hạn chế đã biết

- **Recall truy hồi tự do chưa đạt mục tiêu.** Hướng cải thiện: embedding đa ngôn ngữ (cần tải model khoảng 1 GB; `sentence-transformers` đã cài), từ điển đồng nghĩa học vụ (rớt ↔ điểm F, GPA ↔ ĐTBCTL), và định tuyến câu hỏi về học phần cụ thể sang KB thay vì sang văn bản.
- **Trích dẫn cho kết luận FALSE** đang lấy 3 nguồn đầu theo thứ tự trong certificate, **chưa ưu tiên nguồn của điều kiện bị vi phạm**. Câu giải thích template của Tuần 12 cũng chỉ ghi "không đủ điều kiện" mà không nêu điều kiện nào.
- Bộ 48 câu do một người soạn và gán đáp án; nên có người thứ hai soát lại đáp án trước khi dùng ở Tuần 20.
- Chưa có cơ chế từ chối khi không passage nào đủ liên quan (câu ngoài miền). Để dành cho Tuần 16 (abstention).

---

## 5. Việc còn lại → Tuần 15+

- [ ] Ưu tiên nguồn của điều kiện vi phạm khi trích dẫn cho FALSE/UNKNOWN
- [ ] Thử embedding (cần mạng một lần để tải model) và so sánh trên **cùng tập test**
- [ ] Đưa test10 (bẫy QD-09) và test13 (tiên quyết ngược chiều) vào bộ Adversarial ở Tuần 17
- [ ] Dùng `retriever.search` làm baseline "RAG thuần" ở Tuần 21

### Ghi chú kiểm chứng

- [x] Mọi kết luận có passage nguồn đúng điều/khoản (A, C)
- [x] Hậu kiểm chặn trích dẫn ngoài chứng minh (D)
- [x] Đáp án truy hồi gán trước khi chạy; tách dev/test; test chạy một lần
- [ ] Recall@1 ≥ 0,80 và Recall@5 ≥ 0,95 trên test: **chưa đạt**

## 6. Cập nhật 26/10/2026 — RAG nhẹ có huấn luyện trọng số

Đã bổ sung xếp hạng kết hợp nội dung đoạn, câu mở đầu, cửa sổ từ, IDF coverage, mã học phần và ví dụ truy hồi được gán nguồn từ 67 câu train tổng hợp. Trọng số chọn trên dev; runtime chỉ dùng thư viện chuẩn Python. Grounding nguồn chứng chỉ giữ độc lập với mô hình xếp hạng.

| Bộ | BM25 cũ R@1 / R@5 | Mới R@1 / R@5 |
|---|---|---|
| Dev 24 câu | 19/24 / 21/24 | 23/24 / 24/24 |
| Test cũ, đã xem; chỉ đối chiếu | 16/24 / 22/24 | 17/24 / 23/24 |
| 29 câu tổng hợp giữ lại trước khi chọn mô hình | 10/29 / 17/29 | 14/29 / 23/29 |

R@5 của tập cũ đạt 95,8%; R@1 mới 70,8%, chưa đạt 80%. Bộ giữ lại mới cũng chưa đạt ngưỡng. Nhãn nguồn mới do trợ lý gán từ corpus trước dự đoán, chưa có người thứ hai kiểm tra; có errata nguồn học lực học kỳ ghi trước dự đoán. Không coi đây là Q-Real thật hoặc kết quả đánh giá kết luận học vụ. Giữ nguyên ô nghiệm thu chưa đạt.

Bằng chứng: `w14_rag/evaluation_ranked_v1_fresh_20261026.json`, `evaluation_ranked_v1_diagnostic_20261026.json`, `retrieval_acceptance_v1.json`. Trọng số `retrieval_model_v1.json` tái tạo bằng `train_retrieval.py`; `validate_retrieval_ranker.py` kiểm tra tách tập, đúng nguồn/mã học phần và grounding độc lập. Không sửa gold, split hoặc hồ sơ benchmark cũ.

## 7. Cập nhật 27/10/2026 — soát gold ca trượt (errata, không sửa gold)

Thử nghiệm exp2 ngày 26/10 (bge-m3 + đặc trưng từ vựng + điểm theo Điều, kiểm định chéo 5 nhóm trên 24 dev + 67 train; **không** đụng holdout/test, **không** đưa vào hệ thống) cho R@1 57/91, R@5 82/91. Người dùng soát toàn bộ 34 ca trượt R@1 và 15 ca trúng chọn ngẫu nhiên (seed 2026), đối chiếu 7 PDF nguồn (`soat_gold_ca_truot_v1_da_ra_soat.xlsx`). Kết quả ghi thành `w14_rag/rag_soat_gold_errata_v1.json` (kèm sha256 workbook); gold đóng băng giữ nguyên.

| Nhóm soát | Gold đúng | Gold sai | Chưa đủ nguồn |
|---|---|---|---|
| 34 ca trượt (3 dev, 31 train) | 27 | 7 | — |
| 15 ca trúng mẫu (5 dev, 10 train) | 12 | 2 | 1 (CT177, thiếu CTĐT K49/đề cương) |

Phân loại errata: 30 xác nhận gold · 9 thêm nguồn thay thế · 3 gold sai có mã thay (hạng hệ thống được chấp nhận) · 6 gold sai **chưa có mã nguồn** (căn cứ đúng chỉ nêu bằng điều/khoản ở ghi chú, hoặc câu ngoài văn bản: phúc khảo điểm giảm, trần nghỉ tạm thời, chuyển chuyên ngành) · 1 thiếu tài liệu (không chấm). Mọi gold sai đều thuộc **train**; gold dev đúng 8/8.

| Đo trên | Gold gốc R@1 / R@5 | Theo errata R@1 / R@5 |
|---|---|---|
| exp2, 91 câu dev + train (CV) | 57/91 / 82/91 | 61/90 / 80/90 |
| exp2, dev | 21/24 / 24/24 | 21/24 / 24/24 |
| exp2, train | 36/67 / 58/67 | 40/66 / 56/66 |
| Ranker v1 đã commit, dev | 23/24 / 24/24 | 23/24 / 24/24 |
| BM25 cũ, dev | 19/24 / 21/24 | 20/24 / 22/24 |

Đọc số: errata **không** đổi số dev của ranker v1, và không đụng holdout/test → ô nghiệm thu Recall giữ **chưa đạt**. R@5 theo errata giảm vì 6 câu gold sai chưa có mã nguồn không thể trúng. Errata soát sau khi đã thấy dự đoán, ca trượt soát hết còn ca trúng chỉ 15/57 (42 ca trúng chưa soát vẫn chấm theo gold gốc; ở mẫu, 2/14 gold sai) → số theo errata thiên về tăng, chỉ báo kèm, không thay số chính thức. Một người soát.

Phát hiện phụ:
- **Nhãn train nhiễu** (9/48 ca soát được có gold sai) — ranker v1 dùng chính các nhãn này làm ví dụ truy hồi. Chưa huấn luyện lại: đổi nhãn train đổi `examples_sha256`, tức là model mới, cần holdout mới (Viec_ton_dong C18).
- **Phân đoạn Đ22 k3/k4 sai** (dev23): OCR đọc "4." thành "+," nên nội dung k4 (công bố điểm, PDF tr.14 — đã đối chiếu ảnh trang) nằm trong `D22:K3`. Sửa generator đúng nhưng đổi corpus → ranker v1 khoá `corpus_sha256` không nạp được (và app deploy dùng corpus này). **Hoãn** tới ranker v2; validate_rag thêm kiểm tra báo CHƯA ĐẠT, không chặn (Viec_ton_dong C17).
- 2 ca trúng có "hạng 1 khác gold" (QS-09cf7d201d99, QS-b51c10db8832) không phải lỗi xuất dữ liệu: gold có 2 mã, sheet chỉ in mã đầu, hạng 1 trùng mã thứ hai.
- Cần thêm tài liệu: CTĐT K49 và đề cương CT177, hướng dẫn phúc khảo, quy định chuyển chuyên ngành, chuẩn đầu ra theo ngành/khoá.
