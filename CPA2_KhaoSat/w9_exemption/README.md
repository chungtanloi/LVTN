# Tuần 9 — Exemption & Substitution Solver (CPA2)

**Sản phẩm:** Exemption/Substitution Solver — phân biệt `passed / exempted_M / recognized / substituted`
**Tiêu chí hoàn thành:** Pass bộ test 4 trạng thái ✅ — `validate_exemption.py` 22/22 đạt

## Kết luận trước

> **Miễn không tự động (QD-11) và hai loại miễn khác kế toán (QD-01 sửa) là hai bẫy mà mọi baseline sẽ mắc.** `du_dk_xin_mien` (có IELTS 5.0 → đủ ĐK) **không** suy ra `passed`; chỉ `duoc_mien` (có QĐ phê duyệt) mới sinh `exempted_M` (điểm M, không vào ĐTBCTL) hoặc `recognized` (có vào ĐTBCTL). Thay thế T6 ở K49 chủ yếu là **đổi mã** (CT172↔CT172E) và **bảng LLCT** (ML009→ML014...), còn LVTN ↔ HP thay thế đã được xử thành nhóm T3 `g_tot_nghiep` 15 TC ở Tuần 6 (không phải T6).

## Chạy

```bash
pip install clingo
python validate_exemption.py          # 22/22
```

## File

| File | Vai trò |
|---|---|
| `exemption_substitution_solver.lp` | Tích hợp T5/T6: `exempted_m` vs `recognized`, `substituted`, `hp_dat_nho_mien`, `trang_thai_hp/2`, `chenh_lech_tc/3` |
| `validate_exemption.py` | 22 ca: A 10 ca T5 · B 3 ca nhóm · C 7 ca T6 · D 2 ca tích hợp tốt nghiệp |
| `Tuan9_Exemption_Substitution.md` | Báo cáo đầy đủ |

## Liên kết

- **R-Formal v1.5:** `qd5339_r_formal_v1.lp` (R-M05/M06/M15/M16, QD-11) — mọi `why/2` đã có
- **Tuần 8:** nhóm N-of-M — miễn được tính vào `tich_luy` nên `dat_nhom` tự động đúng
- **Tuần 7:** `certificates[]` + `exemptions[]` → `chung_chi/2`, `duoc_mien/1`
