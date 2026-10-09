# ĐÍNH CHÍNH PROTOTYPE TUẦN 4 — phát hiện khi xây Curriculum KB ở Tuần 6

Đối chiếu `kb.py` với khung CTĐT CNTT K49 thật (`NiênLuan/ctdt/K49/69_7480201_CongNgheThongTin.pdf`,
chép đủ 78 dòng ở `w6_curriculum/`). `kb.py`, `probe_clingo.py`, `probe_z3.py` đã sửa;
kết quả chạy lại ở `bench_output_tuan6.txt`. `bench_output.txt` giữ nguyên làm bằng chứng lịch sử.

## 1. Lỗi dữ liệu trong `kb.py`

| # | Tuần 4 ghi | CTĐT K49 thật | Hệ quả |
|---|---|---|---|
| E1 | CT466E = Luận văn tốt nghiệp, 10 TC | CT466E = **Niên luận** 3 TC (≥80 TC). Luận văn là **CT550E 15 TC** (≥120 TC) | sai cả mã, tên, số TC |
| E2 | Luận văn là học phần bắt buộc (`thesis`) | CT550E nằm trong **nhóm tự chọn 15 TC** cùng CT501E (TLTN 6 TC) và 7 HP 3 TC | luận văn không bắt buộc — đây chính là QĐ3266 Đ.31 k.3 |
| E3 | Nhóm tự chọn "10 chọn 2" | Không tồn tại. Chuyên ngành là **6 TC từ đúng một cặp** CN1/CN2/CN3 | sai cấu trúc nhóm |
| E4 | CT203E, CT280, CT282E, CT299, CT291, CT295 | **không có** trong CTĐT CNTT K49 | 6/10 HP tự chọn là giả |
| E5 | CT172E, CT190E | K49 dùng **CT172, CT190** | mã theo khoá — ca biên T1 của Tuần 2 xảy ra ngay trong prototype |
| E6 | CT182 ← CT176 **và** CT180 | CT182 ← CT176; CT180 là **song hành** | tiên quyết kép sai, song hành bị đọc thành tiên quyết |
| E7 | CT294 ← CT190E; CT282E ← CT294; CT312 ← CT180; CT219 ← CT294; CT299 ← CT180; CT466E ← CT271E | **không có** trong CTĐT K49 | 6 cạnh tiên quyết giả |
| E8 | (thiếu) | CT271E ← CT174, CT176 | thiếu 2 cạnh thật |
| E9 | WARNING_TERM_GPA = 1,20 | 1,00 (0,80 ở HK đầu khoá) — QĐ3266 Đ.18 k.2 đ.a | đã phát hiện ở Tuần 5, nay sửa trong mã |

Nguồn gốc chung: dữ liệu Tuần 4 lấy từ `core/constants.py` và `academiq_ctdt_mysql.sql` của
AcademiQ — **dữ liệu thứ cấp**, trộn nhiều khoá, không phải văn bản CTĐT. Bài học đưa vào
phương pháp: KB chỉ lấy từ văn bản ban hành, không lấy từ CSDL của hệ thống cũ.

## 2. Lỗi phương pháp đo trong `probe_clingo.py` — ảnh hưởng tới Solver Design Note

`min_semesters` dùng `--opt-mode=optN`: clingo **liệt kê mọi kế hoạch tối ưu**, không chỉ
chứng minh tối ưu. Đo lại trên chính `kb.py` CŨ của Tuần 4:

| Chế độ | Thời gian (trung vị 5 lần, máy cloud) | Mô hình liệt kê |
|---|---|---|
| `optN` (Tuần 4) | 23,8 ms | **9 950** kế hoạch tối ưu |
| `opt` (sửa) | 2,6 ms | 1, `optimal = 1` |

→ Con số *"CP-SAT nhanh hơn clingo ~15×"* ở mục 3.2 của Solver Design Note là **tạo tác của
cách đo**, không phải so sánh công bằng. Chạy lại trên dữ liệu đã sửa (`bench_output_tuan6.txt`):

```
Z3 Optimize      k = 4       193,1 ms
clingo (ASP)     k = 4         2,5 ms
CP-SAT           k = 4        19,3 ms
Đối chiếu chéo ba solver: TRÙNG KHỚP (k = 4, 16 học phần)
```

Kết luận chọn **clingo cho T1** không đổi (lý do chính là ngữ nghĩa ba trị, không phải tốc độ).
Lý do *tốc độ* để chọn **CP-SAT cho T3 không còn đứng được** ở quy mô prototype. Hai lý do còn
lại vẫn giữ: CP-SAT báo `OPTIMAL` và co giãn tốt hơn khi bài toán lớn — nhưng điều thứ hai **chưa
được đo**. Việc cần làm: đo lại T3 trên CTĐT đầy đủ 78 HP, nhiều hồ sơ, horizon 9–18 HK (dự kiến
Tuần 12) rồi mới chốt vai trò của CP-SAT.

Lưu ý: kết quả T1 (ba trị) và việc ba solver trùng khớp không bị ảnh hưởng — bằng chứng
đối chiếu chéo của Tuần 4 vẫn đúng; chỉ con số tốc độ T3 bị sai.
