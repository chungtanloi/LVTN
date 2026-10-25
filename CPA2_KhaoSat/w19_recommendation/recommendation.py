"""
recommendation.py — Recommendation v1 (CPA2, Tuần 19): chỉ đề xuất phương án đã chứng minh hợp lệ

  de_xuat(ho_so, hk, them="") → {
      dang_ky:              [{ma, ten, tc, ly_do, chung_chi}] — phương án đăng ký học kỳ `hk` (1/2/3), tổng ≤ 20 TC
      tong_tc:              tổng TC phương án
      can_xac_minh:         [{ma, ly_do}] — HP có thể cần học nhưng hợp lệ chưa chắc (UNKNOWN) → KHÔNG đề xuất
      ung_vien_khong_chon:  [{ma, tc}] — ứng viên hợp lệ không vào phương án (hết chỗ/thứ tự ưu tiên)
      hinh_thuc_tot_nghiep: [{doi_tuong, chung_chi}] — Eligibility (Tuần 18) trả ELIGIBLE
      xin_mien:             [{ma, hanh_dong, nguon}] — đủ điều kiện NỘP ĐƠN xin miễn (QD-11: chưa phải đã miễn)
      thay_the:             [{ma, tu, nguon}] — HP được công nhận thay thế (Eligibility ELIGIBLE)
      khong_du_song_hanh:   [{ma, song_hanh, nguon}] — chưa học HP song hành và không thể học cùng kỳ (R-A04, Đ7 k5)
      mau_thuan:            bản ghi hồ sơ mâu thuẫn (loader chung)
  }

Ứng viên (tính trên MỌI thế giới — ba trị Tuần 16):
  · chưa tích lũy (FALSE mọi thế giới), du_dk_dang_ky TRUE mọi thế giới (R-A03), mở ở HK `hk` (CTĐT), không
    phải GDQP (trường bố trí riêng); và cần cho CTĐT: bắt buộc, hoặc thuộc nhóm tự chọn còn thiếu.
  · nhóm một nhánh (AV/PV; CN1–3): đã bắt đầu nhánh nào thì chỉ nhánh đó; chưa thì chọn tối đa một nhánh.
  · CT550E/CT501E: chỉ khi Eligibility trả ELIGIBLE; khai báo hình thức LVTN → không đề xuất HP khác trong nhóm.
  · song hành (R-A04 · QĐ3266 Đ7 k5 "phải học trước hoặc học cùng lúc"): HP song hành phải ĐÃ HỌC (có bản ghi
    điểm, kể cả F; không tính W) hoặc được chọn cùng kỳ — 'học' ≠ 'tích lũy' (khoản 4); QD-13 rút lại 18/10/2026.
  · Hợp lệ UNKNOWN → can_xac_minh. HP đủ điều kiện xin miễn / được thay thế → tách riêng, không đề xuất học.
Chọn bằng clingo (recommendation.lp): ≤ 20 TC (R-C01, Đ14 k1), không dư nhóm; ưu tiên (CHÍNH SÁCH, không phải quy
chế): TC bắt buộc @5 → số HP mở khóa @4 → TC lấp nhóm @2 → tổng TC @1. Kiểm lại phương án sau khi chọn.

Chạy:  python recommendation.py --student ../w7_student_facts/students/sv_lvtn.json --hk 1
"""
import argparse, json, re, sys
from pathlib import Path
import clingo

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "w16_abstention"))
sys.path.insert(0, str(ROOT / "w18_eligibility"))
import abstention as A
from loader import co_hoc   # w7: định nghĩa "đã học" dùng chung (R-A04)
import eligibility as E

LP = (HERE / "recommendation.lp").read_text(encoding="utf-8")
_CTDT = json.loads((ROOT / "w6_curriculum" / "curriculum_cntt_k49.json").read_text(encoding="utf-8"))
CT = {h["ma"]: h for h in _CTDT["hoc_phan"]}
NHOM = _CTDT["nhom"]
LA_MA = {1: "I", 2: "II", 3: "III"}
TRAN_TC = 20                                  # R-C01 · QĐ3266 Đ14 k1
LUAN_VAN = {"CT550E": "lvtn", "CT501E": "tltn"}


def _nhanh(ma):
    for g, n in NHOM.items():
        for b, ds in (n.get("nhanh") or {}).items():
            if ma in ds:
                return g, b
    return None


def _nhom(ma):
    c = CT[ma]["cot"]
    return c if c != "BB" else (_nhanh(ma) or (None,))[0]


def _moi(models, atom):
    return A.ba_tri(atom, models)


def _nguon_rule(rid):
    r = E._nguon().get(rid)
    return f"{r['van_ban']} Điều {r['dieu']}" + (f" khoản {r['khoan']}" if r.get("khoan") else "") if r else rid


def _chung_chi(atom, chung):
    return [{"atom": atom, "rule_id": k.group(1), "nguon": _nguon_rule(k.group(1))}
            for a in sorted(chung) for k in [re.match(rf"why\({re.escape(atom)},(\w+)\)$", a)] if k]


def _so_tc(models, mau):
    """Giá trị số của atom `mau(...,X)` nếu như nhau trong mọi thế giới, ngược lại None."""
    v = set()
    for m in models:
        x = [int(re.search(r",(-?\d+)\)$", a).group(1)) for a in m if a.startswith(mau)]
        v.add(x[0] if x else 0)
    return v.pop() if len(v) == 1 else None


def _da_hoc(ho_so, tl, ma):
    """R-A04 (Đ7 k5) 'học trước': co / khong / chua_ro — định nghĩa "đã học" lấy từ loader.co_hoc (dùng chung với KB
    da_hoc/1). Đã tích lũy (gồm miễn, thay thế) = đã học; bản ghi trạng thái 'unknown' không điểm = chưa rõ."""
    if tl.get(ma) == "TRUE":
        return "co"
    g = (ho_so.get("grades") or {}).get(ma)
    if g is not None and co_hoc(g):
        return "co"
    if (g is not None and g.get("diem") != "W" and g.get("letter") != "W") or tl.get(ma) == "UNKNOWN":
        return "chua_ro"
    return "khong"


def de_xuat(ho_so, hk, them=""):
    if hk not in LA_MA:
        raise ValueError(f"học kỳ phải là 1, 2 hoặc 3 (QĐ3266 Đ6 k1: một năm học có 3 HK), nhận {hk!r}")
    asp, mt = A.sang_asp(ho_so)
    models = A.giai(asp + "\n" + them)
    kq = {"hk": hk, "dang_ky": [], "tong_tc": 0, "can_xac_minh": [], "ung_vien_khong_chon": [],
          "hinh_thuc_tot_nghiep": [], "xin_mien": [], "thay_the": [], "khong_du_song_hanh": [], "mau_thuan": mt}
    if not models:
        kq["can_xac_minh"].append({"ma": None, "ly_do": "hồ sơ mâu thuẫn với quy chế (không có mô hình)"})
        kq["vo_nghiem"] = True          # solver vô nghiệm: lớp trên phải báo MÂU THUẪN, không phải "không có đề xuất"
        return kq
    chung = frozenset.intersection(*models)
    tl = {ma: _moi(models, f'tich_luy("{ma}")') for ma in CT}

    # --- R2 hình thức tốt nghiệp (Eligibility Tuần 18) ---
    elig = {}
    for x in ("lvtn", "tltn", "tich_luy_tc"):
        r = E.xet(ho_so, x, them)
        elig[x] = r["ket_qua"]
        if r["ket_qua"] == "ELIGIBLE":
            kq["hinh_thuc_tot_nghiep"].append({"doi_tuong": x, "chung_chi": r["chung_chi"]})
        elif r["ket_qua"] == "UNKNOWN":
            kq["can_xac_minh"].append({"ma": x, "ly_do": "Eligibility UNKNOWN: " +
                                       " | ".join(b["hoi"] for b in r["can_bo_sung"])})
    khai_bao = ho_so.get("hinh_thuc_cuoi_khoa")

    # --- nhóm còn thiếu, nhánh được phép ---
    thieu = {}
    for g, n in NHOM.items():
        dat = _moi(models, f"dat_nhom({g})")
        if dat == "TRUE":
            continue
        if n["kieu"] == "mot_nhanh":
            da = {b: _so_tc(models, f"tc_nhanh_dat({g},{b},") for b in n["nhanh"]}
            bat_dau = [b for b, v in da.items() if v]
            ok = bat_dau if len(bat_dau) == 1 else list(n["nhanh"]) if not bat_dau else []
            ly = (f"đã học cả hai nhánh của nhóm {g} ({', '.join(bat_dau)}) — hỏi Phòng Đào tạo nhánh nào được tính"
                  if len(bat_dau) > 1 else f"chưa xác định được nhóm {g} còn thiếu bao nhiêu")
            for b in ok:
                if dat == "FALSE" and da[b] is not None:
                    thieu[(g, b)] = n["min"] - da[b]
            if dat == "UNKNOWN" or not ok or any(da[b] is None for b in ok):
                for b in n["nhanh"]:
                    for ma in n["nhanh"][b]:
                        if tl[ma] != "TRUE":
                            kq["can_xac_minh"].append({"ma": ma, "ly_do": ly})
        else:
            d = _so_tc(models, f"tc_nhom_dat({g},")
            if dat == "FALSE" and d is not None:
                thieu[(g, None)] = n["min"] - d
            else:
                for ma, h in CT.items():
                    if h["cot"] == g and tl[ma] != "TRUE":
                        kq["can_xac_minh"].append({"ma": ma, "ly_do": f"chưa xác định được nhóm {g} còn thiếu bao nhiêu"})

    def khoa(ma):
        g = _nhom(ma)
        if CT[ma]["cot"] == "BB":
            return ("bb", None)
        if g in NHOM and NHOM[g]["kieu"] == "mot_nhanh":
            b = _nhanh(ma)[1]
            return ("nhom", (g, b)) if (g, b) in thieu else (None, None)
        return ("nhom", (g, None)) if (g, None) in thieu else (None, None)

    # --- R3 xin miễn (QD-11) và R4 thay thế: tách khỏi danh sách học ---
    tach = set()
    for ma in CT:
        if any(a.startswith(f'mien_tu("{ma}",') for a in chung):
            if E.xet(ho_so, f"thay_the:{ma}", them)["ket_qua"] == "ELIGIBLE":
                tu = sorted(a.split(",")[1][:-1].strip('"') for a in chung if a.startswith(f'mien_tu("{ma}",'))
                kq["thay_the"].append({"ma": ma, "tu": tu, "chung_chi": _chung_chi(f'mien_tu("{ma}","{tu[0]}")', chung)})
                tach.add(ma)
        elif tl[ma] == "TRUE":
            continue
        elif _moi(models, f'duoc_mien("{ma}")') == "TRUE":
            tach.add(ma)
        elif _moi(models, f'duoc_mien("{ma}")') == "UNKNOWN":
            kq["can_xac_minh"].append({"ma": ma, "ly_do": "quyết định miễn chưa rõ — hỏi Phòng Đào tạo trước khi đăng ký"})
            tach.add(ma)
        elif f'du_dk_xin_mien("{ma}")' in chung and khoa(ma)[0] is not None:     # chỉ HP còn cần cho CTĐT
            kq["xin_mien"].append({"ma": ma, "hanh_dong": f"đủ điều kiện nộp đơn xin miễn {ma} (chưa phải đã miễn — "
                                   "chờ quyết định của Trường)", "chung_chi": _chung_chi(f'du_dk_xin_mien("{ma}")', chung)})
            tach.add(ma)

    # --- ứng viên ---
    ung, xac_minh = {}, {x["ma"] for x in kq["can_xac_minh"]}
    for ma, h in CT.items():
        if ma in tach or ma in xac_minh or h.get("dieu_kien") == "gdqp" or not h["hk"] or LA_MA[hk] not in h["hk"] or tl[ma] == "TRUE":
            continue
        loai, nhom = khoa(ma)
        if loai is None:
            continue
        if ma in LUAN_VAN and elig[LUAN_VAN[ma]] != "ELIGIBLE":
            continue
        # Đ31: một trong ba hình thức — đã khai báo hình thức thì chỉ đề xuất HP của hình thức đó
        if ma in LUAN_VAN and khai_bao in ("lvtn", "tltn", "tich_luy_tc") and LUAN_VAN[ma] != khai_bao:
            continue
        if h["cot"] == "g_tot_nghiep" and khai_bao == "lvtn" and ma != "CT550E":
            continue                         # LVTN 15 TC đã đủ nhóm tốt nghiệp
        dk = _moi(models, f'du_dk_dang_ky("{ma}")')
        if tl[ma] == "UNKNOWN" or dk == "UNKNOWN":
            kq["can_xac_minh"].append({"ma": ma, "ly_do": "tích lũy/tiên quyết chưa chắc (điểm chưa rõ) — "
                                       "xác minh bảng điểm trước khi đăng ký"})
        elif dk == "TRUE":
            ung[ma] = (loai, nhom)

    # R-A04 · Đ7 k5: HP song hành phải đã học hoặc học cùng kỳ → bỏ ứng viên không thể thoả (lặp tới khi ổn định)
    nguon_a04 = _nguon_rule("r_a04")

    def xac_minh_all():
        return {x["ma"] for x in kq["can_xac_minh"]}

    doi = True
    while doi:
        doi = False
        for ma in sorted(ung):
            for sp in CT[ma]["song_hanh"]:
                dh = _da_hoc(ho_so, tl, sp)
                if dh == "khong" and sp not in ung and (sp in xac_minh_all() or sp in tach):
                    dh = "chua_ro"           # HP song hành chưa chắc học được kỳ này (UNKNOWN / chờ xin miễn) — không kết luận chắc
                if dh == "chua_ro":
                    kq["can_xac_minh"].append({"ma": ma, "ly_do": f"chưa rõ đã học HP song hành {sp} chưa (Đ7 k5)"})
                elif dh == "khong" and sp not in ung:
                    kq["khong_du_song_hanh"].append({"ma": ma, "song_hanh": [sp], "nguon": nguon_a04,
                        "ly_do": f"chưa học {sp} và {sp} không thể đăng ký cùng kỳ này — phải học trước hoặc cùng lúc"})
                else:
                    continue
                del ung[ma]
                doi = True
                break
    da_hoc_sh = {(ma, sp): _da_hoc(ho_so, tl, sp) == "co" for ma in ung for sp in CT[ma]["song_hanh"]}

    if ung:
        mo_khoa = {ma: sum(1 for k, h in CT.items() if ma in h["tien_quyet"] and tl[k] != "TRUE") for ma in ung}
        f = [f"tran_tc({TRAN_TC})."]
        for ma, (loai, nhom) in ung.items():
            f.append(f'ung_vien("{ma}"). tc("{ma}",{CT[ma]["tin_chi"]}). mo_khoa("{ma}",{mo_khoa[ma]}).')
            if loai == "bb":
                f.append(f'bb("{ma}").')
            else:
                g, b = nhom
                f.append(f'trong_nhom({g},"{ma}").' if b is None else f'trong_nhanh({g},{b},"{ma}").')
        for (g, b), d in thieu.items():
            f.append(f"thieu({g},{d})." if b is None else f"thieu_nhanh({g},{b},{d}).")
        for (ma, sp), da in da_hoc_sh.items():
            if not da:
                f.append(f'can_cung_ky("{ma}","{sp}").')
        for ma in LUAN_VAN:
            if ma in ung:
                f.append(f'luan_van("{ma}").')
        ctl = clingo.Control(["--warn=none", "--opt-mode=opt"])
        ctl.add("base", [], LP + "\n" + "\n".join(f))
        ctl.ground([("base", [])])
        tot = []
        ctl.solve(on_model=lambda m: tot.__setitem__(slice(None), [str(s.arguments[0]).strip('"')
                                                                     for s in m.symbols(shown=True) if s.name == "chon"]))
        chon = sorted(tot, key=lambda x: (CT[x]["cot"] != "BB", x))
        # kiểm lại độc lập phương án (bất biến): hợp lệ mọi thế giới, chưa tích lũy, mở HK, ≤ 20 TC
        # (kiểm tường minh, không dùng assert — assert bị bỏ khi chạy python -O)
        if not (all(f'du_dk_dang_ky("{x}")' in chung and tl[x] == "FALSE" and LA_MA[hk] in CT[x]["hk"] for x in chon)
                and sum(CT[x]["tin_chi"] for x in chon) <= TRAN_TC
                and all(da_hoc_sh[(x, sp)] or sp in chon for x in chon for sp in CT[x]["song_hanh"])):
            kq["can_xac_minh"].append({"ma": None, "ly_do": f"phương án solver {chon} không qua kiểm lại — không đề xuất"})
            chon = []
        for x in chon:
            loai, nhom = ung[x]
            ly = "học phần bắt buộc" if loai == "bb" else f"lấp nhóm {nhom[0]}" + (f" (nhánh {nhom[1]})" if nhom[1] else "")
            if mo_khoa[x]:
                ly += f"; mở khóa {mo_khoa[x]} HP sau"
            cc = _chung_chi(f'du_dk_dang_ky("{x}")', chung)
            for sp in CT[x]["song_hanh"]:
                ly += f"; song hành {sp} " + ("đã học" if da_hoc_sh[(x, sp)] else "học cùng kỳ")
                cc.append({"atom": f'song_hanh("{x}","{sp}")', "rule_id": "r_a04", "nguon": nguon_a04})
            kq["dang_ky"].append({"ma": x, "ten": CT[x]["ten"], "tc": CT[x]["tin_chi"], "ly_do": ly, "chung_chi": cc})
        kq["tong_tc"] = sum(CT[x]["tin_chi"] for x in chon)
        kq["ung_vien_khong_chon"] = [{"ma": x, "tc": CT[x]["tin_chi"]} for x in sorted(ung) if x not in chon]
    return kq


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--student", required=True)
    ap.add_argument("--hk", type=int, default=1)
    a = ap.parse_args()
    print(json.dumps(de_xuat(json.loads(Path(a.student).read_text(encoding="utf-8")), a.hk),
                     ensure_ascii=False, indent=2))
