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
| Q-Noise v1 (tổng hợp, **không** thay Q-Real) | **đạt** — 240 câu (48 câu gốc × 5 kiểu gõ), đóng băng `5d8601c` trước lần chạy đầu; dev phát hiện P20-5, đã sửa (mục 5c) |
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

### 3b. Biểu mẫu thu câu hỏi + Q-Elicit (Loi duyệt 19/10/2026: giữ chỉ tiêu 400 câu TỰ NHIÊN)

Loi thấy rất khó tìm câu thật. Việc cào dữ liệu nhóm Facebook đã bị loại vì lý do đạo đức, điều khoản sử dụng và Nghị định 13/2023. Vì vậy em làm một **Google Form** để Loi gửi cho sinh viên. Nội dung form ở `qreal/bieu_mau.md`, sinh bằng `build_bieu_mau.py`. Form có:

1. **Đồng ý (NĐ 13/2023):**
   - người thu và liên hệ (`<<ĐIỀN>>` — Loi điền trước khi mở);
   - mục đích;
   - nơi lưu: kho GitHub có thể công khai, có thể gửi tới dịch vụ AI để so sánh;
   - thời hạn xoá bản thô;
   - **rút lại bằng mã tự đặt** (≥ 6 ký tự, chỉ lưu dạng băm trong `_tho/_noi_bo/`, không lên GitHub), kèm giới hạn: lịch sử git, báo cáo, dịch vụ AI thì không thu hồi được;
   - tự nguyện.

   Form không hỏi tên, MSSV, email, SĐT hay ngày sinh.
2. **Câu tự do** `[TU_DO-1..3]`:
   - hỏi **trước** mọi kịch bản; mọi chữ người trả lời đọc trước đó không chứa cụm từ parser dựa vào (B11e2);
   - đây là **Q-Real** (nguồn `bieu_mau`), tính vào chỉ tiêu 400.
3. **Q-Elicit**:
   - 20 kịch bản viết tay (`qreal/kich_ban_q_elicit.json`), 4 bộ × 5; người trả lời tự chọn số 1–4;
   - phủ đủ 11 ý định, có cả ngoài phạm vi;
   - **chống mớm lời:** tình huống không chứa cụm từ parser dựa vào, và parser không tự nhận ra ý định từ chính tình huống (mọi kịch bản → `khong_ro`);
   - ý định gán trước theo kịch bản; split theo kịch bản;
   - kịch bản **đóng băng** trước khi mở form (`qreal/kich_ban_dong_bang.json`, B11h).

   Câu elicit ghi **riêng** ở `qreal/qelicit.json` và **KHÔNG tính** vào 400 vì chủ đề do người làm luận văn đặt.

**`nhap_qreal.py`:**
- nhận ra CSV xuất từ form theo các mã `[..]`, kể cả khi Google thêm tiền tố;
- chỉ lấy dòng đồng ý và cảnh báo mọi file/dòng bị bỏ;
- đánh dấu ô có nhiều câu (`nhieu_cau`);
- `--rut <mã>` xoá câu của người đó; câu trùng của người khác vẫn giữ.

**Kiểm thử:** `validate_benchmark` B11a–h, gồm nhập đầu–cuối trên dữ liệu GIẢ trong thư mục tạm. Có hai lượt review. Lượt 1 có 4 lỗi cao:
- B11 không kiểm đường nhập thật;
- file bị bỏ im lặng;
- câu tự do bị mớm;
- phần đồng ý thiếu.

Lượt 2 có 3 lỗi cao:
- kiểm nhầm đoạn văn bản;
- mã rút băm nằm trong file công khai, dò ngược được;
- câu chữ đồng ý chưa đúng sự thật.

Tất cả đã sửa.

**Hạn chế:**
- Nút *Quay lại* của Google Form cho phép sửa câu tự do sau khi đọc kịch bản (đã nhắc người trả lời).
- Tỉ lệ các bộ phụ thuộc số người tự chọn.
- Người trả lời là ai tuỳ cách Loi phát form: thiên lệch mẫu. Báo cáo sẽ ghi kênh phát.
- Script không bắt được tên người, nên vẫn phải rà tay.

**Trạng thái: Q-Real vẫn CHƯA ĐẠT (0/400)** cho tới khi có câu thật.

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

P20-4 (OCR mất ĐTBCHK thì từ chối cả học kỳ): xem mục 5d.

## 5d. P20-4 — mất ĐTBCHK: giữ từ chối, hỏi đúng MỘT con số (Loi chọn phương án A, 19/10/2026)

**Không nới được mà vẫn an toàn.** Ca M2 (bảng điểm sạch, chỉ mất ĐTBCHK) và ca F1 của `validate_ocr` trông **y hệt nhau** với hệ thống. Ở F1, sự thật là F nhưng OCR đọc nhất quán thành D, và cũng mất ĐTBCHK. Nếu tin điểm từng dòng khi mất ĐTBCHK thì M2 thành TRUE, nhưng F1 cũng thành TRUE, và đó là kết luận sai. Gold "TRUE" của M2 dựa trên sự thật mà hệ thống không biết được.

**Sửa (`w15_ocr/sang_ho_so`):**
- **Vẫn không tin điểm** của học kỳ mất ĐTBCHK.
- **Câu hỏi bổ sung** (`bc["can_hoi"]`) chỉ còn một mục `dtbchk:<học kỳ>`, tức "ĐTBCHK **in** trên bảng điểm", thay vì 5–7 học phần. Việc này cũng cải thiện P17-4/C4 cho trường hợp mất số.
- **Sinh viên khai báo số in** (`khai_bao["dtbchk_khai_bao"]`) thì kiểm chéo được khôi phục:
  - khớp số tính lại thì tin điểm, và ghi `bc["dtbchk_khai_bao"]` làm nguồn;
  - lệch thì vẫn không tin. Ca F1 khai báo số thật vẫn lệch, nên an toàn (F7).
- **Số OCR đọc được luôn thắng khai báo.**
- **Kiểm tra khai báo** (lỗi review: "NaN" từng làm học kỳ được tin):
  - chỉ nhận số hữu hạn trong [0, 4]; nhận cả dạng "3,08";
  - tên học kỳ được chuẩn hoá;
  - khai báo sai, tên học kỳ lạ, hoặc khác số OCR thì báo ở `bc["khai_bao_loi"]` và không crash;
  - học kỳ lệch tổng TC thì không dùng khai báo.

**Kiểm thử:** `validate_ocr` F5–F11.
- F5–F6, F9–F11 viết trước và fail với code cũ.
- F7–F8 là bất biến an toàn: đã đạt từ trước và phải tiếp tục đạt.
- F9 có thêm ca NaN, fail với bản sửa đầu.

**OCR-Noise dev** (`_sau_P20-4`):
- số **không đổi**: M2 vẫn bị từ chối 5/5, 0 unsound;
- câu hỏi lại giảm từ 5–7 học phần xuống **1 con số**.

Benchmark không có lượt hỏi đáp qua lại, nên Coverage của M2 vẫn **0%**. Mô phỏng lượt thứ hai, khi sinh viên trả lời đúng số in, thì cả 5/5 ca M2 ra TRUE, khớp gold. Đây là số **phân tích**, không phải số chính thức.

**Phương án B (Loi xác nhận bảng điểm in ĐTB/TC tích lũy sau từng học kỳ):** kiểm chéo thay thế bằng số tích lũy. Việc này cần đọc thêm dòng tích lũy (OCR) và kiểm trên ảnh thật, vì môi trường cloud không có ảnh, font hay Tesseract của Windows. Phương án này **lập kế hoạch riêng** (Viec_ton_dong C14).

## 5e. C12 — ý định xếp loại tốt nghiệp (Loi chọn (a) → QD-15, 19/10/2026)

**Parser** (`prototype._xep_loai`) dùng **danh sách CHO PHÉP**: chỉ nhận vài mẫu câu, và mẫu phải khớp **toàn câu**. Trước khi so khớp, câu được bỏ lời gọi đầu câu, trợ từ cuối câu và tiền tố "nếu tốt nghiệp (thì)".
- **Câu mở** ("Nếu tốt nghiệp, em xếp hạng gì?", "bằng của em loại gì") → `xep_loai`.
- **Câu có/không về đúng một hạng** ("em có đạt loại giỏi khi tốt nghiệp không", "ra trường em được bằng khá không") → `hang_cuoi(X)`.
- **Mọi câu khác bị từ chối**, gồm:
  - câu ngưỡng "đủ / trở lên / ít nhất loại X" (≥ X, khác QD-15 đúng hạng — chưa hỗ trợ, nên NL-09 vẫn bị từ chối);
  - phủ định, hạng đứng sau trong câu;
  - hệ quả hay định nghĩa của hạng;
  - câu ghép, câu hỏi về cơ hội trong tương lai;
  - người khác, "loại" theo nghĩa khác.

Hai lượt review đầu đi theo hướng **danh sách CHẶN**, và lần nào cũng còn lọt câu cho kết luận sai, nên em đổi sang danh sách cho phép. Lượt 3 tìm thêm hai lỗi, đã sửa:
- **Bỏ dấu toàn câu làm từ khác trùng nhau** (cô→có, hàng→hạng, bảng→bằng, đặt→đạt, tối→tôi). Mẫu nay khớp trên câu chỉ bỏ dấu **từ khoá**, và bắt buộc có chủ ngữ ngôi thứ nhất.
- **"Bằng gì" là hỏi tên văn bằng** (kỹ sư, cử nhân), không phải hạng, nên bị từ chối. Review cũng phát hiện câu "tốt nghiệp em được bằng trung bình hay khá" lọt vào nhánh `tot_nghiep`; nhánh này nay đã loại trừ "bằng + hạng".

**Trả lời** (`answer_xep_loai`):
- **QD-15:** "có đạt loại X" hỏi **đúng** hạng X, và câu trả lời luôn nêu hạng thực.
- **Luôn ghi "hạng DỰ KIẾN theo ĐTBCTL hiện tại"**, vì `hang_cuoi` không phụ thuộc việc đã đủ điều kiện tốt nghiệp.
- **Chưa có ĐTBCTL** thì trả UNKNOWN.

**Review lượt 1 tìm ra lỗ hổng KB (C15).** Đ34 k2 hạ hạng xuất sắc/giỏi một mức khi:
- (a) khối lượng học phần bị điểm F vượt 5%;
- (b) đã bị kỷ luật từ mức cảnh cáo cấp Trường (chép tay tr.20).

Nhưng `tc_diem_f` **không được sinh** ở đâu, và điểm b **chưa được hình thức hoá**, nên KB luôn coi như không hạ.

Câu trả lời nay **không tin hạng cuối của KB** với hạng gốc xuất sắc/giỏi:
- hạng cuối có thể bằng hạng gốc hoặc thấp hơn một mức, nên trả UNKNOWN kèm 2 dữ kiện cần xác nhận;
- câu "có đạt loại khá" khi hạng gốc là xuất sắc trả FALSE chắc chắn;
- khá và trung bình không bị hạ, nên trả lời chắc chắn.

**Kiểm thử:** `validate_integration` E29–E37 (câu mới).
- E29–E30 và E32–E37 viết trước và fail với code cũ.
- E31, E35, E38 và E39 là các ca âm tính. E35, E38 và E39 lấy từ review và fail với các bản trước.
- E40 là các ca dương có lời gọi đầu câu và chủ ngữ "mình/tôi".
- E41: không đạt mức hạng nào thì chứng chỉ vẫn có nguồn R-F06.
- Ba lượt review đối kháng.

**Số đo dev** (`_sau_C12`): G-Truth không đổi (58/58 sound). Q-Noise không đổi, vì NL-09 thuộc test.

**Q-Noise:** NL-09 ("có **đủ** xếp loại giỏi") là câu ngưỡng, nên vẫn bị từ chối, đúng như ý định kỳ vọng lúc đóng băng. Vì vậy **không cần errata**.

**Q-Elicit v2:** KB-05 bản v1 ("bằng của bạn loại gì") trùng đúng mẫu parser mới, nên mớm lời. Em viết lại câu này **trước khi mở form**; hash v1 vẫn giữ.

## 5f. C15 — R-Formal v1.11: hạ một mức hạng xuất sắc/giỏi (QĐ3266 Đ34 k2, Loi duyệt 19/10/2026)

**Lỗi.** Luật hạ bậc chỉ đọc dữ kiện `tc_diem_f`, mà **không nơi nào sinh dữ kiện này** (chỉ có trong test), nên luật không bao giờ chạy. Đ34 k2 điểm b (kỷ luật từ mức cảnh cáo cấp Trường, chép tay tr.20) thì chưa được hình thức hoá. Ngoài ra `why(hang_cuoi, r_f07)` được sinh vô điều kiện.

**Sửa:**
- **R-Formal v1.11:**
  - TC các học phần có **điểm cuối F** là cận dưới chắc chắn, vì điểm cuối F thì không phải lần học cải thiện (R-B13);
  - `tc_diem_f` là khai báo của sinh viên;
  - thêm **R-F07b** (điểm b);
  - các bước `why` chỉ sinh khi thực sự hạ bậc.
- **`graduation_solver` mục 0:** chưa khai báo thì **mở nhánh** trên các atom **tự do**:
  - `f_ngoai_ho_so_vuot_5`: học phần từng F rồi học lại đạt, không còn trên hồ sơ;
  - `ky_luat_canh_cao_cap_truong`.
- **Học phần điều kiện** (GDQP, GDTC, NN/TH căn bản): văn bản không nói rõ chúng có thuộc "tổng số TC quy định của CTĐT" hay không. Nếu chỉ khi tính cả chúng mới vượt 5% thì **mở nhánh** `hp_dk_tinh_vao_tong` (A17, ca D5).
- **Schema và loader:**
  - thêm hai khai báo `tc_diem_f` (TC học phần **không điều kiện** từng bị F) và `ky_luat_canh_cao_cap_truong`;
  - loader kiểm kiểu (số nguyên ≥ 0 / true-false), sai thì bỏ khai báo và báo mâu thuẫn;
  - KB lấy giá trị lớn hơn giữa khai báo và số tính từ hồ sơ.
- **Review lượt 1 tìm ra hai lỗi cao, đã sửa:**
  - Bản đầu chọn trực tiếp trên atom được suy ra `vuot_5_phan_tram`, khiến abstention hỏi nhầm sinh viên về tín chỉ F trong câu hỏi tốt nghiệp (w16 B5 không đạt).
  - Vòng lặp lẻ khiến nhánh A17 không bao giờ mở, tức hệ thống âm thầm chọn cách hiểu "có tính". Nay `vuot_5_chac` tách riêng, và atom tự do độc lập với điểm.
- **Abstention:** hỏi đúng hai dữ kiện này.
- **Prototype:** bỏ phần tạm né của C12, dùng thẳng `hang_cuoi` của KB.
- **Catalog:** 96 quy tắc, F = 60 (thêm R-F07b).

**Kiểm thử:**
- **Ca hồi quy fail với luật cũ:**
  - `validate_rformal`: C47, C49, C50, C52;
  - `validate_graduation`: D1, D3, D5;
  - `validate_student_facts`: L5;
  - `validate_integration`: E42.
- **Bất biến** (đạt cả với luật cũ): C48, C51, C53, D2, D4, D6. w16 B5 giữ: không hỏi thừa.

**Errata G-Truth** (`gtruth_errata.json`, không sửa gold). HG-02/04/08 thuộc split test và được ghi errata **trước** lần chạy test (Tuần 22). Gold errata khớp hệ thống mới là do thiết kế, nên Tuần 22 sẽ báo cả hai cách chấm. Gold TRUE của HG-02/03/04/08 (hạng giỏi/xuất sắc) ngầm giả định "không F, không kỷ luật". Hồ sơ không khai báo hai dữ kiện này, nên theo quy chế câu trả lời đúng là **UNKNOWN**. `run_cpa2` in thêm dòng `[theo errata]`.

**G-Truth dev** (`_sau_C15`):

| Cách chấm | Sound | Coverage | Đúng / 58 | Ghi chú |
|---|---|---|---|---|
| Chính thức (gold đóng băng) | 100% | 91,4% | 57 | HG-03 từ chối thừa |
| Theo errata | 100% | 91,4% | 58 | |

## 5g. C14 — kiểm chéo bằng số tích lũy in sau mỗi học kỳ (P20-4 phương án B, Loi duyệt 19/10/2026)

Sau mỗi học kỳ, bảng điểm in "Tổng Số Tín Chỉ Tích Lũy" và "Điểm T.Bình chung tích lũy (hệ 4)" (Loi xác nhận 19/10/2026). C14 dùng hai số này theo hai cách (`w15_ocr/ocr_transcript.py`).

**1. Luôn kiểm TC tích lũy khi đọc được — bịt một lỗ hổng có sẵn.** Lỗi: GDTC (TC100) thật là F nhưng OCR đọc nhất quán thành D, và hệ thống kết luận **TRUE sai** (sự thật FALSE). ĐTBCHK không tính GDTC (R-B08), nên kiểm chéo cũ không thấy lỗi này. Ca G9 tái hiện lỗi trên mã cũ.
- Số TC tích lũy là số nguyên, nên lỗi đạt↔F luôn làm lệch.
- Lệch ở học kỳ i thì nghi mọi học kỳ từ sau mốc khớp gần nhất đến i.
- Dòng GDTC chỉ được tin qua **phép thử lật giả thuyết**: phải có một lần kiểm mà khi lật đạt↔F của chính dòng đó, số in rơi ra ngoài tập giá trị tính lại.

**2. Cứu học kỳ mất ĐTBCHK** (không có khai báo). Học kỳ được tin khi đủ các điều kiện:
- mọi học kỳ trước đã được tin;
- mọi dòng đến học kỳ này đều biết điểm, và không có dòng miễn trong khi chưa biết quy ước của trường;
- TC tích lũy khớp **chính xác**;
- ĐTBCTL khớp trong ±0,006;
- **đủ độ phân giải:** lệch một bậc (0,5) của học phần không điều kiện nhỏ nhất trong học kỳ làm ĐTBCTL đổi hơn 0,011 (= dung sai 0,006 + sai số làm tròn số in 0,005). Học kỳ muộn có mẫu số lớn nên thường không đạt, ví dụ HK9 của sv_tltn có độ phân giải 0,0107 (G4).

Dòng GDQP trong học kỳ được cứu vẫn để "không chắc", vì số tích lũy chỉ xác nhận đạt/rớt mà TB GDQP cần mức điểm. Hệ thống vẫn hỏi một số ĐTBCHK để chốt.

**Sửa kèm:**
- `render_transcript`: TC tích lũy in ra chỉ cộng 10 TC của CC004 ở đúng học kỳ chứa nó; nay cộng vào mọi học kỳ sau.
- `w17/dau_vao`: bộ dựng tài liệu sinh hai số tích lũy từ dữ liệu oracle, cài độc lập với bộ kiểm. Phép `hoc_lai` tính lại số tích lũy và phải đứng trước mọi phép đọc sai.

**Review hai lượt tìm ra lỗi trong chính bản sửa, đã sửa:**
- **Mức cao — "nhận TC tích lũy có hoặc không cộng TC miễn" là độ chùng.** Nó che lỗi đạt↔F của học phần có TC đúng bằng tổng TC miễn.
  - Nhánh cứu: cho **FALSE sai** (G12). Nay khi có dòng miễn mà chưa biết quy ước (hằng `MIEN_TRONG_TC_TICH_LUY = None`) thì không cứu.
  - Nhánh luôn kiểm: cho TRUE sai với GDTC (G13).
- **Mức trung bình — độ chùng thứ hai.** Dòng không đọc được điểm cùng số TC cũng che lỗi GDTC (G15). Nay xử lý bằng phép thử lật giả thuyết, bao mọi nguồn độ chùng.
- **Mức trung bình — mã GDTC thật TC025–027** (ngoài KB, xem Bài học) bị tính vào ĐTBCTL, nên không cứu được học kỳ nào trên bảng điểm thật. Nay có bảng `DIEU_KIEN_NGOAI_KB` (G14).
- **Mức thấp:**
  - mốc chỉ dời khi khớp không nhờ độ chùng;
  - parser bỏ qua dòng học kỳ bị OCR làm hỏng chữ "Học Kỳ";
  - không ghi khai báo ĐTBCHK làm nguồn cho học kỳ bị nghi;
  - guard `hoc_lai`.

**Kiểm thử** (`validate_ocr` nhóm G/G'): 16 ca G0–G15 và 2 ca G11 OCR ảnh tổng hợp (Tesseract đọc đủ hai số tích lũy).
- Bản đầu: chạy trên mã cũ có **8 ca fail**, trong đó G9 cho TRUE sai.
- G12–G15 viết sau review: fail trên bản sửa trước đó, cho FALSE sai, TRUE sai, mất độ phủ, TRUE sai theo thứ tự.
- Nhóm F (P17-2, P20-4) giữ nguyên ý nghĩa: tài liệu không có dòng tích lũy.

**OCR-Noise dev** (`_sau_C14`; gold không đổi, split test không chạy):

| | Sound | Coverage | Đúng / 20 | M2 |
|---|---|---|---|---|
| Sau P20-4 | 100% | 25,0% | 15 | 0/5 |
| Sau C14 | 100% | 45,0% | 19 | **4/5** |

ON-10M2 vẫn từ chối (HK1 toàn HP điều kiện, có GDQP). ⚠️ **Cách dựng đầu vào M2 đã đổi:** tài liệu nay có thêm hai dòng tích lũy đọc đúng, khớp mô tả "không đọc được ĐTBCHK, không có lỗi nào khác". Gold không đổi. Ca w17 OC-11 (F→D + mất ĐTBCHK) nay bị bắt bởi TC tích lũy và vẫn trả UNKNOWN.

**Giới hạn** (chưa kiểm trên ảnh bảng điểm thật, cần Loi chạy `validate_ocr` phần D trên Windows; kết quả vào `_rieng/`):
- nhãn dòng tích lũy trên bảng điểm thật có đọc được không;
- TC tích lũy có cộng TC dòng miễn không (đặt `MIEN_TRONG_TC_TICH_LUY`);
- TC tích lũy có gồm HP điều kiện không. Đây là giả định "có", theo bố cục bảng điểm đã chép trong `render_transcript`.

Công thức của trường khác giả định thì chỉ mất độ phủ. Không đọc được dòng tích lũy thì GDTC vẫn như trước C14 (chưa kiểm được). Mỗi lần chỉ giả định một lỗi: nhiều lỗi bù trừ nhau chưa xét, giống kiểm chéo ĐTBCHK.

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

- **P20-5 (an toàn — 4 unsound; đã sửa, xem dưới).** Câu không dấu "Em co du dieu kien lam **luan van** tot nghiep khong?" (EL-01…04, V1) bị parser hiểu thành `tot_nghiep`. Nguyên nhân: nhánh tốt nghiệp không dấu có danh sách loại trừ (`luận văn`, `tiểu luận`, `đtbctl`, `loại`…) chỉ ở dạng **có dấu**. Hệ thống trả FALSE cho câu "đủ điều kiện tốt nghiệp", không phải câu đã hỏi.
  - Chấm theo gold thuần thì chỉ 2 ca sai (EL-02/04 tình cờ trùng gold FALSE). Chấm chặt cho 4 — đúng loại lỗi P18-1/P19-4/P20-2: trả lời một câu khác mà vẫn kèm chứng chỉ.
  - Thêm một lỗi tiềm ẩn cùng họ: `answer_eligibility` chọn TLTN bằng cách tìm chuỗi `"tiểu luận"` có dấu, nên câu "tieu luan" sẽ bị xét như LVTN.
- **Parser không nhận câu không dấu và viết tắt (an toàn — chỉ từ chối thừa).**
  - V1: 13/26 câu bị từ chối thừa, do regex đăng ký cần "đăng ký/được".
  - V2/V4: gần như toàn bộ bị từ chối thừa (23/26), do "đk/đki/dky", "đc/dc", "tn", "lv", "hp" không có trong parser.
  - Hệ thống không kết luận sai ở đây, nhưng sinh viên gõ như thật thì hầu như không được trả lời.
- **V3 (gõ vội) bền hơn** (20/26). Các ca hỏng là ca có đúng từ khoá bị mất dấu ("đăng ky", "dang ký", "nien luận").

Theo quy tắc nhiễm dữ liệu (Bài học): đây là số **chính thức** của Q-Noise dev. Q-Noise test (110 câu) để chạy một lần ở Tuần 22 cùng G-Truth test.

### Sửa P20-5 + chuẩn hoá cách gõ (Loi duyệt "cả 2", 18/10/2026) — dev ĐÃ NHÌN THẤY

`prototype.py`: mọi khớp ý định chạy trên `chuan_hoa(câu hỏi)`.

- **Bỏ dấu có chọn lọc.** Bỏ dấu chỉ các từ thuộc bộ từ khoá `TU_KHOA`; từ có dấu khác giữ nguyên nên không khớp mẫu.
  - Lượt review 1 cho thấy bỏ dấu MỌI từ làm *thế→the, dự/dư→du, nền→nen* trùng từ khoá, nên câu trước đây bị từ chối lại bị trả lời như câu khác.
- **Mở viết tắt theo ngữ cảnh:**
  - *đk* trước HP/mã/hủy/rút là "đăng ký", còn lại là "điều kiện";
  - *tn* = tốt nghiệp chỉ sau xét/điều kiện/luận văn/tiểu luận (lượt 2: "em tn cho thầy" là nhắn tin);
  - *tl tn*, *lv*, *lvtn*, *tltn*, *hp*, *hk*, *đc*, *ko*, *e*.
- **Câu hỏi mở bị chặn khỏi ý định có/không.** "Thế nào / ở đâu / là gì / mấy / vì sao…" không còn vào được các ý định có/không.
- **Câu đăng ký** phải đủ các điều kiện sau:
  - đúng MỘT mã HP;
  - có "được/chưa/không";
  - không hỏi trạng thái "đã đăng ký";
  - không có "thì …" sau mã.
- **Câu tốt nghiệp** loại thêm: lễ, thẻ SV, đồ án, khoá luận, thực tập, giỏi, hoãn, "khi tốt nghiệp", tín chỉ. Loại trừ có cả dạng có dấu và không dấu.
- **Câu luận văn** chỉ là "làm LV/TL (tốt nghiệp) chưa/không" — không phải "làm luận văn nhóm", "tiểu luận thay luận văn".
- **Các chỗ khác:**
  - "nếu" là phản thực tế kể cả khi thiếu "thì";
  - đọc chọn TLTN từ câu đã chuẩn hoá;
  - bỏ khoá stub `du_dk_dang_ky` không đối số (P18-1);
  - đề xuất đọc học kỳ từ câu không dấu, ưu tiên "kỳ N", "he" không dấu chỉ là hè sau kỳ/học/mùa (P19-3).

**Kiểm thử:** `validate_integration` E17–E28. Câu mới, không chép từ Q-Noise; E17–E21 và E25–E28 fail với code cũ. Hai lượt review đối kháng: lượt 1 có 5 lỗi cao, lượt 2 có 1 lỗi cao, đều đã sửa và có ca hồi quy. Mọi tuần 5–20 ĐẠT.

**Sau sửa** (`--hau-to _sau_P20-5`, KHÔNG thay số chính thức):

| Bộ dev | Soundness | Coverage | Ghi chú |
|---|---|---|---|
| Q-Noise (130) | 0 unsound → **100%** | 88,5% (V0–V4 đều 26/26 đúng ý định) | phần chưa phủ = câu ngoài phạm vi, gold UNKNOWN |
| G-Truth (58) | 100% | 93,1% | không đổi so với sau P20 |

**Hai lưu ý về độ tin cậy của các số sau sửa:**
- **Q-Noise sau sửa không độc lập.** Bảng viết tắt trong parser trùng bảng sinh Q-Noise, và đã sửa sau khi nhìn thấy dev. Ví dụ câu "khong??" lỗi vì hai dấu hỏi, phát hiện khi chạy dev. Số đáng tin hơn là Q-Noise **test** (Tuần 22), mà test cũng dùng cùng bảng viết tắt, nên chỉ Q-Real mới đo được cách gõ thật.
- **Từ gõ KHÔNG dấu vẫn mơ hồ** ("the", "du", "thi"). Chốt chặn chỉ giảm chứ không loại bỏ hết khả năng trả lời nhầm. Nguyên tắc vẫn là nghiêng về từ chối.

## 6. Hạn chế

- Q-Real 0/400: chưa đo được parser trên câu thật. Q-Noise chỉ đo độ bền với cách gõ do em **tự định nghĩa** (bảng viết tắt, kiểu gõ vội) — không đại diện phân bố câu thật.
- Gold do một người (Claude) viết. Đã có một lượt soát độc lập bằng agent, nhưng **chưa phải người thứ hai** để đo κ (A7).
- OCR-Noise dựng ở mức tài liệu (sau nhận dạng), không render ảnh + Tesseract (phụ thuộc môi trường, như w17).
- Mới chạy dev. Test chạy một lần ở Tuần 22.
- Sau khi sửa P20-1…3 trên dev, dev sẽ "đã thấy". Số chính thức là test (Tuần 22).

## 7. Việc còn lại → Tuần 21+

- [ ] **Cần Loi:** câu hỏi thật cho Q-Real (≥ 400), đặt vào `qreal/_tho/`. Đã có form (§3b): điền `<<ĐIỀN>>`, tạo Google Form theo `qreal/bieu_mau.md`, phát cho sinh viên, xuất CSV vào `_tho/`
- [x] Sửa P20-1 — R-Formal v1.10 + QD-14 (mục 5b)
- [x] Sửa P20-2/P20-3 (mục 5b)
- [x] P20-4 (M2 OCR): giữ từ chối, hỏi 1 số ĐTBCHK, nhận khai báo số in (mục 5d)
- [x] P20-4 phương án B (C14): kiểm chéo bằng ĐTB/TC tích lũy in sau mỗi học kỳ + bịt lỗ GDTC F→D (mục 5g)
- [ ] **A18 (cần Loi, Windows):** kiểm C14 trên ảnh bảng điểm thật — đọc được dòng tích lũy? TC tích lũy có cộng TC miễn / HP điều kiện?
- [x] C12 ý định xếp loại tốt nghiệp (mục 5e, QD-15)
- [x] **C15 (KB):** R-Formal v1.11 — hạ bậc Đ34 k2 a+b, mở nhánh khi chưa khai báo, errata HG (mục 5f)
- [ ] **A17 (cần Loi / Phòng Đào tạo):** học phần điều kiện có tính vào "khối lượng HP bị điểm F … so với tổng số TC quy định của CTĐT" (Đ34 k2 a) không
- [x] **P20-5** (an toàn) + parser chuẩn hoá bỏ dấu/viết tắt (mục 5c, E17–E28)
- [x] Q-Elicit (20 kịch bản, đóng băng) + nội dung Google Form + nhập CSV/rút lại (§3b)
- [ ] Tuần 21: chạy baseline (LLM thuần, RAG thuần, tool-calling) trên `baseline_dev/test.jsonl` (cần API key, `.env`)
- [ ] Tuần 22: chạy CPA² trên test (một lần), báo cáo cả hai loại gold

### Ghi chú kiểm chứng

- [x] Có ground truth: G-Truth 115 + OCR-Noise 40, gold viết tay, nguồn, oracle, dev/test, đóng băng `312b7ff` trước lần chạy đầu
- [x] Đầu vào baseline trung lập (B8)
- [ ] Q-Real (0/400) — chờ dữ liệu
- [x] Q-Noise v1 (tổng hợp): 240 câu, gold kế thừa, ý định gán tay, đóng băng `5d8601c` trước khi chạy; dev đã chạy
- [x] Mọi tuần 5–20 ĐẠT
