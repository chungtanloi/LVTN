# Curriculum KB v1 — CTĐT CNTT K49 (CPA², Tuần 6)

Báo cáo đầy đủ: `../Tuan6_Curriculum_KB_v1.md`.

```bash
pip install -r requirements.txt
python3 build_curriculum.py        # sinh curriculum_cntt_k49.{json,lp}; dừng nếu bản chép sai
python3 validate_curriculum.py     # 31/31 — mã thoát 0 đạt · 1 lỗi · 2 thiếu ortools
python3 doi_chieu_nguon.py         # đối chiếu với PDF (cần poppler-utils + tesseract)
```

| File | Vai trò |
|---|---|
| `build_curriculum.py` | **Nguồn duy nhất** — 78 dòng + 5 nhóm tự chọn, chép từ PDF; kiểm tra nội tại trước khi sinh |
| `curriculum_cntt_k49.json` / `.lp` | Sản phẩm sinh — không sửa tay |
| `curriculum_schema.lp` | Ngữ nghĩa nhóm (đếm tín chỉ / một nhánh), nhóm điều kiện, ràng buộc nội tại — độc lập ngành/khoá |
| `kiem_tra_cau_truc.lp` | Chế độ kế hoạch: tìm tập học phần nhỏ nhất thoả CTĐT |
| `validate_curriculum.py` | S (cấu trúc) · P (clingo ↔ CP-SAT ↔ Python) · I (tích hợp R-Formal, ba trị) · G (mô tả đồ thị) |
| `doi_chieu_nguon.py` | Trang 3: so với lớp văn bản · Trang 4: so với OCR, dòng lệch phải soát tay |
| `curriculum_report.txt`, `doi_chieu_report.txt` | Kết quả chạy thật |

Nạp cùng quy tắc quy chế: `../w5_rformal/qd3266_r_formal_v1.lp` (v1.5) + `qd5339_r_formal_v1.lp`
+ `curriculum_schema.lp` + `curriculum_cntt_k49.lp`.

**Thêm một CTĐT khác:** sao `build_curriculum.py` thành `build_<nganh>_<khoa>.py`, thay `META`, `NHOM`,
`ROWS`; schema giữ nguyên.
