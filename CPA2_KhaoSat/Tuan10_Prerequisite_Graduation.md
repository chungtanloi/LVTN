# TUẦN 10 — PREREQUISITE & GRADUATION SOLVER v1

**Giai đoạn:** Formalization (Tuần 10/24) · **Mục tiêu:** Cài prerequisite, tín chỉ, điều kiện tốt nghiệp
**Sản phẩm:** Graduation Solver v1
**Tiêu chí hoàn thành:** Pass case chuẩn ✅ — `w10_graduation/validate_graduation.py` 19/19 đạt

---

## 0. Kết luận trước

> **Tốt nghiệp là bài toán hợp, không phải tra cứu.** 7 điều kiện `dk_tin_chi, dk_bat_buoc, dk_tu_chon, dk_hp_dieu_kien, dk_dtbctl, dk_gdqp, dk_ky_luat, dk_thoi_gian` phải đồng thời đúng, trong đó `dk_ky_luat` (R-F03) luôn cần `xac_nhan_ky_luat_sach` ngoài bảng điểm — nên mọi câu *"em đủ điều kiện tốt nghiệp chưa?"* thiếu dữ kiện này đều trả `FALSE` ở mức `tot_nghiep`, kèm `thieu_dk(ky_luat)`. Đây là hành vi trung thực mà baseline không có: hệ thống không nói *"đủ"* khi chưa thấy xác nhận kỷ luật, mà nói *"thiếu xác nhận kỷ luật"*.

---

## 1. Ba biến thể tiên quyết T4 — đã có ở R-Formal, nay test qua SV thật

| Biến thể | Nguồn | Ví dụ K49 | Vị từ |
|---|---|---|---|
| **T4a tiên quyết** | QĐ3266 Đ7 k.4, CTĐT cột tiên quyết | CT177 ← CT101, CT271E ← CT174+CT176 | `tien_quyet/2`, `du_dk_dang_ky/1` |
| **T4b ngưỡng TC** | CTĐT `≥80/120/125` (Tuần 6) | CT550E ≥120, CT466E ≥80, CT518E ≥125 | `tien_quyet_tc/2`, `thieu_tc/2`, `du_dk_tc/1` |
| **T4c song hành** | QĐ3266 Đ7 k.5, CTĐT cột song hành | XH024 ← XH023, CT182 song hành CT180 | `song_hanh/2`, `vi_pham_song_hanh/2` |

Chuỗi dài nhất: 5 HP `ML014→ML016→ML018→ML019→ML021` (lý luận chính trị) và 4 HP CNTT `CT101→CT177→CT174→CT271E`.

---

## 2. Thiết kế Graduation Solver v1

`w10_graduation/graduation_solver.lp` là file duy nhất định nghĩa `tot_nghiep/0`:

```prolog
dk_tin_chi      :- tc_tich_luy(T), tc_toi_thieu_ctdt(Min), T >= Min.          % 161
dk_bat_buoc     :- not thieu_bat_buoc(_).                                      % T1
dk_tu_chon      :- not thieu_nhom(G,_) : nhom(G), not nhom_dieu_kien(G).      % T2/T3
has_thieu_dk_nhom :- thieu_nhom(G,_), nhom_dieu_kien(G).
has_thieu_bb_dk   :- thieu_bat_buoc(C), bat_buoc(C), hp_dieu_kien(C).
dk_hp_dieu_kien :- not has_thieu_dk_nhom, not has_thieu_bb_dk.                % T7-điều kiện
dk_dtbctl       :- dtbctl_ge(20).                                              % ≥2.00
dk_gdqp         :- not khong_dat_gdqp(_).                                      % ≥5.0 thang10
dk_ky_luat      :- xac_nhan_ky_luat_sach.                                      % ngoài phạm vi
dk_thoi_gian    :- not qua_thoi_gian_toi_da.                                   % 9 năm

du_dk_hoc_vu :- dk_tin_chi, dk_bat_buoc, dk_tu_chon, dk_hp_dieu_kien, dk_dtbctl, dk_gdqp, dk_thoi_gian.
tot_nghiep   :- du_dk_hoc_vu, dk_ky_luat.
thieu_dk(tu_chon) :- not dk_tu_chon.  % ... 8 nhánh để Verbalizer diễn đạt
```

Mọi `dk_*/thieu_dk` mang `why(..., r_f01a/r_a01/r_f02a/r_e01/r_f03)` về đúng điều khoản QĐ3266.

---

## 3. Bộ test — 19 ca

### A. T4 prerequisite — 7 ca

| Ca | Tình huống | Kết luận |
|---|---|---|
| A1 | CT177 có CT101 | `du_dk_dang_ky(CT177)` |
| A2 | CT177 thiếu CT101 | không `du_dk_dang_ky` |
| A3 | CT550E đủ 120 TC | `du_dk_tc(CT550E)` |
| A4 | 30 TC → thiếu 90 cho CT550E | `thieu_tc(CT550E,90)` |
| A5 | 80 TC → đủ CT466E | `du_dk_tc(CT466E)` |
| A6 | CT182 có CT176 (song hành CT180) | `du_dk_dang_ky(CT182)` |
| A7 | XH024 trước XH023 | `vi_pham_song_hanh` |

### B. Graduation case chuẩn — 7 ca

| Ca | Tình huống | Kết luận |
|---|---|---|
| B1 | Đủ 161 LVTN + 7 điều kiện | `tot_nghiep` + 7 `dk_*` |
| B2 | Thiếu nhóm tốt nghiệp | `thieu_dk(tin_chi)` |
| B3 | Trộn AV+PV | `thieu_dk(hp_dieu_kien)` (không cộng dồn) |
| B4 | Dư CT478 D → ĐTBCTL 1.97 | `thieu_dk(dtbctl)` |
| B5 | GDQP D → `<D+` | `khong_dat_gdqp` → không `dk_gdqp` |
| B6 | Thiếu `xac_nhan_ky_luat_sach` | `tot_nghiep` FALSE (phải có) |
| B7 | Quá hạn 10 năm | `thieu_dk(thoi_gian)` |

### C. Tích hợp miễn/thay thế — 2 ca

| Ca | Tình huống | Kết luận |
|---|---|---|
| C1 | Miễn AV bằng IELTS (exempted_M) | vẫn `tot_nghiep` |
| C2 | ML009→ML014 | `passed(ML014)` |

---

## 4. Kết quả

```
A. T4 — 7/7 đạt
B. Graduation — 7/7 đạt (+7 dk_* kiểm chi tiết ở B1)
C. Tích hợp — 2/2 đạt
KẾT LUẬN: ĐẠT — Graduation Solver v1 pass case chuẩn
```

Không hồi quy: `w5` 39/39 · `w6` 31/31 · `w7` 5/5 · `w8` 29/29 · `w9` 22/22.

---

## 5. Việc còn lại → Tuần 11

- [ ] **Proof Certificate (Tuần 11):** Claim → Proof → Rule → Fact → Source — `why/2` đã có, cần dựng `certificate` kiểm được bằng máy
- [ ] Chuẩn đầu ra ngoại ngữ/CNTT (R-F01b, N) — vẫn `UNKNOWN`
- [ ] So sánh `dtbctl` với `dtbchk` ở ca sát ngưỡng 2.00 (bẫy nhân 10)

---

### Ghi chú kiểm chứng

- [x] 3 biến thể T4 đều có test
- [x] 7 điều kiện tốt nghiệp có test thành phần + hợp
- [x] Tích hợp miễn/thay thế (T5/T6) vào tốt nghiệp
- [ ] Chưa test trên **bảng điểm thật** (chờ OCR Tuần 15)
