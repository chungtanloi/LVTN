# TUẦN 4 — SOLVER DESIGN NOTE

**Sản phẩm:** Solver design note
**Tiêu chí hoàn thành:** chọn solver + lý do ✅
**Bằng chứng kèm theo:** prototype chạy được trong `w4_solver_probe/`, đã đo và **đối chiếu chéo ba solver**


> **ĐÍNH CHÍNH SAU TUẦN 6** — xem `w4_solver_probe/ERRATA_Tuan6.md`.
> 1. Dữ liệu `kb.py` sai 9 chỗ so với CTĐT K49 thật (CT466E là niên luận 3 TC, luận văn là
>    CT550E 15 TC và thuộc nhóm tự chọn; không có nhóm "10 chọn 2"; 6 cạnh tiên quyết giả). Đã sửa.
> 2. Mục 3.2: con số *"CP-SAT nhanh hơn clingo ~15×"* là **tạo tác đo** — clingo chạy
>    `--opt-mode=optN` nên liệt kê 9 950 kế hoạch tối ưu. Với `--opt-mode=opt`, clingo giải T3 trong
>    ~2,5 ms (CP-SAT ~19 ms). Lựa chọn clingo cho T1 giữ nguyên; **vai trò CP-SAT cho T3 để mở**
>    cho tới khi đo trên CTĐT đầy đủ (Tuần 12). Ba solver vẫn trùng khớp (k = 4).

---

## 0. Kết luận trước

> **Chọn kiến trúc HAI SOLVER:**
> **clingo (ASP)** làm bộ giải chính cho suy diễn ba trị và sinh chứng chỉ.
> **OR-Tools CP-SAT** làm bộ giải chuyên dụng cho nhánh lập kế hoạch phản thực (RQ3).
> **Z3 (SMT)** giữ vai trò **bộ đối chứng độc lập** để kiểm tra mô hình hoá, không đưa vào đường chạy chính.

Lý do ngắn gọn: ASP cho **ngữ nghĩa ba trị miễn phí** (cautious/brave consequences) — đúng thứ RQ2 cần và không solver nào khác cho sẵn; CP-SAT nhanh hơn một bậc độ lớn ở bài toán tối ưu tổ hợp; Z3 dùng để bắt lỗi mô hình hoá, vì hai cài đặt độc lập cho cùng đáp án là bằng chứng mạnh hơn một cài đặt tự kiểm tra chính mình.

---

## 1. Ba tác vụ lõi cần solver

| Mã | Tác vụ | Bản chất tính toán | RQ liên quan |
|---|---|---|---|
| **T1** | Xét điều kiện tốt nghiệp dưới dữ kiện khuyết | **Suy diễn có kéo theo (entailment)** trên miền mở | RQ2 |
| **T2** | Nhóm tự chọn N-of-M | Ràng buộc đếm | RQ1 |
| **T3** | Số học kỳ tối thiểu còn lại (phản thực) | **Tối ưu tổ hợp** trên DAG có ràng buộc dung lượng | RQ3 |

T1 và T3 khác nhau **về loại bài toán**, không chỉ về độ khó — đó là lý do một solver duy nhất không phải lựa chọn tốt nhất.

---

## 2. Điểm mấu chốt: ba trị phải là SUY DIỄN, không phải if-else

Đây là chỗ dễ làm sai nhất, và cũng là chỗ đóng góp thật của đề tài.

**Cách làm sai (nhưng rất cám dỗ):** viết `if thiếu_dữ_liệu: return "không biết"`. Cách này không có bảo đảm gì — vẫn phải tự tay liệt kê mọi tình huống thiếu dữ liệu, và sẽ bỏ sót.

**Cách làm đúng:** để dữ kiện chưa biết làm **biến tự do**, rồi hỏi solver về mọi thế giới khả dĩ:

```
KB = quy chế ∧ CTĐT ∧ dữ kiện đã biết       U = tập dữ kiện chưa biết (biến tự do)

  KB ∧ ¬Grad  là UNSAT   →  Grad ĐÚNG trong MỌI thế giới khả dĩ        →  TRUE
  KB ∧  Grad  là UNSAT   →  Grad SAI  trong MỌI thế giới khả dĩ        →  FALSE
  cả hai đều SAT         →  kết luận phụ thuộc U                       →  UNKNOWN
                            và chính U là "dữ kiện còn thiếu" trả về
```

Ba trị lúc này là **hệ quả toán học của mô hình**, không phải một nhánh `if` do lập trình viên nghĩ ra. Đây là điều làm cho tuyên bố *"hệ thống không thể nói sai"* trở nên khả bác bỏ.

**Trong ASP điều này có sẵn trong ngữ nghĩa:**

- `cautious consequences` = tập nguyên tử đúng trong **mọi** answer set → `TRUE`
- `brave consequences` = đúng trong **ít nhất một** answer set
- nằm trong brave nhưng không trong cautious → `UNKNOWN`
- không nằm trong brave → `FALSE`

Chỉ cần chạy solver hai lần với `--enum-mode=cautious` và `--enum-mode=brave`. **Không cần tự dựng công thức phủ định như với SMT.** Đây là lợi thế kiến trúc, không phải lợi thế hiệu năng.

---

## 3. Prototype và kết quả đo thật

Prototype nằm ở `w4_solver_probe/`, mô hình hoá **cùng một bài toán ba lần** bằng ba công nghệ khác nhau.

**Dữ liệu dùng:** trích từ CTĐT ngành CNTT ĐHCT — 30 học phần, đồ thị tiên quyết thật (`core/constants.py: PREREQS`), một nhóm tự chọn 10-chọn-2, trần 20 TC/học kỳ. Ba hồ sơ thử nghiệm: SV-A (đủ điều kiện), SV-B (thiếu điểm 2 môn), SV-C (rớt CT177, có 1 môn được miễn).

### 3.1. T1 + T2 — xét tốt nghiệp ba trị

```
Ho so    Z3               ms   clingo           ms    khop?
SV-A     TRUE           26.6   TRUE            2.8       OK
SV-B     UNKNOWN        28.9   UNKNOWN         8.7       OK
SV-C     FALSE          22.6   FALSE           2.7       OK
```

- **Ba trị chạy đúng.** SV-B ra `UNKNOWN` và hệ thống chỉ đúng hai dữ kiện thiếu: CT312, CT282E. Đây chính là hành vi mà mọi baseline không có — chúng sẽ trả lời chắc nịch.
- SV-C ra `FALSE` kèm ba điều kiện hỏng: `required`, `elective_n_of_m`, `credits` → phản ví dụ dùng được ngay để diễn đạt.
- **clingo nhanh hơn Z3 khoảng 3–10×** ở tác vụ này.

### 3.2. T3 — số học kỳ tối thiểu (truy vấn phản thực)

```
Z3 Optimize      k = 3       281.6 ms
clingo (ASP)     k = 3       499.5 ms
CP-SAT           k = 3        33.6 ms

Doi chieu cheo ba solver: TRUNG KHOP  (k = 3)
So hoc phan trong ke hoach: Z3=15, clingo=15, CP-SAT=15
```

- **CP-SAT nhanh hơn ~8× so với Z3 và ~15× so với clingo** trên cùng bài toán, và chứng minh được tối ưu (`status=OPTIMAL`).
- Ba cài đặt hoàn toàn độc lập cho **cùng đáp án k = 3 và cùng số học phần 15** → bằng chứng mạnh rằng mô hình hoá không sai.

### 3.3. Giá trị phương pháp luận của việc đối chiếu chéo

Đây không chỉ là bài đo hiệu năng. Trong quá trình làm, **việc so ba solver đã bắt được hai lỗi mô hình hoá thật**:

1. Ràng buộc trần tín chỉ ban đầu áp cho **cả học phần không được chọn học**, khiến solver buộc phải học thừa 4 môn tự chọn thay vì 2. Chỉ phát hiện khi thấy Z3 và CP-SAT cho số môn khác nhau.
2. Học phần luận văn CT466E bị bỏ khỏi kế hoạch trong bản ASP do phân loại `required` không bao trùm loại `thesis`. Phát hiện khi số học phần lệch 14 vs 15.

→ **Đề xuất đưa vào phương pháp của luận văn:** giữ cài đặt đối chứng bằng solver thứ hai như một phần của quy trình kiểm chứng, không chỉ là thí nghiệm một lần. Đây là cách kiểm chứng rẻ và mạnh cho phần "KB có đúng không" — vốn là điểm yếu cố hữu của mọi công trình Rules as Code.

---

## 4. So sánh ba công nghệ theo tiêu chí của đề tài

| Tiêu chí | **clingo (ASP)** | **Z3 (SMT)** | **CP-SAT** |
|---|---|---|---|
| Ngữ nghĩa ba trị | ✅ **có sẵn** (cautious/brave) | ⚠️ phải tự dựng entailment hai chiều | ❌ không có khái niệm |
| Suy diễn trên miền mở (open-world) | ✅ tự nhiên với choice rule | ⚠️ mô phỏng được bằng biến tự do | ❌ |
| Sinh **chứng chỉ / dẫn xuất** | ✅ dẫn xuất là answer set, đọc được | ⚠️ có unsat core nhưng khó diễn đạt cho người dùng | ❌ chỉ có lời giải, không có "vì sao" |
| Chỉ ra **dữ kiện còn thiếu** | ✅ hiệu brave \ cautious | ⚠️ phải liệt kê thủ công | ❌ |
| Ràng buộc đếm / N-of-M | ✅ `#count`, `#sum` gọn | ✅ dùng `If`+`Sum` | ✅ |
| Số học thực (CGPA có chia) | ⚠️ phải nhân 10 để dùng số nguyên | ✅ **hỗ trợ Real gốc** | ⚠️ chỉ số nguyên |
| Tối ưu tổ hợp (T3) | ⚠️ được nhưng chậm (~500 ms) | ⚠️ được, trung bình (~280 ms) | ✅ **nhanh nhất (~34 ms)** |
| Chứng minh tối ưu | ✅ | ✅ | ✅ có báo `OPTIMAL` |
| Tốc độ T1 | ✅ **3–9 ms** | ⚠️ 22–29 ms | — |
| Diễn đạt gần với văn bản luật | ✅ **rất gần** (rule ↔ điều khoản) | ⚠️ SMT-LIB xa ngôn ngữ tự nhiên | ❌ xa nhất |
| Hệ sinh thái Python | ✅ `clingo` | ✅ `z3-solver` | ✅ `ortools` |
| Công trình liên quan dùng nó | [10] ASP course planning | [3] CoTu, [5] UW solver-aided | — |

---

## 5. Quyết định và lý do

### 5.1. clingo (ASP) — bộ giải chính

**Bốn lý do:**

1. **Ba trị là ngữ nghĩa sẵn có, không phải kỹ thuật chắp vá.** RQ2 là đóng góp cốt lõi. Với ASP, `UNKNOWN` và danh sách dữ kiện thiếu rơi ra trực tiếp từ hiệu `brave \ cautious`. Với SMT phải tự dựng hai truy vấn phủ định và tự liệt kê biến gây nhập nhằng — làm được, nhưng đó là code của mình chứ không phải bảo đảm của solver, và **luận điểm "không thể nói sai" yếu đi đúng ở chỗ đó**.

2. **Rule ↔ điều khoản gần như một-một.** Điều này quan trọng cho RQ1 và cho chứng chỉ: một dòng ASP ánh xạ được về một khoản của QĐ3266, nên `certificate` truy vết tới nguồn một cách tự nhiên. SMT-LIB không có tính chất này.

3. **Nhanh nhất ở tác vụ chạy nhiều nhất.** T1 là truy vấn phổ biến nhất trong hệ thống thật; 3–9 ms so với 22–29 ms là chênh lệch đáng kể khi nhân với lưu lượng.

4. **Có tiền lệ trong đúng miền.** Kahraman & Erdem [10] đã dùng ASP cho lập kế hoạch học tập cá nhân hoá — có thể trích dẫn để biện minh lựa chọn công nghệ.

### 5.2. CP-SAT — nhánh lập kế hoạch phản thực

**Lý do:** T3 là bài toán tối ưu tổ hợp thuần tuý, không cần suy diễn miền mở. CP-SAT nhanh hơn một bậc độ lớn, chứng minh được tối ưu, và **RQ3 cần đo `Counterfactual Optimality Gap`** — tức phải có lời giải tối ưu thật làm chuẩn. Dùng CP-SAT ở đây là chọn đúng công cụ cho đúng việc.

**Nối hai solver thế nào:** ASP quyết định *phải học những gì* (T1, T2 — kết quả là tập học phần còn thiếu, có chứng chỉ); CP-SAT quyết định *xếp vào các kỳ ra sao* (T3). Ranh giới sạch, không chồng lấn.

### 5.3. Z3 — bộ đối chứng, không nằm trong đường chạy chính

**Lý do giữ lại dù không dùng trong production:**

1. Đã bắt được **2 lỗi mô hình hoá thật** chỉ trong buổi prototype đầu tiên.
2. Z3 hỗ trợ **số thực gốc** — hữu ích khi kiểm tra các ràng buộc CGPA có chia mà ASP phải nhân 10 để tránh. Nếu hai bên cho cùng kết quả thì thủ thuật nhân-10 là đúng.
3. CoTu [3] và Solver-Aided Policy [5] đều dùng Z3 → giữ một cài đặt Z3 cho phép **dựng baseline neuro-symbolic công bằng** cho phần đánh giá (Tuần 21).

---

## 6. Rủi ro kỹ thuật đã nhận diện

| Rủi ro | Bằng chứng | Giảm thiểu |
|---|---|---|
| **Bùng nổ tổ hợp khi nhiều dữ kiện khuyết.** Mỗi môn `unknown` sinh 8 giá trị điểm khả dĩ → 8^n answer set | SV-B với 2 môn khuyết đã chậm gấp ~3× so với SV-A/SV-C (8,7 ms vs 2,8 ms) | Không liệt kê toàn bộ điểm: chỉ cần biến nhị phân `passed/not passed` cho đa số ràng buộc; chỉ mở rộng ra thang điểm khi ràng buộc **thực sự** động tới CGPA. Cần đo lại ở n = 5, 10, 20 |
| **CGPA phải nhân 10 trong ASP** — nguy cơ sai số làm tròn ở ca sát ngưỡng (CGPA đúng 2,00) | Chưa gặp, nhưng ca sát ngưỡng nằm trong bộ Adversarial của Tuần 17 | Đối chứng bằng Z3 với số thực gốc trên toàn bộ ca sát ngưỡng |
| **Chân trời lập kế hoạch cố định (horizon = 8)** | Nếu lời giải cần > 8 kỳ, mô hình báo vô nghiệm thay vì báo "cần nhiều hơn 8 kỳ" | Tăng dần horizon cho tới khi có nghiệm; phân biệt rõ *vô nghiệm* với *vượt chân trời* |
| **KB thu nhỏ**: prototype dùng 30 học phần, CTĐT thật > 60 | Chưa đo ở quy mô thật | Kiểm tra khả năng mở rộng ngay đầu Tuần 6 khi có Curriculum KB đầy đủ |
| **Số liệu quy chế trong prototype là số thu nhỏ** (120 TC, ngưỡng cảnh báo 1,20) | Chỉ để chạy thử | **Bắt buộc** thay bằng số thật từ QĐ3266 và CTĐT K51 ở Tuần 5–6 |

---

## 7. Hồ sơ prototype

```
w4_solver_probe/
├── kb.py             Tri thức nền: 30 học phần, tiên quyết thật, nhóm 10-chọn-2,
│                     3 hồ sơ thử nghiệm (đủ / thiếu dữ liệu / rớt môn)
├── probe_z3.py       Z3 — T1 ba trị bằng entailment hai chiều; T3 bằng Optimize
├── probe_clingo.py   clingo — T1 ba trị bằng cautious/brave; T3 bằng ASP + #minimize
├── probe_cpsat.py    CP-SAT — chỉ T3
├── bench.py          Đo thời gian + đối chiếu chéo ba solver
└── bench_output.txt  Kết quả chạy thật
```

Chạy: `python3 bench.py` (cần `pip install z3-solver clingo ortools`).

---

## 8. Đầu vào cho Tuần 5–6

Việc chọn solver xong không có nghĩa là hết việc. Ba câu hỏi thiết kế còn treo, phải chốt khi bắt đầu hình thức hoá thật:

1. **Biểu diễn điểm số:** giữ nhị phân `passed/failed` ở đâu, giữ thang điểm đầy đủ ở đâu? Đây là đánh đổi trực tiếp giữa hiệu năng và độ chính xác của CGPA.
2. **Con trỏ nguồn:** mỗi rule ASP phải mang theo `source(RuleID, Dieu, Khoan)` để chứng chỉ truy vết được. Thiết kế lược đồ này trước khi viết rule đầu tiên, không phải sau.
3. **Độ tin cậy OCR:** dữ kiện có `confidence` thấp nên coi là `unknown`, hay là dữ kiện có trọng số? Quyết định này ảnh hưởng toàn bộ Tuần 15–16.

---

### Ghi chú kiểm chứng

- [x] Ba solver cho cùng đáp án trên T1 và T3 — đã đối chiếu chéo tự động trong `bench.py`
- [x] Ba trị phân biệt đúng TRUE / FALSE / UNKNOWN trên ba hồ sơ đại diện
- [x] Chưa kiểm tra khả năng mở rộng ở quy mô CTĐT thật (> 60 học phần) — ✅ đã xong: Tuần 6 (CTĐT K49 78 dòng, clingo/CP-SAT/Python)
- [x] Chưa dùng số liệu quy chế thật — mọi ngưỡng trong `kb.py` là **giá trị thu nhỏ để chạy thử** — ✅ đã xong: Tuần 5–6 (R-Formal + CTĐT thật, ERRATA_Tuan6.md)
