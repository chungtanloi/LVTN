# TUẦN 6 — CURRICULUM KB v1

**Sản phẩm:** Curriculum KB v1 — khung CTĐT ngành CNTT K49 dạng dữ kiện ASP, sinh tự động, có con trỏ nguồn
**Tiêu chí hoàn thành:** Solver đọc được curriculum ✅
**Bằng chứng:** `w6_curriculum/` — `python3 validate_curriculum.py` → 31/31 ca đạt, ba solver độc lập trùng khớp

---

## 0. Kết luận trước

1. **Solver đọc được curriculum — kiểm chứng bằng một con số không thể "chép cho khớp".** Từ 78 dòng
   học phần, 5 nhóm tự chọn và các ràng buộc tiên quyết/song hành, clingo **tính ra** số tín chỉ tối
   thiểu để hoàn thành CTĐT là **161 TC** — đúng dòng "Tổng cộng" của văn bản. CP-SAT (đọc JSON, không
   đọc `.lp`) và một bộ liệt kê thuần Python cho cùng con số, và cùng đếm được **2 394** kế hoạch tối
   thiểu khác nhau.
2. **Luận văn tốt nghiệp KHÔNG phải học phần bắt buộc.** CT550E (15 TC) nằm chung ô "15 TC" với
   CT501E (Tiểu luận, 6 TC) và 7 học phần 3 TC. Đó chính là QĐ3266 Đ.31 k.3 hiện hình trong CTĐT.
   File `ctdt_cntt_k49.lp` của Tuần 5 bỏ sót CT550E/CT501E khỏi nhóm này → SV làm luận văn sẽ bị kết
   luận thiếu tự chọn.
3. **Nối KB quy chế với CTĐT thật làm lộ ba lỗi của R-Formal v1.4** mà 39 ca kiểm thử tổng hợp không bắt
   được — trong đó một lỗi **dương tính giả** (vi phạm tính đúng đắn). Đã sửa thành v1.5; 39/39 ca cũ vẫn
   đạt, và nay chạy trên KB CTĐT mới.
4. **Prototype Tuần 4 sai 9 chỗ về dữ liệu, và con số "CP-SAT nhanh hơn clingo 15×" là tạo tác đo**
   (clingo đang liệt kê 9 950 kế hoạch tối ưu). Đã sửa và đo lại; ba solver vẫn trùng khớp.

---

## 1. Sản phẩm và cách chạy

```
w6_curriculum/
  build_curriculum.py        NGUỒN DUY NHẤT: 78 dòng + 5 nhóm, kiểm tra nội tại rồi mới sinh file
  curriculum_cntt_k49.json   (sinh) bản chép có cấu trúc, mỗi dòng có trang + số thứ tự trong PDF
  curriculum_cntt_k49.lp     (sinh) dữ kiện ASP
  curriculum_schema.lp       ngữ nghĩa nhóm/nhánh/điều kiện — ĐỘC LẬP ngành & khoá
  kiem_tra_cau_truc.lp       chế độ kế hoạch: tập HP nhỏ nhất thoả mọi ràng buộc CTĐT
  doi_chieu_nguon.py         đối chiếu bản chép với PDF (lớp văn bản trang 3, OCR trang 4)
  validate_curriculum.py     31 ca: cấu trúc (S) · ba solver (P) · tích hợp R-Formal (I)
  curriculum_report.txt, doi_chieu_report.txt   kết quả chạy thật
```

```bash
cd w6_curriculum
pip install clingo ortools
python3 build_curriculum.py        # sinh .json + .lp (dừng nếu bản chép sai)
python3 validate_curriculum.py     # 31/31
python3 doi_chieu_nguon.py         # cần poppler + tesseract
cd ../w5_rformal && python3 validate_rformal.py   # 39/39 — nay nạp KB CTĐT mới
```

---

## 2. Khung CTĐT CNTT K49 sau khi chép đủ

Nguồn: QĐ 2423/QĐ-ĐHCT (05/6/2023), `NiênLuan/ctdt/K49/69_7480201_CongNgheThongTin.pdf`, mục 6.

| Khối | Tổng | Bắt buộc | Tự chọn | Nhóm tự chọn |
|---|---|---|---|---|
| Đại cương | 56 | 41 | 15 | GDTC 3 · Ngoại ngữ 10 (AV **hoặc** PV) · Xã hội 2 |
| Cơ sở ngành | 46 | 46 | 0 | — |
| Chuyên ngành | 59 | 38 | 21 | Chuyên ngành 6 (CN1 **hoặc** CN2 **hoặc** CN3) · Tốt nghiệp 15 |
| **Cộng** | **161** | **125** | **36** | 5 nhóm, 3 kiểu |

- 78 dòng, 43 học phần bắt buộc, 17 học phần điều kiện (*) — GDQP 4, GDTC 1, ngoại ngữ 12; khối lượng điều kiện tối thiểu 21 TC (8 + 3 + 10).
- Đồ thị: 20 cạnh tiên quyết học phần (T4a), 11 cạnh song hành (T4c), 4 ngưỡng tín chỉ (T4b).
  Chuỗi dài nhất là lý luận chính trị ML014 → … → ML021 (5 HP); nhánh CNTT dài nhất 4 HP.
- CT518E (Thực tập doanh nghiệp, ≥125 TC) **chỉ mở HK III**.

**Độ tin cậy của bản chép.** Trang 3 (dòng 1–41) có lớp văn bản: **41/41 khớp chính xác** mã, số TC và
mã tham chiếu. Trang 4 (dòng 42–78) là ảnh quét: OCR đọc được và khớp mã **26/37**, 1 dòng OCR đọc
lệch đã soát tay trên ảnh (CT482), 10 dòng OCR không đọc được — soát tay trên ảnh 200 dpi. Số TC trang 4
còn được chặn bởi ba ràng buộc độc lập: tổng từng khối = dòng "Cộng", quy đổi LT/TH = số TC × 15 giờ,
và đột biến một số làm KB vô nghiệm (S3, S4). **Cột tiên quyết trang 4 chỉ được soát bằng mắt** — đây
là phần kém chắc chắn nhất của KB.

---

## 3. Kiến trúc: ba lớp tách bạch

```
QĐ3266 + QĐ5339   (w5_rformal/*.lp)          quy tắc quy chế — chung toàn trường
        │ passed/1, tc_tich_luy/1, hp_dieu_kien/1
curriculum_schema.lp                          nhóm/nhánh/T4b nghĩa là gì — chung mọi CTĐT
        │ nhom/1, thuoc_nhom/2, thuoc_nhanh/3, tien_quyet_tc/2, ...
curriculum_cntt_k49.lp  (sinh tự động)        dữ kiện của MỘT (ngành, khoá)
```

Đổi ngành hay đổi khoá chỉ thay lớp dưới cùng. Schema **không tạo RuleId mới**: mọi `why/2` trỏ về
R-A02/R-A03 của QĐ3266; mỗi học phần mang `ctdt_src(Mã, Trang, Dòng)` về đúng dòng trong PDF.

**Ba kiểu nhóm** (Taxonomy Tuần 2, T3 đã cập nhật):

| Kiểu | Ví dụ K49 | Ngữ nghĩa |
|---|---|---|
| đếm tín chỉ | Tốt nghiệp 15 TC, Xã hội 2 TC, GDTC 3 TC | Σ TC đạt trong nhóm ≥ N |
| một nhánh | Ngoại ngữ (AV/PV), Chuyên ngành (CN1/2/3) | ∃ nhánh: Σ TC đạt trong nhánh ≥ N — **không cộng dồn qua nhánh** |
| đếm môn | *(không có trong K49)* | giữ cho tương thích R-Formal v1.4 |

**Nhóm điều kiện**: nhóm mà mọi thành viên là học phần (*) (Ngoại ngữ, GDTC) được xét ở QĐ3266
Đ.32 k.1 **đ.b** (hoàn thành học phần điều kiện), không ở đ.a (tự chọn). Phân biệt này quyết định
Đ.33 k.2 có áp dụng hay không.

---

## 4. Kiểm chứng — 31/31 đạt

**S. Cấu trúc (6/6).** KB có answer set; đổi CT177 3→4 TC hoặc nhóm tốt nghiệp 15→12 TC làm KB **vô
nghiệm**; mọi `why/2` có `rule_src`; 78/78 học phần có `ctdt_src`.

**P. Solver đọc được curriculum (4/4) — ba cài đặt độc lập:**

| | clingo (.lp) | CP-SAT (.json) | Python thuần (.json) |
|---|---|---|---|
| TC tối thiểu hoàn thành CTĐT | **161** | **161** (OPTIMAL) | **161** |
| Số kế hoạch tối thiểu khác nhau | **2 394** | **2 394** | **2 394** |

2 394 = 2 (ngoại ngữ) × 7 (xã hội) × 3 (chuyên ngành) × 57 (tốt nghiệp: LVTN · TLTN + 3 HP chọn từ 7 ·
5 HP chọn từ 7). Nhóm ngoại ngữ chỉ có 2 cách vì **chuỗi song hành** buộc mọi kế hoạch bắt đầu từ căn
bản 1 (10 TC = căn bản 1–3), trừ khi được miễn bằng chứng chỉ.

**I. Tích hợp với R-Formal trên CTĐT thật (21/21):**

| Ca | Tình huống | Kết luận |
|---|---|---|
| I1–I3 | Đủ theo 3 hình thức: LVTN · TLTN + 3 HP · 5 HP tự chọn | `tot_nghiep` |
| I4 | 164 TC nhưng thiếu nhóm 15 TC tốt nghiệp | **không** tốt nghiệp, `thieu_nhom(g_tot_nghiep,15)` |
| I5 | AV 4 TC + PV 7 TC | nhóm ngoại ngữ chưa đạt, thiếu 3 TC |
| I6 | Mới 30 TC | CT550E chưa được đăng ký, thiếu 90 TC |
| I7–I8 | Song hành | XH024 trước XH023 là vi phạm; CT182 chỉ cần đạt CT176 |
| I9 | Hai HP chéo cặp chuyên ngành | nhóm chuyên ngành chưa đạt |
| I10a/b | Quá hạn, chỉ thiếu ngoại ngữ | xem CQ-05 |
| I11 | Học phần (*) điểm thấp | không kéo ĐTBCTL |
| I12–I14 | **Ba trị** | thiếu điểm LVTN → `UNKNOWN`; đủ → `TRUE`; thiếu xác nhận kỷ luật → `FALSE` |
| I15–I16 | Học dư CT478 điểm D | tính tất cả → ĐTBCTL < 2,00; SV chọn bỏ CT478 → tốt nghiệp (CQ-06) |
| I17–I18 | Chọn bỏ sai | bỏ CT550E → thiếu nhóm; bỏ HP bắt buộc → vô nghiệm |
| I19 | Làm cả LVTN và TLTN | tốt nghiệp + `khuyen_nghi(khong_lam_ca_lvtn_tltn)` |
| I20 | Chưa rõ điểm HP dư, SV còn quyền chọn | **∀ thế giới ∃ lựa chọn** → `TRUE` (cautious ngây thơ cho `UNKNOWN` — sai) |

---

## 5. Phát hiện

### 5.1. Ba lỗi của R-Formal v1.4 chỉ lộ ra khi gặp CTĐT thật (đã sửa → v1.5)

| Mã | Lỗi | Loại | Ca hồi quy |
|---|---|---|---|
| **L1** | `dk_hp_dieu_kien` đòi đạt **mọi** học phần điều kiện → đòi cả 12 HP ngoại ngữ (40 TC, cả Anh lẫn Pháp) | âm tính giả: SV đủ bị kết luận **không** tốt nghiệp | I1 |
| **L2** | `dk_tu_chon` chỉ quét nhóm đếm-môn; CTĐT thật toàn nhóm đếm-tín-chỉ → điều kiện **đúng rỗng** | **dương tính giả**: SV thiếu 15 TC nhóm tốt nghiệp vẫn "đủ tự chọn" | I4 |
| **L3** | `du_dk_dang_ky` chỉ xét tiên quyết học phần, bỏ qua T4b | dương tính giả: SV 30 TC "được đăng ký" luận văn | I6 |

L2 là lỗi nguy hiểm nhất: nó vi phạm đúng tính chất mà đề tài hứa (*không bao giờ nói sai*). Nó sống
sót qua 39 ca của Tuần 5 vì mọi ca đó dùng CTĐT thu nhỏ **không có nhóm tự chọn** — điều kiện rỗng
trông giống điều kiện đạt. **Bài học phương pháp:** bộ kiểm thử tổng hợp đo được ngưỡng số, nhưng không
đo được *độ phủ cấu trúc*; phải có ít nhất một bộ ca chạy trên CTĐT thật đầy đủ.

### 5.2. Lỗi trong bản CTĐT chép tay của Tuần 5 (`ctdt_cntt_k49.lp`)

Nhóm "tự chọn tự do 15 TC" bỏ sót CT550E và CT501E; chưa có 15 TC tự chọn đại cương; coi việc học hai
cặp chuyên ngành là vi phạm. File được giữ lại làm lịch sử, có ghi chú lỗi ở đầu; `validate_rformal.py`
nay nạp KB mới.

### 5.3. Prototype Tuần 4 — xem `w4_solver_probe/ERRATA_Tuan6.md`

9 lỗi dữ liệu (CT466E là niên luận 3 TC; nhóm "10 chọn 2" và 6 mã học phần không có thật; 6 cạnh tiên
quyết giả; CT180 là song hành của CT182…). Nguồn gốc chung: dữ liệu lấy từ CSDL của AcademiQ, không từ
văn bản CTĐT. Ngoài ra `--opt-mode=optN` làm clingo liệt kê 9 950 kế hoạch tối ưu → so sánh tốc độ T3
của Tuần 4 không công bằng. Đo lại: clingo 2,5 ms · CP-SAT 19 ms · Z3 193 ms, cả ba k = 4. **Vai trò
CP-SAT cho T3 để mở** tới khi đo trên CTĐT đầy đủ.

### 5.4. Song hành ≠ tiên quyết, và CTĐT dùng nó nhiều hơn ta nghĩ

11 cạnh song hành, 10 trong số đó là chuỗi ngoại ngữ. Hệ quả thực tế: trong chế độ kế hoạch, SV
không thể "chọn" học Anh văn tăng cường để đủ 10 TC mà bỏ qua căn bản — trừ khi được miễn (QĐ5339).

---

## 6. Quyết định diễn giải CTĐT (CQ)

| Mã | Câu hỏi | Quyết định | Trạng thái |
|---|---|---|---|
| CQ-01 | TC100 "1+1+1" ở cột Tự chọn | 1 học phần 3 TC trong nhóm GDTC 3 TC; không mô hình từng môn thể thao | đóng |
| CQ-02 | "10 AV hoặc PV" | nhóm **một nhánh**; TC không cộng dồn qua hai ngoại ngữ | đóng (theo câu chữ "hoặc") |
| CQ-03 | Song hành trong kế hoạch | P phải được học trước hoặc cùng kỳ với C (QĐ3266 Đ.7 k.5) | đóng |
| CQ-04 | Học dư nhánh thứ hai / HP tự chọn dư | không cấm; không tính cho nhóm (`hp_nhanh_khong_tinh/2`); có vào tích lũy hay không do SV chọn — xem CQ-06 | đóng |
| CQ-05 | 161 TC có gồm 21 TC học phần điều kiện khi xét Đ.32 k.1 **đ.a**? | **Có** — cách đọc chặt là mặc định. Chính sách `tc_khong_gom_dk` chỉ giữ để phân tích độ nhạy | **đóng** (Loi xác nhận 19/9/2026) |
| CQ-06 | Làm cả LVTN và TLTN? HP tự chọn dư tính thế nào? | Không cấm làm cả hai, nhưng không nên → `khuyen_nghi/1`, không phải vi phạm. Khi xét tốt nghiệp **SV chọn HP tự chọn nào đưa vào tích lũy**: `khong_tinh_tich_luy/1` | **đóng** (Loi xác nhận 19/9/2026) |

**Hệ quả của CQ-05 (nay là sự thật của quy chế, không còn là câu hỏi):** SV quá hạn *chỉ thiếu học
phần điều kiện* cũng thiếu luôn TC ở đ.a, nên Đ.33 k.2 (được quay lại trong 3 năm) chỉ kích hoạt khi
SV đã học dư tự chọn bù đúng số TC điều kiện còn thiếu (I10a). Đây là một nhận xét đáng đưa vào chương
thảo luận: một điều khoản có câu chữ rộng nhưng phạm vi áp dụng thực tế rất hẹp.

**Cài đặt CQ-06 (R-Formal v1.5).** Tách `passed/1` (đã đạt — dùng cho tiên quyết) khỏi `tich_luy/1`
(được tính — dùng cho số TC tích lũy, ĐTBCTL và nhóm tự chọn):

```prolog
tich_luy(C) :- passed(C), not khong_tinh_tich_luy(C).
:- khong_tinh_tich_luy(C), not hp_trong_nhom(C).          % chỉ bỏ được HP tự chọn
{ khong_tinh_tich_luy(C) : passed(C), hp_trong_nhom(C) } :- che_do(sv_chon_tich_luy).
```

Hai chế độ: SV **đã khai báo** lựa chọn → dữ kiện, suy diễn bình thường; SV **chưa khai báo** →
`che_do(sv_chon_tich_luy)`, hệ thống xét mọi cách chọn.

**Phát hiện phương pháp (I20):** khi có quyền chọn, ba trị không còn là cautious/brave phẳng như
Solver Design Note Tuần 4 mô tả. Câu hỏi đúng là *"với MỌI khả năng của dữ kiện còn thiếu, có TỒN TẠI
cách chọn cho SV tốt nghiệp không?"* — hai lượng từ lồng nhau. Cautious ngây thơ trên toàn bộ answer set
trả `UNKNOWN` cho một ca thực chất là `TRUE`: không sai về tính đúng đắn (không nói sai), nhưng **từ
chối trả lời thừa**, làm giảm Coverage. Bản hiện tại nhóm answer set theo thế giới dữ kiện rồi mới lấy ∃;
cách này liệt kê nên sẽ không co giãn — Tuần 16 (Abstention engine) cần cài bằng kỹ thuật bão hoà
(saturation) hoặc gọi solver hai tầng.

## 7. Hạn chế và việc chuyển tiếp

- **Còn hỏi Phòng Đào tạo:** QD-03 (TC nợ đọng) và công thức TC nợ đọng trên hqtl.ctu.edu.vn. CQ-05 và
  CQ-06 đã đóng theo xác nhận của Loi — nên ghi thêm **ai ở Phòng Đào tạo / văn bản nào** làm nguồn, như
  hạn chế đã nêu với QD-09 ở Tuần 5.
- Cột tiên quyết trang 4 chỉ soát bằng mắt. Nên nhờ người thứ hai soát 37 dòng này cùng lúc với phiếu
  gán nhãn F/P/N của Tuần 5.
- KB mới có **một** (ngành, khoá). Muốn chứng minh lớp schema thật sự độc lập ngành, nên chép thêm một
  CTĐT (vd. KTPM K49) — rẻ vì chỉ cần thêm dữ liệu vào `build_curriculum.py`.
- Chưa mô hình: nội dung môn GDTC, điều kiện "đơn vị đào tạo quy định" ngoài ngưỡng TC để nhận LVTN
  (R-F04), chuẩn đầu ra ngoại ngữ.
- **Tuần 7 (Student Fact Model)** nhận đầu vào trực tiếp từ đây: schema bảng điểm phải sinh được
  `g10/2`, `diem_m/1`, `xep_hk/2`, `dang_ky/2` khớp các vị từ mà KB đang dùng; ≥5 hồ sơ giả lập nên phủ ba
  hình thức tốt nghiệp (I1–I3) và hai nhánh ngoại ngữ. Student Fact Model cũng phải có chỗ cho **lựa chọn
  tích lũy của SV** (`khong_tinh_tich_luy/1`) và phân biệt "chưa chọn" với "chọn tính tất cả".
