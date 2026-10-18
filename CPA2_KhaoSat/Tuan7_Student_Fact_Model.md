# TUẦN 7 — STUDENT FACT MODEL

**Giai đoạn:** Formalization (Tuần 7/24) · **Mục tiêu:** Schema điểm, tín chỉ, GPA, chứng chỉ, miễn
**Sản phẩm:** Student Fact Model (`w7_student_facts/`)
**Tiêu chí hoàn thành:** Có ≥5 hồ sơ giả lập ✅ — `w7_student_facts/validate_student_facts.py` đạt 6/6 hồ sơ + kiểm loader

> Báo cáo này viết bù ngày 09/10/2026. Code Tuần 7 làm ngày 19/09/2026 nhưng chưa có báo cáo riêng như các tuần khác.
> Khi viết bù đã soát lại code và **phát hiện 2 lỗi** (mục 4). Cả hai đã sửa và có test hồi quy.

---

## 0. Kết luận trước

> Hồ sơ sinh viên là **dữ liệu**, không phải quy tắc. Mỗi hồ sơ là một file JSON được kiểm theo `student_fact_schema.json`, rồi đổi sang vị từ ASP (`g10`, `diem_m`, `chung_chi`, `duoc_mien`, `khong_tinh_tich_luy`, ...). Các vị từ này nạp chung với R-Formal (quy chế) và Curriculum KB (CTĐT K49). Không có trạng thái học phần nào được ghi thẳng vào hồ sơ: `passed`, `tich_luy`, `exempted_m` đều do solver **suy ra**. Nhờ vậy, khi đổi quy tắc thì không phải sửa dữ liệu.

---

## 1. Ba lớp dữ liệu và ranh giới

| Lớp | Nguồn | Ví dụ vị từ | Ai sở hữu |
|---|---|---|---|
| Quy chế (R) | QĐ3266 + QĐ5339 | `nguong_cc/3`, `du_dk_xin_mien/1` | `w5_rformal/*.lp` |
| CTĐT (C) | Khung CTĐT CNTT K49 | `course/2`, `thuoc_nhom/2`, `loai_hp/2`, `ngon_ngu_hp/2` | `w6_curriculum/` (sinh tự động) |
| Hồ sơ (S) | Bảng điểm, chứng chỉ, quyết định miễn | `g10/2`, `chung_chi/2`, `duoc_mien/1` | `w7_student_facts/students/*.json` |

Quy tắc ranh giới: **hồ sơ chỉ chứa dữ kiện quan sát được**. Ví dụ, `du_dk_xin_mien` (đủ điều kiện xin miễn) **không** nằm trong hồ sơ vì solver suy được từ `chung_chi`. Ngược lại, `duoc_mien` (đã có quyết định miễn) là dữ kiện ngoài, phải nhập vào vì không suy ra được (QD-11, QĐ5339 Đ2 k6).

---

## 2. Schema (`student_fact_schema.json`)

Bắt buộc: `student_id`, `major`, `cohort`, `grades`. Tuỳ chọn: `certificates[]`, `exemptions[]`, `khong_tinh_tich_luy[]`, `che_do_sv_chon_tich_luy`, `xac_nhan_ky_luat_sach`, `meta`.

| Trường JSON | Vị từ ASP | Nguồn quy chế |
|---|---|---|
| `grades[].thang10` | `g10(C,X)` | R-B02 (bảng quy đổi) |
| `grades[].diem == "M" / "W" / "I"` | `diem_m / diem_w / diem_i` | R-B04, R-B06, R-B05 |
| `certificates[]` | `chung_chi(loai, diem×10)`; `ctu_abc` giữ bậc 1/2/3 | R-M06, R-M07 |
| `exemptions[].quyet_dinh == true` | `duoc_mien(C)` | QD-11 (R-M16) |
| `exemptions[].quyet_dinh == false` | *(không sinh gì)*: solver tự suy `mien_treo(C)` từ chứng chỉ | QD-11 |
| `khong_tinh_tich_luy[]` | `khong_tinh_tich_luy(C)` | CQ-06 |
| `xac_nhan_ky_luat_sach` | `xac_nhan_ky_luat_sach` | R-F03; thiếu trường này thì kết luận là UNKNOWN |

**Quyết định Tuần 7:** `du_dk_xin_mien` là **trạng thái hồ sơ** (thủ tục), không phải trạng thái học phần (Trục C), nên không thêm làm trạng thái thứ 8 của Trục C.

---

## 3. Sáu hồ sơ giả lập

| Hồ sơ | Số HP | Tổng TC | Tình huống | Kết luận solver |
|---|---|---|---|---|
| `sv_lvtn` | 51 | 161 | Làm luận văn CT550E 15 TC (I1) | `tot_nghiep`, `tc_tich_luy(161)` |
| `sv_tltn` | 54 | 161 | Tiểu luận CT501E 6 TC + 3 HP (I2) | `tot_nghiep` |
| `sv_5hp` | 55 | 161 | Không làm LVTN/TLTN, học 5 HP tự chọn (I3) | `tot_nghiep` |
| `sv_tron_ngoai_ngu` | 51 | 162 | Học AV 4 TC + PV 7 TC (I5) | `thieu_nhom(g_ngoai_ngu,3)`, **không** tốt nghiệp |
| `sv_du_hp` | 52 | 164 | Học dư CT478 điểm D (4,5) (I15/I16) | `dtbctl_lt(20)`, **không** tốt nghiệp; bỏ CT478 khỏi tích lũy thì tốt nghiệp (CQ-06) |
| `sv_mien_ielts` *(mới)* | 48 | 151 + 10 miễn | IELTS 6.0, có QĐ miễn XH023–025 (QD-11) | `tot_nghiep`, `exempted_m`, điểm M; **không** được xin miễn Pháp văn |

Biến thể của `sv_mien_ielts`: nếu XH025 chưa có quyết định (`quyet_dinh=false`) thì kết luận là `mien_treo("XH025")` và `thieu_nhom(g_ngoai_ngu,3)`, không tốt nghiệp. Đây là ca "có chứng chỉ chưa phải là được miễn" (QD-11).

Hồ sơ thứ 6 được thêm khi viết bù báo cáo. Lý do: mục tiêu Tuần 7 có "chứng chỉ, miễn", nhưng 5 hồ sơ ban đầu **không hồ sơ nào có chứng chỉ hay quyết định miễn**. Tuần 9 có test miễn, nhưng bằng dữ kiện viết tay, nên đường JSON → ASP cho chứng chỉ chưa từng được chạy. Chính hồ sơ này làm lộ ra hai lỗi ở mục 4.

---

## 4. Lỗi phát hiện khi viết bù

### L7-1 · R-M06 cho IELTS xin miễn cả Pháp văn (dương tính giả)

QĐ5339 Điều 3 khoản 5 tách thành **điểm a** (miễn *Anh văn căn bản* bằng chứng chỉ *tiếng Anh*) và **điểm b** (miễn *Pháp văn căn bản* bằng chứng chỉ *tiếng Pháp*). R-Formal v1.4–1.5 gộp hai điểm: mọi HP `ngoai_ngu_cb` đều thành `du_dk_xin_mien` khi có bậc ngoại ngữ đủ, bất kể ngôn ngữ. Kết quả là hồ sơ `sv_mien_ielts` sinh ra `du_dk_xin_mien("FL001")` … `("FL009")`.

**Sửa (R-Formal v1.6):** thêm `ngon_ngu_cc/2`, `bac_nn/2` và `ngon_ngu_hp/2` (sinh từ `build_curriculum.py`). `du_dk_xin_mien` giờ đòi ngôn ngữ chứng chỉ khớp ngôn ngữ học phần. Test C19b đạt; kiểm tra đột biến cho thấy C19b **thất bại** với luật cũ.

**Còn hở:** bảng quy đổi tiếng Pháp (Phụ lục 1 mục 2, trang 12) chưa chép vì OCR không đọc được, nên hiện không suy được quyền miễn Pháp văn (P). **Câu hỏi mở:** "Anh văn tăng cường" XH031–033 có tính là "Anh văn căn bản" ở điểm a không? KB hiện coi là có.

### L7-2 · Loader chỉ nhân 10 điểm IELTS

`nguong_cc` lưu **mọi** loại điểm theo thang ×10 (IELTS 4.5 → 45, TOEIC 450 → 4500). Ba loader (`w7 validate_student_facts.py`, `w11 generate_certificate.py`, `w12 prototype.py`) chỉ nhân 10 cho IELTS, nên TOEIC 990 thành `chung_chi(toeic,990)` < 4000 và **không bao giờ đạt bậc nào**. Đã sửa cả ba (ngoại lệ `ctu_abc` vẫn giữ bậc 1/2/3). Test: C19c ở Tuần 5 và ca "loader" ở Tuần 7.

Lỗi này lọt qua vì mọi test trước đây đều dùng IELTS. Đây là một ví dụ cho lập luận của luận văn: **một bộ test chỉ có một loại chứng chỉ thì không kiểm được bảng quy đổi**.

---

## 5. Kiểm chứng

```
python w7_student_facts/validate_student_facts.py
[OK] sv_lvtn … [OK] sv_mien_ielts
  [OK] sv_du_hp + khong_tinh_tich_luy(CT478) → tot_nghiep (CQ-06)
  [OK] sv_mien_ielts, XH025 chưa có QĐ → mien_treo, thiếu ngoại ngữ 3 TC (QD-11)
[OK] loader quy đổi điểm chứng chỉ ×10
KẾT LUẬN: ĐẠT 6/6 hồ sơ + loader
```

Validator giờ **kiểm schema trước** (jsonschema Draft 2020-12), rồi mới giải. Trước đây README ghi là có kiểm schema nhưng code không làm. Chạy lại toàn bộ sau khi sửa: Tuần 5 41/41, Tuần 6 ĐẠT (kể cả P2 CP-SAT sau khi cài `ortools`), Tuần 8–13 đều ĐẠT.

---

## 6. Việc còn lại

- [ ] Mở rộng lên ≥20 hồ sơ phủ ca biên điểm (D = 4,0; D+ = 5,0; GDQP cần D+) và đủ loại chứng chỉ (TOEIC, TOEFL, ctu_abc)
- [ ] Chế độ `--strict`: tính lại GPA so với GPA in trên bảng điểm. **Chưa cài**, dời sang Tuần 15 (OCR)
- [x] Trường `confidence` / `ocr_raw` cho từng dữ kiện: Tuần 15 — ✅ đã xong: Tuần 15
- [ ] Chép bảng quy đổi tiếng Pháp (QĐ5339 trang 12) từ **ảnh gốc**, không qua OCR
- [ ] Hỏi Phòng Đào tạo: "Anh văn tăng cường" có được miễn bằng chứng chỉ theo điểm a không
- [ ] Thử trên bảng điểm thật (đã ẩn danh)

### Ghi chú kiểm chứng

- [x] ≥5 hồ sơ giả lập (có 6), tất cả qua schema
- [x] Mỗi hồ sơ có kết luận kỳ vọng và đều đạt
- [x] Có hồ sơ chứng chỉ + quyết định miễn, kể cả biến thể `mien_treo`
- [x] Lỗi phát hiện được ghi lại kèm test hồi quy (L7-1, L7-2)
- [ ] Chưa có bảng điểm thật
