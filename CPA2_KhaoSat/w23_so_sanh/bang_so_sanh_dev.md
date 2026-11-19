# So sánh CPA² vs baseline — split dev

Tập ca chung của các hệ CHÍNH THỨC: **78/78** ca được chấm (G-Truth + OCR-Noise). Hệ không chính thức chấm trên phần giao của tập này với ca của nó (xem cột n).

## Nhóm `tong`

| Hệ | n | Soundness | unsound | Coverage | Selective Acc | đúng gold | từ chối thừa | hỏi đúng | LOI | nhãn thiếu | USD | model |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CPA² | 78 | 92.3% | 6 | 78.2% | 90.2% | 67 | 5 | 1/1 | 0 | 0 | 0.0000 | clingo (CPA²) |
| CPA² [_sau_A17] [không chính thức] | 78 | 100.0% | 0 | 71.8% | 100.0% | 70 | 8 | 1/1 | 0 | 0 | 0.0000 | clingo (CPA²) |
| b1_openai | — | chưa chạy | | | | | | | | | | |
| b1_gemini | 78 | 79.5% | 16 | 55.1% | 62.8% | 38 | 24 | — | 0 | 0 | 0.6644 | google/gemini-4-argon qua openrouter |
| b2_openai | — | chưa chạy | | | | | | | | | | |
| b2_gemini | — | chưa chạy | | | | | | | | | | |
| b3_openai | — | chưa chạy | | | | | | | | | | |
| b3_gemini | — | chưa chạy | | | | | | | | | | |

## Nhóm `[cau_hoi_ro]`

| Hệ | n | Soundness | unsound | Coverage | Selective Acc | đúng gold | từ chối thừa | hỏi đúng | LOI | nhãn thiếu | USD | model |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CPA² | 49 | 93.9% | 3 | 77.6% | 92.1% | 43 | 3 | 1/1 | 0 | 0 | 0.0000 | clingo (CPA²) |
| CPA² [_sau_A17] [không chính thức] | 49 | 100.0% | 0 | 63.3% | 100.0% | 41 | 8 | 1/1 | 0 | 0 | 0.0000 | clingo (CPA²) |
| b1_openai | — | chưa chạy | | | | | | | | | | |
| b1_gemini | 49 | 77.6% | 11 | 65.3% | 65.6% | 29 | 9 | — | 0 | 0 | 0.6644 | google/gemini-4-argon qua openrouter |
| b2_openai | — | chưa chạy | | | | | | | | | | |
| b2_gemini | — | chưa chạy | | | | | | | | | | |
| b3_openai | — | chưa chạy | | | | | | | | | | |
| b3_gemini | — | chưa chạy | | | | | | | | | | |

## Nhóm `[quy_che]`

| Hệ | n | Soundness | unsound | Coverage | Selective Acc | đúng gold | từ chối thừa | hỏi đúng | LOI | nhãn thiếu | USD | model |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CPA² | 65 | 93.8% | 4 | 90.8% | 93.2% | 56 | 5 | 1/1 | 0 | 0 | 0.0000 | clingo (CPA²) |
| CPA² [_sau_A17] [không chính thức] | 65 | 100.0% | 0 | 86.2% | 100.0% | 57 | 8 | 1/1 | 0 | 0 | 0.0000 | clingo (CPA²) |
| b1_openai | — | chưa chạy | | | | | | | | | | |
| b1_gemini | 65 | 80.0% | 13 | 61.5% | 67.5% | 28 | 24 | — | 0 | 0 | 0.6644 | google/gemini-4-argon qua openrouter |
| b2_openai | — | chưa chạy | | | | | | | | | | |
| b2_gemini | — | chưa chạy | | | | | | | | | | |
| b3_openai | — | chưa chạy | | | | | | | | | | |
| b3_gemini | — | chưa chạy | | | | | | | | | | |

## Nhóm `[thiet_ke]`

| Hệ | n | Soundness | unsound | Coverage | Selective Acc | đúng gold | từ chối thừa | hỏi đúng | LOI | nhãn thiếu | USD | model |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CPA² | 13 | 84.6% | 2 | 15.4% | 0.0% | 11 | 0 | — | 0 | 0 | 0.0000 | clingo (CPA²) |
| CPA² [_sau_A17] [không chính thức] | 13 | 100.0% | 0 | 0.0% | — | 13 | 0 | — | 0 | 0 | 0.0000 | clingo (CPA²) |
| b1_openai | — | chưa chạy | | | | | | | | | | |
| b1_gemini | 13 | 76.9% | 3 | 23.1% | 0.0% | 10 | 0 | — | 0 | 0 | 0.6644 | google/gemini-4-argon qua openrouter |
| b2_openai | — | chưa chạy | | | | | | | | | | |
| b2_gemini | — | chưa chạy | | | | | | | | | | |
| b3_openai | — | chưa chạy | | | | | | | | | | |
| b3_gemini | — | chưa chạy | | | | | | | | | | |

## Nhóm `[theo errata]`

| Hệ | n | Soundness | unsound | Coverage | Selective Acc | đúng gold | từ chối thừa | hỏi đúng | LOI | nhãn thiếu | USD | model |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CPA² | 78 | 91.0% | 7 | 78.2% | 88.5% | 66 | 5 | 1/1 | 0 | 0 | 0.0000 | clingo (CPA²) |
| CPA² [_sau_A17] [không chính thức] | 78 | 100.0% | 0 | 71.8% | 100.0% | 71 | 7 | 1/1 | 0 | 0 | 0.0000 | clingo (CPA²) |
| b1_openai | — | chưa chạy | | | | | | | | | | |
| b1_gemini | 78 | 79.5% | 16 | 55.1% | 62.8% | 38 | 24 | — | 0 | 0 | 0.6644 | google/gemini-4-argon qua openrouter |
| b2_openai | — | chưa chạy | | | | | | | | | | |
| b2_gemini | — | chưa chạy | | | | | | | | | | |
| b3_openai | — | chưa chạy | | | | | | | | | | |
| b3_gemini | — | chưa chạy | | | | | | | | | | |

## McNemar chính xác (CPA² vs baseline, cặp bất đồng)

b = ca CPA² kém hơn, c = ca CPA² tốt hơn. Tập nhỏ: p lớn không chứng minh hai hệ như nhau.

| Baseline | n cặp | đúng gold (b / c / p) | không unsound (b / c / p) |
|---|---|---|---|
| b1_gemini | 78 | 7 / 36 / 0.0000 | 6 / 16 / 0.0525 |

## Ca bất đồng (đầu vào phân tích ca sai)

- **b1_gemini** — CPA² đúng / baseline unsound (15): DK-05, DK-14, DK-19, EL-01, EL-02, HG-03, NL-02, ON-02M4, ON-06M4, ON-10M4, RC-02, RC-05, RC-06, RC-09, TN-10; baseline đúng / CPA² unsound (3): NL-06, NL-10, NL-11
