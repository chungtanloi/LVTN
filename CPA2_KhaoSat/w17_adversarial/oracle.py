"""
oracle.py — máy tính độc lập cho tiền đề số học của gold (CPA2, Tuần 17)

KHÔNG dùng clingo, KHÔNG đọc file .lp của R-Formal: cài lại trực tiếp từ câu chữ quy chế, chỉ dùng
dữ liệu CTĐT K49 (số TC, loại học phần điều kiện) để gold của các ca sát ngưỡng không phụ thuộc vào
chính hệ thống được đánh giá.

  QĐ3266 Đ22 k2 (tr.14)  bảng quy đổi thang 10 → chữ → thang 4. OCR mất nhãn hai dòng C+/C; giá trị
                         chép từ ảnh trang ở Tuần 5 (A 9,0–10 · B+ 8,0–8,9 · B 7,0–7,9 · C+ 6,5–6,9 ·
                         C 5,5–6,4 · D+ 5,0–5,4 · D 4,0–4,9 · F < 4,0)
  QĐ3266 Đ22 k3          tích lũy khi đạt từ D trở lên
  QĐ3266 Đ22 k5 a        điểm M: không vào ĐTBCTL, CÓ vào tổng TC tích lũy
  QĐ3266 Đ22 k5 b, c     điểm I, W: không tích lũy, không vào trung bình
  QĐ3266 Đ24 k1          số TC tích lũy = tổng TC các học phần đã tích lũy
  QĐ3266 Đ24 (đ. ĐTBCTL) ĐTBCTL: các HP đã tích lũy, KHÔNG gồm điểm F và học phần điều kiện
  QĐ3266 Đ32 k1 b        TB chung các học phần GDQP&AN ≥ 5,0 (thang 10)
  QĐ3266 Đ5 (tr.4–5)     thiết kế 4,5 năm → tối đa 9 năm; K ≤ 49: mỗi 9 TC công nhận giảm 1 HK

Kết quả là Fraction (chính xác tuyệt đối), in ra dạng chuỗi "a/b" hoặc số nguyên.
"""
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).parent.parent
_CT = {h["ma"]: h for h in json.loads((ROOT / "w6_curriculum" / "curriculum_cntt_k49.json")
                                       .read_text(encoding="utf-8"))["hoc_phan"]}

# (cận dưới thang 10 ×10, chữ, thang 4 ×10) — QĐ3266 Đ22 k2
BANG = [(90, "A", 40), (80, "B+", 35), (70, "B", 30), (65, "C+", 25), (55, "C", 20), (50, "D+", 15), (40, "D", 10), (0, "F", 0)]


def chu(thang10):
    return next(c for lo, c, _ in BANG if thang10 >= lo)


def thang4(thang10):
    return Fraction(next(p for lo, _, p in BANG if thang10 >= lo), 10)


def dieu_kien(ma):
    return (_CT.get(ma) or {}).get("dieu_kien")


def _tich_luy(g):
    if g.get("diem") == "M":
        return True
    if g.get("diem") in ("I", "W") or g.get("thang10") is None:
        return False
    return g["thang10"] >= 40


def tinh(ho_so):
    """Hồ sơ (student_fact_schema) → các đại lượng dùng làm tiền đề gold."""
    g = ho_so["grades"]
    bo = set(ho_so.get("khong_tinh_tich_luy", []))
    mien = {e["ma_hp"] for e in ho_so.get("exemptions", []) if e.get("quyet_dinh")}
    tl = {m: r for m, r in g.items() if _tich_luy(r) and m not in bo}
    tc = sum(r["credits"] for r in tl.values()) + sum(_CT[m]["tin_chi"] for m in mien if m not in tl)
    tu = mau = Fraction(0)
    for m, r in tl.items():
        if r.get("diem") == "M" or dieu_kien(m):
            continue
        tu += thang4(r["thang10"]) * r["credits"]
        mau += r["credits"]
    qp = {m: r for m, r in g.items() if dieu_kien(m) == "gdqp" and r.get("thang10") is not None}
    qp_mau = sum(r["credits"] for r in qp.values())
    # Cách tính SAI phổ biến (để chứng tỏ một ca là bẫy): tính cả HP điểm F (vẫn bỏ HP điều kiện, điểm M)
    f_tu, f_mau = tu, mau
    for m, r in g.items():
        if r.get("thang10") is not None and r["thang10"] < 40 and not dieu_kien(m) and m not in bo:
            f_mau += r["credits"]
    nam2 = ho_so.get("da_hoc_nam2")
    # CNTT K49: thiết kế 4,5 năm → tối đa 9 năm = 18 nửa năm. GIẢ ĐỊNH "1 HK = 1 nửa năm" — giống R-Formal, nên
    # đây KHÔNG phải kiểm độc lập. QĐ3266 Đ6 k1 (tr.5): một năm có 03 HK × 15 tuần → "giảm 1 HK" = 1/3 năm.
    # Gold NG-17/NG-18 đúng theo CẢ HAI cách đọc (xem Tuan17 E17-3).
    tran = 18 - (ho_so.get("tc_cong_nhan") or 0) // 9
    return {
        "tc_tich_luy": tc,
        "dtbctl": tu / mau if mau else None,
        "dtbctl_ge_2": (tu / mau >= 2) if mau else None,
        "dtbctl_tinh_ca_F": f_tu / f_mau if f_mau else None,
        "gdqp_tb": Fraction(sum(r["thang10"] * r["credits"] for r in qp.values()), 10 * qp_mau) if qp_mau else None,
        "tran_nam2": tran,
        "qua_han": (nam2 > tran) if nam2 is not None else None,
    }


if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        print(p, {k: str(v) for k, v in tinh(json.loads(Path(p).read_text(encoding="utf-8"))).items()})
