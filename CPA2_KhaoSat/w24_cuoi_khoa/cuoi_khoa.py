"""
cuoi_khoa.py — so sánh hai phương án hoàn thành nhóm học phần tốt nghiệp (CPA2, Tuần 24).

Không thêm luật mới: mọi dữ kiện lấy từ KB đã có (CTĐT: thuoc_nhom, hinh_thuc_cuoi_khoa, course, mo_hk, ctdt_src,
nhom_min_tc; R-Formal: tich_luy, duoc_dang_ky = tiên quyết + song hành) và từ module điều kiện w18 (nhận đề tài LVTN/TLTN —
QD-12: chỉ ngưỡng TC của CTĐT). Ba trị theo MỌI thế giới cho từng học phần (đã đạt / đăng ký được: chắc / không / chưa chắc).
KHÔNG khuyên "nên": trình bày hai phương án, lựa chọn là của sinh viên (bài học P19-1: đủ điều kiện ≠ nên làm).
"""
import re

NHOM = "g_tot_nghiep"
TEN_KQ = {"ELIGIBLE": "đủ điều kiện nhận đề tài", "DA_HOAN_THANH": "đã hoàn thành (đã đạt)",
          "MAU_THUAN": "hồ sơ mâu thuẫn — không kết luận"}


def _ma(a):
    m = re.search(r'"([A-Z]{1,3}\d{2,3}E?)"', a)
    return m.group(1) if m else None


def _ba_tri(models, atom):
    co = [atom in m for m in models]
    return "TRUE" if all(co) else "FALSE" if not any(co) else "UNKNOWN"


def phan_tich(models):
    """Answer sets của hồ sơ → dữ kiện nhóm tốt nghiệp (không phụ thuộc thế giới: CTĐT; theo thế giới: tích lũy, đăng ký)."""
    m0 = models[0]
    thanh_vien = sorted({_ma(a) for a in m0 if a.startswith(f"thuoc_nhom({NHOM},")})
    tc = {_ma(a): int(a[:-1].split(",")[1]) for a in m0 if a.startswith("course(") and _ma(a) in thanh_vien}
    hinh_thuc = {_ma(a): a[:-1].split(",")[1] for a in m0 if a.startswith("hinh_thuc_cuoi_khoa(")}
    mo_hk = {}
    for a in m0:
        if a.startswith("mo_hk(") and _ma(a) in thanh_vien:
            mo_hk.setdefault(_ma(a), []).append(int(a[:-1].split(",")[1]))
    toi_thieu = next(int(a[:-1].split(",")[1]) for a in m0 if a.startswith(f"nhom_min_tc({NHOM},"))
    nguong = {_ma(a): int(a[:-1].split(",")[1]) for a in m0 if a.startswith("tien_quyet_tc(") and _ma(a) in hinh_thuc}
    tc_tl = sorted({int(a[len("tc_tich_luy("):-1]) for m in models for a in m if a.startswith("tc_tich_luy(")})
    dat = {c: _ba_tri(models, f'tich_luy("{c}")') for c in thanh_vien}
    dang_ky = {c: _ba_tri(models, f'duoc_dang_ky("{c}")') for c in thanh_vien}
    return {"thanh_vien": thanh_vien, "tc": tc, "hinh_thuc": hinh_thuc, "mo_hk": mo_hk, "toi_thieu": toi_thieu,
            "nguong": nguong, "tc_tich_luy": tc_tl, "dat": dat, "dang_ky": dang_ky}


def phuong_an(pt, elig_lv, elig_tl):
    """Dữ kiện → BA phương án + nhóm. Luật nhóm (CTĐT): TỔNG ≥ toi_thieu TC trong các học phần của nhóm (ô gộp '15' gồm cả
    LVTN và TLTN). Ba cách đạt (review H1): (1) luận văn; (2) tiểu luận + học phần thay thế; (3) không làm luận văn/tiểu luận,
    chỉ học học phần thay thế (QĐ3266 Điều 31 khoản 3, R-F05). Số TC thay thế còn thiếu = toi_thieu − TC đã chắc chắn đạt
    (phép trừ, không phải câu chữ CTĐT). 'Đã đạt' lấy từ CHÍNH học phần đó (review H2), không từ da_hoan_thanh của w18
    (w18 coi nhóm đã đủ là 'đã hoàn thành' cho cả LVTN lẫn TLTN)."""
    lv = next(c for c, k in pt["hinh_thuc"].items() if k == "luan_van")
    tl = next(c for c, k in pt["hinh_thuc"].items() if k == "tieu_luan")
    thay = [c for c in pt["thanh_vien"] if c not in (lv, tl)]
    da = sorted(c for c in thay if pt["dat"][c] == "TRUE")
    chac = lambda c: pt["dat"][c] == "TRUE"                       # noqa: E731
    tc_da = sum(pt["tc"][c] for c in pt["thanh_vien"] if chac(c))
    tc_tt = sum(pt["tc"][c] for c in da)
    co_chua_chac = any(pt["dat"][c] == "UNKNOWN" for c in pt["thanh_vien"])
    chua_chac = sorted(c for c in thay if not chac(c) and (pt["dang_ky"][c] == "UNKNOWN" or pt["dat"][c] == "UNKNOWN"))
    con = [c for c in thay if not chac(c) and c not in chua_chac]        # review M3: chưa chắc → không vào "đăng ký được"
    hoc_them = {"thay_the": thay, "thay_the_da_dat": da,
                "dang_ky_duoc": sorted(c for c in con if pt["dang_ky"][c] == "TRUE"),
                "chua_du_dk": sorted(c for c in con if pt["dang_ky"][c] == "FALSE"), "chua_chac": chua_chac}

    def mot(c, elig):
        return {"ma": c, "tc": pt["tc"][c], "mo_hk": sorted(pt["mo_hk"].get(c, [])), "du_dk": elig["ket_qua"],
                "ly_do": elig["ly_do"], "nguong_tc": pt["nguong"].get(c), "da_dat": chac(c),
                "chua_chac_dat": pt["dat"][c] == "UNKNOWN"}
    return {
        "luan_van": mot(lv, elig_lv),
        "tieu_luan": {**mot(tl, elig_tl), **hoc_them,
                      "tc_con_thieu": max(0, pt["toi_thieu"] - pt["tc"][tl] - tc_tt)},   # phương án (2) gồm CT501E
        "khong_lv_tl": {**hoc_them, "tc_con_thieu": max(0, pt["toi_thieu"] - tc_tt)},
    }, {"toi_thieu": pt["toi_thieu"], "tc_da_dat": tc_da, "da_du": tc_da >= pt["toi_thieu"], "co_chua_chac": co_chua_chac}


def _hk(ds):
    return ", ".join(f"HK{k}" for k in ds) if ds else "chưa rõ học kỳ mở"


def _trang_thai(x, nhom, tc_tl, can_bo_sung=(), khac=None):
    """khac: phương án cuối khoá còn lại (luận văn ↔ tiểu luận). w18 trả DA_HOAN_THANH cho X khi (a) chính X đã đạt, (b) hình
    thức kia đã đạt (Đ31: thực hiện MỘT trong ba hình thức), hoặc (c) nhóm đã đủ — ba lý do nói khác nhau (review H2)."""
    if x["da_dat"]:
        return f"đã đạt {x['ma']}"
    if x["chua_chac_dat"]:
        return f"chưa chắc đã đạt {x['ma']} (điểm chưa chắc)"
    kq = x["du_dk"]
    if khac and khac["da_dat"]:
        return (f"không áp dụng — bạn đã đạt {khac['ma']} (QĐ3266 Điều 31: sinh viên thực hiện một trong ba hình thức "
                "cuối khoá)")
    if nhom["da_du"]:
        return "không còn cần — nhóm tốt nghiệp đã đủ tín chỉ"
    if kq == "NOT_ELIGIBLE":
        if any(l_.startswith("dv_cong_bo_khac(") for l_ in x["ly_do"]):    # review M2
            return ("chưa đủ điều kiện nhận đề tài: hồ sơ đã khai báo hình thức cuối khoá khác (đơn vị đào tạo xét và công "
                    "bố — QĐ3266 Điều 31)")
        if any(l_.startswith("thieu_tc(") for l_ in x["ly_do"]):
            hien = f" (hiện có {tc_tl[0]} TC)" if len(tc_tl) == 1 else ""
            return f"chưa đủ điều kiện nhận đề tài: cần tích lũy ít nhất {x['nguong_tc']} TC{hien}"
        return "chưa đủ điều kiện nhận đề tài"
    if kq == "UNKNOWN":
        return "chưa chắc đủ điều kiện nhận đề tài" + (" — cần bổ sung: " + " | ".join(can_bo_sung) if can_bo_sung else "")
    return TEN_KQ.get(kq, kq)


def _hoc_them(x):
    t = (f"đã đạt {', '.join(x['thay_the_da_dat'])}" if x["thay_the_da_dat"] else "chưa đạt học phần thay thế nào")
    t += f"; còn thiếu {x['tc_con_thieu']} TC trong nhóm"
    if x["tc_con_thieu"]:
        if x["dang_ky_duoc"]:      # review M1: chỉ tiên quyết + song hành, không phải lịch đăng ký
            t += (f"; đủ điều kiện tiên quyết/song hành để đăng ký: {', '.join(x['dang_ky_duoc'])} (chưa xét học kỳ mở và "
                  "thời gian đăng ký)")
        if x["chua_du_dk"]:
            t += f"; chưa đủ điều kiện đăng ký: {', '.join(x['chua_du_dk'])}"
    if x["chua_chac"]:
        t += f"; chưa chắc: {', '.join(x['chua_chac'])}"
    return t


def dien_giai(pa, nhom, tc_tl, hoi_lv=(), hoi_tl=()):
    lv, tl, kh = pa["luan_van"], pa["tieu_luan"], pa["khong_lv_tl"]
    dong = [f"Nhóm học phần tốt nghiệp của CTĐT cần TỔNG ít nhất {nhom['toi_thieu']} TC trong các học phần của nhóm "
            f"({lv['ma']}, {tl['ma']}, {', '.join(tl['thay_the'])}); có ba phương án:"]
    dong.append(f"(1) Luận văn — {lv['ma']} ({lv['tc']} TC, mở {_hk(lv['mo_hk'])}): "
                f"{_trang_thai(lv, nhom, tc_tl, hoi_lv, khac=tl)}.")
    dong.append(f"(2) Tiểu luận — {tl['ma']} ({tl['tc']} TC, mở {_hk(tl['mo_hk'])}) cộng học phần thay thế trong nhóm cho đủ "
                f"{nhom['toi_thieu']} TC: {_trang_thai(tl, nhom, tc_tl, hoi_tl, khac=lv)}; {_hoc_them(tl)}.")
    dong.append(f"(3) Không làm luận văn hay tiểu luận, chỉ học học phần thay thế trong nhóm cho đủ {nhom['toi_thieu']} TC "
                f"(QĐ3266 Điều 31 khoản 3): {_hoc_them(kh)}.")
    dong.append(f"Nhóm tốt nghiệp: đã tích lũy {'chắc chắn ' if nhom['co_chua_chac'] else ''}{nhom['tc_da_dat']}/"
                f"{nhom['toi_thieu']} TC" + (" — đã đủ." if nhom["da_du"] else "."))
    dong.append("Quy chế chỉ quy định điều kiện nhận đề tài là ngưỡng tín chỉ của CTĐT (QĐ3266 Điều 31, quyết định diễn giải "
                "QD-12); tiêu chí khác của khoa (nếu có) chưa có trong văn bản đã hình thức hoá. Hệ thống không khuyên chọn "
                "phương án nào — lựa chọn là của bạn.")
    return " ".join(dong)
