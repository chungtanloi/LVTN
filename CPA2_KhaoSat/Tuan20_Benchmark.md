# TUẦN 20 — XÂY BENCHMARK

**Giai đoạn:** Evaluation (Tuần 20/24) · **Mục tiêu:** Hoàn thiện Q-Real, G-Truth, OCR-Noise, baseline
**Sản phẩm:** Evaluation dataset (`w20_benchmark/`)
**Tiêu chí hoàn thành:** Có ground truth

| Hạng mục | Trạng thái |
|---|---|
| G-Truth v1 | **đạt** — 115 ca (114 chấm), gold viết tay, đóng băng tại `312b7ff` trước lần chạy đầu |
| OCR-Noise v1 | **đạt** — 40 ca (10 kịch bản × 4 mức nhiễu), đóng băng cùng commit |
| Đầu vào baseline | **đạt** — `baseline_dev.jsonl` (78 ca), `baseline_test.jsonl` (77 ca), không lộ đáp án |
| Q-Real | **chưa đạt (0/400)** — đã có pipeline nhập, ẩn danh, chia split và quy trình gán nhãn; chờ Loi cung cấp câu hỏi thật (phương án 1a) |
| Q-Noise v1 (tổng hợp, **không** thay Q-Real) | **đạt** — 240 câu (48 câu gốc × 5 kiểu gõ), đóng băng `5d8601c` trước lần chạy đầu; dev phát hiện P20-5 (mục 5c) |
| `validate_benchmark.py` | ĐẠT (B1–B10); mọi tuần 5–20 ĐẠT |

---

## 0. Kết luận trước

> Có ground truth cho phần suy diễn: **155 ca mới, gold viết tay và đóng băng trước khi chạy hệ thống**, kèm nguồn điều/khoản và tiền đề số học kiểm bằng oracle độc lập. **Chưa có câu hỏi thật**: Q-Real là dữ liệu người dùng, không tự tạo được mà vẫn trung thực. Lần chạy dev đầu tiên đã bắt được **một lỗi thật trong KB** (hạng tốt nghiệp) và **hai lỗi parser** — đúng việc mà một bộ đánh giá mới phải làm.

---

## 1. G-Truth v1

| Nhóm | n | Ví dụ |
|---|---|---|
| đăng ký (tiên quyết + song hành) | 22 | CT182 khi chưa học CT180 / CT180 thiếu CT177 / CT180 bị F / CT180 điểm W; biên 119–120, 79–80, 124–125 TC; mã ngoài CTĐT |
| đủ điều kiện | 17 | LVTN/TLTN theo công bố hình thức; LVTN bị F được làm lại; niên luận, thực tập, niên luận cơ sở; đủ điều kiện được xét công nhận Lý luận chính trị |
| bất biến đề xuất | 12 | không đề xuất HP thiếu tiên quyết, không mở học kỳ đó, đã tích lũy, nhánh ngoại ngữ khác, song hành bị chặn, tiên quyết chưa chắc; ≤ 20 TC |
| tốt nghiệp và điều kiện | 24 | D/F sát ngưỡng; GDQP F / TB đúng 5,0 / 4,75; trần thời gian theo HK (Đ5, Đ6 k1); 159 / 164 TC; W; điểm chưa chắc quyết định / không quyết định |
| nhóm tự chọn | 8 | trộn nhánh chuyên ngành; Pháp văn đủ 10 TC; AV + PV không cộng dồn; nhóm tốt nghiệp 12 / 15 TC |
| miễn và thay thế | 12 | TOEIC 445/450, IELTS 4.0/4.5, CTU bậc 2/3; IELTS không miễn Pháp văn; Lý luận chính trị cũ chưa có quyết định công nhận |
| hạng tốt nghiệp | 8 | ĐTBCTL đúng 3,60 / 3,55 / 3,25 / 3,20 / 3,19 / 2,50 / 2,49 |
| câu tự nhiên (đầu-cuối) | 12 | đăng ký, luận văn, tốt nghiệp; phản thực tế, học phí, học bổng, cảnh báo, chuyển ngành (ngoài phạm vi) |

**Gold:** TRUE 61 · FALSE 44 · UNKNOWN 10. Mỗi ca có:
- lý do và nguồn (văn bản, điều, khoản, trang);
- danh sách cần hỏi lại (`can_hoi`) cho ca UNKNOWN;
- `loai_gold`: **quy_che** (127 ca, theo câu chữ quy chế/CTĐT) hoặc **thiet_ke** (27 ca, theo nguyên tắc thiết kế: không kết luận ngoài KB, OCR mâu thuẫn hoặc mất dòng, chính sách tư vấn). Hai loại được **báo cáo tách riêng**.

**Độc lập với hệ thống:**
- Bộ **mới**, không trùng ca nào của w17 (validate B5 kiểm theo claim + đầu vào dựng được). Bản đầu có 5 ca trùng w17 và 1 cặp trùng nội bộ; em đã thay trước khi đóng băng.
- 41 tiền đề số học (TC, ĐTBCTL, TB GDQP, trần HK) được kiểm bằng oracle Python **không dùng clingo, không đọc .lp** (B3).
- Validate B2 kiểm mọi claim là vị từ có đầu luật trong KB, chống lỗi P18-1 (claim không ai suy ra nên luôn FALSE).

**Soát gold độc lập trước khi đóng băng.** Một agent đã đối chiếu 155 ca với văn bản quy chế và CTĐT, **không chạy hệ thống**. Các điểm đã xử lý trước khi đóng băng:
- **Công nhận Lý luận chính trị cần quyết định** (QĐ5339 Đ3 k9, tr.8, nằm trong thủ tục "xét miễn và công nhận điểm"; Đ2 k6: SV phải làm đơn). Gold của MT-08, MT-09, MT-11 và DK-21 đổi từ TRUE sang FALSE, cùng tinh thần với QD-11.
- **TN-11 không chấm:** Đ5 có hai cách đọc trần thời gian khi có TC công nhận (câu chính và ví dụ cho kết quả khác nhau).
- Sửa số TC của ML010/ML011 (3 TC), trang nguồn tr.8, câu lý do của TN-07.
- Gắn nhãn `thiet_ke` cho các ca gold dựa trên nguyên tắc thiết kế.

⚠️ **HG-02** (ĐTBCTL 3,55) **nảy ra khi đọc code KB** (cận nguyên của bảng hạng). Gold vẫn theo câu chữ Đ34, nhưng ca này không "mù" với hệ thống. Em ghi ở đây để minh bạch.

## 2. OCR-Noise v1

Có 10 kịch bản (hồ sơ, học phần quyết định, claim), mỗi kịch bản 4 mức nhiễu:

| Mức | Nhiễu | Gold |
|---|---|---|
| M1 | cột điểm thi đọc kém (conf 0,4), T.Hợp và chữ rõ | TRUE |
| M2 | không đọc được ĐTBCHK của học kỳ (mất kiểm chéo, không lỗi) | TRUE |
| M3 | điểm chữ đọc thành F trái với T.Hợp | UNKNOWN (thiết kế) |
| M4 | mất dòng, tổng TC học kỳ lệch | UNKNOWN (thiết kế) |

Sự thật phía sau của mọi kịch bản là TRUE.

## 3. Q-Real — chưa đạt (0/400)

Theo phương án 1a, câu hỏi thật do Loi cung cấp. Đã có sẵn:
- `nhap_qreal.py`: chuẩn hoá NFC, ẩn danh MSSV/email/SĐT, khử trùng, id ổn định, chia dev/test theo hash, giữ nhãn khi nhập lại;
- thư mục thô `qreal/_tho/` đã gitignore;
- quy trình rà tay và gán nhãn ý định (`qreal/README.md`).

Script ẩn danh chỉ bắt được các mẫu cố định, nên **bước rà tay là bắt buộc**.

## 4. Đầu vào baseline (cho Tuần 21)

`baseline.py` sinh cho mỗi ca:
- câu hỏi;
- hồ sơ đã bỏ `student_id` và `meta`, và đã bỏ điểm của HP "chưa rõ"; hoặc bảng điểm OCR kèm khai báo;
- mô tả dữ kiện mở bằng tiếng Việt;
- dạng câu trả lời (TRUE / FALSE / UNKNOWN).

Không có gold, lý do, nguồn, sự thật hay tên hồ sơ gốc (B8). Baseline sẽ được chấm bằng cùng bộ chấm với CPA².

## 5. Chạy thử CPA² trên DEV (kiểm đường ống — test để Tuần 22)

| Bộ / split | n | Soundness | Coverage | Sel. Acc | Unsound | Từ chối thừa |
|---|---|---|---|---|---|---|
| G-Truth dev | 58 | **89,7%** | 96,6% | 89,3% | 6 | 0 |
| └ gold quy chế | 55 | 92,7% | 98,2% | 92,6% | 4 | 0 |
| └ gold thiết kế | 3 | 33,3% | 66,7% | 0,0% | 2 | 0 |
| OCR-Noise dev | 20 | **100%** | 25,0% | 100% | 0 | 5 (toàn bộ M2) |

Theo nhóm (G-Truth dev):
- 100%: đăng ký 11/11, đủ điều kiện 9/9, đề xuất 6/6, tốt nghiệp 12/12, nhóm 4/4, miễn/thay thế 6/6.
- Còn lỗi: **hạng 1/4**, **câu tự nhiên 3/6**.

### Phát hiện

**P20-1 · Hạng tốt nghiệp: ĐTBCTL nằm giữa các mốc nguyên không thuộc hạng nào (HG-01, HG-05, HG-07 unsound).**
- KB khai báo `hang(kha, 25, 31)` và so `N ≤ Hi·D` trên thang ×10. Vì vậy ĐTBCTL 3,14 (31,4 > 31), 3,19 hay 2,49 không có `hang_cuoi`, nên trả FALSE.
- Đây là lỗi thật: ngay hồ sơ gốc sv_lvtn (3,14, khá theo Đ34) cũng sai. Các test Tuần 5–10 không bắt được vì chỉ dùng giá trị trùng mốc.
- **Chưa sửa.** Sửa R-Formal cần kế hoạch được duyệt (đề xuất ở mục 7).

**P20-2 · Câu ngoài phạm vi bị trả lời như câu hỏi tốt nghiệp (NL-06 học phí, NL-10 chuyển ngành → TRUE).**
- Parser stub rơi về mặc định `tot_nghiep`. Cùng họ lỗi P18-1 và P19-4: ý định sai mà không báo lỗi.

**P20-3 · "Đăng ký niên luận CT466E" không được nhận là câu đăng ký (NL-11 → FALSE).**
- Mẫu câu đòi mã HP đứng ngay sau "đăng ký". Câu có chữ "niên luận" chen giữa nên rơi về `tot_nghiep`.

**P20-4 · OCR mất ĐTBCHK thì từ chối cả học kỳ (M2: 5/5 từ chối thừa).**
- An toàn (không unsound) nhưng Coverage thấp. Đây là lựa chọn thiết kế của Tuần 15; nên xem lại.

Ca HG-03 (3,60, trùng mốc) đúng. Mọi ca thuộc nhóm mới của Tuần 18–19 (đăng ký, song hành, eligibility, đề xuất) đều đúng trên dev.

### Review code (sửa trước khi báo cáo)

- **Lộ đáp án qua id ở đầu vào baseline:** `ON-xxM1/M2` luôn TRUE, `RC-*` luôn TRUE. Đã sửa: id mờ (`id_mo`, hash) và đảo thứ tự ca. B8 nay kiểm cả id.
- **Hash đóng băng mở rộng.** Bản đầu chỉ băm id/hệ/claim/đầu vào/gold. Nay băm mọi trường ảnh hưởng đầu vào hoặc cách chấm (câu hỏi, hk, sự thật, can_hoi, cham_diem, split, loai_gold, oracle), cùng hash của 6 hồ sơ gốc và CTĐT (B6a, B6b). Hash mới được tính trên **đúng nội dung của 312b7ff** (git diff rỗng); hash cũ vẫn giữ trong `gold_dong_bang.json`.
- **Ca đề xuất qua điểm mà không kiểm gì:** phương án rỗng (vô nghiệm) trước đây làm mọi ca `khong_de_xuat` thành TRUE. Nay phương án rỗng được tính là từ chối.
- **Ca câu tự nhiên** ghi lại claim mà parser thực sự trả lời (ví dụ NL-06 → `tot_nghiep`). `DA_HOAN_THANH` được quy về FALSE.
- **B2** kiểm cả mã học phần trong claim, trừ ca thiết kế ngoài KB (DK-22).
- **Q-Real, ẩn danh:**
  - thêm link Facebook/Zalo, mã lớp (DI20V7A1), MSSV có dấu cách;
  - SĐT chỉ bắt đầu số di động Việt Nam, để không nuốt số thường;
  - sửa lỗi lồng "[MSSV] [MSSV";
  - `nguon` chỉ giữ loại nguồn;
  - câu đã xoá tay được ghi vào `meta.da_xoa` và không bị nhập lại.

  **Tên người vẫn không bắt được tự động**, nên bước rà tay là bắt buộc.
- **Còn lại, ghi nhận:**
  - OCR-Noise không có gold FALSE và mọi `su_that` đều TRUE;
  - G-Truth chỉ có 10 ca gold UNKNOWN, nên số đo về từ chối dựa trên ít ca;
  - chia split theo hash câu nên câu gần nghĩa có thể rơi vào cả hai split.

  Không thêm ca sau đóng băng; nếu cần sẽ làm G-Truth v1.1 với bản đóng băng riêng.

## 5b. Sửa P20-1…P20-3 (Loi duyệt "hoàn thiện đi", 18/10/2026) — dev ĐÃ NHÌN THẤY

TDD: mọi ca dưới đây fail với code/luật cũ.

| | Sửa | Ca hồi quy |
|---|---|---|
| **P20-1** | R-Formal **v1.10**: bỏ mốc nguyên; `dat_can_hang` so **hữu tỉ** theo cận dưới thang ×100, hạng = mức cao nhất đạt cận dưới. **QD-14** (quyết định của tác giả): QĐ3266 không quy định làm tròn ĐTBCTL nên giá trị giữa 3,59 và 3,60 thuộc Giỏi. Ghi ở catalog R-F06 và phụ lục (sinh lại). | rformal C42 (3,14 → khá), C43 (3,57 → giỏi), C44 (2,45 → TB), C46 (3,595 → giỏi), C45 (biên 3,20) |
| **P20-2** | Parser **không còn mặc định `tot_nghiep`**. Câu không nhận ra ý định trả `khong_ro` → UNKNOWN "chưa hỗ trợ". Câu tốt nghiệp diễn đạt khác ("ra trường được chưa") nhận bằng mẫu riêng, trừ câu hỏi xếp loại, học phí, học bổng. | integration E10 (học phí, chuyển ngành, câu lạc đề), E11 |
| **P20-3** | Cho phép tên học phần chen giữa "đăng ký … <MÃ>". | integration E12 (niên luận CT466E, luận văn CT550E) |

Câu hỏi trong ca hồi quy được **diễn đạt khác** câu của G-Truth để không khớp đúng bộ đánh giá.

**Review lượt 2 (đã sửa, ca hồi quy E13–E16 fail trước khi sửa):**
- Khe "đăng ký … <MÃ>" từng bắt nhầm câu về **học phần khác** ("đăng ký học phần tiên quyết **của** CT180", "song hành **với**", "học phần **gì để** tốt nghiệp CT550E") và câu **hủy/rút**. Nay khe chỉ chấp nhận tên học phần.
- Mẫu tốt nghiệp không còn bắt câu về luận văn, ĐTBCTL, miễn, hồ sơ, xếp loại. "Đủ điều kiện làm luận văn/tiểu luận" chuyển sang Eligibility.
- Nhận thêm câu không dấu ("tot nghiep chua"), "có thể / kịp tốt nghiệp", "đăng **kí** … được **ko**".
- Phần hạng tốt nghiệp: review xác nhận đúng; đã kiểm biên < 2,00 (không hạng) và giảm một mức khi điểm F vượt 5%.

**G-Truth dev sau khi sửa** (`ket_qua_gtruth_dev_sau_P20.json`, giữ nguyên số lần chạy đầu):

| | n | Soundness | Coverage | Sel. Acc | Unsound |
|---|---|---|---|---|---|
| Lần đầu (chính thức dev) | 58 | 89,7% | 96,6% | 89,3% | 6 |
| Sau P20 | 58 | **100%** | 93,1% | 100% | 0 |

Coverage giảm vì 2 câu ngoài phạm vi nay trả UNKNOWN đúng như gold. Dev **đã nhìn thấy**, nên số chính thức của hệ thống là test, chạy một lần ở Tuần 22. Ca NL-09 (hỏi xếp loại giỏi) nay cũng trả UNKNOWN, tức từ chối chứ không sai, vì parser chưa có ý định xếp loại (C12).

P20-4 (OCR mất ĐTBCHK thì từ chối cả học kỳ) **chưa sửa**. Đây là lựa chọn an toàn của Tuần 15; nới ra cần cân nhắc thêm (C11).

## 5c. Q-Noise v1 — độ bền parser trước cách gõ của sinh viên (TỔNG HỢP)

Q-Real chưa có câu thật (A16), nên em đo trước một phần việc Q-Real phải đo: **parser có chịu được cách sinh viên gõ hay không**. Q-Noise **không** cho biết sinh viên hỏi *gì* và **không** tính vào chỉ tiêu Q-Real (vẫn 0/400).

- **Câu gốc:** 48 ca G-Truth có câu hỏi đi qua parser (đăng ký một HP, tốt nghiệp, đủ điều kiện làm LVTN/TLTN, câu tự nhiên) và không có dữ kiện mở. Chọn theo claim và đầu vào, **không** theo kết quả chạy.
- **Biến thể** (`build_qnoise.py`, tất định, seed theo id):
  - V0 câu gốc;
  - V1 bỏ dấu;
  - V2 viết tắt (đk, đki, tn, hp, đc, ko, e, lv, tl, hk, kì);
  - V3 gõ vội (chữ thường, "ad ơi cho e hỏi", thiếu dấu một từ, "??");
  - V4 = V2 bỏ dấu.
  
  Mã HP được viết thường.
- **Gold:** kế thừa nguyên từ G-Truth (`312b7ff`). Biến đổi chỉ đổi cách viết, không đổi nghĩa (soát tay bằng cách đọc, không chạy hệ thống).
- **Ý định kỳ vọng (`claim_ky_vong`):** gán tay trước khi chạy. Câu ngoài phạm vi thì để rỗng, nghĩa là phải từ chối.
- **Chấm chặt (theo review trước đóng băng):** kết luận TRUE/FALSE suy từ claim KHÁC tính là **unsound**, kể cả khi trùng gold, vì chứng chỉ khi đó chứng minh cho một câu hỏi khác.
- **Đóng băng:** `qnoise_dong_bang.json` (hash toàn bộ ca), commit `5d8601c`, trước lần chạy đầu. Validate B10a–h.

**Dev, lần chạy chính thức đầu** (130 câu; `ket_qua_qnoise_dev.json`, `run_output_qnoise_dev.txt`):

| Biến thể | n | Soundness | Coverage | Đúng ý định | Cùng verdict với V0 |
|---|---|---|---|---|---|
| V0 câu gốc | 26 | 100% | 88,5% | 26/26 | — |
| V1 bỏ dấu | 26 | **84,6%** | 38,5% | 9/26 | 11/26 |
| V2 viết tắt | 26 | 100% | **0%** | 3/26 | 3/26 |
| V3 gõ vội | 26 | 100% | 65,4% | 20/26 | 20/26 |
| V4 bỏ dấu + viết tắt | 26 | 100% | **0%** | 3/26 | 3/26 |
| **Tổng** | 130 | **96,9%** | 38,5% | 61/130 | |

V0 là câu dev **đã thấy** khi sửa P20-2/P20-3, nên 26/26 ở V0 không có giá trị như số đo độc lập.

### Phát hiện

- **P20-5 (an toàn — 4 unsound, chưa sửa).** Câu không dấu "Em co du dieu kien lam **luan van** tot nghiep khong?" (EL-01…04, V1) bị parser hiểu thành `tot_nghiep`. Nguyên nhân: nhánh tốt nghiệp không dấu có danh sách loại trừ (`luận văn`, `tiểu luận`, `đtbctl`, `loại`…) chỉ ở dạng **có dấu**. Hệ thống trả FALSE cho câu "đủ điều kiện tốt nghiệp", không phải câu đã hỏi.
  - Chấm theo gold thuần thì chỉ 2 ca sai (EL-02/04 tình cờ trùng gold FALSE). Chấm chặt cho 4 — đúng loại lỗi P18-1/P19-4/P20-2: trả lời một câu khác mà vẫn kèm chứng chỉ.
  - Thêm một lỗi tiềm ẩn cùng họ: `answer_eligibility` chọn TLTN bằng cách tìm chuỗi `"tiểu luận"` có dấu, nên câu "tieu luan" sẽ bị xét như LVTN.
- **Parser không nhận câu không dấu và viết tắt (an toàn — chỉ từ chối thừa).**
  - V1: 13/26 câu bị từ chối thừa, do regex đăng ký cần "đăng ký/được".
  - V2/V4: gần như toàn bộ bị từ chối thừa (23/26), do "đk/đki/dky", "đc/dc", "tn", "lv", "hp" không có trong parser.
  - Hệ thống không kết luận sai ở đây, nhưng sinh viên gõ như thật thì hầu như không được trả lời.
- **V3 (gõ vội) bền hơn** (20/26). Các ca hỏng là ca có đúng từ khoá bị mất dấu ("đăng ky", "dang ký", "nien luận").

Theo quy tắc nhiễm dữ liệu (Bài học): đây là số **chính thức** của Q-Noise dev. Nếu sửa P20-5 hoặc chuẩn hoá viết tắt, số sau sửa ghi ra file riêng (`--hau-to`). Q-Noise test (110 câu) để chạy một lần ở Tuần 22 cùng G-Truth test.

## 6. Hạn chế

- Q-Real 0/400: chưa đo được parser trên câu thật. Q-Noise chỉ đo độ bền với cách gõ do em **tự định nghĩa** (bảng viết tắt, kiểu gõ vội) — không đại diện phân bố câu thật.
- Gold do một người (Claude) viết. Đã có một lượt soát độc lập bằng agent, nhưng **chưa phải người thứ hai** để đo κ (A7).
- OCR-Noise dựng ở mức tài liệu (sau nhận dạng), không render ảnh + Tesseract (phụ thuộc môi trường, như w17).
- Mới chạy dev. Test chạy một lần ở Tuần 22.
- Sau khi sửa P20-1…3 trên dev, dev sẽ "đã thấy". Số chính thức là test (Tuần 22).

## 7. Việc còn lại → Tuần 21+

- [ ] **Cần Loi:** câu hỏi thật cho Q-Real (≥ 400), đặt vào `qreal/_tho/`
- [x] Sửa P20-1 — R-Formal v1.10 + QD-14 (mục 5b)
- [x] Sửa P20-2/P20-3 (mục 5b)
- [ ] Xem lại P20-4 (M2 OCR)
- [ ] **P20-5** (an toàn): loại trừ không dấu ở nhánh tốt nghiệp + TLTN không dấu — chờ Loi duyệt kế hoạch
- [ ] Parser chuẩn hoá bỏ dấu/viết tắt (coverage V1/V2/V4) — chờ Loi duyệt
- [ ] Sau: Q-Elicit (phiếu kịch bản) + Google Form Q-Real nhỏ (Loi: "sau cập nhật thêm")
- [ ] Tuần 21: chạy baseline (LLM thuần, RAG thuần, tool-calling) trên `baseline_dev/test.jsonl` (cần API key, `.env`)
- [ ] Tuần 22: chạy CPA² trên test (một lần), báo cáo cả hai loại gold

### Ghi chú kiểm chứng

- [x] Có ground truth: G-Truth 115 + OCR-Noise 40, gold viết tay, nguồn, oracle, dev/test, đóng băng `312b7ff` trước lần chạy đầu
- [x] Đầu vào baseline trung lập (B8)
- [ ] Q-Real (0/400) — chờ dữ liệu
- [x] Q-Noise v1 (tổng hợp): 240 câu, gold kế thừa, ý định gán tay, đóng băng `5d8601c` trước khi chạy; dev đã chạy
- [x] Mọi tuần 5–20 ĐẠT
