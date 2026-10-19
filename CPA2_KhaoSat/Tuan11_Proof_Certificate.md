# TUẦN 11 — PROOF CERTIFICATE

**Giai đoạn:** Proof (Tuần 11/24) · **Mục tiêu:** Thiết kế Claim → Proof → Rule → Fact → Source
**Sản phẩm:** Proof schema
**Tiêu chí hoàn thành:** Mỗi kết luận có trace ✅ — `w11_proof/validate_proof.py` 13/13 đạt

---

## 0. Kết luận trước

> **Chứng chỉ là dẫn xuất kiểm được bằng máy, không phải đoạn văn giải thích.** Với `TRUE` kèm `why(tot_nghiep,r_f01a)` và `why(du_dk_hoc_vu,r_f01a)` truy về QĐ3266 Điều 32 k.1a; với `FALSE` kèm phản ví dụ `thieu_nhom(g_tot_nghiep,15)` truy về Điều 7 k.3; với `UNKNOWN` kèm `missing_facts = brave \ cautious` (ví dụ `g10("CT550E")`). Bất biến bắt buộc (Tuần 1 §2.2): mọi số/mã HP trong `explanation_vi` phải xuất hiện trong `certificate`.

---

## 1. Lược đồ Claim → Proof → Rule → Fact → Source

```json
{
  "claim": "tot_nghiep",
  "verdict": "TRUE|FALSE|UNKNOWN",
  "proof": { "steps": [ { "atom": "du_dk_hoc_vu", "rule_id": "r_f01a",
             "source": { "van_ban": "qd3266", "dieu": 32, "khoan": 1, "diem": "a",
                         "trich": "Tích lũy đủ các học phần ..." },
             "facts": ["tich_luy(CT550E)", "tc_tich_luy(161)"] } ] },
  "missing_facts": ["g10(\"CT550E\",80)"],
  "meta": { "qd_dien_giai": ["qd09"] }
}
```

- **Claim:** atom ASP được hỏi
- **Proof:** danh sách `why(atom, rule_id)` trong answer set đại diện, mỗi `rule_id` có `rule_src/5` và `trich` trong `r_formal_v1.json`
- **Rule → Source:** `rule_src(RuleId, VanBan, Dieu, Khoan, Diem)` → trích nguyên văn (đã đối chiếu ảnh)
- **Fact:** `g10/2, tich_luy/1, duoc_mien/1...` — dữ kiện sinh viên (Student Facts Tuần 7)
- **missing_facts:** khi `UNKNOWN`, `brave \ cautious` — chính là dữ kiện cần hỏi tiếp (Tuần 16 Abstention)

Quy tắc diễn giải (QD/CQ) phát kèm `dien_giai(qd09/qd03/cq05/cq06)` để Verbalizer phải ghi rõ *"kết luận này dựa trên quyết định diễn giải, không phải câu chữ trực tiếp"* (yêu cầu Tuần 5 v1.2 §9.3).

---

## 2. Bộ test — 13 ca

### A. Bất biến (2 ca)

| Ca | Kiểm tra |
|---|---|
| A1 | mọi `why/2` (41) có `rule_src/5` (54) |
| A2 | mọi `why` có bản ghi JSON |

### B. TRUE — có proof đầy đủ (4 ca)

| Ca | Claim | Verdict | Trace |
|---|---|---|---|
| B1 | `tot_nghiep` đủ 161 LVTN | TRUE | `why(tot_nghiep,r_f01a)` |
| B2 | `du_dk_hoc_vu` | why | |
| B4 | không có `thieu_dk` | | |

### C. FALSE — có phản ví dụ (3 ca)

| Ca | Claim | Phản ví dụ | Nguồn |
|---|---|---|---|
| C1 | `tot_nghiep` thiếu nhóm | FALSE | |
| C2 | `thieu_nhom(g_tot_nghiep,15)` | Điều 7 k.3 |
| C3 | `why(thieu_nhom...,r_a02)` | | |

### D. UNKNOWN — có missing_facts (3 ca)

| Ca | Claim | missing_facts |
|---|---|---|
| D1 | `tot_nghiep` thiếu điểm LVTN (2 thế giới) | UNKNOWN |
| D2 | `brave\cautious` chứa `CT550E` | |
| D3 | `tot_nghiep` không cautious | |

### E. Miễn/thay thế (1 ca)

| Ca | Claim | Nguồn |
|---|---|---|
| E1 | `exempted_m(AV1)` | `why(...,r_m15)` Đ3 k.11 |

---

## 3. Kết quả

```
A. Bất biến — 2/2 đạt
B. TRUE — 4/4 đạt
C. FALSE — 3/3 đạt
D. UNKNOWN — 3/3 đạt
E. Miễn/thay thế — 1/1 đạt
KẾT LUẬN: ĐẠT — Mỗi kết luận có trace Claim→Proof→Rule→Fact→Source
```

`generate_certificate.py` đã chạy demo: `sv_lvtn.json` → `tot_nghiep TRUE` với ~10 steps `dat_nhom/why` truy về `r_a02/r_f01a`.

---

## 4. Việc còn lại → Tuần 12

- [x] **Tích hợp Solver + Proof (Prototype v1):** nối 4 tầng (Parser → KB → Solver → Verbalizer + hậu kiểm), trả về `⟨ verdict, certificate, explanation_vi, missing_facts ⟩` end-to-end — ✅ đã xong: w12_integration (Tuần 12)
- [x] Hậu kiểm `explanation_vi`: chặn mọi số/mã không có trong `certificate` — ✅ đã xong: w12 prototype.verbalize + validate_integration D
- [ ] Đo `Counterfactual Optimality Gap` cho RQ3 (T3 lập kế hoạch)

---

### Ghi chú kiểm chứng

- [x] Bất biến `why/2 → rule_src/5 → JSON` kiểm bằng máy (A1-A2)
- [x] Ba trị có trace khác nhau (TRUE có proof, FALSE có phản ví dụ, UNKNOWN có missing_facts)
- [x] QD/CQ phát `dien_giai` để Verbalizer ghi nguồn diễn giải
- [ ] Chưa có Verbalizer LLM (Tuần 14)
