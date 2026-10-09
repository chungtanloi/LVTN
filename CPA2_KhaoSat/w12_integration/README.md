# Tuần 12 — Tích hợp Solver + Proof (CPA2)

**Sản phẩm:** Prototype v1 — `⟨ verdict, certificate, explanation_vi, missing_facts ⟩` end-to-end
**Tiêu chí hoàn thành:** Answer đi kèm proof ✅ — `validate_integration.py` 11/11 đạt

## Chạy

```bash
pip install clingo
python prototype.py --demo
python validate_integration.py
python prototype.py --student ../w7_student_facts/students/sv_lvtn.json --question "em đủ điều kiện tốt nghiệp chưa?"
```

## File

| File | Vai trò |
|---|---|
| `prototype.py` | 4 tầng: Parser stub → KB (R-Formal+Curriculum+Elective+Exemption+Graduation) → Solver (clingo ba trị) → Verbalizer template + hậu kiểm |
| `validate_integration.py` | 4 nhóm: A TRUE · B FALSE · C UNKNOWN · D hậu kiểm |
| `Tuan12_Tich_hop_Solver_Proof.md` | Báo cáo đầy đủ |

## Bất biến

> **Mọi số/mã HP trong `explanation_vi` phải xuất hiện trong `certificate`, không khớp → chặn.** Đây là van an toàn cho RQ4 (Verbalization Faithfulness).

## Liên kết

- **W11 Proof:** `proof_schema.json` + `why/2 → rule_src/5` — mọi step có nguồn
- **W7-W10:** Student Facts + Elective + Exemption + Graduation — prototype nối tất cả
