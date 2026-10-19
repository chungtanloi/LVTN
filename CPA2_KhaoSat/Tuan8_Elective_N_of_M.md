# TUẦN 8 — ELECTIVE & N-of-M SOLVER

**Giai đoạn:** Formalization (Tuần 8/24) · **Mục tiêu:** Cài nhóm "10 chọn 2" và các case tương tự
**Sản phẩm:** Elective Solver
**Tiêu chí hoàn thành:** Pass bộ test N-of-M ✅ — `w8_elective/validate_elective.py` 29/29 đạt

---

## 0. Kết luận trước

> **Không có nhóm "10 chọn 2" ở CNTT K49.** Tuần 2 và prototype Tuần 4 giả định nhóm này, nhưng CTĐT thật (78 dòng, Tuần 6) chỉ có 5 nhóm thuộc **2 kiểu**: *đếm tín chỉ* và *một nhánh*. Kiểu *đếm môn* được giữ lại bằng nhóm demo `DEMO1-4` để không gãy tương thích với R-Formal v1.4 và để CTĐT khác (ví dụ ngành khác/khoá khác) vẫn chạy được. Elective Solver xử lý cả 3 kiểu, giữ nguyên hai ràng buộc cứng của `curriculum_schema.lp`: *một HP không thuộc hai nhóm* và *tín chỉ không cộng dồn qua nhánh*.

---

## 1. Phạm vi Tuần 8 — từ kế hoạch tới CTĐT thật

| Kế hoạch Excel (Tuần 8) | CTĐT K49 thực tế (Tuần 6) | Xử lý |
|---|---|---|
| "Nhóm 10 chọn 2" (N môn) | **Không tồn tại** | Tạo nhóm demo `g_demo` (DEMO1-4, 2-môn) để test kiểu `dem_mon` |
| (ngầm) đếm tín chỉ | **GDTC 3, Xã hội 2, Tốt nghiệp 15** | `tin_chi`: Σ TC ≥ N |
| (ngầm) một nhánh | **Ngoại ngữ 10 AV/PV, Chuyên ngành 6 CN1/2/3** | `mot_nhanh`: ∃ nhánh Σ TC ≥ N, không cộng dồn |

Ba ca biên bắt buộc của Taxonomy Tuần 2, T3:

1. **Chồng nhóm** — một môn thuộc hai nhóm: có được tính hai lần không? → **Không**, đã có `:- thuoc_nhom_bat_ky(G1,C), thuoc_nhom_bat_ky(G2,C), G1 != G2.` (schema dòng 105). Test demo dùng `DEMO1-4` riêng để không vi phạm.
2. **Đếm môn vs đếm tín chỉ** — "chọn 2 môn" khác "tích luỹ 6 TC" khi các môn khác tín chỉ → giữ cả hai kiểu, test A vs C.
3. **Dư thừa** — SV đạt 4/10 môn: 2 môn tính vào nhóm, 2 môn dư đi đâu? → **vào tổng tín chỉ tự do** (vẫn `tich_luy`), chỉ `canh_bao_du_nhom` ghi nhận.

---

## 2. Thiết kế Elective Solver

`w8_elective/elective_solver.lp` mở rộng `curriculum_schema.lp` (không sửa schema):

```prolog
%% 1. Kiểu đếm môn (giữ tương thích)
mon_nhom_dat(G,X) :- nhom_kieu(G,dem_mon), X = #count{ C : thuoc_nhom(G,C), tich_luy(C) }.
dat_nhom(G) :- nhom_kieu(G,dem_mon), nhom_min_mon(G,N), mon_nhom_dat(G,X), X >= N.
thieu_nhom(G,D) :- nhom_kieu(G,dem_mon), nhom_min_mon(G,N), mon_nhom_dat(G,X), X < N, D=N-X.

%% 2. Helper tư vấn
hp_thieu_trong_nhom(G,C) :- thuoc_nhom(G,C), not tich_luy(C).
nhanh_thieu(G,B,D) :- nhanh(G,B), nhom_min_tc(G,N), tc_nhanh_dat(G,B,X), D=N-X.
nhom_trang_thai(G,du) :- dat_nhom(G).
nhom_du_tc(G,X) :- nhom_kieu(G,tin_chi), dat_nhom(G), tc_nhom_dat(G,X), X > N.  % dư thừa
```

Mọi `dat_nhom/thieu_nhom` đều có `why(..., r_a02)` về **QĐ3266 Điều 7 k.3** (học phần tự chọn).

---

## 3. Bộ test N-of-M — 29 ca

Chạy: `python w8_elective/validate_elective.py` (chỉ cần `clingo`)

### A. Đếm tín chỉ — 10 ca

| Ca | Nhóm | Tình huống | Kết luận |
|---|---|---|---|
| A1 | GDTC | rỗng | thiếu 3 |
| A2 | GDTC | TC100 3 | đủ |
| A3 | Xã hội | rỗng | thiếu 2 |
| A4 | Xã hội | ML007 2 | đủ |
| A5 | Xã hội | ML007+XH028 4 | đủ + dư (ca biên 3) |
| A6 | Tốt nghiệp | rỗng | thiếu 15 |
| A7 | Tốt nghiệp | CT550E 15 | đủ |
| A8 | Tốt nghiệp | CT501E 6 + 3 HP | đủ |
| A9 | Tốt nghiệp | 5 HP lẻ 15 | đủ (QĐ31 k.3) |
| A10 | Tốt nghiệp | CT478 3 | thiếu 12 |

### B. Một nhánh — 10 ca

| Ca | Nhóm | Tình huống | Kết luận |
|---|---|---|---|
| B1 | Ngoại ngữ | AV 4+3+3=10 | đủ AV |
| B2 | Ngoại ngữ | PV 4+3+3=10 | đủ PV |
| B3 | Ngoại ngữ | AV 4 + PV 7 | **thiếu 3** — không cộng dồn (I5, CQ-02) |
| B4 | Ngoại ngữ | AV 4 | thiếu 6 |
| B5 | Ngoại ngữ | AV 7 | thiếu 3 |
| B6 | Chuyên ngành | CT211+CT297 | đủ CN1 |
| B7 | Chuyên ngành | CT449+CT484 | đủ CN2 |
| B8 | Chuyên ngành | CT522+CT279 | đủ CN3 |
| B9 | Chuyên ngành | CT211+CT449 chéo | **thiếu 3** (I9) |
| B10 | Chuyên ngành | CT211 3 | thiếu 3 |

### C. Đếm môn (demo) — 5 ca

| Ca | Tình huống | Kết luận |
|---|---|---|
| C1 | 0 môn | thiếu 2 |
| C2 | DEMO1 | thiếu 1 |
| C3 | DEMO1+2 | đủ |
| C4 | DEMO1+2+3 | đủ + dư 3 |
| C5 | DEMO1(F)+DEMO2 | thiếu 1 — điểm F không tính |

### D. Tích hợp w7 — 4 ca

| Ca | Hồ sơ | Kết luận |
|---|---|---|
| D1 | sv_lvtn đủ mọi nhóm | `dat_nhom` cả 5 nhóm |
| D2 | sv_lvtn | `tot_nghiep` |
| D3 | sv_tron_ngoai_ngu (AV 4+PV 7) | thiếu ngoại ngữ 3, không tốt nghiệp |
| D4 | sv_tron_ngoai_ngu | `hp_thieu_trong_nhom` gợi ý HP thiếu |

---

## 4. Kết quả chạy

```
A. NHÓM ĐẾM TÍN CHỈ — 10/10 đạt
B. NHÓM MỘT NHÁNH — 10/10 đạt
C. NHÓM ĐẾM MÔN — 5/5 đạt
D. TÍCH HỢP — 4/4 đạt
KẾT LUẬN: ĐẠT — Elective Solver pass toàn bộ N-of-M
```

`validate_curriculum.py` cũ (Tuần 6) vẫn 31/31 và `validate_student_facts.py` (Tuần 7) vẫn 5/5 — không hồi quy.

---

## 5. Việc còn lại → Tuần 9

- [x] **Exemption & Substitution (T5/T6):** phân biệt `passed / exempted_M / recognized / substituted` trên nhóm (ví dụ miễn AV bằng IELTS có tính cho `g_ngoai_ngu` không? → có, 10 TC, nhưng điểm M không vào ĐTBCTL) — ✅ đã xong: w9_exemption (Tuần 9)
- [x] Tích hợp `du_dk_xin_mien` → `duoc_mien` (QD-11) với nhóm ngoại ngữ — ✅ đã xong: w9_exemption (Tuần 9)
- [x] Chênh lệch tín chỉ khi thay thế (QD-10, QĐ5339 Đ3 k.3) — học phần thay thế có TC khác — ✅ đã xong: w9 validate_exemption A6, C6

---

### Ghi chú kiểm chứng

- [x] 3 kiểu nhóm (tin_chi / mot_nhanh / dem_mon) đều có test
- [x] 3 ca biên T3 của Tuần 2 đều có test (B3/B9 demo chồng nhóm, A vs C, A5 dư)
- [x] 5 nhóm thật của K49 đều có test, kèm nhóm demo cho kiểu vắng mặt
- [x] Tích hợp với 5 hồ sơ Tuần 7, không làm gãy `validate_curriculum` / `validate_student_facts`
- [ ] Chưa test trên **bảng điểm thật** (chờ Tuần 7 mở rộng lên 20 hồ sơ)
