# cpa2_api — dịch vụ Python (FastAPI) bọc lõi CPA²

Mốc 1 của kế hoạch triển khai website. Lõi suy diễn nằm ở `CPA2_KhaoSat/` (clingo + BM25 + OCR); thư mục này chỉ là lớp HTTP:
kiểm hồ sơ, giới hạn tài nguyên, ánh xạ kết quả sang trạng thái mà giao diện hiểu. **Chỉ được gọi từ phía máy chủ** (Convex action),
không bao giờ từ trình duyệt.

```
Next.js → Convex action → [X-API-Key] cpa2_api → CPA2_KhaoSat (clingo, BM25, Tesseract)
```

## Chạy cục bộ

```bash
cd services/cpa2_api
python -m venv .venv && . .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt                    # cần thêm: cài Tesseract + gói 'vie' của hệ điều hành để dùng /v1/ocr
export CPA2_API_KEY=dat-mot-chuoi-ngau-nhien-dai       # bắt buộc; thiếu thì /v1/* trả 503 (đóng, không mở công khai)
export CPA2_ROOT=../../CPA2_KhaoSat                    # mặc định đã đúng khi chạy trong repo
uvicorn cpa2_api.main:tao_app --factory --port 8000
python validate_api.py            # ~150 kiểm tra; --nhanh bỏ OCR ảnh thật (vài phút)
```

## Hợp đồng

Mọi phản hồi có `trang_thai` và `ket_luan`. **`ket_luan` chỉ khác `null` khi `trang_thai` là `ok` hoặc `ho_so_mau_thuan`.**
Lỗi kỹ thuật không bao giờ thành kết luận học vụ. **Mọi phản hồi không-ok có đủ `thong_bao` (chuỗi) và `chi_tiet` (danh sách)** — kể cả lỗi
của framework (400/404/405/413/422): một hình dạng để máy khách TypeScript xử lý bằng một nhánh. Mọi phản hồi có
`Cache-Control: no-store`. Xác thực được kiểm **trước** khi đọc body.

| `trang_thai` | HTTP | Ý nghĩa | `ket_luan` |
|---|---|---|---|
| `ok` | 200 | solver + chứng chỉ cho kết luận | `TRUE` `FALSE` `UNKNOWN` `DA_HOAN_THANH` |
| `ngoai_pham_vi` | 200 | câu hỏi chưa hỗ trợ: ngoài quy chế đã hình thức hoá, phản thực tế, hoặc loại câu chưa có lời giải đúng (**"còn thiếu môn gì", "còn thiếu bao nhiêu tín chỉ", "chứng chỉ nào miễn được môn nào"** — xem dưới). Không kèm chứng chỉ / nguồn | `null` |
| `hau_kiem_chan` | 200 | hậu kiểm chặn câu trả lời (trích nguồn/mã học phần sai). Không kèm chứng chỉ / nguồn / nội dung bị chặn | `null` |
| `ho_so_mau_thuan` | 200 | solver vô nghiệm | `MAU_THUAN` |
| `khong_ho_tro_ho_so` | 200 | không phải CNTT K49 | `null` |
| `loi_dau_vao` | 200 / 413 / 422 | hồ sơ/ảnh/yêu cầu sai; kèm `chi_tiet` (đường dẫn trường, **không** kèm giá trị) | `null` |
| `khong_xac_thuc` | 401 | thiếu hoặc sai `X-API-Key` | — |
| `loi_he_thong` | 500 / 503 | lỗi nội bộ (`ma_loi` để tra log) / chưa cấu hình khoá | `null` |
| `het_gio` | 504 | yêu cầu quá thời gian (advice 25s, lookup 10s, recommendations 25s, OCR 240s): tiến trình xử lý bị **giết** | `null` |
| `qua_tai` | 503 | mọi tiến trình xử lý đang bận quá 5s | `null` |

`UNKNOWN` là kết luận hợp lệ của hệ thống ba trị (thiếu dữ kiện → kèm `du_kien_thieu`, `can_bo_sung`), **khác** `ngoai_pham_vi` và
`loi_he_thong`. Hồ sơ tự mâu thuẫn (vd. điểm chữ ≠ điểm số) cho `UNKNOWN` kèm `mau_thuan` và câu hỏi bổ sung.

### `GET /health` (không cần khoá)
`{"trang_thai":"ok","dich_vu":"cpa2_api","phien_ban":"0.1.0","kb":{"r_formal":"v1.11","sha256":"…","ctdt":"cntt_k49"}}`

### `POST /v1/advice`
Yêu cầu: `{"ho_so": {…student_fact_schema…}, "cau_hoi": "em đủ điều kiện tốt nghiệp chưa?"}` (câu hỏi 1–500 ký tự; trường thừa bị từ chối).
Phản hồi: `trang_thai`, `ket_luan`, `claim`, `loi_giai` (tiếng Việt), `chung_chi` (các bước suy diễn: atom, rule_id, điều/khoản),
`nguon` (điều/khoản trích, đã hậu kiểm), `du_kien_thieu`, `can_bo_sung`, `mau_thuan`, `canh_bao`, `phien_ban_kb`.
Hỗ trợ (`trang_thai: ok`): `tot_nghiep`, `duoc_dang_ky("<mã>")`, `du_dk(lvtn|tltn)`, `xep_loai` / `hang_cuoi(...)`, `de_xuat`.
**Mọi `claim` khác là `ngoai_pham_vi`**: các ý định `thieu_bat_buoc`, `thieu_nhom`, `du_dk_xin_mien` của parser sinh claim KHÔNG đối số, không bao giờ có
trong answer set nên lõi (CLI) luôn trả FALSE sai (họ lỗi P18-1); API không biến nó thành kết luận. Ý định `de_xuat`: `ket_luan` TRUE/UNKNOWN nghĩa là
"có / không có đề xuất", **không phải** kết luận đúng-sai — giao diện không nên hiển thị như một phán quyết.

### `POST /v1/lookup`
`{"truy_van": "điều kiện tốt nghiệp", "k": 5}` (k 1–10) → `ket_qua`: danh sách điều/khoản (`id`, `van_ban`, `dia_chi`, `trang`, `noi_dung`, `diem`).

### `POST /v1/recommendations`
`{"ho_so": {…}, "hoc_ky": 1}` (1–3; 3 = học kỳ hè) → `dang_ky` (mỗi học phần kèm `chung_chi`), `tong_tc`, `can_xac_minh`,
`mau_thuan`. Chỉ đề xuất học phần hợp lệ trên **mọi** thế giới; chưa chắc thì vào `can_xac_minh`.

### `POST /v1/ocr` (multipart)
Trường `anh` (1–12 file PNG/JPEG, ≤ 8 MB và ≤ 25 triệu điểm ảnh mỗi file), tuỳ chọn `khai_bao` (JSON: `xac_nhan_ky_luat_sach`, `da_hoc_nam2`,
`tc_cong_nhan`, `khong_tinh_tich_luy`, `che_do_sv_chon_tich_luy`, `dtbchk_khai_bao`).
Khai báo kiểm kiểu và khoảng (sai → `loi_dau_vao`). Tổng điểm ảnh một yêu cầu ≤ 60 triệu; ảnh bị cắt dở bị từ chối. Trả `ho_so_nhap` là **bản nháp**: `da_xac_minh: false`, mỗi học phần có `confidence` và `ocr_raw`; `bao_cao` liệt kê học phần không chắc,
học kỳ lệch tổng, câu cần hỏi lại. **Không có `ket_luan`**: người dùng rà soát và sửa, rồi mới gọi `/v1/advice`.
Sửa tay không biến dữ kiện thành "đã xác minh".

## Bảo mật và giới hạn

- Khoá: `CPA2_API_KEY` (biến môi trường, so sánh thời gian hằng, không log). Thiếu khoá → `503` ở mọi `/v1/*`.
- Body: JSON ≤ 1 MB, OCR ≤ 40 MB (kể cả chunked) → `413`. Hồ sơ ≤ 400 học phần. Ảnh bị chặn theo số điểm ảnh *trước* khi giải nén.
- **Chống tiêm mã ASP** (review bảo mật): mã học phần, `ma_hp`, mục `khong_tinh_tich_luy` chỉ gồm chữ-số-`_` ≤ 20 ký tự; số khai báo phải là
  số nguyên thật trong khoảng; NaN / Infinity bị từ chối. Lớp thứ hai nằm ở `loader.py` (lõi dùng chung): sai dạng thì bỏ bản ghi và báo mâu thuẫn.
  Trước đây `X"). xac_nhan_ky_luat_sach. %` làm kết luận UNKNOWN thành TRUE, `#include` đọc file, và `b(1..20000)` làm solver chạy hàng chục giây.
- **Giới hạn thời gian cứng**: lõi chạy trong `CPA2_WORKERS` (mặc định 2) tiến trình con (`tien_trinh.py`, 'spawn'); quá giờ thì giết và dựng lại ở nền.
  Hồ sơ có > 3 bản ghi tự mâu thuẫn bị từ chối ngay (mỗi bản ghi mở 4 nhánh, thời gian solver ×4,5: 4 bản ghi ≈ 21 giây, 6 bản ghi > 100 giây).
  `so_worker = 0` chạy trong tiến trình (phát triển, test) và **không** có giới hạn thời gian.
- Hồ sơ vào lõi **chỉ ở dạng dict đã chuẩn hoá** (trường lạ và `meta` bị loại), không bao giờ là đường dẫn file.
- Log (stdout, INFO) chỉ có endpoint, trạng thái, thời gian, loại ngoại lệ. Không có hồ sơ, câu hỏi, khoá hay nội dung ngoại lệ.
- Các phản hồi 4xx **không phản hồi lại giá trị đầu vào** (kể cả tên trường thừa do người dùng đặt).
- Chạy bằng người dùng không đặc quyền trong Docker; khoá nằm trong biến môi trường của nơi chạy, không nằm trong image.

## Docker

`docker build -f services/cpa2_api/Dockerfile -t cpa2-api .` (từ gốc repo), chạy với `-e CPA2_API_KEY=…`. Cài từ `requirements.lock` (đủ phụ thuộc gián tiếp).
Có `.dockerignore` ở gốc repo (bộ dựng cũ không đọc `Dockerfile.dockerignore`).

⚠️ **Chưa build được image trong môi trường phát triển (không có Docker daemon).** Đã kiểm thay thế: dựng cây thư mục đúng theo các dòng
`COPY` của Dockerfile, cài venv sạch từ `requirements.lock` (Linux, Python 3.13), chạy `validate_api.py` và khởi động `uvicorn … --factory`
trên cây đó. Chưa kiểm: lệnh `apt-get` (gói `tesseract-ocr-vie`), `HEALTHCHECK`, quyền người dùng không đặc quyền khi chạy trong container,
và image gốc `python:3.13-slim` chưa ghim digest. Dự án dùng Python 3.14 nhưng image dùng 3.13 (clingo 5.8.2 có wheel cho 3.13).

## Chưa làm (các mốc sau)

- **Adapter AcademiQ → `student_fact_schema`**: cần mẫu dữ liệu / schema hồ sơ của niên luận (không có trong repo này).
- **Lõi sai với 3 ý định** (`thieu_bat_buoc`, `thieu_nhom`, `du_dk_xin_mien`): hiện API trả `ngoai_pham_vi`. Hỏi "miễn học phần nào" là tính năng nằm
  trong kế hoạch web nên cần hiện thực đúng ở lõi (lặp `du_dk_xin_mien("<mã>")` qua các học phần ngoại ngữ), không chỉ chặn.
- OCR đồng bộ trong một yêu cầu HTTP (mất vài chục giây đến vài phút cho bảng điểm nhiều trang); tác vụ có trạng thái chờ / đang xử lý /
  hoàn tất nằm ở Convex (Mốc 4).
- Chưa có lớp AI (parser/verbalizer LLM) — kết luận luôn do solver.
