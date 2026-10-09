# Tuần 11 — Proof Certificate (CPA2)

**Sản phẩm:** Proof Schema `Claim → Proof → Rule → Fact → Source`
**Tiêu chí hoàn thành:** Mỗi kết luận có trace ✅ — `validate_proof.py` 13/13 đạt

## Kết luận trước

> **Mọi con số/mã HP trong `explanation_vi` phải xuất hiện trong `certificate`, không khớp → chặn.** Bất biến này biến "chứng chỉ" từ lời hứa thành kiểm tra bằng máy. Tuần 11 đóng được tầng 3 (Solver) sang tầng 4 (Verbalizer) của kiến trúc 4 tầng Tuần 1.

## Chạy

```bash
pip install clingo
python validate_proof.py
python generate_certificate.py --claim tot_nghiep --student ../w7_student_facts/students/sv_lvtn.json
```

## File

| File | Vai trò |
|---|---|
| `proof_schema.json` | JSON Schema cho certificate (claim, verdict, proof.steps[], missing_facts, meta.qd_dien_giai) |
| `generate_certificate.py` | Sinh certificate từ claim + hồ sơ + KB (verdict TRUE/FALSE/UNKNOWN, why/2 → rule_src/5 → trích) |
| `validate_proof.py` | 5 nhóm: A bất biến, B TRUE, C FALSE (phản ví dụ), D UNKNOWN (missing_facts), E miễn/thay thế |
| `Tuan11_Proof_Certificate.md` | Báo cáo đầy đủ |

## Liên kết

- **R-Formal v1.5:** `rule_src/5` + `why/2` — mọi proof step đều có nguồn
- **W10 Graduation:** `tot_nghiep` + `thieu_dk/1` — dùng để test ba trị
- **W7-W9:** Student Facts + Elective + Exemption — proof cho cả T3/T5/T6
