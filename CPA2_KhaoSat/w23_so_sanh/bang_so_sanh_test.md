# So sánh CPA² vs baseline — split test

Tập ca chung của các hệ CHÍNH THỨC: **76/76** ca được chấm (G-Truth + OCR-Noise). Hệ không chính thức chấm trên phần giao của tập này với ca của nó (xem cột n).

## Nhóm `tong`

| Hệ | n | Soundness | unsound | Coverage | Selective Acc | đúng gold | từ chối thừa | hỏi đúng | LOI | nhãn thiếu | USD | model |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CPA² | 76 | 93.4% | 5 | 63.2% | 89.6% | 58 | 13 | 3/3 | 0 | 0 | 0.0000 | clingo (CPA²) |
| CPA² [_sau_A17] [không chính thức] | 76 | 100.0% | 0 | 61.8% | 100.0% | 63 | 13 | 3/3 | 0 | 0 | 0.0000 | clingo (CPA²) |
| b1_openai | 76 | 100.0% | 0 | 3.9% | 100.0% | 19 | 57 | — | 0 | 0 | 0.5350 | openai/gpt-6.1-sol qua openrouter |
| b1_gemini | 76 | 80.3% | 15 | 47.4% | 58.3% | 36 | 25 | — | 0 | 0 | 0.6651 | google/gemini-4-argon qua openrouter |
| b2_openai | 76 | 100.0% | 0 | 10.5% | 100.0% | 24 | 52 | — | 0 | 0 | 0.7534 | openai/gpt-6.1-sol qua openrouter |
| b2_gemini | 76 | 94.7% | 4 | 22.4% | 76.5% | 28 | 44 | — | 0 | 0 | 0.8975 | google/gemini-4-argon qua openrouter |
| b3_openai | 76 | 94.7% | 4 | 30.3% | 82.6% | 34 | 38 | — | 0 | 6 | 1.9913 | openai/gpt-6.1-sol qua openrouter |
| b3_gemini | 76 | 89.5% | 8 | 52.6% | 80.0% | 44 | 24 | — | 0 | 7 | 2.4357 | google/gemini-4-argon qua openrouter |

## Nhóm `[cau_hoi_ro]`

| Hệ | n | Soundness | unsound | Coverage | Selective Acc | đúng gold | từ chối thừa | hỏi đúng | LOI | nhãn thiếu | USD | model |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CPA² | 50 | 96.0% | 2 | 54.0% | 92.6% | 36 | 12 | 3/3 | 0 | 0 | 0.0000 | clingo (CPA²) |
| CPA² [_sau_A17] [không chính thức] | 50 | 100.0% | 0 | 52.0% | 100.0% | 38 | 12 | 3/3 | 0 | 0 | 0.0000 | clingo (CPA²) |
| b1_openai | 50 | 100.0% | 0 | 2.0% | 100.0% | 13 | 37 | — | 0 | 0 | 0.5350 | openai/gpt-6.1-sol qua openrouter |
| b1_gemini | 50 | 78.0% | 11 | 56.0% | 60.7% | 28 | 11 | — | 0 | 0 | 0.6651 | google/gemini-4-argon qua openrouter |
| b2_openai | 50 | 100.0% | 0 | 10.0% | 100.0% | 17 | 33 | — | 0 | 0 | 0.7534 | openai/gpt-6.1-sol qua openrouter |
| b2_gemini | 50 | 96.0% | 2 | 22.0% | 81.8% | 21 | 27 | — | 0 | 0 | 0.8975 | google/gemini-4-argon qua openrouter |
| b3_openai | 50 | 100.0% | 0 | 28.0% | 100.0% | 26 | 24 | — | 0 | 6 | 1.9913 | openai/gpt-6.1-sol qua openrouter |
| b3_gemini | 50 | 92.0% | 4 | 62.0% | 87.1% | 35 | 11 | — | 0 | 6 | 2.4357 | google/gemini-4-argon qua openrouter |

## Nhóm `[quy_che]`

| Hệ | n | Soundness | unsound | Coverage | Selective Acc | đúng gold | từ chối thừa | hỏi đúng | LOI | nhãn thiếu | USD | model |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CPA² | 62 | 93.5% | 4 | 72.6% | 91.1% | 45 | 13 | 3/3 | 0 | 0 | 0.0000 | clingo (CPA²) |
| CPA² [_sau_A17] [không chính thức] | 62 | 100.0% | 0 | 72.6% | 100.0% | 49 | 13 | 3/3 | 0 | 0 | 0.0000 | clingo (CPA²) |
| b1_openai | 62 | 100.0% | 0 | 4.8% | 100.0% | 7 | 55 | — | 0 | 0 | 0.5350 | openai/gpt-6.1-sol qua openrouter |
| b1_gemini | 62 | 79.0% | 13 | 53.2% | 60.6% | 24 | 25 | — | 0 | 0 | 0.6651 | google/gemini-4-argon qua openrouter |
| b2_openai | 62 | 100.0% | 0 | 12.9% | 100.0% | 12 | 50 | — | 0 | 0 | 0.7534 | openai/gpt-6.1-sol qua openrouter |
| b2_gemini | 62 | 96.8% | 2 | 24.2% | 86.7% | 17 | 43 | — | 0 | 0 | 0.8975 | google/gemini-4-argon qua openrouter |
| b3_openai | 62 | 95.2% | 3 | 33.9% | 85.7% | 22 | 37 | — | 0 | 6 | 1.9913 | openai/gpt-6.1-sol qua openrouter |
| b3_gemini | 62 | 95.2% | 3 | 54.8% | 91.2% | 35 | 24 | — | 0 | 6 | 2.4357 | google/gemini-4-argon qua openrouter |

## Nhóm `[thiet_ke]`

| Hệ | n | Soundness | unsound | Coverage | Selective Acc | đúng gold | từ chối thừa | hỏi đúng | LOI | nhãn thiếu | USD | model |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CPA² | 14 | 92.9% | 1 | 21.4% | 66.7% | 13 | 0 | — | 0 | 0 | 0.0000 | clingo (CPA²) |
| CPA² [_sau_A17] [không chính thức] | 14 | 100.0% | 0 | 14.3% | 100.0% | 14 | 0 | — | 0 | 0 | 0.0000 | clingo (CPA²) |
| b1_openai | 14 | 100.0% | 0 | 0.0% | — | 12 | 2 | — | 0 | 0 | 0.5350 | openai/gpt-6.1-sol qua openrouter |
| b1_gemini | 14 | 85.7% | 2 | 21.4% | 33.3% | 12 | 0 | — | 0 | 0 | 0.6651 | google/gemini-4-argon qua openrouter |
| b2_openai | 14 | 100.0% | 0 | 0.0% | — | 12 | 2 | — | 0 | 0 | 0.7534 | openai/gpt-6.1-sol qua openrouter |
| b2_gemini | 14 | 85.7% | 2 | 14.3% | 0.0% | 11 | 1 | — | 0 | 0 | 0.8975 | google/gemini-4-argon qua openrouter |
| b3_openai | 14 | 92.9% | 1 | 14.3% | 50.0% | 12 | 1 | — | 0 | 0 | 1.9913 | openai/gpt-6.1-sol qua openrouter |
| b3_gemini | 14 | 64.3% | 5 | 42.9% | 16.7% | 9 | 0 | — | 0 | 1 | 2.4357 | google/gemini-4-argon qua openrouter |

## Nhóm `[theo errata]`

| Hệ | n | Soundness | unsound | Coverage | Selective Acc | đúng gold | từ chối thừa | hỏi đúng | LOI | nhãn thiếu | USD | model |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CPA² | 76 | 93.4% | 5 | 63.2% | 89.6% | 64 | 7 | 3/3 | 0 | 0 | 0.0000 | clingo (CPA²) |
| CPA² [_sau_A17] [không chính thức] | 76 | 100.0% | 0 | 61.8% | 100.0% | 69 | 7 | 3/3 | 0 | 0 | 0.0000 | clingo (CPA²) |
| b1_openai | 76 | 100.0% | 0 | 3.9% | 100.0% | 25 | 51 | — | 0 | 0 | 0.5350 | openai/gpt-6.1-sol qua openrouter |
| b1_gemini | 76 | 76.3% | 18 | 47.4% | 50.0% | 35 | 23 | — | 0 | 0 | 0.6651 | google/gemini-4-argon qua openrouter |
| b2_openai | 76 | 100.0% | 0 | 10.5% | 100.0% | 30 | 46 | — | 0 | 0 | 0.7534 | openai/gpt-6.1-sol qua openrouter |
| b2_gemini | 76 | 93.4% | 5 | 22.4% | 70.6% | 31 | 40 | — | 0 | 0 | 0.8975 | google/gemini-4-argon qua openrouter |
| b3_openai | 76 | 93.4% | 5 | 30.3% | 78.3% | 38 | 33 | — | 0 | 6 | 1.9913 | openai/gpt-6.1-sol qua openrouter |
| b3_gemini | 76 | 85.5% | 11 | 52.6% | 72.5% | 44 | 21 | — | 0 | 7 | 2.4357 | google/gemini-4-argon qua openrouter |

## McNemar chính xác (CPA² vs baseline, cặp bất đồng)

b = ca CPA² kém hơn, c = ca CPA² tốt hơn. Tập nhỏ: p lớn không chứng minh hai hệ như nhau.

| Baseline | n cặp | đúng gold (b / c / p) | không unsound (b / c / p) |
|---|---|---|---|
| b1_openai | 76 | 1 / 40 / 0.0000 | 5 / 0 / 0.0625 |
| b1_gemini | 76 | 6 / 28 / 0.0002 | 5 / 15 / 0.0414 |
| b2_openai | 76 | 1 / 35 / 0.0000 | 5 / 0 / 0.0625 |
| b2_gemini | 76 | 3 / 33 / 0.0000 | 5 / 4 / 1.0000 |
| b3_openai | 76 | 3 / 27 / 0.0000 | 5 / 4 / 1.0000 |
| b3_gemini | 76 | 6 / 20 / 0.0094 | 5 / 8 / 0.5811 |

## Ca bất đồng (đầu vào phân tích ca sai)

- **b1_openai** — CPA² đúng / baseline unsound (0): —; baseline đúng / CPA² unsound (1): DK-22
- **b1_gemini** — CPA² đúng / baseline unsound (13): DK-11, DK-13, DK-17, DK-18, DK-20, EL-05, EL-17, ON-04M4, RC-01, RC-03, RC-12, TN-12, TN-13; baseline đúng / CPA² unsound (2): DK-21, DK-22
- **b2_openai** — CPA² đúng / baseline unsound (0): —; baseline đúng / CPA² unsound (1): DK-22
- **b2_gemini** — CPA² đúng / baseline unsound (3): ON-08M4, RC-03, TN-13; baseline đúng / CPA² unsound (1): DK-22
- **b3_openai** — CPA² đúng / baseline unsound (4): ON-07M4, RC-01, RC-07, RC-12; baseline đúng / CPA² unsound (2): DK-21, DK-22
- **b3_gemini** — CPA² đúng / baseline unsound (8): ON-03M4, ON-04M3, ON-04M4, ON-10M3, RC-01, RC-03, RC-07, RC-12; baseline đúng / CPA² unsound (2): DK-21, DK-22
