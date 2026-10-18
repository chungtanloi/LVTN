# w19_recommendation — Recommendation v1 (Tuần 19)

Chỉ đề xuất phương án **đã chứng minh hợp lệ trên mọi thế giới** (ba trị Tuần 16). Hợp lệ chưa chắc → `can_xac_minh`, không đề xuất.

```bash
python recommendation.py --student ../w7_student_facts/students/sv_lvtn.json --hk 1
python validate_recommendation.py      # gold viết tay trước khi cài đặt
```

| Đầu ra | Nội dung | Nguồn |
|---|---|---|
| `dang_ky` | HP đăng ký HK `hk` ∈ {1,2,3}, tổng ≤ 20 TC, mỗi HP có chứng chỉ `du_dk_dang_ky` | R-A03 (Đ7 k4), R-C01 (Đ14 k1), lịch mở HK của CTĐT |
| `can_xac_minh` | HP có thể cần nhưng tiên quyết/tích lũy/nhóm chưa chắc; Eligibility UNKNOWN | engine w16 |
| `hinh_thuc_tot_nghiep` | LVTN/TLTN/tích lũy TC mà Eligibility trả ELIGIBLE | w18, QD-12 |
| `xin_mien` | đủ điều kiện **nộp đơn** xin miễn (chưa phải đã miễn), chỉ HP còn cần | R-M06/R-M16, QD-11 |
| `thay_the` | HP được công nhận thay thế (Eligibility ELIGIBLE) | R-M13 (QĐ5339 Đ3 k9) |
| `khong_du_song_hanh` | HP chưa học HP song hành và không thể học cùng kỳ → không đề xuất | R-A04 (QĐ3266 Đ7 k5) |

**Ràng buộc** (`recommendation.lp`): ≤ 20 TC; nhóm một nhánh chỉ một nhánh (đã bắt đầu nhánh nào thì giữ nhánh đó); không cùng lúc LVTN + TLTN; không chọn HP thừa trong nhóm; HP song hành phải đã học (có bản ghi điểm, kể cả F; không tính W) hoặc chọn cùng kỳ (Đ7 k5 — QD-13 đã rút). **Ưu tiên** là CHÍNH SÁCH tư vấn, không phải quy chế: TC bắt buộc @5 → số HP mở khóa @4 → TC lấp nhóm @2 → tổng TC @1. Sau khi chọn, phương án được kiểm lại tường minh (không dùng `assert`).

Prototype (w12): câu "kỳ này em (có) nên đăng ký gì", "học kì 2 …", "HK III …", "học hè …" → `claim = de_xuat`; "học kỳ 4" → hỏi lại.
