# TUẦN 3 — LITERATURE REVIEW: RAG & NEURO-SYMBOLIC

**Sản phẩm:** Literature review + bảng so sánh
**Tiêu chí hoàn thành:** 8–12 nguồn + research gap ✅ (**13 nguồn**, đã tra cứu và xác minh trực tiếp tháng 8/2026)

> **Ghi chú về độ tin cậy.** Mọi nguồn dưới đây tôi đã mở trang gốc (arXiv/ACL Anthology/Springer/dblp/trang hội nghị) và đọc nội dung. Tuy vậy, **trước khi trích dẫn trong luận văn bạn vẫn phải tự đọc toàn văn** — bảng này là bản đồ định hướng, không phải nguồn thứ cấp để trích lại.

> **Ghi chú về tên gọi.** **CPA²** (*Certified Personalized Academic Advising*) là **tên do chính tác giả luận văn đặt cho hệ thống đề xuất** — chưa phải một công trình đã công bố, và không phải thuật ngữ có sẵn trong tài liệu nào. Trong mọi bảng so sánh dưới đây, 13 mục đánh số [1]–[13] là **công trình của người khác đã công bố**; CPA² là **cột đề xuất của mình**, luôn được ghi rõ "(đề xuất)". Khi viết luận văn, cần giữ nguyên sự phân biệt này để hội đồng không hiểu nhầm là đang trích dẫn một công trình có sẵn.

---

## 1. Bản đồ sáu nhánh nghiên cứu bao quanh CPA² (hệ thống đề xuất)

```
        Nhánh 1: RAG cho quy chế giáo dục        (REBot, EXACT, XAI Challenge)
        Nhánh 2: LLM + solver cho suy luận logic (Logic-LM, LINC, CoTu)
        Nhánh 3: Verification chính sách cho tác tử (UW solver-aided, PolicyGuide)
        Nhánh 4: Rules as Code                    (Mowbray et al.)
        Nhánh 5: Lập kế hoạch học tập bằng ASP    (Kahraman & Erdem)
        Nhánh 6: Abstention / selective prediction (Wen et al. TACL 2025)
                              ↓
                   CPA² nằm ở giao của cả sáu
```

---

## 2. Bảng so sánh 13 công trình (đã bổ sung cột "Quy mô bộ quy tắc" — yêu cầu từ Excel Kế hoạch Tuần 3)

| # | Công trình | Năm/Nơi | Quy mô bộ quy tắc | Làm được gì | **Không** làm gì (khoảng trống) |
|---|---|---|---|---|---|
| **1** | **REBot / CatRAG** — Thanh Ma, Tam-Tri La, Nghi-Minh Nguyen, Van-Khanh Pham Luu, Thu-Lam Le Huu, Huu-Hoa Nguyen (**ĐH Cần Thơ**) | arXiv 2510.01800; MIWAI 2025 (Springer) | **0 quy tắc** (RAG thuần, không có bộ quy tắc) · 1.319 Q&A, 3.256 câu phân loại | Hỏi–đáp quy chế học vụ ĐHCT bằng RAG + GraphRAG; embedding PhoBERTv2, đồ thị Neo4j, bộ phân loại FastText định tuyến; **F1 98,89%**; 6 nhóm chủ đề | **Không có hồ sơ sinh viên.** Không tính toán trên bảng điểm. Không lập kế hoạch. Chỉ trả lời *văn bản nói gì*. Tác giả tự nêu hạn chế: GraphRAG đưa quá nhiều ngữ cảnh gây trả lời thiếu mạch lạc; độ trễ ~7 s |
| **2** | **EXACT 2026** — thử thách XAI lần 2, nhóm URA, **ĐH Bách Khoa TP.HCM**, IEEE IJCNN 2026 | ura.hcmut.edu.vn/exact | **~30 khuôn logic** sinh Z3 kiểm chứng (cho bộ 913 câu Type 1); không phải bộ quy tắc vận hành | Hỏi–đáp giáo dục **có giải thích**; Type 1: 464 bản ghi / **913 câu** về quy chế (điểm, đăng ký, học bổng); Type 2: 5.520 bài vật lý; chấm 3 chiều P1 đáp án / P2 chất lượng giải thích / P3 chiều sâu suy luận; bắt buộc LLM mã nguồn mở ≤ 8B | Trang chính thức ghi rõ **không có dữ liệu sinh viên cá nhân, không tính toán trên bảng điểm, không lập kế hoạch chương trình** |
| **3** | **CoTu at EXACT 2026** — Tran, Nguyen, Thai, Bui, Ma, Pham | arXiv 2607.14735 (7/2026) | **Sinh động từng câu hỏi** (LLM→Z3, không có KB quy tắc tĩnh) | **Gần CPA² nhất về kỹ thuật:** LLM 4B sinh mã hoá **Z3** cho câu hỏi quy chế (Program-of-Thought), vòng tự sửa lỗi, xuất JSON có giải thích; điểm kỹ thuật cao nhất cuộc thi 13,44/15 | Vẫn trên dữ liệu thi (quy chế chung, không có hồ sơ cá nhân). Không có ngữ nghĩa ba trị, không có cơ chế từ chối, không lập kế hoạch. Tác giả tự nêu: khó khăn còn lại nằm ở **chọn tiền đề**, không phải ở suy diễn |
| **4** | **Bridging LLMs and Symbolic Reasoning in Educational QA** — tổng kết XAI Challenge IJCNN 2025 | arXiv 2508.01263 | **Không công bố số lượng quy tắc** — dùng Z3 kiểm chứng bộ dữ liệu | Bộ dữ liệu quy chế đại học xây bằng **khuôn logic có Z3 kiểm chứng**, sau đó sinh viên rà soát; khảo sát các hệ lai LLM + suy luận ký hiệu | Là báo cáo tổng kết cuộc thi, không đề xuất kiến trúc; vẫn không đụng dữ liệu cá nhân |
| **5** | **Solver-Aided Verification of Policy Compliance in Tool-Augmented LLM Agents** — Cailin Winston, Claris Winston, René Just (**Univ. of Washington**) | arXiv 2603.20449 (3/2026) | **~20 chính sách** dịch sang SMT-LIB (TauBench) | Dịch chính sách ngôn ngữ tự nhiên sang **SMT-LIB 2.0**, dùng **Z3** chặn lời gọi công cụ vi phạm trước khi thực thi; đánh giá trên TauBench: giảm vi phạm mà không giảm độ chính xác tác vụ | Miền tác tử dịch vụ khách hàng nói chung, **không phải giáo dục**. Không có suy luận số cá nhân hoá, không có logic ba trị, không sinh chứng chỉ cho người dùng cuối |
| **6** | **PolicyGuide** — Seongjae Kang, Taehyung Yu, Sung Ju Hwang | arXiv 2608.19861 (8/2026) | **~50 luồng công việc** (workflow graph) | Biên dịch chính sách thành **đồ thị luồng công việc**, kiểm tra chủ động ở ranh giới lượt hội thoại thay vì từng hành động đơn lẻ; compliance 0,42 → 0,62 | Cùng miền customer-service; không có bảo đảm hình thức ở mức chứng minh; không xử lý dữ kiện khuyết |
| **7** | **Logic-LM** — Pan et al. | Findings of EMNLP 2023 (arXiv 2305.12295) | **8 bộ suy luận logic tổng hợp** (không phải quy tắc miền) | LLM dịch bài toán ngôn ngữ tự nhiên sang biểu diễn ký hiệu, giao cho solver, có vòng tự sửa theo phản hồi lỗi của solver | Đánh giá trên **bộ suy luận logic tổng hợp**, không phải dữ liệu thật của người dùng; không có khái niệm dữ kiện khuyết hay từ chối trả lời |
| **8** | **LINC** — Olausson et al. | EMNLP 2023 | **Không có KB miền** — dịch sang FOL từng câu | LLM làm **semantic parser** sang FOL, prover định lý quyết định; đo lợi ích của việc tách "dịch" khỏi "suy luận" | Cùng hạn chế: bài toán đóng, dữ kiện đầy đủ, không có miền ứng dụng có chi phí lỗi thật |
| **9** | **Rules as Code: Reducing the problems of 'scaling up'** — Andrew Mowbray, Philip Chung, Graham Greenleaf | Computer Law & Security Review 48:105772 (2023) | **Không đưa số lượng** — phân tích định tính | Hình thức hoá luật thành mã chạy được; phân tích vì sao Rules as Code khó nhân rộng | Chưa áp cho **quy chế học vụ đại học**; không gắn với trợ lý hội thoại; không có tầng LLM |
| **10** | **Personalized Course Schedule Planning Using ASP** — Muhammed Kerem Kahraman, Esra Erdem | PADL 2019 (Springer) | **~40 ràng buộc ASP** (lập lịch) | Lập lịch học **cá nhân hoá** bằng Answer Set Programming, theo sở thích sinh viên, phân bố học phần | Không có ngôn ngữ tự nhiên, **không có chứng chỉ/giải thích**, không suy luận trên quy chế, không xử lý dữ kiện khuyết |
| **11** | **Know Your Limits: A Survey of Abstention in LLMs** — Bingbing Wen, Jihan Yao, Shangbin Feng, Chenjun Xu, Yulia Tsvetkov, Bill Howe, Lucy Lu Wang | TACL vol. 13 (2025) | **0 quy tắc** (khảo sát abstention thống kê) | Khảo sát toàn diện về **abstention**: phân loại theo giai đoạn (pretraining / alignment / inference) và ba góc nhìn (khả năng trả lời của câu hỏi, độ tự tin mô hình, giá trị con người) | Toàn bộ dựa trên **độ tin cậy thống kê của mô hình**, không dựa trên chứng minh logic. Tác giả nêu đúng khoảng trống của CPA²: *"abstention bị coi là điểm kết thúc thay vì kích hoạt bước tiếp theo của hội thoại"* — tức **không hệ nào chỉ ra dữ kiện nào còn thiếu** |
| **12** | **Adaptive RAG / Query Routing** — Jeong et al. và dòng benchmark bộ định tuyến 2024–2026 | NAACL 2024 và tiếp nối | **0 quy tắc** | Quyết định *có nên truy hồi hay không* và truy hồi sâu đến đâu theo độ khó câu hỏi | Vẫn giả định **đáp án nằm sẵn trong tài liệu**. Định tuyến giữa các *cách truy hồi*, không định tuyến sang *tính toán trên dữ liệu người dùng* |
| **13** | **Degree audit / "What-if report"** — Northwestern, Harvard, BU, PeopleSoft | phần mềm vận hành | **Không công bố** (phần mềm đóng) | Có thật: sinh viên bấm nút xem "nếu đổi ngành thì sao"; chứng minh **nhu cầu này tồn tại trong thực tế vận hành** | Là **phần mềm hành chính**, không phải nghiên cứu. Không ngôn ngữ tự nhiên, không bảo đảm hình thức, không ai công bố phương pháp hay đánh giá |
| **CPA² (đề xuất)** | — | **QĐ3266 (36 điều) + QĐ5339 (4 điều) → 71 đơn vị trong miền (F 58 / P 8 / N 5), 53 quy tắc ASP + 78 dòng CTĐT CNTT K49 (161 TC)** | Kiến trúc 4 tầng (Parser → KB → Solver → Verbalizer) với ngữ nghĩa ba trị + chứng chỉ | — |

---

## 3. Định vị bằng hai trục

Trục ngang: hệ thống có suy luận trên **dữ liệu cá nhân** của người học không?
Trục dọc: kết luận có **bảo đảm hình thức** (chứng minh bằng solver) không?

```
                        KHÔNG CÁ NHÂN HOÁ              CÁ NHÂN HOÁ
                  ┌────────────────────────────┬────────────────────────────┐
                  │  REBot / CatRAG      [1]   │  AcademiQ (niên luận)      │
  KHÔNG BẢO ĐẢM   │  EXACT 2026          [2]   │  Degree audit "what-if"[13]│
  HÌNH THỨC       │  Adaptive RAG       [12]   │  Chatbot tư vấn khác       │
                  │  Abstention (thống kê)[11] │                            │
                  ├────────────────────────────┼────────────────────────────┤
                  │  CoTu (Z3)           [3]   │                            │
  CÓ BẢO ĐẢM      │  Solver-aided policy [5]   │      ←  Ô TRỐNG  →         │
  HÌNH THỨC       │  PolicyGuide         [6]   │         CPA²               │
                  │  Logic-LM, LINC    [7,8]   │                            │
                  │  Rules as Code       [9]   │                            │
                  │  ASP course planning[10]   │  (gần nhất, nhưng thiếu    │
                  │                            │   NL + chứng chỉ + ba trị) │
                  └────────────────────────────┴────────────────────────────┘
```

**Lưu ý trung thực:** ô dưới-phải **không hoàn toàn trống**. Kahraman & Erdem [10] đã lập kế hoạch học tập cá nhân hoá bằng ASP — tức có cả cá nhân hoá lẫn bảo đảm hình thức. Nhưng công trình đó **không có giao diện ngôn ngữ tự nhiên, không sinh chứng chỉ giải thích được cho sinh viên, không suy luận trên văn bản quy chế, và không xử lý dữ kiện khuyết**. Nên nói *"ô trống hoàn toàn"* là nói quá; phát biểu chính xác hơn nằm ở mục 4.

---

## 4. Research gap — phát biểu chính xác

### 4.1. Ba quan sát ghép lại

1. **Giả định nền của RAG sai trong miền này.** Toàn bộ dòng RAG [1, 12] giả định đáp án nằm sẵn trong tài liệu. Không tài liệu nào chứa câu *"sinh viên X còn thiếu 34 tín chỉ"* — mệnh đề đó phải được **suy ra**, không phải **tìm ra**.

2. **Nhánh solver đã chạm giáo dục, nhưng dừng trước hồ sơ cá nhân.** CoTu [3] đã dùng Z3 cho quy chế giáo dục — đây là công trình gần nhất và **phải được trích dẫn ngay ở chương Related Work**, không được bỏ qua. Nhưng CoTu chạy trên dữ liệu thi có tiền đề cho sẵn; EXACT 2026 [2] tuyên bố rõ **không đụng dữ liệu sinh viên cá nhân, không tính toán bảng điểm, không lập kế hoạch**. Nhánh verification tổng quát [5, 6] thì làm cho tác tử dịch vụ khách hàng.

3. **Abstention hiện nay dựa trên độ tự tin thống kê, không dựa trên chứng minh.** Khảo sát TACL 2025 [11] nêu đúng hai khoảng trống của CPA²: abstention bị coi là *điểm kết thúc* chứ không phải bước mở đầu hội thoại tiếp theo, và không hệ nào **chỉ ra chính xác dữ kiện nào còn thiếu**.

### 4.2. Phát biểu khe hở

> **Chưa có công trình nào ghép đủ bốn yếu tố sau:**
> **(a)** suy luận trên **hồ sơ học tập cá nhân** của người học, **(b)** với **bảo đảm hình thức bằng solver** cho mọi mệnh đề phát ra, **(c)** dưới **ngữ nghĩa ba trị** biết từ chối khi dữ kiện khuyết và **chỉ ra đúng dữ kiện còn thiếu**, **(d)** qua **giao diện hội thoại tiếng Việt** có chứng chỉ diễn đạt lại được.

**Mức tin cậy:** *cao* rằng chưa có công trình nào ghép đủ cả bốn. *Trung bình* với từng cặp hai yếu tố — đặc biệt cặp (a)+(b) đã bị [10] chạm tới ở dạng lập kế hoạch, và cặp (b)+(d) đã bị [3] chạm tới ở dạng hỏi–đáp quy chế. Đây là lý do phần Related Work phải viết cẩn thận: **định vị bằng sự kết hợp và bằng ngữ nghĩa ba trị, không bằng tuyên bố "chưa ai làm gì cả"**.

### 4.3. Bốn đóng góp tương ứng

| Đóng góp | Lấp khoảng trống của | Sản phẩm cụ thể |
|---|---|---|
| **C1.** Taxonomy khả năng hình thức hoá quy chế học vụ đại học Việt Nam + bộ quy tắc R-Formal công bố được | [9] chưa áp cho giáo dục; [1] không hình thức hoá gì | Bộ dữ liệu R-Formal + chỉ số Formalization Coverage |
| **C2.** Ngữ nghĩa ba trị có **chỉ điểm dữ kiện thiếu**, dựa trên suy diễn chứ không dựa trên độ tự tin | [11] nêu đúng khoảng trống này | Abstention engine + đường cong Coverage ↔ Selective Accuracy |
| **C3.** Phát biểu hình thức bài toán **tư vấn học vụ phản thực** + thuật toán + bộ test | [10] có lập kế hoạch nhưng không phản thực, không NL; [3] không lập kế hoạch | CF-Bench + Counterfactual Optimality Gap |
| **C4.** Độ đo **bảo toàn chân trị khi diễn đạt** (verbalization faithfulness) | [5, 6] không có bước diễn đạt cho người dùng cuối | Độ đo + thí nghiệm đánh đổi tự nhiên ↔ trung thực |

---

## 5. Vị trí của hệ thống đề xuất (CPA²) so với ba công trình gần nhất — bảng cần đưa vào luận văn

*Ba cột đầu là công trình đã công bố; cột cuối là hệ thống mình đề xuất, chưa tồn tại — mọi dấu ✅ ở cột đó là **mục tiêu phải chứng minh**, không phải kết quả đã có.*

| Tiêu chí | REBot [1] | CoTu [3] | Solver-aided policy [5] | **CPA² (đề xuất)** |
|---|:-:|:-:|:-:|:-:|
| Miền giáo dục | ✅ | ✅ | ❌ | ✅ |
| Tiếng Việt | ✅ | ✅ | ❌ | ✅ |
| Dùng solver | ❌ | ✅ Z3 | ✅ Z3 | ✅ ASP + CP-SAT |
| Suy luận trên **hồ sơ cá nhân** | ❌ | ❌ | ❌ | ✅ |
| Ngữ nghĩa **ba trị** | ❌ | ❌ | ❌ | ✅ |
| **Chỉ ra dữ kiện còn thiếu** | ❌ | ❌ | ❌ | ✅ |
| Truy vấn **phản thực** / lập kế hoạch | ❌ | ❌ | ❌ | ✅ |
| **Chứng chỉ** truy vết tới điều khoản nguồn | ❌ | một phần | một phần | ✅ |
| Hậu kiểm bước diễn đạt | ❌ | ❌ | ❌ | ✅ |

---

## 6. Baseline bắt buộc (chốt từ phần khảo sát này)

| Baseline | Đại diện cho dòng nào | Vai trò |
|---|---|---|
| LLM sinh trực tiếp, không truy hồi | — | Chặn dưới |
| RAG thuần | REBot [1] và dòng chính hiện nay | So sánh chính về hỏi–đáp quy chế |
| **RAG + LLM tự gọi công cụ** (ReAct/Toolformer) | Kiến trúc cả ngành đang mặc định là "đủ tốt" | **Baseline mạnh nhất, bắt buộc có** |
| **LLM → Z3 kiểu Program-of-Thought** | CoTu [3] | Baseline neuro-symbolic cùng hướng — nếu thắng cả cái này thì đóng góp mới thật sự nằm ở ba trị + phản thực |
| AcademiQ hiện tại (tính bằng Python, điền mẫu) | Chính niên luận của mình | Cho thấy mức cải thiện |

> Nếu chứng minh được CPA² thắng cả baseline "LLM tự gọi công cụ" **và** baseline "LLM → Z3", kết quả rất mạnh — vì cả hai đều là kiến trúc đang được coi là đủ tốt.

---

## 7. Việc còn treo sau Tuần 3

- [ ] Đọc **toàn văn** [3] CoTu và [5] Solver-Aided — đây là hai bài gần nhất về phương pháp, phải hiểu kỹ mượn được gì và phải tự làm gì
- [ ] Liên hệ nhóm tác giả REBot **ngay trong ĐHCT** — nếu chia sẻ được bộ dữ liệu quy chế thì có ngay baseline thật thay vì tự dựng
- [ ] Kiểm tra bộ 913 câu logic của EXACT 2026 có công khai không → dùng làm **baseline bên ngoài**, chứng minh không chỉ tự đánh giá trên dữ liệu nhà làm
- [ ] Xác minh lại chi tiết [7] Logic-LM, [8] LINC, [12] Adaptive-RAG trên ACL Anthology (bảng này ghi theo tri thức đã có, mức xác minh thấp hơn các mục còn lại)
- [ ] Tra thêm nhánh **curriculum/degree-audit formal verification** — có thể còn công trình chưa tìm ra, đặc biệt trong cộng đồng Educational Data Mining

---

## Nguồn đã tra cứu và xác minh

1. [REBot: From RAG to CatRAG with Semantic Enrichment and Graph Routing — arXiv 2510.01800](https://arxiv.org/abs/2510.01800) · [bản Springer, MIWAI 2025](https://link.springer.com/chapter/10.1007/978-981-95-4960-3_35)
2. [EXACT 2026 — 2nd International XAI Challenge for Transparent Educational QA, IJCNN 2026 (URA, HCMUT)](https://ura.hcmut.edu.vn/exact)
3. [CoTu at EXACT 2026: Neuro-Symbolic Reasoning for Transparent Educational QA — arXiv 2607.14735](https://arxiv.org/abs/2607.14735)
4. [Bridging LLMs and Symbolic Reasoning in Educational QA Systems: Insights from the XAI Challenge at IJCNN 2025 — arXiv 2508.01263](https://arxiv.org/abs/2508.01263)
5. [Solver-Aided Verification of Policy Compliance in Tool-Augmented LLM Agents — arXiv 2603.20449 (UW)](https://arxiv.org/abs/2603.20449)
6. [PolicyGuide: From Guarding One Action to Guiding the Whole Workflow — arXiv 2608.19861](https://arxiv.org/abs/2608.19861)
7. [Logic-LM: Empowering LLMs with Symbolic Solvers for Faithful Logical Reasoning — Findings of EMNLP 2023](https://aclanthology.org/2023.findings-emnlp.248/)
8. [LINC: A Neurosymbolic Approach for Logical Reasoning by Combining LMs with First-Order Logic Provers — EMNLP 2023](https://openreview.net/forum?id=h00GHjWDEp)
9. [Mowbray, Chung, Greenleaf — Representing legislative Rules as Code: Reducing the problems of 'scaling up', Computer Law & Security Review 48:105772 (2023)](https://dblp.org/db/journals/clsr/clsr48.html)
10. [Kahraman & Erdem — Personalized Course Schedule Planning Using Answer Set Programming, PADL 2019](https://link.springer.com/chapter/10.1007/978-3-030-05998-9_3)
11. [Wen et al. — Know Your Limits: A Survey of Abstention in Large Language Models, TACL vol. 13 (2025)](https://aclanthology.org/2025.tacl-1.26.pdf)
12. Adaptive RAG / Query Routing (Jeong et al., NAACL 2024) — *chưa mở toàn văn ở vòng này, cần xác minh*
13. [Degree "What-If" reports — Northwestern University](https://www.northwestern.edu/ses/staff/student-records/generating-degree-what-if-reports.html)
