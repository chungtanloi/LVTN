# Tuần 13 — Semantic Parser (CPA2)

**Sản phẩm:** Parser v1 — Q tiếng Việt → formal query
**Tiêu chí hoàn thành:** Parse ≥80% test nội bộ ✅ — `validate_parser.py` 100% (20/20)

## Kết luận trước

> **Parser là tầng duy nhất được phép dùng LLM, và bị cấm suy luận về SV.** Nó chỉ dịch câu hỏi thành `claim` (vd `tot_nghiep`, `du_dk_dang_ky("CT180")`) để Solver quyết định. Tuần 13 đóng bằng hybrid: **template regex ưu tiên cụ thể→chung** (đảm bảo ≥80% trên 7 intent), `llm_parse()` stub sẵn sàng cho Tuần 14 khi có `OPENAI_API_KEY`.

## Chạy

```bash
python parser.py --question "em đủ điều kiện tốt nghiệp chưa?"
python parser.py --test
python validate_parser.py
```

## Formal query

```json
{"intent": "dang_ky", "claim": "du_dk_dang_ky(\"CT180\")", "params": {"ma_hp": "CT180"}, "confidence": 1.0, "method": "template"}
```

7 intent (Tuan2 ma trận): `tot_nghiep, thieu_mon, thieu_tc, dang_ky, du_dk_luan_van, mien, counterfactual`

## Liên kết

- **W12 Prototype:** thay `PARSER_STUB` bằng `parser.parse()`
- **W1 Kiến trúc 4 tầng:** tầng 1 chỉ dịch, không suy luận
