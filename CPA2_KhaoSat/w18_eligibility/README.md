# Tuần 18 — Eligibility engine (CPA2)

**Sản phẩm:** Eligibility module v1 — đủ điều kiện làm luận văn / tiểu luận / niên luận / niên luận cơ sở / thực tập / tích lũy TC thay LVTN / học phần thay thế
**Tiêu chí hoàn thành:** Eligible / Not Eligible / Unknown ✅ — `validate_eligibility.py` ĐẠT 36/36 (xem `../Tuan18_Eligibility.md`)

## Chạy

```bash
python validate_eligibility.py
python eligibility.py --student ../w7_student_facts/students/sv_lvtn.json --doi-tuong lvtn
python eligibility.py --student ... --doi-tuong thay_the:ML014
```

## File

| File | Vai trò |
|---|---|
| `eligibility.lp` | Quy tắc: đối tượng ↔ HP CTĐT, tiên quyết (R-A03), điều kiện do đơn vị đào tạo (R-F04, dữ kiện ngoài), tích lũy TC (R-F05), thay thế (R-M13), đã hoàn thành |
| `eligibility.py` | `xet(hồ sơ, đối tượng)` → ELIGIBLE / NOT_ELIGIBLE / UNKNOWN / DA_HOAN_THANH / MAU_THUAN + lý do + chứng chỉ + câu hỏi bổ sung |
| `validate_eligibility.py` | 36 kiểm tra, gold viết tay trước khi cài đặt |

## Bất biến

> **Đủ tín chỉ ≠ đủ điều kiện.** QĐ3266 Đ31 giao điều kiện nhận đề tài LVTN/TLTN cho đơn vị đào tạo; nội dung không có trong quy chế → hệ thống không bịa, chỉ nhận **kết quả xét** của đơn vị (`hinh_thuc_cuoi_khoa`). Chưa biết → UNKNOWN + hỏi.
