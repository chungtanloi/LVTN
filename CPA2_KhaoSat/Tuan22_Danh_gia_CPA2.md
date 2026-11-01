# TUẦN 22 — ĐÁNH GIÁ CPA² TRÊN TẬP TEST

**Giai đoạn:** Evaluation (Tuần 22/24) · **Mục tiêu:** Soundness, Coverage, Selective Accuracy, consistency trên tập test
**Sản phẩm:** CPA² results (`w20_benchmark/ket_qua_*_test.json`, `run_output_*_test.txt`)
**Tiêu chí hoàn thành:** Có số liệu + error analysis

---

## 1. Giao thức (đăng ký TRƯỚC lần chạy test, commit riêng)

Phần này viết và commit **trước** khi chạy bất kỳ ca test nào. Kết quả ghi ở các mục sau, không sửa mục 1.

### 1.1 Dữ liệu

| Bộ | Ca test chấm điểm | Gold | Ghi chú |
|---|---|---|---|
| G-Truth v1 | 56 | viết tay, đóng băng `312b7ff` | errata `gtruth_errata.json` có 3 ca test (HG-02, HG-04, HG-08) — chỉ in dòng `[theo errata]`, số chính thức theo gold đóng băng |
| OCR-Noise v1 | 20 | viết tay, đóng băng `312b7ff` | không có errata |
| Q-Noise | 110 | tổng hợp, kế thừa gold G-Truth, đóng băng `qnoise_dong_bang.json` | chấm chặt theo ý định; báo RIÊNG, không gộp vào G-Truth, không thay Q-Real |

Dev đã bị nhiễm (hệ thống đã sửa sau khi xem lỗi dev: P20, P20-4, P20-5, C12, C14, C15). Số dev chỉ để đối chiếu; số chính thức là test.

### 1.2 Lệnh (chạy từ `w20_benchmark/`, `PYTHONIOENCODING=utf-8`)

```
python run_cpa2.py --bo gtruth    --split test > run_output_gtruth_test.txt
python run_cpa2.py --bo ocr_noise --split test > run_output_ocr_noise_test.txt
python run_cpa2.py --bo qnoise    --split test > run_output_qnoise_test.txt
```

Tính tất định: chạy G-Truth test lần hai với `--hau-to _lap2`, chỉ so khớp từng ca (verdict + câu hỏi bổ sung) với lần một; không dùng để chọn gì.

### 1.3 Chỉ số và chỉ tiêu

Cách chấm của `w17_adversarial/run_adversarial.cham / tong_hop` (dùng chung với baseline Tuần 21), không đổi:
Soundness = 1 − #kết luận TRUE/FALSE sai / n · Coverage · Selective Accuracy · Đúng gold · Từ chối thừa · Hỏi đúng. LOI tính là SAI.

- Chỉ tiêu (Tuần 1, mức "Tối thiểu"): **Soundness = 100% trên G-Truth**. Áp cho test G-Truth, số chính thức theo gold đóng băng.
- Coverage, Selective Accuracy: báo cáo, không có ngưỡng đặt trước.
- Báo tách `[quy_che]` / `[thiet_ke]` như Tuần 20.

### 1.4 Xử lý khi thấy lỗi

- Không sửa hệ thống, gold hoặc cách chấm trước khi ghi xong số test.
- Mọi ca unsound / từ chối thừa / LOI được phân tích nguyên nhân (parser · KB · OCR · thiếu dữ kiện · gold) kèm điều/khoản.
- Gold sai phát hiện sau → errata, không sửa gold. Nếu sửa hệ thống sau đó: chạy với `--hau-to _sau_<mã>`, số chính thức giữ nguyên, tập test coi như đã nhiễm.

### 1.5 Môi trường

Nhánh `codex/cpa2-web-deploy` (bản đang chạy trên web), commit giao thức là con của `ab080bb`. Windows 11, Python 3.14.0, clingo 5.8.2, Tesseract v5.5.0.20241111 (`C:/Program Files/Tesseract-OCR`). Số OCR-Noise chỉ so được với lượt chạy cùng môi trường.

Trước khi chạy: toàn bộ `w*/validate_*.py` phải ĐẠT (gồm `validate_benchmark` B6 — hash gold khớp).

---

## 2. Kết quả (chạy một lần, 02/11/2026, trên `e880ee4`)

> **Chỉ tiêu Soundness = 100% trên G-Truth: CHƯA ĐẠT — 91,1% (5 kết luận sai / 56 ca).** 4/5 ca sai cùng một nguyên nhân trong KB (mục 3.1).

### 2.1 G-Truth v1 test (56 ca) — `run_output_gtruth_test.txt`

| | n | Soundness | Coverage | Sel. Acc | Đúng gold | Unsound | Từ chối thừa | Hỏi đúng |
|---|---|---|---|---|---|---|---|---|
| **tổng (chính thức)** | 56 | **91,1%** | 76,8% | 88,4% | 43 | **5** | 8 | 3/3 |
| [quy_che] | 52 | 92,3% | 76,9% | 90,0% | 40 | 4 | 8 | 3/3 |
| [thiet_ke] | 4 | 75,0% | 75,0% | 66,7% | 3 | 1 | 0 | 0/0 |
| [theo errata] (không chính thức) | 56 | 91,1% | 76,8% | 88,4% | 46 | 5 | 5 | 3/3 |

Theo nhóm: `mien_thay_the` Soundness 50% (3/6 unsound) · `dang_ky` 81,8% (2 unsound) · `hang` Coverage 25% · `tot_nghiep` Coverage 63,6% · các nhóm còn lại Soundness 100%.

### 2.2 OCR-Noise v1 test (20 ca) — `run_output_ocr_noise_test.txt`

| | n | Soundness | Coverage | Sel. Acc | Đúng gold | Unsound | Từ chối thừa |
|---|---|---|---|---|---|---|---|
| **tổng** | 20 | **100%** | 25,0% | 100% | 15 | 0 | 5 |
| [quy_che] | 10 | 100% | 50,0% | 100% | 5 | 0 | 5 |
| [thiet_ke] | 10 | 100% | 0% | — | 10 | 0 | 0 |

M1 3/5 · M2 2/5 · M3 5/5 · M4 5/5 đúng gold. Không có kết luận sai; từ chối thừa ở M1 (2) và M2 (3).

### 2.3 Q-Noise test (110 ca, tổng hợp — báo riêng)

| | n | Soundness | Coverage | Sel. Acc | Unsound | Từ chối thừa |
|---|---|---|---|---|---|---|
| tổng | 110 | 90,9% | 72,7% | 87,5% | 10 | 20 |

Nhất quán theo biến thể: mỗi biến thể V0–V4 cùng số liệu; **cùng verdict với V0 110/110, cùng claim với V0 110/110**; đúng ý định 21/22 mỗi biến thể; 0 kết luận sai ý định. 10 unsound = 5 biến thể × 2 câu gốc (DK-21, DK-22) — lỗi của KB/thiết kế, không phải của parser.

### 2.4 Tính tất định

Lần chạy lặp G-Truth test (`--hau-to _lap2`): **56/56 ca trùng** verdict và câu hỏi bổ sung.

## 3. Phân tích lỗi

### 3.1 Unsound (5 ca G-Truth)

| Ca | Gold → CPA² | Nguyên nhân | Loại |
|---|---|---|---|
| MT-08, MT-09 | FALSE → TRUE | `passed("ML016")`/`passed("ML018")` suy **tự động** từ ML010 đạt: `w9_exemption/exemption_substitution_solver.lp` dòng 59–60 (`passed(B) :- mien_tu(B,A), passed(A).`) với `mien_tu` của R-M13 (`qd5339_r_formal_v1.lp` dòng 181). QĐ5339 Đ2 k6 (tr.4): công nhận cần đơn + đơn vị xét duyệt → chưa có quyết định thì chưa đạt. Bài học trong CLAUDE.md đã ghi đúng điều này nhưng **KB chưa sửa theo** (luật có từ `cbe784c`, 09/10). | KB |
| MT-11 | FALSE → TRUE | Như trên, ML011 (D) → ML019. | KB |
| DK-21 | FALSE → TRUE | Như trên: ML018 (tiên quyết của ML019) bị coi là đã tích lũy. | KB (cùng gốc) |
| DK-22 | UNKNOWN → FALSE | Mã CT999 không có trong CTĐT K49; KB thế giới đóng cho `duoc_dang_ky` FALSE thay vì "không có dữ kiện". | thiết kế |

Dev chỉ có một ca chuyển đổi Lý luận chính trị (EL-16), và ca đó hỏi claim khác ("đủ điều kiện được xét", `thay_the:ML019`), không hỏi `passed`/`duoc_dang_ky`, nên lỗi chỉ lộ ở test. MT-10 (`passed("ML021")`, gold FALSE) đúng vì ML006 không đạt trong hồ sơ của ca đó, không phải vì luật đã đúng.

### 3.2 Từ chối thừa G-Truth (8 ca)

| Ca | Gold → CPA² | Nguyên nhân |
|---|---|---|
| TN-01, TN-03 | TRUE → UNKNOWN (hỏi `qua_thoi_gian_toi_da`) | `graduation_solver.lp` R21 (thêm 25/10, `b5e2d48`, **sau** đóng băng gold 18/10): chưa khai báo `tc_cong_nhan` thì mở nhánh quá hạn. Hồ sơ `sv_lvtn`/`sv_tltn` có `da_hoc_nam2` nhưng không có `tc_cong_nhan`. Gold viết theo KB cũ (thiếu = 0). |
| TN-08 | FALSE → UNKNOWN | Như trên: đúng 27 HK; nếu được công nhận ≥ 9 TC thì trần còn 26 HK (QĐ3266 Đ5) → không còn chắc "chưa vượt". Gold giả định không có TC công nhận. |
| HG-02, HG-04, HG-08 | TRUE → UNKNOWN | Hạng tốt nghiệp sau C15 (R-F07b mở nhánh từng-F / kỷ luật). Đã có errata (`gtruth_errata.json`: gold đúng là UNKNOWN) → theo errata là đúng. |
| RC-11 | TRUE → UNKNOWN (`phuong_an_rong`) | Tiên quyết CT176 chưa chắc → recommendation trả phương án rỗng và từ chối cả câu, trong khi "không đề xuất CT182" vẫn chắc chắn. |
| NL-09 | FALSE → UNKNOWN (`khong_ro`) | Parser không nhận câu "ĐTBCTL của em có đủ xếp loại giỏi khi tốt nghiệp không?" (danh sách cho phép của ý định xếp loại chưa phủ dạng này). |

Hệ thống đã hỏi đúng dữ kiện thiếu ở 3/3 ca có câu hỏi kỳ vọng.

### 3.3 OCR-Noise (5 từ chối thừa, 0 unsound)

- ON-01M2, ON-03M2, ON-09M2: mất ĐTBCHK → không tin điểm (thiết kế P20-4, benchmark không có lượt hỏi lại). ON-03M2 hỏi đúng 1 số `dtbchk:HK9`; ON-01M2, ON-09M2 không sinh câu hỏi — **chưa xác định vì sao**.
- ON-03M1, ON-04M1: cột điểm thi đọc kém nhưng T.Hợp và điểm chữ khớp → vẫn từ chối, không hỏi gì. **Chưa xác định nguyên nhân**, cần điều tra (không làm trong Tuần 22 để giữ số chính thức).

### 3.4 Q-Noise

Ngoài DK-21/DK-22 (mục 3.1), từ chối thừa: TN-01, TN-03 (R21, như 3.2) và hai câu parser trả `khong_ro`: EL-06 "Em bị F luận văn, em có được làm lại luận văn không?" và NL-09.

### 3.5 Đối chiếu dev

Lần chạy dev cuối là 19/10 (`b6eb10d`), **trước** các thay đổi lõi 25/10 (`b5e2d48`) và các commit RAG/OCR của nhánh deploy; dev chưa chạy lại sau đó, nên số dev (Soundness 100%, Coverage 91,4%) không phản ánh đúng hệ thống đã chạy test. Dev cũng đã nhiễm. Không dùng dev để kết luận.

## 4. Kết luận và việc mở

- Soundness = 100% trên G-Truth: **chưa đạt** (91,1%). Lỗi chính là một luật KB công nhận tự động (C20), đã có trong KB từ Tuần 9 và không có ca dev nào bắt được.
- OCR-Noise: Soundness 100%, Coverage thấp (25%) — an toàn nhưng từ chối nhiều.
- Q-Noise: nhất quán tuyệt đối giữa biến thể (110/110): lỗi không đến từ biến thể câu chữ mà từ KB (DK-21, TN-01/03), thiết kế (DK-22) và hai mẫu câu parser chưa phủ (EL-06, NL-09) — sai như nhau ở mọi biến thể.
- Không sửa hệ thống hay gold trong Tuần 22. Sau khi sửa (nếu Loi duyệt) thì chạy `--hau-to _sau_<mã>`; số ở mục 2 là số chính thức, tập test coi như đã nhiễm.

Việc mới ghi vào `Viec_ton_dong.md`: A21 (gold TN-01/03/08 vs R21), C20–C24.
