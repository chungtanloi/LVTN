# TUẦN 12 — TÍCH HỢP SOLVER + PROOF

**Giai đoạn:** Proof (Tuần 12/24) · **Mục tiêu:** Kết nối solver với proof engine
**Sản phẩm:** Prototype v1
**Tiêu chí hoàn thành:** Answer đi kèm proof ✅ — `w12_integration/validate_integration.py` 11/11 đạt

---

## 0. Kết luận trước

> **Prototype v1 là mạch kín đầu tiên từ câu hỏi tiếng Việt tới chứng chỉ có thể kiểm bằng máy.** `Q: "em đủ điều kiện tốt nghiệp chưa?" + hồ sơ sv_lvtn (161 TC)` → `TRUE` + 20 steps `why(...,r_a02/r_f01a)` + `explanation_vi`; `sv_tron_ngoai_ngu (trộn AV/PV)` → `FALSE` + phản ví dụ `thieu_nhom`; `thiếu điểm CT550E (2 thế giới)` → `UNKNOWN` + `missing_facts: g10("CT550E")`. Mọi `explanation_vi` qua **hậu kiểm**: quét mã HP/số, không có trong `certificate` → chặn — đây là van an toàn cho RQ4 trước khi có LLM Verbalizer thật (Tuần 14).

---

## 1. Kiến trúc Prototype v1 — 4 tầng (Tuần 1 §3)

```
Q tiếng Việt ──► [1] Parser stub ──► claim (tot_nghiep)
                         │
               [2] KB hình thức (R-Formal 71 đơn vị + CTĐT 78 dòng + Elective + Exemption + Graduation)
                         │
               [3] Solver (clingo ba trị) ──► verdict TRUE/FALSE/UNKNOWN + models
                         │
               [4] Verbalizer template + HẬU KIỂM ──► explanation_vi (mọi mã/số phải có trong certificate)
                         │
               ⟨ verdict, certificate, explanation_vi, missing_facts ⟩
```

- **Tầng 1:** stub `PARSER_STUB` map 7 câu hỏi trọng tâm (Tuan2 ma trận) → claim (`tot_nghiep`, `du_dk_xin_mien`...). Tuần 13 sẽ thay bằng LLM Semantic Parser.
- **Tầng 2+3:** nạp toàn bộ KB (53 quy tắc ASP + 78 dòng CTĐT + 5 nhóm + T5/T6 + Graduation) và chạy `solve_verdict` (cautious/brave) như Tuần 4 §2.
- **Tầng 4:** template `TRUE/FALSE/UNKNOWN` + hậu kiểm regex `CT\d+E?` và số — chặn nếu không khớp (Tuần 1 bất biến).

---

## 2. Ba luồng end-to-end

| Hồ sơ | Câu hỏi | Verdict | Certificate | Explanation |
|---|---|---|---|---|
| `sv_lvtn` (161 TC LVTN) | "em đủ điều kiện tốt nghiệp chưa?" | **TRUE** | 20 steps (`dat_nhom`, `dk_*`, `why(...,r_a02)`) | "đủ mọi điều kiện..." |
| `sv_tron_ngoai_ngu` (AV 4+PV 7) | "em đủ điều kiện tốt nghiệp chưa?" | **FALSE** | phản ví dụ `thieu_nhom(g_ngoai_ngu)` + `why(...,r_a02)` | "thiếu..." |
| thiếu `CT550E` (2 thế giới) | `tot_nghiep` | **UNKNOWN** | `missing_facts: g10("CT550E",80/30)` = `brave\cautious` | "Thiếu dữ kiện: g10..." |

---

## 3. Bộ test — 11 ca

### A. TRUE (4 ca)

| Ca | Kiểm tra |
|---|---|
| A1 | verdict TRUE |
| A2 | certificate có steps |
| A3 | explanation chứa claim |
| A4 | không có missing_facts |

### B. FALSE (3 ca)

| Ca | Kiểm tra |
|---|---|
| B1 | verdict FALSE |
| B2 | certificate có steps (phản ví dụ) |
| B3 | explanation đề cập thiếu |

### C. UNKNOWN (4 ca)

| Ca | Kiểm tra |
|---|---|
| C1 | verdict UNKNOWN |
| C2 | missing_facts chứa `CT550E` |
| C3 | hậu kiểm không chặn |
| C4 | explanation đề cập missing |

### D. Hậu kiểm (2 ca)

| Ca | Kiểm tra |
|---|---|
| D1 | mã lạ `CT999` không trong certificate → chặn |
| D2 | case thật không bị chặn |

---

## 4. Kết quả

```
A. TRUE — 4/4 đạt
B. FALSE — 3/3 đạt
C. UNKNOWN — 4/4 đạt
D. Hậu kiểm — 2/2 đạt
KẾT LUẬN: ĐẠT — Prototype v1 trả lời kèm proof và hậu kiểm
```

Không hồi quy: `w5` 39/39 · `w6` 31/31 · `w7` 5/5 · `w8` 29/29 · `w9` 22/22 · `w10` 19/19 · `w11` 13/13.

---

## 5. Việc còn lại → Tuần 13

- [ ] **Semantic Parser (LLM):** thay stub bằng LLM dịch tiếng Việt → formal query (`?X : Requires(SV,X) ∧ ¬Completed(SV,X)`)
- [x] RAG grounding (Tuần 14) — truy hồi quy chế/CTĐT cho parser — ✅ đã xong: w14_rag (Tuần 14)
- [ ] Verbalizer LLM thật + đo Faithfulness (RQ4)

---

### Ghi chú kiểm chứng

- [x] End-to-end từ Q tiếng Việt (stub) tới `⟨ verdict, certificate, explanation_vi, missing_facts ⟩`
- [x] Ba trị có proof khác nhau (TRUE proof, FALSE phản ví dụ, UNKNOWN missing_facts)
- [x] Hậu kiểm chặn mọi số/mã không có trong certificate
- [ ] Parser/Verbalizer LLM thật chưa có (Tuần 13-14)
