# TUẦN 1 — PROBLEM STATEMENT & SCOPE

**Đề tài:** CPA² — *Certified Personalized Academic Advising*
Tư vấn học vụ cá nhân hoá có chứng chỉ chứng minh

**Sinh viên:** Chung Tấn Lợi — B2306555 — Trường CNTT&TT, ĐH Cần Thơ
**Giai đoạn:** Khảo sát (Tuần 1/24) · **Sản phẩm:** Problem statement + scope
**Tiêu chí hoàn thành:** chốt được bài toán và giới hạn ✅
**Sửa đổi 09/10/2026:** bỏ "sàn tín chỉ" (P-2), tách giả định 5.3 số 3 thành 3a/3b (QD-09), CTĐT chính K51 → K49.

---

## 1. Phát biểu bài toán

### 1.1. Bối cảnh

Sinh viên đại học liên tục phải ra quyết định học vụ dựa trên ba nguồn tri thức khác nhau:

| Nguồn | Ví dụ | Bản chất |
|---|---|---|
| Văn bản quy chế | QĐ3266/2024 về công tác học vụ | Văn bản pháp quy, tĩnh, dùng chung |
| Chương trình đào tạo (CTĐT) | CTĐT ngành CNTT khoá K49 (ban đầu dự kiến K51) | Cấu trúc yêu cầu + đồ thị tiên quyết |
| Hồ sơ cá nhân | Bảng điểm, tín chỉ tích luỹ, chứng chỉ miễn | Dữ kiện riêng từng người, **luôn không đầy đủ** |

Các trợ lý ảo học vụ hiện nay — kể cả REBot/CatRAG được công bố ngay tại ĐHCT — chỉ khai thác nguồn thứ nhất. Chúng trả lời *"văn bản quy định thế nào"*. Chúng **không** trả lời được *"trường hợp của em thì sao"*.

### 1.2. Bài toán trung tâm

> **Cho** một câu hỏi tiếng Việt của sinh viên, một bộ quy chế học vụ, một CTĐT, và một hồ sơ học tập **có thể khuyết dữ liệu**,
> **hãy** sinh ra một câu trả lời mà **mọi mệnh đề nói về sinh viên đó đều được một bộ giải ràng buộc chứng minh trước khi được phát ra**, và khi dữ liệu chưa đủ để chứng minh thì hệ thống **phải từ chối kết luận** và chỉ ra chính xác dữ kiện còn thiếu.

### 1.3. Vì sao RAG không giải được — về nguyên lý

Toàn bộ dòng RAG (kể cả Adaptive RAG, GraphRAG, Self-RAG) đứng trên một giả định nền:

> *Đáp án đã nằm sẵn ở đâu đó trong tập tài liệu; việc của hệ thống là tìm ra nó.*

Với tư vấn học vụ cá nhân hoá, giả định này **sai**. Không tài liệu nào chứa câu *"Lợi còn thiếu 34 tín chỉ"*. Mệnh đề đó phải **được suy ra** từ phép hợp của quy chế × CTĐT × bảng điểm. Truy hồi không tạo ra tri thức mới; chỉ suy diễn mới tạo ra.

Đây là luận điểm khoa học trung tâm của đề tài: **chỉ ra rằng một dòng nghiên cứu lớn đang dùng sai công cụ cho một lớp bài toán quan trọng.**

### 1.4. Vì sao lỗi ở đây đắt

Chatbot nói sai về phim ảnh thì buồn cười. Chatbot nói sai *"em đủ điều kiện tốt nghiệp rồi"* khiến sinh viên chậm một học kỳ và mất một cơ hội việc làm. Chi phí lỗi ở miền này **bất đối xứng và có thật** — điều này biện minh cho công sức hình thức hoá, khác với phần lớn công trình verification phải chật vật giải thích vì sao cần phức tạp đến thế.

---

## 2. Input / Output

### 2.1. Input

| Ký hiệu | Thành phần | Dạng | Nguồn thực tế đang có |
|---|---|---|---|
| `Q` | Câu hỏi tiếng Việt | chuỗi | Bộ Q-Real sẽ xây (400–600 câu) |
| `R` | Quy chế học vụ đã hình thức hoá | tập quy tắc logic + con trỏ nguồn (điều/khoản) | QĐ3266/2024 (PDF, ĐHCT) |
| `C` | Chương trình đào tạo | học phần, tín chỉ, loại, nhóm tự chọn, đồ thị tiên quyết (DAG) | 40+ file CTĐT K48–K51, 8 ngành |
| `F` | Dữ kiện sinh viên | tập bộ ba `(học_phần, trạng_thái, độ_tin_cậy)` | Bảng điểm thật + hồ sơ giả lập |
| `U` | Tập dữ kiện **khuyết** | danh sách dữ kiện chưa biết | suy ra từ `C \ F` và OCR lỗi |

Trạng thái học phần ∈ `{passed, failed, exempted, substituted, in_progress, unknown}`.

### 2.2. Output

Hệ thống trả về một bộ bốn:

```
⟨ verdict , certificate , explanation_vi , missing_facts ⟩
```

| Thành phần | Nội dung |
|---|---|
| `verdict` | `TRUE` / `FALSE` / `UNKNOWN` — **ngữ nghĩa ba trị, bắt buộc** |
| `certificate` | Dẫn xuất kiểm tra được bằng máy: Claim → Proof → Rule → Fact → Source. Với `FALSE`: kèm phản ví dụ. Với truy vấn tối ưu: kèm chứng minh không tồn tại phương án tốt hơn |
| `explanation_vi` | Câu tiếng Việt do LLM **diễn đạt lại chứng chỉ** — không được thêm mệnh đề mới |
| `missing_facts` | Khi `UNKNOWN`: đúng những dữ kiện nào còn thiếu, và mỗi khả năng dẫn tới kết luận gì |

**Bất biến bắt buộc (system invariant):** mọi con số và mọi mã học phần xuất hiện trong `explanation_vi` phải xuất hiện trong `certificate`. Không khớp → chặn câu trả lời.

---

## 3. Kiến trúc bốn tầng

```
              Câu hỏi tiếng Việt
                      │
   ┌──────────────────▼──────────────────┐
   │ [1] SEMANTIC PARSER  (LLM)          │  câu hỏi → truy vấn hình thức
   │  "em còn thiếu gì để ra trường?"    │  ?X : Requires(SV,X) ∧ ¬Completed(SV,X)
   └──────────────────┬──────────────────┘
                      │
   ┌──────────────────▼──────────────────┐
   │ [2] KNOWLEDGE BASE hình thức        │  • R: quy chế QĐ3266 (Rules as Code)
   │                                     │  • C: CTĐT + DAG tiên quyết
   │                                     │  • F: dữ kiện sinh viên + confidence
   └──────────────────┬──────────────────┘
                      │
   ┌──────────────────▼──────────────────┐
   │ [3] SOLVER  (ASP / SMT / CP-SAT)    │  TRUE  + chứng chỉ dẫn xuất
   │                                     │  FALSE + phản ví dụ
   │                                     │  UNKNOWN + dữ kiện còn thiếu
   └──────────────────┬──────────────────┘
                      │
   ┌──────────────────▼──────────────────┐
   │ [4] VERBALIZER (LLM) + HẬU KIỂM     │  chứng chỉ → tiếng Việt
   │                                     │  quét mọi số/mã: không khớp → chặn
   └─────────────────────────────────────┘
```

**Đảo ngược vai trò LLM.** Ở mọi hệ thống hiện nay, LLM suy luận rồi (có thể) được kiểm tra sau. Trong CPA², **LLM bị cấm suy luận về sinh viên**; nó chỉ được dịch câu hỏi vào (tầng 1) và diễn đạt kết quả ra (tầng 4). Hệ quả: hệ thống không thể nói sai về sinh viên — không phải vì được huấn luyện tốt hơn, mà vì **về mặt kiến trúc không có đường nào để nói sai**.

---

## 4. Câu hỏi nghiên cứu và giả thuyết

| Mã | Câu hỏi nghiên cứu |
|---|---|
| **RQ1** | Bao nhiêu phần trăm điều khoản của một quy chế học vụ đại học Việt Nam dịch được sang logic thực thi? Loại điều khoản nào kháng lại việc hình thức hoá, và vì sao? |
| **RQ2** | Thiết kế ngữ nghĩa ba trị (TRUE/FALSE/UNKNOWN) như thế nào để hệ thống từ chối đúng lúc và chỉ ra đúng dữ kiện còn thiếu? |
| **RQ3** | Có thể trả lời truy vấn **phản thực** (*"nếu em rớt CT177 thì tốt nghiệp trễ mấy kỳ?"*) bằng lập kế hoạch có ràng buộc, kèm chứng minh tối ưu, hay không? |
| **RQ4** | Bước diễn đạt của LLM bảo toàn chân trị của chứng chỉ ở mức nào, và ràng buộc giải mã nào giữ nó cao mà không làm câu văn cứng nhắc? |

| Mã | Giả thuyết kiểm chứng được |
|---|---|
| **H1** | CPA² đạt Soundness Rate cao hơn có ý nghĩa thống kê so với cả 4 baseline, đặc biệt trên bộ Adversarial |
| **H2** | RAG và LLM-gọi-công-cụ có Coverage cao nhưng Soundness thấp trên câu hỏi cá nhân hoá — tức **tự tin một cách sai lầm** |
| **H3** | Trên nhóm câu phản thực, mọi baseline gần như thất bại hoàn toàn, còn CPA² giải được |
| **H4** | Tồn tại đánh đổi **đo được** giữa ràng buộc diễn đạt và cảm nhận tự nhiên của người đọc |

**Tính khả bác bỏ (falsifiability).** Tuyên bố *"hệ thống không thể phát biểu sai về sinh viên"* bị bác ngay nếu hội đồng tìm được một câu hỏi khiến nó nói sai. Đây là điều một luận văn dạng *"chatbot của tôi đạt 80% accuracy"* không bao giờ có được.

---

## 5. Phạm vi đề tài (SCOPE)

### 5.1. TRONG phạm vi ✅

| Hạng mục | Giới hạn cụ thể |
|---|---|
| Quy chế | **QĐ3266/2024** của ĐH Cần Thơ, hệ đại học chính quy |
| Nhóm điều khoản ưu tiên | (1) cảnh báo học vụ · (2) điều kiện tốt nghiệp · (3) trần tín chỉ đăng ký (QĐ3266 không có sàn — xem Tuần 5, phát hiện P-2) · (4) xếp loại · (5) miễn & thay thế học phần |
| CTĐT | Ngành **CNTT khoá K49** làm ngành chính (đổi từ K51 sang K49 từ Tuần 5; Curriculum KB v1 ở Tuần 6 là CTĐT K49 — **cần ghi lý do chọn K49**); mở rộng sang 8 ngành của Trường CNTT&TT nếu kịp |
| Ngôn ngữ | Tiếng Việt (đầu vào và đầu ra) |
| Loại truy vấn | Tra cứu quy chế · tính toán cá nhân hoá · truy vấn phản thực · kiểm tra đủ điều kiện |
| Dữ liệu vào | Bảng điểm PDF/ảnh (có OCR + confidence), hồ sơ giả lập, dữ liệu thật đã ẩn danh |
| Solver | **clingo (ASP)** làm bộ giải chính + **CP-SAT** cho nhánh lập kế hoạch (xem Tuần 4) |

### 5.2. NGOÀI phạm vi ❌

| Không làm | Lý do |
|---|---|
| Xếp thời khoá biểu theo phòng/giảng viên/khung giờ | Bài toán timetabling khác về bản chất, đã có nhiều công trình |
| Dự báo điểm số tương lai của sinh viên | Bài toán học máy dự báo, không phải suy diễn có bảo đảm |
| Tư vấn nghề nghiệp, tâm lý, tài chính | Ngoài miền học vụ |
| Triển khai vận hành thật trên hệ thống Phòng Đào tạo | Vấn đề hạ tầng và pháp lý dữ liệu, không phải nghiên cứu |
| Tự động hoá **toàn bộ** quy chế | Có điều khoản không hình thức hoá được (xem RQ1) — đó là **kết quả nghiên cứu**, không phải thất bại |
| Xử lý điều khoản dạng *"trường hợp đặc biệt do Hiệu trưởng quyết định"* | Được **phân loại là Not-Formalizable** và trả về `UNKNOWN` có kèm hướng dẫn liên hệ, không đoán |
| So sánh nhiều LLM backbone | Chọn 1–2 mô hình, cố định; đóng góp nằm ở kiến trúc chứ không ở mô hình |

### 5.3. Giả định làm việc

1. Bảng điểm là nguồn dữ kiện có thẩm quyền, nhưng **có thể khuyết và có thể sai do OCR** → mọi dữ kiện mang `confidence`.
2. CTĐT của một khoá là cố định trong suốt thời gian sinh viên theo học.
3. Quy chế áp dụng theo phiên bản có hiệu lực tại thời điểm hỏi. Giả định này tách làm hai:
   - **3a. Xung đột liên phiên bản** (văn bản mới thay văn bản cũ cùng phạm vi): **không xử lý**, chỉ dùng bản đang hiệu lực.
   - **3b. Xung đột liên văn bản** (hai văn bản **cùng hiệu lực, khác phạm vi**, ví dụ QĐ3266 và QĐ5339 có bảng quy đổi điểm khác nhau): **có thật và phải xử lý**. CPA² phân giải theo **phạm vi áp dụng** (quyết định diễn giải QD-09, xem Tuần 5 phụ lục v1.4 mục 4) và mọi kết luận dựa trên QD-09 phải ghi rõ trong chứng chỉ.
4. Một học phần đã `passed` thì không bị thu hồi.
5. Chỉ mô hình hoá các học kỳ chính; học kỳ hè xử lý như học kỳ có trần tín chỉ riêng.

---

## 6. Tiêu chí thành công của luận văn

| Mức | Điều kiện đạt |
|---|---|
| **Tối thiểu** | Hình thức hoá được 3 nhóm điều khoản; solver trả lời được các câu hiện AcademiQ đang trả lời, kèm chứng chỉ; Soundness = 100% trên bộ G-Truth |
| **Đạt kỳ vọng** | Thêm logic ba trị + cơ chế từ chối; báo cáo đường cong Coverage–Selective Accuracy; thắng 4 baseline trên bộ Adversarial |
| **Vượt kỳ vọng** | Thêm suy luận phản thực có chứng minh tối ưu; đo Verbalization Faithfulness; công bố bộ dữ liệu R-Formal |

## 7. Rủi ro và van an toàn

| Rủi ro | Van an toàn |
|---|---|
| Hình thức hoá quy chế bế tắc | Thu hẹp xuống **3 nhóm điều khoản** làm thật sâu. Ba điều khoản chứng minh chặt chẽ có giá trị hơn hai mươi điều khoản hời hợt |
| Semantic parser tiếng Việt yếu | Hạ xuống tập truy vấn mẫu có khe (query templates); parser trở thành phần đánh giá riêng, không phải điểm chặn |
| Không đủ dữ liệu thật | Dùng hồ sơ giả lập phủ ca biên; đã có sẵn ~60 hồ sơ JSON từ niên luận |
| Bị coi là trùng REBot | Nhấn mạnh: REBot định tuyến giữa **hai cách truy hồi tài liệu**; CPA² suy diễn trên **dữ liệu cá nhân** — khác về bản chất (xem Tuần 3) |

---

## 8. Nền tảng đã có sẵn từ niên luận AcademiQ

Đây là lợi thế cần nói rõ với giảng viên hướng dẫn — phần hạ tầng không phải làm lại:

- Quy chế QĐ3266 dạng PDF + pipeline ingest và RAG (Chroma, PhoBERT-based embedding)
- 40+ file CTĐT các khoá K48–K51 cho 8 ngành
- Đồ thị tiên quyết đã mã hoá (`core/constants.py: PREREQS`) và bảng tín chỉ
- Bộ phân tích bảng điểm có OCR (`core/transcript_parser.py`)
- ~60 hồ sơ sinh viên JSON và tầng nghiệp vụ tính toán học vụ
- Baseline sẵn có để so sánh: chính AcademiQ hiện tại

---

### Ghi chú kiểm chứng (bắt buộc trước khi đưa vào luận văn)

- [ ] Đối chiếu lại **toàn văn QĐ3266** để chốt danh sách 5 nhóm điều khoản ở mục 5.1 — bản hiện tại dựa trên tri thức đã dùng trong niên luận, chưa trích dẫn số điều/khoản.
- [ ] Xác nhận `MIN_CREDITS_TO_GRADUATE` và trần tín chỉ theo đúng CTĐT K51 ngành CNTT (số dùng trong prototype Tuần 4 là số **thu nhỏ**, không phải số thật). → **Đã xong ở Tuần 5–6 cho K49:** 161 TC, 4,5 năm, trần 20 TC/HK (QĐ3266 Đ.14 k.1).
- [ ] Chốt với GVHD phạm vi 1 ngành hay 8 ngành.
