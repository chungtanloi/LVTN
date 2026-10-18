# Tuần 7 — Student Fact Model (CPA²)

**Mục tiêu Tuần 7 (Formalization):** Mô hình Student Facts — `Schema điểm, tín chỉ, GPA, chứng chỉ, miễn`

**Tiêu chí hoàn thành:** Có ≥5 hồ sơ giả lập — **ĐÃ HOÀN THÀNH** (6 hồ sơ trong `students/`)

## Đầu vào
- `../w5_rformal/qd3266_r_formal_v1.lp` + `qd5339_r_formal_v1.lp` — quy chế đã hình thức hoá (v1.5)
- `../w6_curriculum/curriculum_cntt_k49.json` + `curriculum_schema.lp` — CTĐT CNTT K49 (78 dòng, 161 TC)
- Taxonomy Tuần 2 — Trục C (7 trạng thái + `du_dk_xin_mien`)

## Sản phẩm

```
w7_student_facts/
├── README.md                     tài liệu này
├── student_fact_schema.json      JSON Schema cho hồ sơ sinh viên
├── student_fact_schema.lp        vị từ ASP sinh từ hồ sơ (g10/diem_m/dang_ky/...)
├── validate_student_facts.py     kiểm tra schema + chạy thử 5 hồ sơ qua R-Formal + Curriculum KB
├── students/
│   ├── sv_lvtn.json              đủ 161 TC — hình thức LVTN (CT550E 15 TC) — I1
│   ├── sv_tltn.json              đủ 161 TC — hình thức TLTN (CT501E 6 + 3 HP) — I2
│   ├── sv_5hp.json               đủ 161 TC — không làm LVTN/TLTN, 5 HP tự chọn — I3
│   ├── sv_tron_ngoai_ngu.json    162 TC nhưng trộn AV/PV → thiếu nhóm ngoại ngữ — I5
│   ├── sv_du_hp.json             học dư CT478 điểm D — cần quyền chọn CQ-06 — I15/I16
│   └── sv_mien_ielts.json        miễn 10 TC Anh văn bằng IELTS 6.0 (QD-11) — thêm 09/10/2026
└── Mau_Hoi_Phong_Dao_Tao.md      (ở ../w5_rformal/) — mẫu hỏi QD-03/QD-09/CQ-05/CQ-06
```

## Chạy

```bash
pip install clingo jsonschema
python validate_student_facts.py          # kiểm schema + 6/6 hồ sơ + loader đạt, đối chiếu R-Formal + Curriculum
# (chế độ --strict tính lại GPA so với transcript: CHƯA cài — để Tuần 15 khi có bảng điểm OCR)
```

## Liên kết với KB

| Trường JSON | Vị từ ASP | Nguồn quy chế |
|---|---|---|
| `grades[].thang10` | `g10(C,X)` | R-B02 (bảng quy đổi) |
| `grades[].diem == "M"` | `diem_m(C)` | R-B04, R-M05 (điểm M) |
| `grades[].diem == "W"` | `diem_w(C)` | R-B06 |
| `grades[].diem == "I"` | `diem_i(C)` | R-B05 (QD-05) |
| `exemptions[].quyet_dinh == true` | `duoc_mien(C)` + `diem_m(C)` | QD-11 (R-M16) |
| `exemptions[].quyet_dinh == false` | `du_dk_xin_mien(C)` + `mien_treo(C)` | QD-11 |
| `certificates[]` | `chung_chi(loai,diem)` | R-M06/R-M07 |
| `khong_tinh_tich_luy[]` | `khong_tinh_tich_luy(C)` | CQ-06 |
| `xac_nhan_ky_luat_sach` | `xac_nhan_ky_luat_sach` | R-F03 (UNKNOWN nếu thiếu) |

## Quyết định Tuần 7

**Vị trí của `du_dk_xin_mien`:** là **trạng thái hồ sơ**, không phải trạng thái học phần (Trục C). Lý do: QĐ5339 Điều 2 k.6 — miễn cần đơn + phê duyệt; có chứng chỉ chỉ tạo quyền nộp đơn. KB dùng hai vị từ riêng (`du_dk_xin_mien/1` suy được từ chứng chỉ, `duoc_mien/1` là dữ kiện ngoài). Không đưa `du_dk_xin_mien` vào Trục C để tránh nhầm trạng thái học phần với trạng thái thủ tục. Chốt theo đề xuất ở Taxonomy Tuần 2 mục 5.

## Việc còn lại → Tuần 8

- [ ] Mở rộng lên ≥20 hồ sơ phủ ca biên điểm (D=4.0, D+=5.0, GDQP) — Tuần 8 cần cho Elective & N-of-M
- [ ] OCR pipeline Tuần 15: trường `confidence` + `ocr_raw` hiện để `null` với hồ sơ giả lập

## Loader dùng chung (sau Tuần 17)

`loader.py` — `sang_asp(hồ sơ)` → (dữ kiện ASP, danh sách mâu thuẫn): rà soát bản ghi tự mâu thuẫn (P17-1), chứng chỉ ×10, lựa chọn tích lũy (CQ-06). Mọi đường vào (w7 `load_facts`, w11, w12, w15, w16) gọi hàm này; `validate_student_facts.py` L1–L3 kiểm.
