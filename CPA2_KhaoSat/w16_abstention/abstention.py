"""
abstention.py — Abstention engine v1 (CPA2, Tuần 16)

Ba trị TRUE / FALSE / UNKNOWN trên MỌI answer set + "missing evidence" + chính sách từ chối kết luận.

  Dữ kiện mở (thế giới mở có kiểm soát, graduation_solver.lp mục 0):
    xac_nhan_ky_luat_sach   — hồ sơ null/thiếu → { xac_nhan_ky_luat_sach } (R-F03, QĐ3266 Đ32 k1)
    qua_thoi_gian_toi_da    — thiếu da_hoc_nam2 → { qua_thoi_gian_toi_da } (R-E01, QĐ3266 Đ5)
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
import validate_student_facts as w7

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


# ---------------------------------------------------------------- rà soát hồ sơ (P17-1, sau Tuần 17)
# Bảng quy đổi QĐ3266 Đ22 k2 (tr.13–14): cận dưới thang 10 ×10 → điểm chữ. Viết riêng ở đây (không dùng
# oracle của w17) để oracle vẫn độc lập với hệ thống được chấm.
_BANG = [(90, "A"), (80, "B+"), (70, "B"), (65, "C+"), (55, "C"), (50, "D+"), (40, "D"), (0, "F")]
_CT = {h["ma"]: h for h in json.loads((ROOT / "w6_curriculum" / "curriculum_cntt_k49.json")
                                       .read_text(encoding="utf-8"))["hoc_phan"]}
DIEM_MO = (0, 40, 100)          # F / D / A — như HP không chắc của Tuần 15 (tot_nghiep không đơn điệu theo điểm)
TC_TOI_DA_HK = 20               # QĐ3266 Đ14 k1 (tr.8)


def _chu(t):
    return next(c for lo, c in _BANG if t >= lo)


def _so_hop_le(t):
    return isinstance(t, int) and not isinstance(t, bool) and 0 <= t <= 100


def _loi_ban_ghi(ma, g):
    t, L, st, cr = g.get("thang10"), g.get("letter"), g.get("status"), g.get("credits")
    loi = []
    if t is not None and not (isinstance(t, int) and not isinstance(t, bool)):
        return [f"điểm {t!r} không phải số nguyên thang 10 ×10"]
    if t is not None and not 0 <= t <= 100:
        loi.append(f"điểm {t / 10:.1f} ngoài thang 0–10 (Đ22 k1)")
    if g.get("diem") in ("M", "W", "I") and t is not None:
        loi.append(f"điểm {g['diem']} nhưng vẫn có điểm số {t / 10:.1f}")
    if t is not None and 0 <= t <= 100:
        if L and L not in ("M", "W", "I") and L != _chu(t):
            loi.append(f"{t / 10:.1f} quy đổi là {_chu(t)}, hồ sơ ghi {L} (Đ22 k2)")
        if st in ("passed", "failed") and (st == "passed") != (t >= 40):
            loi.append(f"{t / 10:.1f} {'đạt' if t >= 40 else 'không đạt'} nhưng trạng thái ghi {st} (Đ22 k3)")
    if ma in _CT and cr is not None and cr != _CT[ma]["tin_chi"]:
        loi.append(f"{cr} TC, CTĐT ghi {_CT[ma]['tin_chi']} TC")
    return loi


def ra_soat(ho_so):
    """Hồ sơ → (hồ sơ đã bỏ bản ghi mâu thuẫn, ASP mở các bản ghi đó, danh sách mâu thuẫn).
    Bản ghi điểm tự mâu thuẫn → bỏ, mở điểm HP thành F/D/A (+ điểm số ghi trên hồ sơ nếu hợp lệ): không biết trường
    nào đúng thì không đoán. Thời gian đã học không thể (TC đã đăng ký > 20 TC × số HK, 3 HK/năm — Đ14 k1, Đ6 k1)
    → coi như chưa khai báo (KB tự mở nhánh)."""
    hs = json.loads(json.dumps(ho_so))
    them, mt = [], []
    for ma, g in list(hs.get("grades", {}).items()):
        loi = _loi_ban_ghi(ma, g)
        if not loi:
            continue
        hs["grades"].pop(ma)
        mt.append(f"{ma}: " + "; ".join(loi))
        ds = sorted(set(DIEM_MO) | ({g["thang10"]} if _so_hop_le(g.get("thang10")) else set()))
        lc = [f'g10("{ma}",{v})' for v in ds]
        if g.get("diem") in ("M", "W", "I"):          # bản ghi tự nhận là M/W/I → giữ cả khả năng đó
            lc.append(f'diem_{g["diem"].lower()}("{ma}")')
        them.append("1 { " + "; ".join(lc) + " } 1.")
    nam2 = hs.get("da_hoc_nam2")
    if nam2 is not None:
        tc = sum(g.get("credits") or 0 for g in hs.get("grades", {}).values() if g.get("diem") != "M")
        so_hk = -(-3 * nam2 // 2)                 # nửa năm → HK (làm tròn lên, có lợi cho SV)
        if tc > TC_TOI_DA_HK * so_hk:
            hs.pop("da_hoc_nam2")
            mt.append(f"da_hoc_nam2: {nam2} nửa năm ({so_hk} HK) nhưng đã đăng ký {tc} TC > {TC_TOI_DA_HK} TC/HK "
                      f"(Đ14 k1) — coi như chưa khai báo")
    return hs, "\n".join(them), mt


def tra_loi(claim, ho_so=None, them=""):
    mt = []
    if ho_so is not None:
        ho_so, them_rs, mt = ra_soat(ho_so)
        them = them_rs + "\n" + them
    asp = (w7.load_facts(ho_so) if ho_so is not None else "") + "\n" + them
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
