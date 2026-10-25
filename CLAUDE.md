# CPA² — Certified Personalized Academic Advising (Luận văn tốt nghiệp)

## Tổng quan
- Mục tiêu: trợ lý tư vấn học vụ cá nhân hoá cho SV ĐH Cần Thơ, mọi kết luận (TRUE/FALSE/UNKNOWN) đi kèm **chứng chỉ chứng minh** truy về điều/khoản quy chế (QĐ3266, QĐ5339) và CTĐT CNTT K49. Kế hoạch 24 tuần; tiến độ ở `Ke_hoach_nghien_cuu_CPA2_24_tuan.xlsx`.
- Stack: Python 3.14 · clingo (ASP, solver chính) · ortools CP-SAT (đối chiếu) · jsonschema · openpyxl (Excel). Truy hồi RAG tự viết (BM25), không cần mạng.
- Lệnh (chạy từ `CPA2_KhaoSat/`, Windows cần `PYTHONIOENCODING=utf-8`):
  - build: `python w6_curriculum/build_curriculum.py` (sinh CTĐT .lp/.json) · `python w14_rag/build_corpus.py` (sinh corpus)
  - test: chạy `validate_*.py` trong từng thư mục tuần (`cd wN_xxx && python validate_*.py`); tất cả phải in `KẾT LUẬN: ĐẠT` và exit 0
  - lint: chưa cấu hình
  - dev/demo: `python w14_rag/grounded_answer.py --student w7_student_facts/students/sv_lvtn.json`

Chạy toàn bộ test:
```bash
cd CPA2_KhaoSat && export PYTHONIOENCODING=utf-8
for f in w*/validate_*.py; do (cd $(dirname $f) && python $(basename $f) >/dev/null; echo "$f exit=$?"); done
```
Dịch vụ web (cần fastapi + httpx2, xem `services/cpa2_api/requirements-dev.txt`): `cd services/cpa2_api && python validate_api.py [--nhanh]`.

## Quy trình bắt buộc (ECC)

Với MỌI tính năng hoặc thay đổi không tầm thường:
1. **Plan**: dùng ECC plan; trình bày kế hoạch và CHỜ tôi xác nhận rồi mới code.
2. **TDD**: dùng ECC tdd; viết test trước, test phải fail, rồi mới implement. Ở dự án này "test" = thêm ca vào `validate_*.py` của tuần tương ứng (atom kỳ vọng có/không có trong answer set). Sửa quy tắc R-Formal thì phải có ca hồi quy **fail với luật cũ**.
3. **Implement**: sửa nhỏ, đúng phạm vi kế hoạch đã duyệt.
4. **Review**: dùng ECC code-review cho phần vừa thay đổi; sửa các vấn đề mức cao/nghiêm trọng.
5. **Verify**: build + test của **mọi tuần** đều pass mới báo "xong" (sửa R-Formal/CTĐT ảnh hưởng tuần 5–14). Lỗi build thì dùng ECC build-fix.
6. **Ghi nhớ**: cuối phiên dài chạy ECC save-session; khi phát hiện pattern hay lỗi lặp lại, ghi vào phần "Bài học" bên dưới.

Sửa nhỏ (typo, đổi text, config 1 dòng) được bỏ qua Plan và TDD, nhưng vẫn phải Verify.

## Quy tắc
- Ưu tiên skill/agent ECC (namespace `ecc:`) khi có bản tương đương.
- Không cài thêm thư viện, không đổi kiến trúc hay cấu trúc thư mục khi chưa hỏi.
- Không commit/push khi chưa được yêu cầu; commit message theo Conventional Commits.
- Không hardcode secret; dùng `.env` (và có `.env.example`).
- Trước khi deploy: chạy ECC security-scan.
- **Không bịa nội dung quy chế.** Mọi quy tắc phải có con trỏ nguồn (văn bản, điều, khoản, trang). Chỗ OCR không đọc được thì ghi là khoảng trống, không đoán (ví dụ: bảng quy đổi tiếng Pháp QĐ5339 tr.12).
- **Báo cáo trung thực:** chỉ tiêu chưa đạt thì ghi "chưa đạt" kèm số; checklist Excel chỉ tích ô có bằng chứng.
- Đánh giá: đáp án gán trước khi chạy; tách dev/test; chỉ tinh chỉnh trên dev, test chạy để báo cáo.
- File sinh tự động (`curriculum_cntt_k49.lp/.json`, `corpus.jsonl`) — sửa generator rồi chạy lại, không sửa tay. Ngoại lệ: `r_formal_v1.json` có chỉnh tay sau khi sinh, **không** chạy lại `build_catalog.py`.
- Sửa Excel: sao lưu trước, dùng openpyxl (không `data_only`) để giữ công thức Dashboard.
- Không đưa dữ liệu sinh viên thật vào repo; hồ sơ trong `w7_student_facts/students/` là giả lập.

## Stack khi tích hợp thành ứng dụng (Loi chốt 18/10/2026 — dùng cho demo Tuần 24 và về sau)
Khi đóng gói CPA² thành web app thì dùng đúng các công nghệ này (chưa dùng ở Tuần 1–19):
- Web framework: Next.js · Styling: Tailwind
- Backend + Database: **chỉ Convex** (bỏ Supabase — Loi 18/10/2026) · Auth: Clerk · Payments: Stripe · Emails: Resend
- Hosting giao diện Next.js: chưa chốt (Supabase đã bỏ)
- AI: logic nhẹ — ChatGPT Terra; logic nặng/sáng tạo — ChatGPT Sol; tác vụ rẻ — Gemini Flash
- Thiết kế giao diện: GPT image gen 2 + Claude Design · Công cụ build: Codex desktop app + ChatGPT Voice

Lưu ý khi tích hợp (chưa quyết, hỏi trước khi làm):
- Lõi suy diễn là Python + clingo → cần một dịch vụ Python riêng (API) để Convex (action) / Next.js gọi; Convex chạy JS, không chạy Python. Chọn nơi chạy dịch vụ này trước khi code.
- Convex giữ dữ liệu ứng dụng (người dùng, phiên hỏi đáp, kết quả + chứng chỉ); KB quy chế/CTĐT vẫn là file .lp/.json trong repo, nạp vào dịch vụ Python.
- LLM CHỈ ở tầng Parser/Verbalizer (w13, w12); kết luận TRUE/FALSE/UNKNOWN luôn do solver + chứng chỉ, có hậu kiểm. Không để LLM tự kết luận học vụ.
- API key (OpenAI, Gemini, Clerk, Stripe, Resend, Convex) để trong `.env`, có `.env.example`; không commit secret. Chạy ECC security-scan trước khi deploy.
- Hồ sơ/bảng điểm SV thật là dữ liệu nhạy cảm → không lưu khi chưa có đồng ý; tên model AI ở trên ghi đúng như Loi cung cấp, kiểm lại tên/giá API lúc tích hợp.

## Cấu trúc thư mục
```
D:\LVTN\                          (git repo)
├── CLAUDE.md
├── Ke_hoach_nghien_cuu_CPA2_24_tuan.xlsx   kế hoạch + checklist + dashboard
├── CPA2_KhaoSat\
│   ├── TuanN_*.md                báo cáo từng tuần (1–20)
│   ├── Viec_ton_dong.md          sổ việc tồn đọng (A cần người · B tuần sau · C kỹ thuật · D không hình thức hoá)
│   ├── w4_solver_probe\          so sánh clingo / CP-SAT / Z3
│   ├── w5_rformal\               R-Formal: qd3266/qd5339 *.lp, r_formal_v1.json, source/*_ocr_raw.txt
│   ├── w6_curriculum\            Curriculum KB CNTT K49 (build_curriculum.py → .lp/.json)
│   ├── w7_student_facts\         schema hồ sơ SV + 6 hồ sơ giả lập + loader.py (loader DÙNG CHUNG hồ sơ → ASP)
│   ├── w8_elective\ … w10_graduation\   solver nhóm tự chọn / miễn-thay thế / tốt nghiệp
│   ├── w11_proof\                proof certificate (why/2 → rule_src)
│   ├── w12_integration\          Prototype v1: Parser → KB → Solver ba trị → Verbalizer + hậu kiểm
│   ├── w13_parser\               semantic parser (regex; LLM mới là stub)
│   ├── w14_rag\                  corpus điều/khoản, BM25, grounding, rag_queries.json
│   ├── w15_ocr\                  OCR bảng điểm (Tesseract vie) → hồ sơ có confidence; _rieng/ _anh/ gitignore
│   ├── w16_abstention\           ba trị + missing evidence + từ chối kết luận (abstention.py)
│   ├── w17_adversarial\          bộ đối kháng 80 ca, gold đóng băng (gold_dong_bang.json), oracle, run_adversarial.py
│   ├── w18_eligibility\          đủ điều kiện LVTN/TLTN/niên luận/thực tập/thay thế (eligibility.lp/.py)
│   ├── w19_recommendation\       đề xuất đăng ký 1 HK: ứng viên ba trị + clingo tối ưu (recommendation.py/.lp)
│   ├── w20_benchmark\            G-Truth v1 + OCR-Noise v1 (gold đóng băng 312b7ff), Q-Noise (tổng hợp), Q-Real + Q-Elicit + biểu mẫu (qreal/, _tho/ gitignore), baseline.py, run_cpa2.py
│   └── w21_baseline\            baseline LLM/RAG/tool-calling (llm.py urllib, baselines.py, run_baseline.py), prompt_dong_bang.json; cần khoá trong .env (xem .env.example)
├── services\cpa2_api\            Mốc 1 web: dịch vụ FastAPI bọc lõi CPA² (cpa2_api/, validate_api.py, Dockerfile, README.md = hợp đồng API). Gọi chỉ từ phía máy chủ (Convex)
├── ctu\                          PDF quy chế gốc (gitignore)
├── NiênLuan\                     niên luận cũ, có dữ liệu SV (gitignore)
└── LVTN\                         repo riêng, chưa dùng (gitignore)
```

## Bài học
- Windows: luôn `PYTHONIOENCODING=utf-8`, nếu không thì print tiếng Việt crash (cp1258).
- Tiếng Việt trong file có thể ở dạng Unicode tổ hợp khác chuỗi gõ vào → `str.replace`/assert khớp chuỗi thất bại. Dùng công cụ Edit hoặc khớp theo số dòng/ký tự ASCII.
- `nguong_cc` lưu MỌI điểm chứng chỉ ×10 (IELTS 4.5→45, TOEIC 450→4500), riêng `ctu_abc` giữ bậc 1/2/3. Loader nào đổi chứng chỉ sang ASP cũng phải theo quy ước này (đã từng sai ở w7/w11/w12).
- Miễn ngoại ngữ phải khớp ngôn ngữ chứng chỉ ↔ học phần (QĐ5339 Đ3 k5 điểm a ≠ điểm b) — R-Formal v1.6.
- Test chỉ dùng một loại dữ liệu (chỉ IELTS) thì không kiểm được bảng quy đổi; bộ test phải phủ các biến thể đầu vào.
- OCR QĐ3266: số khoản hay bị hỏng (`5,` · `2 Điểm` · `10.SV` · `+,`), trang 20 trắng (Điều 32 k4 → Điều 35) → nay có bản chép tay từ PDF gốc (`source/QD3266_tr20_chep_tay.txt`, `nguon=chep_tay`); chỗ OCR hỏng khác vẫn dùng trích R-Formal (`nguon=trich_r_formal`). Có PDF gốc thì chép tay trang trắng thay vì để khoảng trống.
- Nguồn của một kết luận lấy từ chứng minh (asp → passage), không lấy từ truy hồi: truy hồi chọn sai văn bản ở bẫy QD-09 (điểm chuyển đổi 4,0–4,9).
- README/báo cáo từng ghi tính năng chưa có trong code (kiểm schema, `--strict`) → khi viết báo cáo, đối chiếu với code và chạy thật.
- KB dùng giả định thế giới đóng: dữ kiện ngoài bị thiếu (vd. `xac_nhan_ky_luat_sach`) cho FALSE, không phải UNKNOWN. Muốn "chưa biết" thì phải mở nhánh (`{ p }.`).
- `tot_nghiep` KHÔNG đơn điệu theo điểm: D đạt vẫn vào ĐTBCTL và kéo GPA xuống, còn F bị loại khỏi ĐTBCTL. Muốn xét "mọi khả năng" của một điểm thì phải gồm F, D và A.
- Bảng điểm thật khác CTĐT: miễn ngoại ngữ in thành dòng CC004 (10 TC, M); GDTC là TC025–027, trong khi KB K49 chỉ có TC100.
- OCR: OCR cả dòng dính số với chữ (`97A`), nên đọc theo dải cột có whitelist. Xoay ảnh dù rất nhỏ cũng làm hỏng chữ, nên chỉ dựng thẳng khi góc ≥ 0,15°.
- Không đưa bảng điểm thật hay kết quả OCR của nó vào repo (`w15_ocr/_rieng/`).
- Mở nhánh dữ kiện ngoài: `{ p } :- not khai_bao(x).` thì `khai_bao(x)` chỉ được suy từ dữ kiện ĐẦU VÀO. Viết `khai_bao(x) :- p.` làm nhánh p tự triệt tiêu → thế giới đóng lại im lặng (P16-1).
- `tot_nghiep`/`du_dk_hoc_vu` định nghĩa ở CẢ R-Formal lẫn `graduation_solver.lp` (hợp lại) → thêm điều kiện ở một nơi không chặn được kết luận (P16-2) Điều kiện thời gian (Đ5) đã thêm vào cả hai `tot_nghiep` (R-Formal v1.7).
- Ba trị theo số thế giới: UNKNOWN là UNKNOWN dù đa số thế giới nghiêng một phía — số answer set không phải xác suất.
- Chạy trên Linux/cloud: w15 cố định font `C:/Windows/Fonts` và Tesseract Windows (đặt `TESSERACT_EXE`); số liệu OCR đổi theo font/phiên bản Tesseract → chỉ so sánh trước/sau trên CÙNG môi trường. Chạy `validate_rag.py` sinh lại `corpus.jsonl` với LF → khôi phục, đừng commit.
- Quy định không có trong QĐ3266/QĐ5339 (vd. học phí ×1,5 sau thời gian thiết kế — Đ10 chỉ ghi "do Hiệu trưởng quyết định") thì chưa hình thức hoá, xin văn bản nguồn trước.
- Bộ đánh giá: gold viết tay + commit TRƯỚC lần chạy đầu (w17: 200b860, `gold_dong_bang.json`, validate G1/G2). Sai sót phát hiện sau → errata, KHÔNG sửa gold; sửa công thức chấm thì báo cả số cũ lẫn mới.
- Oracle kiểm gold phải độc lập với KB: nếu chung giả định (vd. "1 HK = nửa năm") thì ghi rõ là không kiểm được điểm đó.
- QĐ3266 Đ6 k1 (tr.5): một năm học có 03 HK → "giảm 1 HK" (Đ5) = 1/3 năm, không phải nửa năm. R-Formal v1.8 tính trần theo HK: `thoi_gian_toi_da_hk`, so `3·da_hoc_nam2 > 2·M` (P17-3).
- Hồ sơ → ASP CHỈ qua `w7_student_facts/loader.py` (`sang_asp`: rà soát mâu thuẫn P17-1 + chứng chỉ ×10 + CQ-06). Trước đây 3 bản chép lệch nhau (w11/w12 thiếu `che_do`, w7 thiếu rà soát). validate_student_facts L3 chặn module nào tự đổi hồ sơ → ASP.
- Việc còn mở gom ở `CPA2_KhaoSat/Viec_ton_dong.md`; đóng mục nào thì tích ở cả sổ lẫn báo cáo tuần.
- Sửa hệ thống sau khi đã thấy ca test thất bại → test đã nhiễm: giữ số chính thức, ghi số sau sửa ra file riêng (`--hau-to`), cần bộ test mới.
- Điều khoản giao cho đơn vị đào tạo → KHÔNG bịa nội dung: mở nhánh (UNKNOWN) cho tới khi có văn bản hoặc xác nhận. QĐ3266 Đ31 (R-F04): QD-12 (Loi 18/10/2026) xác nhận điều kiện nhận đề tài LVTN/TLTN CHỈ là ngưỡng TC của CTĐT → R-F04 lớp F; `hinh_thuc_cuoi_khoa` chỉ dùng khi có khai báo.
- Quyết định diễn giải ghi ở trường `quyet_dinh` của catalog + `NGUON` trong `gen_quyet_dinh.py`, rồi SINH LẠI phụ lục (không sửa tay `PhuLuc_Quyet_dinh_dien_giai.md`).
- Claim không đối số (vd. `du_dk_tc` thay vì `du_dk_tc("CT550E")`) không bao giờ có trong answer set → ba trị luôn FALSE, im lặng (P18-1). Ý định mới của parser phải có ca kiểm thử đi qua prototype.
- Recommendation: chỉ đề xuất điều hợp lệ trên MỌI thế giới; UNKNOWN → `can_xac_minh`. Thứ tự ưu tiên là CHÍNH SÁCH (ghi rõ), không phải quy chế. Đủ điều kiện ≠ nên làm: chỉ gợi ý xin miễn HP còn cần (P19-1).
- Song hành (R-A04, QĐ3266 Đ7 k5): phải HỌC TRƯỚC hoặc HỌC CÙNG LÚC; "học" ≠ "tích lũy" → đã học dù F vẫn thoả, W không tính. QD-13 (học sau cũng được) đã RÚT sau khi đối chiếu PDF gốc. Xác nhận ngoài văn bản trái câu chữ → đối chiếu lại văn bản gốc trước khi áp dụng, và không bao giờ sửa R-Formal ngược câu chữ.
- Bất biến kiểm lại không dùng `assert` (`python -O` bỏ). Parser: chuẩn hoá NFC, chấp nhận "kì"/"kỳ", số học kỳ ngoài 1–3 → hỏi lại, không mặc định im lặng (P19-3).
- Khoá so khớp của parser phải cùng dạng với câu hỏi đã chuẩn hoá (NFC + lower): khoá stub chứa "CT180" viết HOA không bao giờ khớp → câu đăng ký rơi về `tot_nghiep` suốt từ Tuần 12 (P19-4). Ý định có mã HP phải sinh claim có đối số (`duoc_dang_ky("CT180")`).
- "Đã học" (song hành) chỉ định nghĩa một nơi: `loader.co_hoc` → dữ kiện `da_hoc/1` (KB) và w19 dùng lại; `duoc_dang_ky(C)` = tiên quyết + song hành, `du_dk_dang_ky(C)` chỉ tiên quyết (R-Formal v1.9).
- Bộ đánh giá Tuần 20: gold viết tay → soát độc lập KHÔNG chạy hệ thống → đóng băng (hash + commit) → mới chạy dev. Ca gold dựa nguyên tắc thiết kế (ngoài KB, OCR mâu thuẫn, chính sách) gắn `loai_gold=thiet_ke`, báo cáo tách khỏi gold theo quy chế. Sửa sau khi chạy = errata.
- Công nhận/chuyển đổi (Lý luận chính trị QĐ5339 Đ3 k9, miễn QD-11) KHÔNG tự động: cần đơn + quyết định (Đ2 k6) → `passed` FALSE khi chưa có quyết định; "đủ điều kiện được xét" là claim khác.
- So ngưỡng có biên thập phân (hạng 3,20–3,59 …) phải so hữu tỉ đúng câu chữ; mốc nguyên thang ×10 bỏ sót giá trị giữa hai mốc (P20-1, đã sửa R-Formal v1.10 + QD-14: không làm tròn ĐTBCTL, xếp theo cận dưới). Test ngưỡng phải có giá trị KHÔNG trùng mốc.
- Parser KHÔNG có ý định mặc định: câu không nhận ra → `khong_ro` (UNKNOWN "chưa hỗ trợ"). Mặc định `tot_nghiep` từng trả TRUE cho câu học phí/chuyển ngành (P20-2). Sửa file qua heredoc Python: `\b` trong chuỗi thường thành ký tự backspace — dùng chuỗi raw hoặc công cụ Edit.
- Bộ tổng hợp kế thừa gold (Q-Noise) phải chấm cả Ý ĐỊNH: kết luận từ claim khác mà tình cờ trùng gold vẫn là unsound (chứng chỉ chứng minh câu khác). Danh sách loại trừ/từ khoá của parser phải có cả dạng KHÔNG DẤU — loại trừ chỉ có dấu làm "luan van tot nghiep" thành `tot_nghiep` (P20-5). Nhưng KHÔNG bỏ dấu mọi từ: thế→the, dự→du, nền→nen trùng từ khoá → chỉ bỏ dấu từ trong `TU_KHOA`, viết tắt mơ hồ (đk, tn) mở theo ngữ cảnh, câu hỏi mở (thế nào/ở đâu/là gì) không vào ý định có/không. Mỗi lần nới parser phải có ca ÂM TÍNH (câu phải vẫn bị từ chối).
- Thu câu hỏi thật: KHÔNG cào nhóm/diễn đàn (đạo đức, ToS, NĐ 13/2023) → biểu mẫu có đồng ý đầy đủ (người thu + liên hệ, mục đích, nơi lưu GitHub + dịch vụ AI, hạn xoá bản thô, rút lại bằng mã tự đặt + giới hạn rút). Câu đồng ý phải ĐÚNG sự thật (băm ≠ mã hoá; mã rút không lên repo). Câu tự do hỏi TRƯỚC kịch bản; kịch bản không chứa cụm từ parser dựa vào (chống mớm). Câu elicit báo RIÊNG, không tính vào Q-Real (Loi 19/10/2026: giữ 400 câu tự nhiên).
- Không nới kiểm chéo khi hai tình huống KHÔNG phân biệt được với hệ thống (M2 bảng sạch mất ĐTBCHK ≡ F1 đọc nhầm F→D mất ĐTBCHK) — thay vào đó hỏi đúng dữ kiện còn thiếu (1 số ĐTBCHK in), nhận khai báo để kiểm chéo lại (P20-4). Dữ kiện khai báo dạng số phải kiểm hữu hạn + miền: NaN làm phép so lệch luôn False → "qua" kiểm chéo.
- Dữ kiện ASP chỉ được dùng nếu CÓ nơi sinh ra nó: `tc_diem_f` chỉ có trong test → luật hạ bậc R-F07 không bao giờ chạy (C15). Thêm ý định mới phải kiểm KB đằng sau còn thiếu điều/khoản nào (Đ34 k2 b bị "..." trong trích). Thêm ý định thì kiểm cả kịch bản Q-Elicit đã đóng băng (KB-05 thành mớm lời → v2). Ý định mới của parser: dùng DANH SÁCH CHO PHÉP khớp toàn câu (có chủ ngữ), không dùng danh sách chặn — C12 qua 2 lượt review danh sách chặn vẫn lọt phủ định, câu ngưỡng, câu ghép, người khác. Đừng bỏ dấu toàn câu khi khớp dương (cô→có, hàng→hạng).
- C15 (R-Formal v1.11): hồ sơ chỉ giữ điểm CUỐI → "từng bị F" (Đ34 k2 a) và kỷ luật cảnh cáo cấp Trường (k2 b) là KHAI BÁO (`tc_diem_f`, `ky_luat_canh_cao_cap_truong`); điểm cuối F là cận dưới chắc chắn; chưa khai báo → mở nhánh (graduation_solver mục 0). Chỗ văn bản mơ hồ (HP điều kiện có tính không) → mở nhánh + hỏi (A17), không tự chọn cách hiểu. Gold đóng băng sai vì KB cũ → errata `<bo>_errata.json`, run_cpa2 in thêm dòng [theo errata]. Mở nhánh chỉ trên atom TỰ DO, độc lập với dữ kiện khác: chọn trên atom được suy ra (`{ vuot_5_phan_tram }`) hoặc có điều kiện phụ thuộc điểm làm abstention coi nhầm là biến quyết định; `co_the :- …, not X` + `{ X } :- co_the` là vòng lặp lẻ → nhánh không bao giờ mở.
- Kiểm chéo có ĐỘ CHÙNG (nhận nhiều cách tính: có/không cộng TC miễn, dòng chưa biết điểm) che đúng lỗi có độ lớn bằng khoảng chùng (C14: FALSE/TRUE sai qua 2 lượt review). Khớp nhờ độ chùng KHÔNG được làm bằng chứng tin; kiểm một dòng bằng phép LẬT GIẢ THUYẾT (lật đạt↔F của chính dòng đó, số in phải rơi ra ngoài). Tổng kiểm chéo nào không chứa một loại HP (ĐTBCHK bỏ GDTC — R-B08) thì lỗi đạt↔F của loại đó lọt — tìm tổng khác chứa nó (TC tích lũy). Số in làm tròn 2 chữ số chỉ phát hiện được lệch > dung sai + 0,005: ghi rõ điều kiện độ phân giải.
- Baseline Tuần 21: so sánh phải CÙNG ĐẦU VÀO CÂU HỎI — hệ thống đọc `claim`, baseline đọc `cau_hoi`; 29/78 ca dev có câu hỏi rỗng / ký hiệu ASP / đảo chiều → báo hai dòng `tong` và `[cau_hoi_ro]`, không sửa gold. Chạy API thật: chỉ qua `run_baseline.py --chay-that` (đóng băng hash prompt + dữ liệu + mã nguồn; trần USD; checkpoint; dừng ngay khi 4xx vĩnh viễn; không ghi kết quả khi còn ca LOI; test chỉ một lần). Giá/trần = số hữu hạn > 0 (giá 0/NaN làm trần không bao giờ chạy); khoá chỉ ở header và phải scrub khỏi thông báo lỗi (nhà cung cấp nhắc lại khoá đã che). Sửa R-Formal thì SINH LẠI và commit `w14_rag/corpus.jsonl` (C15 bỏ sót → R-F07b mất nguồn, validate_rag che lỗi vì tự sinh lại). Test mã gọi API dùng máy chủ HTTP cục bộ (`BASELINE_<NHA>_BASE_URL`) và `CPA2_ENV_FILE` trỏ file tạm, không bao giờ để test đọc `.env` thật.
- Web (Mốc 1): dữ liệu NGƯỜI DÙNG đi vào lõi ASP/regex thì phải coi là không tin cậy. `loader.sang_asp` ghép mã học phần, `ma_hp`, mục `khong_tinh_tich_luy`, số khai báo vào chương trình ASP bằng f-string → mã `X"). xac_nhan_ky_luat_sach. %` TIÊM dữ kiện giả (UNKNOWN → TRUE), `#include` đọc file, `b(1..20000)` làm solver nổ. Mọi định danh phải khớp `[A-Za-z0-9_]{1,20}\Z`, số phải là số nguyên thật trong khoảng (5.0, True, NaN, 10**22 bị loại), sai dạng thì BỎ và báo mâu thuẫn; kiểm ở HAI lớp (loader + cổng API). Regex có lượng từ lồng nhau `(?:[…]+|…)*$` bùng nổ tổ hợp trên đầu vào không khớp (câu 53 ký tự treo > 20s): dùng dạng tuyến tính `[…]*(?:từ[…]*)*$`, và test ReDoS phải gồm đuôi KHÔNG khớp (chạy trong tiến trình con có giới hạn thời gian để test fail gọn, không treo). Lõi (clingo, OCR) không tự dừng được → chạy trong tiến trình con giết được ('spawn', không fork từ tiến trình nhiều luồng); hồ sơ có nhiều bản ghi tự mâu thuẫn làm solver ×4,5 mỗi bản ghi → chặn ở cổng vào. API chỉ trả `ok` cho claim thuộc danh sách cho phép: claim KHÔNG đối số (thieu_bat_buoc, thieu_nhom, du_dk_xin_mien) luôn FALSE sai ở CLI (P18-1) — test so với CLI không phát hiện được lỗi mà cả hai cùng mắc, phải có kỳ vọng độc lập. Phản hồi lỗi một hình dạng (trang_thai, ket_luan=null, thong_bao, chi_tiet) kể cả lỗi framework (400/404/405/413/422); xác thực TRƯỚC khi đọc body; không phản hồi lại giá trị / tên trường người dùng; Cache-Control: no-store; log không có nội dung. `.dockerignore` phải ở gốc ngữ cảnh build (bộ dựng cũ không đọc `Dockerfile.dockerignore`). Kiểm cảnh sát bằng đột biến (cố ý bỏ từng lớp bảo vệ, test phải fail).
