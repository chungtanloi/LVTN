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
- **Không bịa nội dung quy chế.** Mọi quy tắc phải có con trỏ nguồn (văn bản, điều, khoản, trang). Chỗ OCR không đọc được thì ghi là khoảng trống, không đoán (ví dụ: tiêu đề Điều 33–34, bảng quy đổi tiếng Pháp QĐ5339 tr.12).
- **Báo cáo trung thực:** chỉ tiêu chưa đạt thì ghi "chưa đạt" kèm số; checklist Excel chỉ tích ô có bằng chứng.
- Đánh giá: đáp án gán trước khi chạy; tách dev/test; chỉ tinh chỉnh trên dev, test chạy để báo cáo.
- File sinh tự động (`curriculum_cntt_k49.lp/.json`, `corpus.jsonl`) — sửa generator rồi chạy lại, không sửa tay. Ngoại lệ: `r_formal_v1.json` có chỉnh tay sau khi sinh, **không** chạy lại `build_catalog.py`.
- Sửa Excel: sao lưu trước, dùng openpyxl (không `data_only`) để giữ công thức Dashboard.
- Không đưa dữ liệu sinh viên thật vào repo; hồ sơ trong `w7_student_facts/students/` là giả lập.

## Cấu trúc thư mục
```
D:\LVTN\                          (git repo)
├── CLAUDE.md
├── Ke_hoach_nghien_cuu_CPA2_24_tuan.xlsx   kế hoạch + checklist + dashboard
├── CPA2_KhaoSat\
│   ├── TuanN_*.md                báo cáo từng tuần (1–14)
│   ├── w4_solver_probe\          so sánh clingo / CP-SAT / Z3
│   ├── w5_rformal\               R-Formal: qd3266/qd5339 *.lp, r_formal_v1.json, source/*_ocr_raw.txt
│   ├── w6_curriculum\            Curriculum KB CNTT K49 (build_curriculum.py → .lp/.json)
│   ├── w7_student_facts\         schema hồ sơ SV + 6 hồ sơ giả lập
│   ├── w8_elective\ … w10_graduation\   solver nhóm tự chọn / miễn-thay thế / tốt nghiệp
│   ├── w11_proof\                proof certificate (why/2 → rule_src)
│   ├── w12_integration\          Prototype v1: Parser → KB → Solver ba trị → Verbalizer + hậu kiểm
│   ├── w13_parser\               semantic parser (regex; LLM mới là stub)
│   └── w14_rag\                  corpus điều/khoản, BM25, grounding, rag_queries.json
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
- OCR QĐ3266: số khoản hay bị hỏng (`5,` · `2 Điểm` · `10.SV` · `+,`), trang 20 trắng (Điều 33–35) → dùng trích R-Formal làm nguồn dự phòng, ghi rõ `nguon=trich_r_formal`.
- Nguồn của một kết luận lấy từ chứng minh (asp → passage), không lấy từ truy hồi: truy hồi chọn sai văn bản ở bẫy QD-09 (điểm chuyển đổi 4,0–4,9).
- README/báo cáo từng ghi tính năng chưa có trong code (kiểm schema, `--strict`) → khi viết báo cáo, đối chiếu với code và chạy thật.
