# Tuần 15 — OCR bảng điểm (CPA2)

**Sản phẩm:** OCR pipeline v1: ảnh bảng điểm ĐHCT (Mẫu In D5050A0) → hồ sơ `student_fact_schema` có `confidence` + `ocr_raw`
**Tiêu chí hoàn thành:** Có fact + confidence ✅ — `validate_ocr.py` ĐẠT (xem `../Tuan15_OCR_Bang_Diem.md`)

## Chạy

```bash
# cần Tesseract 5 + gói 'vie' (mặc định C:/Program Files/Tesseract-OCR; đổi bằng biến TESSERACT_EXE)
python validate_ocr.py --nhanh      # ~2 phút: A, C, E + bảng điểm tổng hợp sạch
python validate_ocr.py              # ~6 phút: thêm biến thể mờ/JPEG, nghiêng, bảng điểm thật (nếu có ở máy)
python render_transcript.py ../w7_student_facts/students/sv_lvtn.json   # xem ảnh tổng hợp → _anh/
python ocr_transcript.py trang1.png trang2.png                           # OCR ảnh bất kỳ → báo cáo
```

## File

| File | Vai trò |
|---|---|
| `render_transcript.py` | Vẽ bảng điểm tổng hợp từ hồ sơ Tuần 7 (đáp án tuyệt đối) + biến thể nhiễu |
| `ocr_transcript.py` | Dựng thẳng → OCR lượt chính (vie) + OCR từng dải cột (whitelist) → chuẩn hoá → kiểm chéo → hồ sơ |
| `validate_ocr.py` | A chuẩn hoá · B tổng hợp × nhiễu · C tiêm lỗi · E hồi quy review · D bảng điểm thật (không commit) |
| `validate_output.txt` | Kết quả lần chạy đầy đủ gần nhất |
| `_rieng/`, `_anh/` | gitignore — kết quả bảng điểm thật (dữ liệu cá nhân) và ảnh sinh lại được |

## Bất biến

> **Không chắc ≠ sai.** Fact chỉ vào hồ sơ khi qua kiểm chéo (mã ∈ CTĐT, TC khớp CTĐT, điểm chữ khớp T.Hợp theo R-B02, tổng TC học kỳ, ĐTBCHK) và confidence ≥ τ = 0,70. HP đọc được mã nhưng không chắc điểm → solver xét F/D/A. Học kỳ lệch tổng TC hoặc dòng không đọc được → UNKNOWN. Pipeline không bao giờ biến "OCR bỏ sót" thành "sinh viên thiếu môn".
