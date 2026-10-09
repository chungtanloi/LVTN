# TUẦN 9 — EXEMPTION & SUBSTITUTION SOLVER

**Giai đoạn:** Formalization (Tuần 9/24) · **Mục tiêu:** Mô hình miễn bằng chứng chỉ và học phần thay thế
**Sản phẩm:** Exemption/Substitution Solver
**Tiêu chí hoàn thành:** Phân biệt `passed / exempted_M / recognized / substituted` ✅ — `w9_exemption/validate_exemption.py` 22/22 đạt

---

## 0. Kết luận trước

> Tuần 9 đóng được **hai bẫy tri thức mạnh nhất cho H2** (baseline tự tin sai). Bẫy 1: *có IELTS 5.0 → đã được miễn AV* là **sai** — QĐ5339 Điều 2 k.6 (QD-11) yêu cầu đơn + Tổ Xét miễn + Hội đồng Trường, nên `du_dk_xin_mien` **không** suy ra `passed`. Bẫy 2: *mọi HP miễn đều không vào ĐTBCTL* là **sai** — QĐ5339 Điều 3 k.11 (QD-01 sửa) tách `exempted_M` (điểm M, không vào) khỏi `recognized` (có vào). Cả hai đều có test đối kháng (A1 vs A2, A4 vs A5) mà baseline LLM/RAG gần như chắc chắn mắc vì đó là câu trả lời "hữu ích" nhất về mặt ngôn ngữ.

Về T6: **LVTN không phải học phần thay thế ở K49** — CT550E/TLTN nằm chung nhóm `g_tot_nghiep` 15 TC (phát hiện Tuần 6). T6 còn lại ở K49 là **đổi mã** (CT172↔CT172E) và **bảng LLCT** (ML009→ML014...), cộng ca chênh lệch tín chỉ QD-10.

---

## 1. Phạm vi Tuần 9

| Loại | Nguồn | Trạng thái trong KB | Kế toán |
|---|---|---|---|
| **T5 exempted_M** | QĐ5339 Đ3 k.4, k.5a, k.6-8 + QĐ3266 Đ22 k.5a | `exempted_m(C)` — HP điều kiện miễn bằng chứng chỉ, điểm M | vào TC tích lũy, **KHÔNG** vào ĐTBCTL (`khong_tinh_tb`) |
| **T5 recognized** | QĐ5339 Đ3 k.11 (R-M15) | `recognized(C)` — công nhận điểm từ CTĐT đã học | vào TC **VÀ** vào ĐTBCTL (`vao_dtbctl`) |
| **T6 substitution** | QĐ5339 Đ3 k.9 (R-M13) + Đ20 k.6 (R-H02) | `substituted(C)` — `substitutes(A,B)` + `passed(A)` | TC theo HP được miễn (B), điểm theo trọng số HP đã học (QD-10, R-M04) |
| **Đổi mã** | Taxonomy Tuần 2, T1 ca biên | `substitutes(CT172,CT172E)` hai chiều | alias |

Trục C Tuần 2 nay là 7 trạng thái: `passed, failed, exempted_M, recognized, substituted, in_progress, unknown` + `du_dk_xin_mien` (trạng thái hồ sơ, không phải trạng thái HP — chốt Tuần 7).

---

## 2. Thiết kế Solver

`w9_exemption/exemption_substitution_solver.lp` tích hợp với `curriculum_schema.lp` + `elective_solver.lp`:

```prolog
%% T5: đã có ở qd5339, chỉ alias + helper
hp_dat_nho_mien(C)     :- exempted_m(C).
hp_dat_nho_cong_nhan(C):- recognized(C).
nhom_dat_nho_mien(G)   :- dat_nhom(G), #count{ C: exempted_m(C)}>=1.
%% Tích lũy: tich_luy(C) :- passed(C) (qd3266) nên miễn tự động tính vào nhóm

%% T6: thay thế
substituted(B) :- substitutes(A,B), passed(A).
passed(B)      :- substituted(B).
%% ML qua mien_tu cũng coi như thay thế
substituted(B) :- mien_tu(B,A), passed(A).
passed(B)      :- mien_tu(B,A), passed(A).

%% Đổi mã hai chiều (T1 ca biên)
substitutes("CT172","CT172E"). substitutes("CT172E","CT172").
%% LVTN ở K49: không phải T6, là nhóm g_tot_nghiep (Tuần 6)
hinh_thuc_tot_nghiep(luan_van) :- tich_luy("CT550E").

%% Trạng thái HP — phân biệt passed thật vs substituted
trang_thai_hp(C, passed)     :- passed(C), g10(C,_), not exempted_m(C).
trang_thai_hp(C, exempted_M) :- exempted_m(C).
trang_thai_hp(C, recognized) :- recognized(C).
trang_thai_hp(C, substituted):- substituted(C), not g10(C,_).

%% Chênh lệch TC (QD-10)
chenh_lech_tc(A,B,DA) :- substitutes(A,B), course(A,CA), course(B,CB), DA=CB-CA.
chenh_lech_tc(A,B,DA) :- ml_thay(A,B), course(A,CA), course(B,CB), DA=CB-CA.
```

Mọi kết luận mang `why(..., r_m05/r_m15/r_m13/r_m04)` về đúng điều khoản QĐ5339.

---

## 3. Bộ test — 22 ca

### A. T5 miễn bằng chứng chỉ — 10 ca

| Ca | Tình huống | Kỳ vọng | Nguồn |
|---|---|---|---|
| A1 | IELTS 5.0 K49 → đủ ĐK AV | `du_dk_xin_mien` + `mien_treo`, **không** `passed` | QD-11 (R-M16) |
| A2 | + `duoc_mien` | `exempted_M`, `passed`, `diem_m` | R-M05 |
| A3 | IELTS 4.0 | không đủ bậc 3 | R-M06 |
| A4 | `recognized(C1)` từ S1 (B=3.0) | `recognized`, `vao_dtbctl`, `tl_mau(3)` | R-M15 (QD-01 sửa) |
| A5 | `exempted_M` không vào ĐTBCTL | `khong_tinh_tb` | R-M05 vs R-M15 |
| A5b | tl_mau loại M | `tl_mau(3)` không phải 6 |  |
| A6 | Gộp 2→1: 4*2+3*3/5=3.4 | `g4(C2,34)` | QD-10 (R-M04) |

### B. Miễn tính cho nhóm N-of-M — 3 ca

| Ca | Tình huống | Kết luận |
|---|---|---|
| B1 | Miễn XH023+XH024+XH025 (10 TC AV) | `dat_nhom(g_ngoai_ngu)` |
| B2 | Chỉ XH023 4 TC | `thieu_nhom(g_ngoai_ngu,6)` |
| B3 | Chỉ có chứng chỉ, chưa `duoc_mien` | `dat_nhom` **không** đạt (QD-11) |

### C. T6 thay thế — 7 ca

| Ca | Tình huống | Kết luận |
|---|---|---|
| C1 | CT172 → CT172E | `substituted` + `passed` |
| C2 | CT172E → CT172 | ngược lại |
| C3 | CT271E → CT201E | `substituted` |
| C4 | ML009 → ML014 | `passed` (bảng LLCT) |
| C5 | ML010 → ML016+ML018 | cả hai `passed` (một→nhiều) |
| C6 | Chênh lệch TC ML009 2→3 | `chenh_lech_tc(...,1)` |
| C7 | Phân biệt `trang_thai_hp` | `exempted_M` vs `passed` vs `substituted` |

### D. Tích hợp tốt nghiệp — 2 ca

| Ca | Tình huống | Kết luận |
|---|---|---|
| D1 | Miễn AV bằng IELTS + đủ 161 TC | `tot_nghiep` + `exempted_M` + `dk_hp_dieu_kien` |
| D2 | `recognized` vào nhóm tốt nghiệp | `recognized(CT478)` |

---

## 4. Kết quả

```
A. T5 — 10/10 đạt
B. Nhóm — 3/3 đạt
C. T6 — 7/7 đạt
D. Tích hợp — 2/2 đạt
KẾT LUẬN: ĐẠT — phân biệt đúng 4 trạng thái
```

`validate_rformal.py` vẫn 39/39, `validate_curriculum.py` 31/31, `validate_elective.py` 29/29 — không hồi quy.

---

## 5. Việc còn lại → Tuần 10

- [ ] **Prerequisite & Graduation (T4/T7):** ngưỡng tín chỉ T4b (≥80/120/125 TC) + đồ thị tiên quyết đã có, cần test `du_dk_dang_ky` qua `passed/substituted/exempted_M`
- [ ] Chuẩn đầu ra ngoại ngữ/CNTT (R-F01b, N) — vẫn `UNKNOWN`
- [ ] Thời gian học tập tối đa (R-E01, 9 năm) + `tc_cong_nhan` giảm trần

---

### Ghi chú kiểm chứng

- [x] 4 trạng thái `passed / exempted_M / recognized / substituted` phân biệt bằng `trang_thai_hp/2`
- [x] QD-11 (mien_treo) và QD-01 sửa có test đối kháng A1/A2 và A4/A5
- [x] Miễn tính vào nhóm N-of-M (B1-B3) và vào tốt nghiệp (D1)
- [x] Thay thế đổi mã, LLCT, một→nhiều, chênh lệch TC có test
- [ ] Chưa test trên **bảng điểm thật** (cần OCR Tuần 15)
