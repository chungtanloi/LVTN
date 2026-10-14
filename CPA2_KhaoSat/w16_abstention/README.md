# Tuần 16 — Three-valued logic / Abstention engine (CPA2)

**Sản phẩm:** Abstention engine v1: ba trị TRUE/FALSE/UNKNOWN trên mọi answer set + missing evidence + chính sách từ chối kết luận
**Tiêu chí hoàn thành:** Không đoán khi thiếu dữ liệu ✅. `validate_abstention.py` ĐẠT 28/28 kiểm tra (xem `../Tuan16_Abstention_Engine.md`)

## Chạy

```bash
python validate_abstention.py
python abstention.py --student ../w7_student_facts/students/sv_lvtn.json --claim tot_nghiep
```

## File

| File | Vai trò |
|---|---|
| `abstention.py` | `tra_loi(claim, ho_so, them)` → verdict, `ket_luan` (None nếu không chắc), `can_bo_sung` (dữ kiện quyết định + câu hỏi + nguồn), `giai_thich` |
| `validate_abstention.py` | A thế giới mở · B missing evidence · C chính sách từ chối · D tích hợp Prototype + 6 hồ sơ |
| `validate_output.txt` | Kết quả lần chạy gần nhất |

Thay đổi ngoài thư mục: `w10_graduation/graduation_solver.lp` mục 0 (mở nhánh dữ kiện ngoài); loader w7/w11/w12 (`khai_bao(ky_luat)`, `da_hoc_nam2`, `tc_cong_nhan`); `w12_integration/prototype.py` (missing evidence, bỏ đường dẫn `D:/`); 6 hồ sơ giả lập thêm `da_hoc_nam2: 9`.

## Bất biến

> **Thiếu ≠ sai, đa số ≠ chắc chắn.** Dữ kiện ngoài chưa khai báo được mở thành cả hai nhánh. Engine chỉ kết luận khi claim đúng (hoặc sai) trong **mọi** thế giới. Nếu không, `ket_luan = None` và engine trả về danh sách câu hỏi cho đúng các dữ kiện làm kết luận thay đổi.
