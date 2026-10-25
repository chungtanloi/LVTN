# R-Formal — bộ quy tắc học vụ hình thức hoá (CPA², Tuần 5)

Phiên bản hiện tại: **v1.6** (quy tắc) · danh mục JSON v1.4 · Nguồn: **QĐ 3266/QĐ-ĐHCT (15/8/2024)** và **QĐ 5339/QĐ-ĐHCT (05/11/2019)**

> **v1.6 (09/10/2026, phát hiện khi làm hồ sơ chứng chỉ ở Tuần 7)** — R-M06 gộp điểm a (Anh văn) và
> điểm b (Pháp văn) của QĐ5339 Đ3 k5 → IELTS cho xin miễn cả FL001–FL009 (dương tính giả). Sửa: thêm
> `ngon_ngu_cc/2`, `bac_nn/2`, và `du_dk_xin_mien` đòi `ngon_ngu_hp(C,NN)` khớp ngôn ngữ chứng chỉ
> (`ngon_ngu_hp/2` sinh từ `../w6_curriculum/build_curriculum.py`). `bac_ngoai_ngu/1` giữ để tương thích.
> **Còn hở (P):** bảng quy đổi tiếng Pháp (Phụ lục 1 mục 2, trang 12) chưa chép vì OCR không đọc được
> → miễn Pháp văn chưa suy được. **Câu hỏi mở:** "Anh văn **tăng cường**" (XH031–033) có thuộc "Anh văn
> căn bản" ở điểm a không — KB hiện coi là có (cùng `ngoai_ngu_cb`). Thêm C19b, C19c → 41/41.
> Cùng đợt: loader ở w7/w11/w12 chỉ nhân 10 điểm IELTS, trong khi `nguong_cc` lưu mọi điểm ×10 → TOEIC/TOEFL
> không bao giờ đạt bậc; đã sửa (ctu_abc giữ bậc 1/2/3).

> **v1.5 (Tuần 6)** — sửa 3 lỗi chỉ lộ ra khi nối với CTĐT thật (`../w6_curriculum/`):
> L1 `dk_hp_dieu_kien` đòi đạt mọi HP ngoại ngữ · L2 `dk_tu_chon` đúng rỗng với nhóm đếm tín chỉ
> (dương tính giả) · L3 `du_dk_dang_ky` bỏ qua tiên quyết theo ngưỡng TC. CQ-05 đóng theo cách đọc
> chặt (161 TC gồm HP điều kiện). CQ-06: tách `passed/1` khỏi `tich_luy/1` — SV chọn HP tự chọn nào
> đưa vào tích lũy (`khong_tinh_tich_luy/1`). `validate_rformal.py` nay nạp Curriculum KB v1 thay cho `ctdt_cntt_k49.lp`.
> Con trỏ nguồn không đổi (không thêm RuleId) nên danh mục JSON giữ v1.4.

---

## Chạy lại toàn bộ kiểm chứng

```bash
cd w5_rformal
pip install -r requirements.txt      # chỉ cần clingo
python3 validate_rformal.py
```

Mã thoát: `0` = đạt toàn bộ · `1` = có lỗi · `2` = phần A/B đạt nhưng chưa chạy được phần C
(thiếu `clingo`). Phần A và B **không** cần `clingo` — chúng chỉ đọc JSON và các file `.lp`
dạng văn bản, nên vẫn kiểm chứng được con trỏ nguồn và số liệu coverage trên máy trắng.

Kết quả mong đợi ở v1.4:

```
7/7 bất biến con trỏ nguồn đạt
Formalization Coverage = 81,7 %   (F=58, P=8, N=5 trên 71 đơn vị trong miền)
Executable Coverage    = 59,2 %
39/39 ca kiểm thử ngữ nghĩa đạt
```

## Sinh lại các sản phẩm phái sinh

```bash
python3 build_catalog.py     # r_formal_v1.json      (danh mục — NGUỒN DUY NHẤT)
python3 gen_quyet_dinh.py    # PhuLuc_Quyet_dinh_dien_giai.md
python3 make_review_kit.py   # phieu_gan_nhan_mu.xlsx
```

Danh mục là **mã nguồn**, không phải bảng gõ tay: mọi bản ghi nằm trong `build_catalog.py`
và JSON được sinh ra từ đó. Phụ lục quyết định diễn giải cũng sinh từ JSON, nên tài liệu
không thể trôi khỏi KB — đây là cách chặn đúng loại lỗi đã xảy ra một lần giữa v1.1 và v1.2.

## Soát chéo độc lập nhãn F/P/N

Toàn bộ nhãn hiện do **một người** gán — hạn chế phương pháp lớn nhất còn lại của RQ1.

```bash
python3 make_review_kit.py            # hoặc --n 20 để lấy mẫu phân tầng, seed cố định
# gửi phieu_gan_nhan_mu.xlsx cho người thứ hai điền (phiếu KHÔNG chứa nhãn người thứ nhất)
python3 tinh_kappa.py phieu_da_dien.xlsx
```

Báo cáo gồm đồng thuận thô, Cohen's kappa cho từng trục, ma trận nhầm lẫn và danh sách
đơn vị bất đồng. Nhãn chốt sau khi hai người thống nhất mới đưa ngược vào `build_catalog.py`.

---

## Các file

| File | Vai trò |
|---|---|
| `build_catalog.py` | **Nguồn duy nhất** của danh mục — 93 bản ghi, mỗi bản ghi có trích nguyên văn, con trỏ nguồn, lớp F/P/N, trục khả dụng dữ kiện |
| `r_formal_v1.json` | Danh mục đã sinh (v1.4). Không sửa tay |
| `qd3266_r_formal_v1.lp` | Quy tắc ASP từ QĐ3266 |
| `qd5339_r_formal_v1.lp` | Quy tắc ASP từ QĐ5339 (nhóm miễn & công nhận điểm) |
| `ctdt_cntt_k49.lp` | *(Đã thay bằng `../w6_curriculum/` — giữ làm lịch sử, có ghi lỗi ở đầu file.)* **Tham số thật của CTĐT CNTT K49** — 161 TC, 4,5 năm, nhóm CN1/CN2/CN3, tiên quyết theo tín chỉ. Là DỮ LIỆU của một (ngành, khoá), tách khỏi quy tắc quy chế |
| `adversarial/bay_tri_thuc.py` → `BoBayTriThuc.md` | Bộ bẫy tri thức: 8 mệnh đề học vụ phổ biến, 7 sai, kèm ground truth và nguồn |
| `validate_rformal.py` | Kiểm bất biến nguồn (A) · thống kê coverage (B) · 39 ca kiểm thử ngữ nghĩa (C) |
| `coverage_report.txt` | Kết quả chạy thật, dùng làm bằng chứng |
| `gen_quyet_dinh.py` → `PhuLuc_Quyet_dinh_dien_giai.md` | Phụ lục 11 quyết định diễn giải |
| `make_review_kit.py` → `phieu_gan_nhan_mu.xlsx` | Phiếu gán nhãn mù cho người soát thứ hai |
| `tinh_kappa.py` | Tính Cohen's kappa giữa phiếu đã điền và danh mục |
| `source/*.txt` | Văn bản OCR thô — **để đối chiếu, KHÔNG dùng trực tiếp** (xem cảnh báo dưới) |

## Lược đồ con trỏ nguồn

```prolog
rule_src(RuleId, VanBan, Dieu, Khoan, Diem).   % địa chỉ tĩnh của quy tắc
why(Atom, RuleId).                             % vết động: vì sao Atom được suy ra
```

Mỗi quy tắc suy diễn đi kèm một quy tắc `why/2` cùng thân. Nhờ vậy chứng chỉ dựng được bằng
một truy vấn duy nhất trên `why/2`, và tính đầy đủ của con trỏ nguồn kiểm được bằng máy —
đó là điều biến *"mỗi rule có nguồn"* từ lời hứa thành bất biến.

Từ v1.1 con trỏ mang thêm mã văn bản: địa chỉ của một quy tắc pháp lý là
**(văn bản, điều, khoản, điểm)**, không phải (điều, khoản).

## Cảnh báo về văn bản nguồn

Cả hai QĐ đều là **bản quét không có lớp văn bản**; `pdftotext` trả về gần như rỗng. Quy
trình đã dùng: `pdftoppm -r 300 -gray` → `tesseract -l vie` → **đối chiếu thủ công trên ảnh
trang** cho mọi điều khoản có số hoặc bảng.

Bước đối chiếu tay là bắt buộc, không phải cẩn thận thừa: OCR trả **trang trắng hoàn toàn**
cho trang 20 của QĐ3266 (chứa Điều 33–35 và bảng hạng tốt nghiệp) mà không báo lỗi, làm nát
cả ba bảng của QĐ5339, và bỏ mất đúng hai dòng C⁺ và C trong bảng quy đổi điểm. Đừng tin
`source/*.txt`.

Trang 20 của QĐ3266 nay có bản **chép tay từ PDF gốc** (`source/QD3266_tr20_chep_tay.txt`, 18/10/2026) —
corpus RAG dùng bản này (`nguon=chep_tay`) thay cho trích R-Formal.

## Hạn chế đã biết

- Nhãn F/P/N do **một người** gán — chưa có kappa. Dùng bộ soát chéo ở trên để đóng.
- Chưa kiểm thử trên **bảng điểm thật**; 39 ca hiện dùng hồ sơ tổng hợp (dự kiến Tuần 7).
- **QD-03** (*"TC nợ đọng"*) đã có định nghĩa vận hành chạy được nhưng **chưa có nguồn
  xác nhận**; hai chính sách con QD-03a/QD-03b cho hai con số khác nhau trên cùng bảng điểm.
- **QD-09** được xác nhận ngoài văn bản nhưng **chưa ghi rõ ai xác nhận và ngày nào**.
- Bộ bẫy tri thức (`adversarial/`) có **cỡ mẫu rất nhỏ và không ngẫu nhiên** (2 câu trả lời,
  8 mệnh đề); giá trị hiện tại là định tính. Muốn dùng làm dữ liệu chính thức thì phải chạy
  lại có kiểm soát: cố định mô hình, prompt, ngày, lưu nguyên văn.
- ~~Nhóm tự chọn khối đại cương chưa mã hoá~~ — xong ở Tuần 6 (`../w6_curriculum/`).
