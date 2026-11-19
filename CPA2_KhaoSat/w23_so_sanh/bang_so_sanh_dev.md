# So sánh CPA² vs baseline — split dev

Tập ca chung của các hệ CHÍNH THỨC: **78/78** ca được chấm (G-Truth + OCR-Noise). Hệ không chính thức chấm trên phần giao của tập này với ca của nó (xem cột n).

## Nhóm `tong`

| Hệ | n | Soundness | unsound | Coverage | Selective Acc | đúng gold | từ chối thừa | hỏi đúng | LOI | nhãn thiếu | USD | model |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CPA² | 78 | 92.3% | 6 | 78.2% | 90.2% | 67 | 5 | 1/1 | 0 | 0 | 0.0000 | clingo (CPA²) |
| CPA² [_sau_A17] [không chính thức] | 78 | 100.0% | 0 | 71.8% | 100.0% | 70 | 8 | 1/1 | 0 | 0 | 0.0000 | clingo (CPA²) |
| b1_openai | 78 | 100.0% | 0 | 3.8% | 100.0% | 17 | 61 | — | 0 | 0 | 0.5352 | openai/gpt-6.1-sol qua openrouter |
| b1_gemini | 78 | 79.5% | 16 | 55.1% | 62.8% | 38 | 24 | — | 0 | 0 | 0.6644 | google/gemini-4-argon qua openrouter |
| b2_openai | 78 | 98.7% | 1 | 10.3% | 87.5% | 21 | 56 | — | 0 | 0 | 0.7545 | openai/gpt-6.1-sol qua openrouter |
| b2_gemini | 78 | 93.6% | 5 | 29.5% | 78.3% | 29 | 44 | — | 0 | 0 | 0.8732 | google/gemini-4-argon qua openrouter |
| b3_openai | 78 | 89.7% | 8 | 44.9% | 77.1% | 38 | 32 | — | 0 | 1 | 2.1922 | openai/gpt-6.1-sol qua openrouter |
| b3_gemini | 78 | 85.9% | 11 | 53.8% | 73.8% | 38 | 29 | — | 0 | 9 | 2.3502 | google/gemini-4-argon qua openrouter |

## Nhóm `[cau_hoi_ro]`

| Hệ | n | Soundness | unsound | Coverage | Selective Acc | đúng gold | từ chối thừa | hỏi đúng | LOI | nhãn thiếu | USD | model |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CPA² | 49 | 93.9% | 3 | 77.6% | 92.1% | 43 | 3 | 1/1 | 0 | 0 | 0.0000 | clingo (CPA²) |
| CPA² [_sau_A17] [không chính thức] | 49 | 100.0% | 0 | 63.3% | 100.0% | 41 | 8 | 1/1 | 0 | 0 | 0.0000 | clingo (CPA²) |
| b1_openai | 49 | 100.0% | 0 | 2.0% | 100.0% | 11 | 38 | — | 0 | 0 | 0.5352 | openai/gpt-6.1-sol qua openrouter |
| b1_gemini | 49 | 77.6% | 11 | 65.3% | 65.6% | 29 | 9 | — | 0 | 0 | 0.6644 | google/gemini-4-argon qua openrouter |
| b2_openai | 49 | 98.0% | 1 | 10.2% | 80.0% | 14 | 34 | — | 0 | 0 | 0.7545 | openai/gpt-6.1-sol qua openrouter |
| b2_gemini | 49 | 95.9% | 2 | 30.6% | 86.7% | 22 | 25 | — | 0 | 0 | 0.8732 | google/gemini-4-argon qua openrouter |
| b3_openai | 49 | 95.9% | 2 | 46.9% | 91.3% | 30 | 17 | — | 0 | 0 | 2.1922 | openai/gpt-6.1-sol qua openrouter |
| b3_gemini | 49 | 89.8% | 5 | 57.1% | 82.1% | 28 | 16 | — | 0 | 9 | 2.3502 | google/gemini-4-argon qua openrouter |

## Nhóm `[quy_che]`

| Hệ | n | Soundness | unsound | Coverage | Selective Acc | đúng gold | từ chối thừa | hỏi đúng | LOI | nhãn thiếu | USD | model |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CPA² | 65 | 93.8% | 4 | 90.8% | 93.2% | 56 | 5 | 1/1 | 0 | 0 | 0.0000 | clingo (CPA²) |
| CPA² [_sau_A17] [không chính thức] | 65 | 100.0% | 0 | 86.2% | 100.0% | 57 | 8 | 1/1 | 0 | 0 | 0.0000 | clingo (CPA²) |
| b1_openai | 65 | 100.0% | 0 | 4.6% | 100.0% | 4 | 61 | — | 0 | 0 | 0.5352 | openai/gpt-6.1-sol qua openrouter |
| b1_gemini | 65 | 80.0% | 13 | 61.5% | 67.5% | 28 | 24 | — | 0 | 0 | 0.6644 | google/gemini-4-argon qua openrouter |
| b2_openai | 65 | 98.5% | 1 | 12.3% | 87.5% | 8 | 56 | — | 0 | 0 | 0.7545 | openai/gpt-6.1-sol qua openrouter |
| b2_gemini | 65 | 96.9% | 2 | 30.8% | 90.0% | 19 | 44 | — | 0 | 0 | 0.8732 | google/gemini-4-argon qua openrouter |
| b3_openai | 65 | 92.3% | 5 | 49.2% | 84.4% | 28 | 32 | — | 0 | 1 | 2.1922 | openai/gpt-6.1-sol qua openrouter |
| b3_gemini | 65 | 93.8% | 4 | 53.8% | 88.6% | 32 | 29 | — | 0 | 9 | 2.3502 | google/gemini-4-argon qua openrouter |

## Nhóm `[thiet_ke]`

| Hệ | n | Soundness | unsound | Coverage | Selective Acc | đúng gold | từ chối thừa | hỏi đúng | LOI | nhãn thiếu | USD | model |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CPA² | 13 | 84.6% | 2 | 15.4% | 0.0% | 11 | 0 | — | 0 | 0 | 0.0000 | clingo (CPA²) |
| CPA² [_sau_A17] [không chính thức] | 13 | 100.0% | 0 | 0.0% | — | 13 | 0 | — | 0 | 0 | 0.0000 | clingo (CPA²) |
| b1_openai | 13 | 100.0% | 0 | 0.0% | — | 13 | 0 | — | 0 | 0 | 0.5352 | openai/gpt-6.1-sol qua openrouter |
| b1_gemini | 13 | 76.9% | 3 | 23.1% | 0.0% | 10 | 0 | — | 0 | 0 | 0.6644 | google/gemini-4-argon qua openrouter |
| b2_openai | 13 | 100.0% | 0 | 0.0% | — | 13 | 0 | — | 0 | 0 | 0.7545 | openai/gpt-6.1-sol qua openrouter |
| b2_gemini | 13 | 76.9% | 3 | 23.1% | 0.0% | 10 | 0 | — | 0 | 0 | 0.8732 | google/gemini-4-argon qua openrouter |
| b3_openai | 13 | 76.9% | 3 | 23.1% | 0.0% | 10 | 0 | — | 0 | 0 | 2.1922 | openai/gpt-6.1-sol qua openrouter |
| b3_gemini | 13 | 46.2% | 7 | 53.8% | 0.0% | 6 | 0 | — | 0 | 0 | 2.3502 | google/gemini-4-argon qua openrouter |

## Nhóm `[theo errata]`

| Hệ | n | Soundness | unsound | Coverage | Selective Acc | đúng gold | từ chối thừa | hỏi đúng | LOI | nhãn thiếu | USD | model |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CPA² | 78 | 91.0% | 7 | 78.2% | 88.5% | 66 | 5 | 1/1 | 0 | 0 | 0.0000 | clingo (CPA²) |
| CPA² [_sau_A17] [không chính thức] | 78 | 100.0% | 0 | 71.8% | 100.0% | 71 | 7 | 1/1 | 0 | 0 | 0.0000 | clingo (CPA²) |
| b1_openai | 78 | 100.0% | 0 | 3.8% | 100.0% | 18 | 60 | — | 0 | 0 | 0.5352 | openai/gpt-6.1-sol qua openrouter |
| b1_gemini | 78 | 79.5% | 16 | 55.1% | 62.8% | 38 | 24 | — | 0 | 0 | 0.6644 | google/gemini-4-argon qua openrouter |
| b2_openai | 78 | 98.7% | 1 | 10.3% | 87.5% | 22 | 55 | — | 0 | 0 | 0.7545 | openai/gpt-6.1-sol qua openrouter |
| b2_gemini | 78 | 93.6% | 5 | 29.5% | 78.3% | 29 | 44 | — | 0 | 0 | 0.8732 | google/gemini-4-argon qua openrouter |
| b3_openai | 78 | 88.5% | 9 | 44.9% | 74.3% | 37 | 32 | — | 0 | 1 | 2.1922 | openai/gpt-6.1-sol qua openrouter |
| b3_gemini | 78 | 85.9% | 11 | 53.8% | 73.8% | 39 | 28 | — | 0 | 9 | 2.3502 | google/gemini-4-argon qua openrouter |

## McNemar chính xác (CPA² vs baseline, cặp bất đồng)

b = ca CPA² kém hơn, c = ca CPA² tốt hơn. Tập nhỏ: p lớn không chứng minh hai hệ như nhau.

| Baseline | n cặp | đúng gold (b / c / p) | không unsound (b / c / p) |
|---|---|---|---|
| b1_openai | 78 | 3 / 53 / 0.0000 | 6 / 0 / 0.0312 |
| b1_gemini | 78 | 7 / 36 / 0.0000 | 6 / 16 / 0.0525 |
| b2_openai | 78 | 3 / 49 / 0.0000 | 6 / 1 / 0.1250 |
| b2_gemini | 78 | 7 / 45 / 0.0000 | 6 / 5 / 1.0000 |
| b3_openai | 78 | 5 / 34 / 0.0000 | 6 / 8 / 0.7905 |
| b3_gemini | 78 | 8 / 37 / 0.0000 | 5 / 10 / 0.3018 |

## Ca bất đồng (đầu vào phân tích ca sai)

- **b1_openai** — CPA² đúng / baseline unsound (0): —; baseline đúng / CPA² unsound (2): NL-06, NL-10
- **b1_gemini** — CPA² đúng / baseline unsound (15): DK-05, DK-14, DK-19, EL-01, EL-02, HG-03, NL-02, ON-02M4, ON-06M4, ON-10M4, RC-02, RC-05, RC-06, RC-09, TN-10; baseline đúng / CPA² unsound (3): NL-06, NL-10, NL-11
- **b2_openai** — CPA² đúng / baseline unsound (1): EL-09; baseline đúng / CPA² unsound (2): NL-06, NL-10
- **b2_gemini** — CPA² đúng / baseline unsound (5): HG-03, ON-06M3, ON-06M4, ON-10M4, RC-09; baseline đúng / CPA² unsound (4): HG-01, NL-06, NL-10, NL-11
- **b3_openai** — CPA² đúng / baseline unsound (8): DK-16, ON-05M4, ON-06M4, ON-10M4, RC-02, RC-04, RC-05, RC-06; baseline đúng / CPA² unsound (3): NL-06, NL-10, NL-11
- **b3_gemini** — CPA² đúng / baseline unsound (10): ON-02M3, ON-02M4, ON-05M4, ON-06M4, ON-09M4, ON-10M4, RC-02, RC-04, RC-05, RC-06; baseline đúng / CPA² unsound (5): HG-01, HG-05, HG-07, NL-06, NL-11
