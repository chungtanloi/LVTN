"""
loader.py — LOADER DÙNG CHUNG: hồ sơ sinh viên (student_fact_schema) → dữ kiện ASP (CPA2, sau Tuần 17)

Trước đây có 3 bản chép (w7 load_facts, w11 load_student, w12 load_student) và chúng lệch nhau: w11/w12 thiếu
che_do(sv_chon_tich_luy) (CQ-06); w7 không rà soát hồ sơ mâu thuẫn (P17-1); quy ước chứng chỉ ×10 từng sai ở cả
ba (Bài học, CLAUDE.md). Mọi đường vào giờ gọi sang_asp() ở đây.

  sang_asp(j) → (asp, mau_thuan)    rà soát (ra_soat) rồi sinh dữ kiện
  ra_soat(j)  → (hồ sơ sạch, ASP mở các bản ghi mâu thuẫn, danh sách mâu thuẫn)
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent

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
    ht = hs.get("hinh_thuc_cuoi_khoa")
    if ht is not None and ht not in ("lvtn", "tltn", "tich_luy_tc"):       # sai giá trị → không tin, coi như chưa khai báo
        hs.pop("hinh_thuc_cuoi_khoa")
        mt.append(f"hinh_thuc_cuoi_khoa: {ht!r} không thuộc {{lvtn, tltn, tich_luy_tc}} — coi như chưa khai báo")
    nam2 = hs.get("da_hoc_nam2")
    if nam2 is not None:
        tc = sum(g.get("credits") or 0 for g in hs.get("grades", {}).values() if g.get("diem") != "M")
        so_hk = -(-3 * nam2 // 2)                 # nửa năm → HK (làm tròn lên, có lợi cho SV)
        if tc > TC_TOI_DA_HK * so_hk:
            hs.pop("da_hoc_nam2")
            mt.append(f"da_hoc_nam2: {nam2} nửa năm ({so_hk} HK) nhưng đã đăng ký {tc} TC > {TC_TOI_DA_HK} TC/HK "
                      f"(Đ14 k1) — coi như chưa khai báo")
    return hs, "\n".join(them), mt


def sang_asp(j):
    """Hồ sơ → (chuỗi dữ kiện ASP, danh sách mâu thuẫn). LUÔN rà soát trước (P17-1). Thứ tự dòng cố định."""
    j, them, mt = ra_soat(j)
    lines = [them] if them else []
    for code, g in j.get("grades", {}).items():
        th, diem = g.get("thang10"), g.get("diem")
        if diem == "M":
            lines.append(f'diem_m("{code}").')
        elif diem == "W":
            lines.append(f'diem_w("{code}").')
        elif diem == "I":
            lines.append(f'diem_i("{code}").')
        elif th is not None:
            lines.append(f'g10("{code}",{th}).')
    for c in j.get("khong_tinh_tich_luy", []):
        lines.append(f'khong_tinh_tich_luy("{c}").')
    if j.get("che_do_sv_chon_tich_luy"):
        lines.append("che_do(sv_chon_tich_luy).")                       # CQ-06
    if j.get("xac_nhan_ky_luat_sach") is True:
        lines.append("xac_nhan_ky_luat_sach.")
    elif j.get("xac_nhan_ky_luat_sach") is False:
        lines.append("khai_bao(ky_luat).")   # khai báo "không" → FALSE; null/thiếu → KB mở nhánh (Tuần 16)
    ht = j.get("hinh_thuc_cuoi_khoa")      # QĐ3266 Đ31, R-F04: đơn vị đào tạo xét và công bố hình thức (Tuần 18)
    if ht is not None:
        lines.append("khai_bao(hinh_thuc).")  # đã biết → đóng nhánh; null/thiếu → eligibility.lp mở nhánh
        if ht in ("lvtn", "tltn"):
            lines.append(f"dv_cong_bo({ht}).")
    for k in ("da_hoc_nam2", "tc_cong_nhan"):
        if j.get(k) is not None:
            lines.append(f"{k}({j[k]}).")
    for c in j.get("certificates", []):
        loai = c["loai"]
        diem = int(c["diem"]) if loai == "ctu_abc" else round(c["diem"] * 10)   # nguong_cc lưu điểm ×10
        lines.append(f"chung_chi({loai},{diem}).")
    for ex in j.get("exemptions", []):
        if ex["quyet_dinh"]:
            lines.append(f'duoc_mien("{ex["ma_hp"]}").')
    return "\n".join(lines), mt
