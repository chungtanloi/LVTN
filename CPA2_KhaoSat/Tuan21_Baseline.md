# TUẦN 21 — BASELINE (đường ống xong · CHƯA chạy thật)

**Giai đoạn:** Evaluation (Tuần 21/24) · **Mục tiêu:** Chạy baseline LLM thuần, RAG thuần, tool-calling trên cùng bộ ca và cùng bộ chấm với CPA²
**Sản phẩm:** Baseline results (`w21_baseline/`)
**Tiêu chí hoàn thành:** Có bảng kết quả

| Hạng mục | Trạng thái |
|---|---|
| Đường ống baseline (3 baseline, 2 nhà cung cấp, bộ chấm chung với CPA²) | **đạt** — `validate_baseline.py` 148 kiểm tra, thử với client giả và máy chủ HTTP cục bộ |
| Chạy baseline **thật** trên dev | **chưa làm** — thiếu khoá API, ID model, giá token (việc A19). Cloud không có khoá; niên luận cũ nằm ở máy Windows |
| Bảng kết quả CPA² vs baseline | **chưa có** — **tiêu chí hoàn thành Tuần 21 chưa đạt** |
| Adapter OpenAI / Gemini | viết theo tài liệu công khai, **chưa kiểm với API thật** (C16) |
| Câu hỏi của benchmark cho baseline | **29/78 ca dev (26/76 test) không phải câu hỏi đúng/sai rõ nghĩa** — lỗi thiết kế của đề từ Tuần 20, báo cáo kèm dòng `[cau_hoi_ro]` (mục 3) |
| `validate_*.py` toàn bộ | **17/17 ĐẠT** (tuần 5–21, đủ 17 file và 17 log) |

---

## 0. Kết luận trước

> Em đã dựng xong đường ống để so CPA² với ba baseline **mà không cần solver**, và kiểm kỹ bằng client giả. **Chưa có con số baseline nào**, nên chưa nói được CPA² hơn baseline bao nhiêu. Review độc lập tìm ra hai điều đáng nói hơn cả code: (1) **bộ ca Tuần 20 đặt câu hỏi cho baseline chưa công bằng ở 29/78 ca dev**; (2) **corpus điều khoản đã commit bị lỗi thời từ C15** (thiếu liên kết R-F07b), đã sinh lại và sửa.

---

## 1. Ba baseline (đều KHÔNG có solver)

| | Mô tả | Cái model nhìn thấy |
|---|---|---|
| **b1** LLM thuần | hồ sơ/bảng điểm + câu hỏi | không có văn bản quy chế |
| **b2** RAG thuần | như b1 + 5 điều khoản BM25 (w14 `Retriever`) tìm theo câu hỏi | chỉ văn bản điều khoản + địa chỉ. Đã gỡ mã quy tắc R-Formal (vd. "xem R-M16") |
| **b3** Tool-calling | như b1 + 3 công cụ **tổng quát**: `may_tinh`, `tra_ctdt`, `tra_cuu_quy_che` | không có công cụ tính ĐTBCTL hay xét tốt nghiệp — nếu có thì đã thành solver |

- **Nhãn:** model phải kết thúc bằng dòng `NHAN: TRUE|FALSE|UNKNOWN`. Thiếu hoặc mơ hồ → UNKNOWN, **đếm riêng** ở cột "thiếu nhãn" để người đọc tự đánh giá.
- **Hai nhà cung cấp** (OpenAI, Gemini) để baseline không lệ thuộc một hãng. Tên model và giá token do người chạy khai trong môi trường — **hệ thống không đoán** (CLAUDE.md ghi "Terra/Sol/Flash" là tên thương mại; cần đối chiếu ID API).
- **Thư viện:** chỉ `urllib` của thư viện chuẩn (CLAUDE.md cấm cài thêm).

## 2. Quy tắc đánh giá và bộ chặn

- **Cùng bộ chấm với CPA²** (`run_adversarial.cham/tong_hop`). Lỗi gọi API (LOI) tính là SAI, như CPA²; khai riêng cột `lỗi`. "Hỏi đúng" **không đo được** cho baseline (câu trả lời tự do không có danh sách biến cần hỏi) → ghi 0/0.
- **Dòng bổ sung như `run_cpa2`:** `[theo errata]` (gold HG sửa sau đóng băng) và `[cau_hoi_ro theo errata]`.
- **Chỉ dev ở Tuần 21.** Test cần `--cho-phep-test`, và chỉ chạy **một lần** (từ chối nếu đã có kết quả test, kể cả đổi `--hau-to`).
- **Đóng băng** (`prompt_dong_bang.json`, hai hash): mẫu prompt + công cụ + tham số gọi model; và prompt **đã dựng** cho mọi ca dev+test + nội dung corpus/CTĐT + mã nguồn dựng yêu cầu. Khác bản đóng băng → chỉ chạy được với `--hau-to`, số chính thức giữ nguyên. Không ghi đè file kết quả đã có.
- **Chi phí:** giá token và trần bắt buộc phải hữu hạn và > 0 (giá 0 hoặc NaN từng làm trần không bao giờ chạy). Trần mặc định **5 USD mỗi lần chạy**. Ước lượng trước khi gọi; phản hồi thiếu `usage` được ước lượng theo ký tự, không tính là miễn phí. Chi phí các ca đã lưu trong checkpoint cộng vào trần khi chạy lại.
- **An toàn khi chạy dở:** mỗi ca xong ghi ngay vào checkpoint (có `fsync`; dòng cuối bị cắt dở thì bỏ qua). Dừng ngay khi vượt trần, lỗi vĩnh viễn của nhà cung cấp (sai model/khoá/tham số), hoặc 5 ca lỗi liên tiếp. Còn ca LOI thì **không ghi kết quả chính thức**, chạy lại sẽ thử đúng các ca đó.
- **Khoá API:** chỉ ở header, đã scrub khỏi mọi thông báo lỗi, không có trong file kết quả hay sổ chi phí. `.env`, `.env.*` nằm trong `.gitignore`; `.env.example` chỉ có tên biến. Test chạy CLI luôn dùng `CPA2_ENV_FILE` trỏ vào file tạm nên không bao giờ gọi API thật.
- **Dữ liệu gửi đi** chỉ là hồ sơ giả lập của benchmark. Câu trả lời thật của form Q-Real **không** gửi đi ở bước này.

## 3. ⚠️ Câu hỏi của benchmark chưa công bằng cho baseline (H1)

CPA² đọc thẳng `claim` của ca (kb/elig/rec/ocr) và không đọc `cau_hoi`; baseline thì phải hiểu `cau_hoi`. Review phát hiện bộ ca Tuần 20 chưa viết câu hỏi tự nhiên đúng nghĩa cho nhiều claim. Em phân loại **theo hình thức câu hỏi và loại ca, không theo kết quả chạy**:

| Lý do | Dev | Test | Vì sao không rõ nghĩa |
|---|---|---|---|
| `rong` | 10 | 10 | câu hỏi rỗng; claim chỉ có ở trường `claim` |
| `atom` | 9 | 7 | hỏi bằng ký hiệu ASP, vd. `passed("ML019")?` |
| `rec_dao_chieu` | 6 | 6 | claim là **phủ định** của câu hỏi (`khong_de_xuat`, `tong_tc_le_20`): trả lời đúng bị chấm sai |
| `hang_khong_co_khong` | 3 | 1 | "xếp hạng gì?" không trả lời được bằng TRUE/FALSE |
| `thay_the_cong_nhan` | 1 | 2 | hỏi "được công nhận" nhưng claim chỉ là "đủ điều kiện được xét" (QĐ5339 Đ2 k6: công nhận cần đơn + quyết định) |
| **Tổng không rõ nghĩa** | **29/78** | **26/76** | |

Báo cáo sẽ có **hai dòng**: `tong` (mọi ca) và `[cau_hoi_ro]` (49 ca dev, 50 ca test). Còn lệch nhẹ không loại được, ghi để người đọc biết:
- câu "đăng ký … được không?" rộng hơn `duoc_dang_ky` (chỉ xét tiên quyết + song hành, không xét học phần có mở kỳ này hay trần 20 TC);
- vài ca gold TRUE kèm điều kiện ("đăng ký cùng CT180");
- NL-05/06/10 là câu hỏi mở nhưng gold UNKNOWN nên câu trả lời đúng vẫn được tính đúng.

**Chưa làm — cần Loi quyết (A20):** viết câu hỏi tự nhiên cho các claim đó (đúng chiều, đóng băng, **soát độc lập như gold** vì đây thực chất là gold thứ hai). Em không tự viết, vì câu hỏi do em viết có thể vô tình hợp hay không hợp với baseline.

## 4. Review đã tìm ra gì (hai lượt, sửa hết các mục cao và trung bình)

- **Lỗi sót của C15 (ngoài Tuần 21):** `w14_rag/corpus.jsonl` đã commit chưa có liên kết sang **R-F07b** ở đoạn Điều 34 khoản 2, nên truy hồi chứng cứ cho quy tắc đó báo "không có nguồn". Mọi validate vẫn đạt vì `validate_rag` tự sinh lại file. Đã chạy lại bộ sinh và commit riêng (`fix(w14)`), diff đúng 1 dòng. **Bài học:** sửa R-Formal thì phải sinh lại và commit corpus.
- **Đốt tiền vô ích:** bản đầu gọi hết 78 ca dù sai model/khoá (404/401), rồi ghi file "kết quả" Soundness 0%. Nay dừng ngay lần đầu, giữ checkpoint.
- **Ngân sách có thể bị bỏ qua:** giá 0 hoặc NaN, phản hồi thiếu `usage`, trần tính lại từ 0 sau mỗi lần chạy lại.
- **Lộ khoá:** nội dung lỗi của nhà cung cấp (thường nhắc lại khoá đã che) từng được lưu vào file kết quả.
- **Hash đóng băng chưa đủ rộng:** thiếu dạng trả lời của w20, độ dài cắt điều khoản, nội dung corpus, mã nguồn dựng yêu cầu, tham số nhiệt độ.
- **Gemini 3 cần "chữ ký suy nghĩ"** khi gọi công cụ: nay phát lại nguyên văn các phần model đã trả.
- **Công bằng:** điều khoản dài bị cắt ở 900 ký tự (28/227 đoạn); mã quy tắc R-Formal lọt vào văn bản đưa cho baseline.
- **Ca LOI lọt vào số chính thức** và không sửa được sau đó (file không ghi đè được) → nay không ghi kết quả khi còn LOI.
- Cả hai lượt đều dùng **kiểm thử đột biến**: cố ý phá (lộ gold, lỗi 404 coi là tạm thời, scrub vô tác dụng, phân loại sai) để chắc test bắt được.

## 5. Ước lượng chi phí (thô, chưa có giá)

Một lần chạy toàn bộ dev, mỗi nhà cung cấp: b1 khoảng 0,24 triệu token vào; b2 khoảng 0,34 triệu; **b3 khoảng 1,15 triệu** (nhiều lượt). Ước lượng dùng 1 token ≈ 2,5 ký tự, chưa tính token suy nghĩ của model suy luận, nên b3 có thể cao hơn. Chạy `python run_baseline.py --bl b3 --nha openai --split dev --uoc-luong` để ra USD khi đã khai giá. Với giá cao, **b3 có thể vượt trần mặc định 5 USD** — khi đó hệ thống dừng và yêu cầu nâng `BASELINE_MAX_USD` có chủ đích.

## 6. Kiểm thử

`w21_baseline/validate_baseline.py` — 148 kiểm tra, không gọi mạng ra ngoài:

| Nhóm | Nội dung |
|---|---|
| A | đọc nhãn |
| B | prompt không lộ gold / id gốc / lý do; b2 không có mã quy tắc |
| C | công cụ b3 (máy tính an toàn, tra CTĐT, vòng lặp có trần lượt) |
| D | khoá API, `.env`, `.env.example` |
| E | ngân sách |
| F | chấm bằng đúng bộ chấm CPA² (client giả; tính tay kỳ vọng) |
| G | bộ chặn, hash đóng băng |
| H | bộ chuyển đổi OpenAI/Gemini với phản hồi mẫu |
| I | sửa theo review lượt 1 (có máy chủ HTTP cục bộ) |
| J | chạy CLI đầu-cuối vào máy chủ giả: kết quả, chi phí, trần, lỗi vĩnh viễn, không lộ khoá |
| K | sửa theo review lượt 2 |

Toàn bộ 17 bộ validate (tuần 5–21): **17/17 `KẾT LUẬN: ĐẠT`**, không có ca FAIL.

## 7. Hạn chế

- **Chưa có số liệu baseline nào.** Mọi kết luận kiểu "CPA² tốt hơn baseline" chưa có cơ sở.
- Adapter OpenAI/Gemini **chưa kiểm với API thật**: tên trường, tham số (model suy luận có thể từ chối `temperature` → đặt `BASELINE_TEMPERATURE=none` *trước* lần chạy đầu và `--ghi-bang --ghi-de`), và hành vi gọi công cụ.
- Bộ ca Tuần 20 do em viết, gold do em viết; baseline do chính em dựng. Cần người thứ hai soát (A7).
- Ước lượng chi phí thô; b3 nhiều lượt khó đoán.
- Giới hạn "một lần chạy test" chỉ được chặn trong phạm vi một thư mục kết quả.

## 8. Việc còn lại

- [ ] **A19 (cần Loi):** đặt `OPENAI_API_KEY`, `GEMINI_API_KEY`, `BASELINE_*_MODEL`, `BASELINE_*_PRICE_IN/OUT` vào **biến môi trường của phiên cloud** (Edit environment → Network secrets / biến môi trường; không dán vào chat). Sau đó: cân nhắc `BASELINE_TEMPERATURE`, chạy `--ghi-bang --ghi-de`, commit, rồi chạy dev (b1 → b2 → b3, từng nhà).
- [ ] **A20 (cần Loi):** có viết câu hỏi tự nhiên cho 29 + 26 ca ở mục 3 (kèm soát độc lập) hay chỉ báo cáo hai dòng `tong` / `[cau_hoi_ro]`.
- [ ] **C16:** kiểm adapter OpenAI/Gemini với API thật; xử lý phản hồi rỗng do `MAX_TOKENS`/`SAFETY` (hiện tính là thiếu nhãn → UNKNOWN).
- [ ] So sánh CPA² và baseline trên **cùng tập ca**: CPA² hiện báo riêng từng bộ (58 + 20 ca dev); cần hàm gộp, làm khi đã có số baseline.
- [ ] Tuần 22: chạy test một lần cho CPA² và baseline, báo cả số gold và số theo errata.

## Cập nhật 27/10/2026 — đóng băng lại prompt (chưa có lần chạy thật nào)

`validate_baseline` M2 báo `prompt_dong_bang.json` lệch: mẫu prompt (`sha256` be0fd8eb…) không đổi, nhưng `sha256_dau_vao` (prompt đã dựng cho mọi ca, gồm đoạn truy hồi của baseline RAG) đổi 1c5687d0… → b06a364a… vì `w14_rag/retriever.py` đổi sau khi đóng băng (ca3c728, c88891b — ranker có huấn luyện, 26/10). Chưa có file kết quả chạy thật nào nên đóng băng lại bằng `run_baseline.py --ghi-bang --ghi-de` là hợp lệ theo quy trình (đóng băng TRƯỚC lần chạy thật đầu tiên). Baseline RAG nay dùng cùng ranker v1 với hệ thống.
