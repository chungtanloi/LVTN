# Tuần 8 — Elective & N-of-M Solver (CPA2)

**Sản phẩm:** Elective Solver — cài đặt đầy đủ 3 kiểu nhóm T3 của Taxonomy Tuần 2
**Tiêu chí hoàn thành:** Pass bộ test N-of-M ✅ — `validate_elective.py` 29/29 ca đạt

## Kết luận trước

> **Tuần 8 đóng được "nhóm 10 chọn 2" theo nghĩa đúng:** K49 **không có** nhóm đếm môn nào (phát hiện Tuần 6), nên nhóm này được kiểm bằng nhóm demo `DEMO1-4` để giữ tương thích R-Formal v1.4. Trên CTĐT thật, 5 nhóm thuộc 2 kiểu: **đếm tín chỉ** (GDTC 3, Xã hội 2, Tốt nghiệp 15) và **một nhánh** (Ngoại ngữ 10 AV/PV, Chuyên ngành 6 CN1/2/3). Elective Solver xử lý cả 3 kiểu, giữ ràng buộc *không trùng nhóm* và *không cộng dồn qua nhánh*.

## Chạy

```bash
pip install clingo
python validate_elective.py          # 29/29 ca
```

## File

| File | Vai trò |
|---|---|
| `elective_solver.lp` | Mở rộng `curriculum_schema.lp`: kiểu `dem_mon` + helper `hp_thieu_trong_nhom/2`, `nhanh_thieu/3`, `nhom_trang_thai/2`, `canh_bao_du_nhom/2` |
| `validate_elective.py` | Bộ test 4 nhóm A-D: 10 ca `tin_chi` · 10 ca `mot_nhanh` · 5 ca `dem_mon` (demo) · 4 ca tích hợp w7 |
| `Tuan8_Elective_N_of_M.md` | Báo cáo đầy đủ (nguồn, số liệu, 3 ca biên T3) |

## Liên kết

- **Taxonomy Tuần 2, T3:** 3 kiểu nhóm + 3 ca biên (chồng nhóm, đếm môn vs tín chỉ, dư thừa) — nay đều có test
- **Curriculum KB v1 (Tuần 6):** 5 nhóm thật, 2 kiểu — Elective Solver không sửa schema, chỉ thêm lớp `dem_mon`
- **Student Facts Tuần 7:** 5 hồ sơ giả lập — D1-D4 kiểm tra tích hợp `sv_lvtn` vs `sv_tron_ngoai_ngu`
- **R-Formal v1.5:** `why(dat_nhom/1, r_a02)` — mọi kết luận nhóm đều truy về QĐ3266 Đ.7 k.3

## Việc còn lại → Tuần 9

- Exemption & Substitution (T5/T6): phân biệt `passed/exempted_M/recognized/substituted` trên cùng nhóm
- Tích hợp chứng chỉ IELTS → `du_dk_xin_mien` → `duoc_mien` đã có ở Tuần 7, cần test qua nhóm ngoại ngữ
