# Tuần 10 — Prerequisite & Graduation Solver v1 (CPA2)

**Sản phẩm:** Graduation Solver v1 — tổng hợp T1–T7 + T4a/b/c
**Tiêu chí hoàn thành:** Pass case chuẩn ✅ — `validate_graduation.py` 19/19 đạt

## Kết luận trước

> **Tốt nghiệp là hợp của 7 điều kiện, không phải một ngưỡng.** `tot_nghiep` chỉ khi `du_dk_hoc_vu` (6 điều kiện học vụ) **và** `dk_ky_luat` (xác nhận ngoài). Trong 1 case `THIẾU xac_nhan_ky_luat_sach` hệ thống trả `FALSE` (không phải `UNKNOWN`) — đúng thiết kế `cond_discipline` của Tuần 2: thiếu dữ kiện kỷ luật → không tốt nghiệp, phải nói *"thiếu xác nhận kỷ luật"* chứ không im lặng.

## Chạy

```bash
pip install clingo
python validate_graduation.py          # 19/19
```

## File

| File | Vai trò |
|---|---|
| `graduation_solver.lp` | `dk_tin_chi / dk_bat_buoc / dk_tu_chon / dk_hp_dieu_kien / dk_dtbctl / dk_gdqp / dk_ky_luat / dk_thoi_gian` → `du_dk_hoc_vu` → `tot_nghiep`, `thieu_dk/1`, `hp_chua_du_dk/1` |
| `validate_graduation.py` | 7 ca T4a/b/c · 7 ca tốt nghiệp chuẩn · 2 ca tích hợp miễn/thay thế |
| `Tuan10_Prerequisite_Graduation.md` | Báo cáo đầy đủ |

## Liên kết

- **T4:** 20 cạnh tiên quyết (T4a), 11 song hành (T4c), 4 ngưỡng TC (T4b ≥80/120/125) — `du_dk_dang_ky`, `thieu_tc`, `vi_pham_song_hanh`
- **T7:** 7 điều kiện → `thieu_dk/1` để Verbalizer diễn đạt
- **W5-W9:** R-Formal + Curriculum + Elective + Exemption — không hồi quy
