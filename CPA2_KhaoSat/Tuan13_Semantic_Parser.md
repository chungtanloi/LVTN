# TUẦN 13 — SEMANTIC PARSER

**Giai đoạn:** LLM (Tuần 13/24) · **Mục tiêu:** LLM chuyển câu hỏi tiếng Việt thành formal query
**Sản phẩm:** Parser v1
**Tiêu chí hoàn thành:** Parse ≥80% test nội bộ ✅ — `w13_parser/validate_parser.py` 100% (20/20)

---

## 0. Kết luận trước

> **LLM ở CPA² bị cấm suy luận về sinh viên.** Nó chỉ được làm hai việc: dịch câu hỏi vào (Tuần 13) và diễn đạt chứng chỉ ra (Tuần 14). Tuần 13 đóng bằng hybrid: **template regex** cho 7 intent trọng tâm (đảm bảo ≥80% ngay cả khi không có LLM) + **LLM stub** (`llm_parse()` kiểm `OPENAI_API_KEY`, hiện fallback về template). Formal query là `claim` atom ASP (`tot_nghiep`, `du_dk_dang_ky("CT180")`, `du_dk_xin_mien("AV1")`) để Solver quyết định.

---

## 1. Tập intent — 7 câu hỏi trọng tâm (Tuan2 ma trận)

| Intent | Claim mẫu | Ví dụ tiếng Việt |
|---|---|---|
| `tot_nghiep` | `tot_nghiep` | "em đủ điều kiện tốt nghiệp chưa?" |
| `thieu_mon` | `thieu_bat_buoc` | "em còn thiếu môn gì?" |
| `thieu_tc` | `thieu_nhom` | "em còn thiếu bao nhiêu tín chỉ?" |
| `dang_ky` | `du_dk_dang_ky("CT180")` | "kỳ này em đăng ký CT180 được chưa?" |
| `du_dk_luan_van` | `du_dk_tc("CT550E")` | "em đủ điều kiện làm luận văn chưa?" |
| `mien` | `du_dk_xin_mien("AV1")` | "IELTS 5.5 miễn được môn nào?" |
| `counterfactual` | `counterfactual("CT177")` | "nếu em rớt CT177 thì trễ mấy kỳ?" |

Thứ tự ưu tiên regex: `counterfactual → mien → du_dk_luan_van → dang_ky → thieu_mon → thieu_tc → tot_nghiep` (cụ thể → chung) để câu *"còn thiếu môn gì để ra trường?"* không bị hút về `tot_nghiep`.

---

## 2. Thiết kế Parser v1

`w13_parser/parser.py` — 80 dòng:

```python
def template_parse(q):
    for intent in INTENTS_ordered:  # ưu tiên cụ thể
        if re.search(pattern, q.lower()): return intent
    # trích ma_hp, chung_chi
    m = MA_HP_RE.search(q)  # CT\d+E?
    if m: params["ma_hp"]=m.group(1).upper()
```

`llm_parse(q)` stub: nếu `OPENAI_API_KEY` tồn tại thì gọi LLM few-shot (prompt yêu cầu JSON `{intent, claim, params}`), không thì `None` → fallback template. Đây là van an toàn của Tuần 1 §7: nếu LLM yếu, parser vẫn hạ xuống template mà không thành điểm chặn.

---

## 3. Bộ test — 20 câu

Chạy: `python w13_parser/validate_parser.py`

```
[OK] em đủ điều kiện tốt nghiệp chưa?              → tot_nghiep
[OK] Em còn thiếu môn gì để ra trường?             → thieu_mon
[OK] Em còn thiếu bao nhiêu tín chỉ?               → thieu_tc
[OK] Kỳ này em đăng ký CT180 được chưa?            → dang_ky
[OK] Em đủ điều kiện làm luận văn tốt nghiệp chưa? → du_dk_luan_van
[OK] Chứng chỉ IELTS 5.5 của em miễn được môn nào? → mien
[OK] Nếu em rớt CT177 thì tốt nghiệp trễ mấy kỳ?   → counterfactual
... 20/20 = 100% (đạt ≥80%)
```

---

## 4. Tích hợp Prototype v1

`w12_integration/prototype.py` hiện dùng `PARSER_STUB` dict. Thay bằng:

```python
from w13_parser.parser import parse
formal = parse(question)["claim"]  # tot_nghiep / du_dk_dang_ky("CT180") ...
verdict, cert = solve(formal, student_facts)
```

Khi `confidence < 0.8` hoặc `intent` mơ hồ, Prototype trả `UNKNOWN` kèm *"câu hỏi chưa rõ, vui lòng nêu mã HP"* — đúng ngữ nghĩa ba trị.

---

## 5. Việc còn lại → Tuần 14

- [x] **RAG grounding:** kết nối retrieval với quy chế/CTĐT để LLM có ngữ cảnh khi dịch (ví dụ "môn tự chọn" → nhóm nào?) — ✅ đã xong: w14_rag (Tuần 14)
- [ ] Đánh giá parser trên **Q-Real** (400-600 câu thật, Tuần 1 Input Q) — hiện mới 20 câu nội bộ
- [ ] Đo **Verbalization Faithfulness** (RQ4) khi Verbalizer LLM hoạt động

---

### Ghi chú kiểm chứng

- [x] 7 intent phủ ma trận Tuần 2
- [x] 20 câu test nội bộ 100% ≥80%
- [x] Hybrid template + LLM stub (không thành điểm chặn)
- [ ] Chưa có LLM thật (cần API key), chưa test trên Q-Real
