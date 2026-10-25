"""
abstention.py — Abstention engine v1 (CPA2, Tuần 16)

Ba trị TRUE / FALSE / UNKNOWN trên MỌI answer set + "missing evidence" + chính sách từ chối kết luận.

  Dữ kiện mở (thế giới mở có kiểm soát, graduation_solver.lp mục 0):
    xac_nhan_ky_luat_sach   — hồ sơ null/thiếu → { xac_nhan_ky_luat_sach } (R-F03, QĐ3266 Đ32 k1)
    qua_thoi_gian_toi_da    — thiếu da_hoc_nam2 → { qua_thoi_gian_toi_da } (R-E01, QĐ3266 Đ5)
    f_ngoai_ho_so_vuot_5, hp_dk_tinh_vao_tong, ky_luat_canh_cao_cap_truong — thiếu tc_diem_f / HP điều kiện chưa rõ
                            (A17) / thiếu khai báo kỷ luật cấp Trường (R-F07/F07b, Đ34 k2)
    g10(C,_)                — điểm không chắc (OCR Tuần 15) → lựa chọn 1 { g10(C,v) ... } 1

  missing evidence: mỗi answer set là một "thế giới" (một cách gán dữ kiện mở). Với mỗi biến mở,
  chia các thế giới theo giá trị của biến và tính ba trị trong từng phần — tương đương giải lại với
  ràng buộc biến = giá trị, nhưng không phải giải lại. Biến QUYẾT ĐỊNH nếu kết luận đổi theo giá trị.

  Chính sách: chỉ kết luận khi TRUE/FALSE trên mọi thế giới. UNKNOWN → ket_luan = None + câu hỏi,
  KHÔNG chọn theo đa số thế giới (số thế giới không phải xác suất). Vô nghiệm → MAU_THUAN.

Chạy:  python abstention.py --student ../w7_student_facts/students/sv_lvtn.json [--claim tot_nghiep]
"""
import sys, json, re, argparse
from pathlib import Path
import clingo

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "w7_student_facts"))

KB_FILES = [ROOT / "w5_rformal" / "qd3266_r_formal_v1.lp", ROOT / "w5_rformal" / "qd5339_r_formal_v1.lp",
            ROOT / "w6_curriculum" / "curriculum_schema.lp", ROOT / "w8_elective" / "elective_solver.lp",
            ROOT / "w9_exemption" / "exemption_substitution_solver.lp",
            ROOT / "w6_curriculum" / "curriculum_cntt_k49.lp", ROOT / "w10_graduation" / "graduation_solver.lp"]

BO = object()   # đánh dấu "xoá trường" cho test

# Biến mở dạng atom 0 ngôi: tên → (câu hỏi cho SV, nguồn)
BIEN_BOOL = {
    "xac_nhan_ky_luat_sach": (
        "Tại thời điểm xét tốt nghiệp, bạn có đang bị truy cứu trách nhiệm hình sự hoặc đang trong thời gian "
        "bị kỷ luật ở mức đình chỉ học tập không? (cần xác nhận của nhà trường)",
        "R-F03 · QĐ3266 Điều 32 khoản 1"),
    "qua_thoi_gian_toi_da": (
        "Bạn đã học bao lâu kể từ khi nhập học (tính theo nửa năm, ví dụ 4,5 năm = 9), và có được công nhận/chuyển đổi "
        "tín chỉ nào không? (lưu ý: một năm học có 3 học kỳ — không đếm số học kỳ)",
        "R-E01, R-E02 · QĐ3266 Điều 5"),
    # C15 (Tuần 20): hạ một mức hạng xuất sắc/giỏi — QĐ3266 Đ34 k2 (graduation_solver.lp mục 0)
    "f_ngoai_ho_so_vuot_5": (
        "Tổng số tín chỉ các học phần (không tính học phần điều kiện: GDQP, GDTC, ngoại ngữ/tin học căn bản) bạn TỪNG bị "
        "điểm F — kể cả học phần sau đó đã học lại đạt, không tính lần học cải thiện điểm bị F — là bao nhiêu?",
        "R-F07 · QĐ3266 Điều 34 khoản 2 điểm a"),
    "hp_dk_tinh_vao_tong": (
        "Học phần điều kiện (GDQP, GDTC, ngoại ngữ/tin học căn bản) bị điểm F có tính vào 'khối lượng học phần bị điểm F' "
        "của Điều 34 khoản 2 điểm a không? (văn bản chưa rõ — cần Phòng Đào tạo xác nhận)",
        "R-F07 · QĐ3266 Điều 34 khoản 2 điểm a · việc tồn đọng A17"),
    "ky_luat_canh_cao_cap_truong": (
        "Trong thời gian học, bạn có từng bị kỷ luật từ mức cảnh cáo cấp Trường trở lên không?",
        "R-F07b · QĐ3266 Điều 34 khoản 2 điểm b"),
}
G10 = re.compile(r'^g10\(("[^"]+"),(-?\d+)\)$')


def giai(asp):
    ctl = clingo.Control(["--warn=none", "--models=0"])
    ctl.add("base", [], "\n".join(p.read_text(encoding="utf-8") for p in KB_FILES) + "\n" + asp)
    ctl.ground([("base", [])])
    out = []
    with ctl.solve(yield_=True) as h:
        for m in h:
            out.append(frozenset(str(a) for a in m.symbols(atoms=True)))
    return out


def ba_tri(claim, models):
    if not models:
        return "MAU_THUAN"
    co = [claim in m for m in models]
    return "TRUE" if all(co) else ("FALSE" if not any(co) else "UNKNOWN")


def _gia_tri(models):
    """Biến mở → {model: giá trị}. Chỉ giữ biến thật sự thay đổi giữa các thế giới."""
    bien = {}
    for b in BIEN_BOOL:
        bien[b] = {m: ("true" if b in m else "false") for m in models}
    # g10 có thể vừa là dữ kiện vừa được suy ra (miễn thi, điểm học cao hơn — qd5339) → một mô hình
    # có thể có nhiều g10 cho cùng HP: giá trị = tập điểm, sắp xếp cố định.
    g = {}
    for m in models:
        for a in m:
            k = G10.match(a)
            if k:
                g.setdefault(f"g10({k.group(1)})", {}).setdefault(m, set()).add(int(k.group(2)))
    for ten, v in g.items():
        bien[ten] = {m: ",".join(str(x) for x in sorted(v.get(m, ()))) or "khong_co" for m in models}
    # quyết định miễn chưa rõ (vd. { duoc_mien("XH025") })
    mien = {a for m in models for a in m if a.startswith("duoc_mien(")}
    for a in mien:
        bien[a] = {m: ("true" if a in m else "false") for m in models}
    return {ten: v for ten, v in bien.items() if len(set(v.values())) > 1}


def bang_chung_thieu(claim, models):
    """Danh sách dữ kiện mở QUYẾT ĐỊNH kết luận, xếp: biến một mình đủ kết luận trước."""
    ds = []
    for ten, gan in _gia_tri(models).items():
        theo = {val: ba_tri(claim, [m for m in models if gan[m] == val]) for val in sorted(set(gan.values()))}
        if len(set(theo.values())) < 2:
            continue                       # không quyết định: mọi giá trị cho cùng kết luận
        if ten in BIEN_BOOL:
            hoi, nguon = BIEN_BOOL[ten]
        elif ten.startswith("duoc_mien("):
            ma = ten[len('duoc_mien("'):-2]
            hoi, nguon = f"Học phần {ma} đã có quyết định miễn được phê duyệt chưa?", "R-M16 · QĐ5339 Điều 2 khoản 6 (bẫy QD-11: đủ điều kiện miễn ≠ đã được miễn)"
        else:
            ma = ten[len('g10("'):-2]
            hoi, nguon = f"Điểm học phần {ma} (thang 10) trên bảng điểm chính thức là bao nhiêu?", "bảng điểm (OCR không chắc)"
        ds.append({"bien": ten, "quyet_dinh": True, "theo_gia_tri": theo,
                   "du_ket_luan": all(v in ("TRUE", "FALSE") for v in theo.values()), "hoi": hoi, "nguon": nguon})
    ds.sort(key=lambda b: (not b["du_ket_luan"], b["bien"]))
    return ds


# Rà soát hồ sơ (P17-1) + đổi hồ sơ → ASP: loader dùng chung ở w7_student_facts/loader.py
from loader import ra_soat, sang_asp  # noqa: E402,F401  (ra_soat xuất lại: validate_abstention E9 gọi abstention.ra_soat)


def tra_loi(claim, ho_so=None, them=""):
    asp, mt = sang_asp(ho_so) if ho_so is not None else ("", [])
    asp += "\n" + them
    models = giai(asp)
    v = ba_tri(claim, models)
    can = bang_chung_thieu(claim, models) if v == "UNKNOWN" else []
    if v == "TRUE":
        gt = f"Kết luận: {claim} đúng trong mọi trường hợp dữ kiện hiện có."
    elif v == "FALSE":
        gt = f"Kết luận: {claim} không đạt trong mọi trường hợp dữ kiện hiện có."
    elif v == "UNKNOWN":
        gt = ("Chưa đủ dữ kiện để kết luận — hệ thống không đoán. Cần bổ sung: "
              + " | ".join(b["hoi"] for b in can) if can else
              "Chưa đủ dữ kiện để kết luận — kết luận phụ thuộc lựa chọn của sinh viên.")
    else:
        gt = "Dữ kiện mâu thuẫn với quy chế (không có mô hình) — không kết luận, cần kiểm tra lại hồ sơ."
    if mt:
        gt += " Hồ sơ có bản ghi mâu thuẫn, cần xác minh: " + " | ".join(mt)
    return {"claim": claim, "verdict": v, "ket_luan": {"TRUE": True, "FALSE": False}.get(v),
            "so_the_gioi": len(models), "can_bo_sung": can, "mau_thuan": mt, "giai_thich": gt}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--student", required=True)
    ap.add_argument("--claim", default="tot_nghiep")
    a = ap.parse_args()
    print(json.dumps(tra_loi(a.claim, json.loads(Path(a.student).read_text(encoding="utf-8"))),
                     ensure_ascii=False, indent=2))
