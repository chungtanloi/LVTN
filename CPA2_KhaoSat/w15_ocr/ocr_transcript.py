"""
ocr_transcript.py — OCR bảng điểm ĐHCT → dữ kiện sinh viên có confidence (CPA2, Tuần 15)

  ảnh trang ──► dựng thẳng ──► lượt OCR chính (vie): học kỳ, dòng tiêu đề cột, dòng HP, dòng tổng
           └──► OCR từng dải cột (eng + whitelist): Mã HP · TC · Thi · T.Hợp · Q/Đổi
  ──► chuẩn hoá (sửa mã, điểm thang 10 luôn 1 chữ số thập phân) ──► kiểm chéo ──► hồ sơ + báo cáo

Kiểm chéo (fact chỉ được nhận khi qua hết và confidence ≥ TAU):
  - mã HP có trong CTĐT K49 · TC khớp CTĐT · điểm chữ khớp T.Hợp theo R-B02
  - học kỳ: Σ TC các dòng = "Tổng Số Tín Chỉ Đăng Ký"; ĐTBCHK tính lại = số in (R-B08)
Không chắc ≠ sai: HP đọc được mã mà điểm không chắc → solver xét CẢ hai khả năng (đạt/rớt).
Có dòng không đọc được hoặc học kỳ lệch tổng TC → có thể có HP bị ẩn → kết luận UNKNOWN.

Bảng điểm không ghi tình trạng kỷ luật, lựa chọn tích lũy (CQ-06) → lấy từ `khai_bao`, không OCR.
"""
import json, os, re, sys, unicodedata
from pathlib import Path

import numpy as np
import pytesseract
from PIL import Image

HERE = Path(__file__).parent
ROOT = HERE.parent
CURRICULUM = ROOT / "w6_curriculum" / "curriculum_cntt_k49.json"
sys.path.insert(0, str(ROOT / "w7_student_facts"))
sys.path.insert(0, str(ROOT / "w12_integration"))

pytesseract.pytesseract.tesseract_cmd = os.environ.get(
    "TESSERACT_EXE", r"C:/Program Files/Tesseract-OCR/tesseract.exe")

TAU = 0.70                    # ngưỡng confidence (0–1) của một trường OCR — chốt trước khi đo
MAX_KHONG_CHAC = 6            # quá số HP không chắc → không giải (3^k mô hình), trả UNKNOWN
CHU_4 = {"A": 4.0, "B+": 3.5, "B": 3.0, "C+": 2.5, "C": 2.0, "D+": 1.5, "D": 1.0, "F": 0.0}
NGUONG = [(9.0, "A"), (8.0, "B+"), (7.0, "B"), (6.5, "C+"), (5.5, "C"), (5.0, "D+"), (4.0, "D")]   # R-B02
# OCR hay nhầm chữ ↔ số trong phần số của mã HP
SO = {"O": "0", "D": "0", "Q": "0", "U": "0", "I": "1", "L": "1", "T": "1", "J": "1",
      "S": "5", "B": "8", "Z": "2", "G": "6"}
CHU = {"0": "O", "1": "I", "5": "S", "8": "B", "2": "Z", "6": "G"}
# vị trí cột theo tỉ lệ khổ trang, dùng khi không đọc được dòng tiêu đề (bố cục Mẫu In D5050A0)
COT_TI_LE = {"ma": .061, "ten": .144, "nhom": .481, "tc": .552, "thi": .585, "l2": .641,
             "thop": .688, "qd": .744, "sao": .800}

_CTDT = None


def ctdt():
    global _CTDT
    if _CTDT is None:
        cur = json.loads(CURRICULUM.read_text(encoding="utf-8"))
        _CTDT = {h["ma"]: {"tc": h["tin_chi"], "dieu_kien": h["dieu_kien"]} for h in cur["hoc_phan"]}
    return _CTDT


def bo_dau(s):
    s = s.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()


# ---------------------------------------------------------------- chuẩn hoá
def sua_ma(raw):
    """Mã HP CTĐT: 2 chữ + 3 số + 'E' tuỳ chọn (CT100, QP010E). Sửa nhầm chữ/số theo vị trí."""
    s = re.sub(r"[^A-Z0-9]", "", (raw or "").upper())
    if s.startswith("SHCV"):
        return "SHCVHT"
    if len(s) < 5:
        return None
    dau, than = "".join(CHU.get(c, c) for c in s[:2]), s[2:]
    duoi = ""
    if len(than) == 4 and than.endswith("E"):
        than, duoi = than[:3], "E"
    if len(than) != 3 or not dau.isalpha():
        return None
    than = "".join(SO.get(c, c) for c in than)
    return dau + than + duoi if than.isdigit() else None


def so_thang10(raw):
    """Điểm thang 10 trên bảng điểm luôn có đúng 1 chữ số thập phân → '97' là 9.7, '100' là 10.0."""
    s = (raw or "").strip().replace(",", ".").replace("/", ".")
    if re.fullmatch(r"\d{1,2}\.\d", s):
        v = float(s)
    elif re.fullmatch(r"\d{2,3}", s):
        v = int(s) / 10
    else:
        return None
    return v if 0 <= v <= 10 else None


def chu_tu_diem(x):
    x = round(x, 1)
    for nguong, chu in NGUONG:
        if x >= nguong:
            return chu
    return "F"


def anh_xa_dac_biet(d):
    if d.get("ma") == "SHCVHT":
        return {"bo_qua": True}
    if d.get("ma") == "CC004" and d.get("mien"):
        return {"duoc_mien": ["XH023", "XH024", "XH025"],
                "can_xac_nhan": "CC004 'Chứng chỉ trình độ Tiếng Anh' 10 TC Miễn M → giả định miễn trọn nhánh "
                                "Anh văn của g_ngoai_ngu (XH023–025, 10 TC); chờ Phòng Đào tạo xác nhận"}
    return None


def _conf_dong(d):
    """Confidence của dòng = min(mã, TC, điểm). Điểm có tới 3 lần đọc riêng: T.Hợp, điểm chữ (khi khớp
    R-B02) và cột Thi (khi bằng T.Hợp — không có L2). Các lần đọc khớp nhau dưới ràng buộc tất định
    → gộp 1 − Π(1 − cᵢ). Giả định: lỗi OCR giữa các cột gần độc lập (cùng ảnh nên chỉ là xấp xỉ)."""
    c = d.get("conf") or {}
    if not c:
        return 0.0
    phan = [c.get("ma", 0.0)] + ([c.get("tc", 0.0)] if "tc" in c else [])
    if "thop" in c:
        doc = [c["thop"]]
        if d.get("chu") and d.get("thop") is not None and chu_tu_diem(d["thop"]) == d["chu"]:
            doc.append(c.get("chu", 0.0))
        if d.get("thi") is not None and d.get("thi") == d.get("thop"):
            doc.append(c.get("thi", 0.0))
        phan.append(1 - float(np.prod([1 - x for x in doc])))
    return min(phan)


def kiem_dong(d, ct, tau=None):
    """Kiểm một dòng HP. Trả {'hop_le', 'ly_do', 'conf'}."""
    tau = TAU if tau is None else tau
    ly_do = []
    ma = d.get("ma")
    if ma is None:
        ly_do.append("không đọc được mã")
    elif ma not in ct:
        ly_do.append("mã ngoài CTĐT")
    else:
        if d.get("tc") != ct[ma]["tc"]:
            ly_do.append(f"TC {d.get('tc')} ≠ CTĐT {ct[ma]['tc']}")
        if not d.get("mien"):
            if d.get("thop") is None or d.get("chu") is None:
                ly_do.append("thiếu điểm")
            elif chu_tu_diem(d["thop"]) != d["chu"]:
                ly_do.append(f"điểm chữ {d['chu']} ≠ R-B02({d['thop']}) = {chu_tu_diem(d['thop'])}")
    conf = _conf_dong(d)
    if conf < tau:
        ly_do.append(f"confidence {conf:.2f} < {tau}")
    return {"hop_le": not ly_do, "ly_do": ly_do, "conf": conf}


# ---------------------------------------------------------------- OCR
def _tu(img, cfg, lang):
    d = pytesseract.image_to_data(img, lang=lang, config=cfg, output_type=pytesseract.Output.DICT)
    out = []
    for i, t in enumerate(d["text"]):
        if t.strip() and float(d["conf"][i]) >= 0:
            out.append({"t": t.strip(), "c": float(d["conf"][i]) / 100, "x": d["left"][i], "y": d["top"][i],
                        "w": d["width"][i], "h": d["height"][i],
                        "k": (d["block_num"][i], d["par_num"][i], d["line_num"][i])})
    return out


def _dung_thang(g):
    """Dựng thẳng ảnh lệch bằng projection profile (phương sai tổng hàng ngang lớn nhất)."""
    nho = g.resize((g.width // 2, g.height // 2))
    def diem(goc):
        a = np.asarray(nho.rotate(goc, fillcolor=255)) < 128
        return a.sum(axis=1).astype(float).var()
    goc = max(np.arange(-2, 2.01, 0.2), key=diem)
    goc = max(np.arange(goc - 0.2, goc + 0.21, 0.05), key=diem)
    # góc rất nhỏ chỉ thêm nhiễu nội suy (xoay -0,05° làm "ML018" thành "ML01§") → bỏ qua
    return g.rotate(goc, resample=Image.BICUBIC, fillcolor=255) if abs(goc) >= 0.15 else g


def _gom_dong(tu):
    dong = {}
    for w in tu:
        dong.setdefault(w["k"], []).append(w)
    out = []
    for ws in dong.values():
        ws.sort(key=lambda w: w["x"])
        out.append({"tu": ws, "text": " ".join(w["t"] for w in ws),
                    "y0": min(w["y"] for w in ws), "y1": max(w["y"] + w["h"] for w in ws)})
    return sorted(out, key=lambda l: l["y0"])


def _cot(dong, rong):
    """Ranh giới cột từ dòng tiêu đề; thiếu tiêu đề nào thì dùng tỉ lệ khổ trang."""
    x = {k: v * rong for k, v in COT_TI_LE.items()}
    for w in dong["tu"]:
        b = bo_dau(w["t"])
        for k, tien_to in (("ma", "ma"), ("ten", "ten"), ("nhom", "nhom"), ("tc", "tc"), ("thi", "thi"),
                           ("l2", "l2"), ("thop", "t.h"), ("qd", "q/"), ("sao", "*")):
            if b.startswith(tien_to):
                x[k] = w["x"]
    e = rong * 0.008
    return {"ma": (x["ma"] - 2 * e, x["ten"] - e), "tc": (x["tc"] - e, x["thi"] - e),
            "thi": (x["thi"] - e, x["l2"] - e), "thop": (x["thop"] - e, x["qd"] - e),
            "chu": (x["qd"] - e, x["sao"] - e)}


WHITELIST = {"ma": "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", "tc": "0123456789",
             "thi": "0123456789.-", "thop": "0123456789.", "chu": "ABCDFM+"}
# token đầu của dòng HP ở cột Mã: chữ hoa đầu + 3–7 ký tự bất kỳ (OCR: "CTlIl2", "ML01§");
# giá trị mã thật lấy từ OCR dải cột, token này chỉ để nhận ra dòng
# KHÔNG nhận chữ có dấu: tiêu đề lặp ở trang sau ("Bảng Ghi Điểm…", "Loại…") từng bị nhận nhầm là dòng HP
LA_DONG_HP = re.compile(r"^[A-Z][A-Za-z0-9§|$_]{3,7}$")


def doc_trang(img, st):
    g = img.convert("L")
    if g.width < 2000:
        g = g.resize((g.width * 2, g.height * 2), Image.LANCZOS)
    g = _dung_thang(g)
    dong_trang = []
    for l in _gom_dong(_tu(g, "--psm 6", "vie")):
        b = bo_dau(l["text"])
        if "hoc ky" in b and "nam hoc" in b:
            m = re.search(r"hoc ky\s*(\w)\W+nam hoc\s*(\d{2})\s*-\s*(\d{2})", b)
            st["hk"].append({"ten": f"HK{m.group(1)} {m.group(2)}-{m.group(3)}" if m else f"HK? #{len(st['hk']) + 1}",
                             "dong": [], "tong_dk": None, "dtbchk": None})
            continue
        if "nhom" in b and ("hop" in b or "doi" in b):
            st["cot"] = _cot(l, g.width)
            continue
        if not st["hk"]:
            continue
        hk = st["hk"][-1]
        if "dang ky" in b and "tong" in b:
            so = re.findall(r"\b\d{1,3}\b", l["text"])
            hk["tong_dk"] = int(so[-1]) if so else None
            continue
        if "chung hoc ky" in b:
            so = re.findall(r"\d[.,]\d{2}", l["text"])
            hk["dtbchk"] = float(so[-1].replace(",", ".")) if so else None
            continue
        if "tong so" in b or "ren luyen" in b or st["cot"] is None:
            continue
        dau = l["tu"][0]
        if LA_DONG_HP.match(dau["t"]) and dau["x"] < st["cot"]["ma"][1]:
            d = {"ma_dong": dau["t"], "c_ma_dong": dau["c"], "yc": dau["y"] + dau["h"] / 2, "cao": dau["h"], "mien": "mien" in b,
                 "ocr_raw": l["text"], "conf": {}}
            hk["dong"].append(d)
            dong_trang.append(d)
    if not dong_trang:
        return
    y0 = int(min(d["yc"] for d in dong_trang) - 60)
    y1 = int(max(d["yc"] for d in dong_trang) + 60)
    for cot, (xa, xb) in st["cot"].items():
        dai = g.crop((int(xa), max(y0, 0), int(xb), min(y1, g.height)))
        tu = _tu(dai, f"--psm 6 -c tessedit_char_whitelist={WHITELIST[cot]}", "eng")
        gan = {}
        for w in tu:
            yc = w["y"] + w["h"] / 2 + y0
            d = min(dong_trang, key=lambda d: abs(d["yc"] - yc))
            if abs(d["yc"] - yc) <= max(d["cao"], 20):
                gan.setdefault(id(d), []).append(w)
        for d in dong_trang:
            ws = sorted(gan.get(id(d), []), key=lambda w: w["x"])
            d[f"{cot}_raw"] = "".join(w["t"] for w in ws)
            d["conf"][cot] = min((w["c"] for w in ws), default=0.0)
    for d in dong_trang:
        # mã có hai lần đọc: dải cột (whitelist) và token đầu dòng (lượt chính)
        ma_s, ma_d = sua_ma(d["ma_raw"]), sua_ma(d["ma_dong"])
        c_s, c_d = d["conf"].get("ma", 0.0), d.pop("c_ma_dong")
        if ma_s and ma_s == ma_d:
            d["ma"], d["conf"]["ma"] = ma_s, 1 - (1 - c_s) * (1 - c_d)
        elif ma_s and ma_d:          # hai lần đọc ra hai mã khác nhau
            trong = [m for m in (ma_s, ma_d) if m in ctdt() or m == "SHCVHT"]
            if len(trong) == 1:
                d["ma"], d["conf"]["ma"] = trong[0], (c_s if trong[0] == ma_s else c_d)
            else:                    # cùng hợp lệ (CT518E / CT515E) → không biết dòng là HP nào
                d["ma"], d["ma_khac"], d["conf"]["ma"] = ma_s, ma_d, 0.0
        else:
            d["ma"] = ma_s or ma_d
            d["conf"]["ma"] = c_s if ma_s else c_d
        d["tc"] = int(d["tc_raw"]) if d["tc_raw"].isdigit() else None
        d["thi"] = so_thang10(d["thi_raw"])
        d["thop"] = so_thang10(d["thop_raw"])
        d["chu"] = d["chu_raw"] if d["chu_raw"] in CHU_4 else None
        if d["mien"]:   # dòng miễn: không có T.Hợp / điểm chữ để kiểm
            for k in ("thi", "thop", "chu"):
                d["conf"].pop(k, None)
        if d["ma"] == "SHCVHT":
            d["conf"] = {"ma": d["conf"].get("ma", 0)}


def doc_bang_diem(anh):
    """Danh sách ảnh trang (theo thứ tự) → {'hoc_ky': [{'ten','dong','tong_dk','dtbchk'}]}."""
    st = {"hk": [], "cot": None}
    for img in (anh if isinstance(anh, list) else [anh]):
        doc_trang(img, st)
    for hk in st["hk"]:
        for d in hk["dong"]:
            for k in ("yc", "cao"):
                d.pop(k, None)
    return {"hoc_ky": st["hk"]}


# ---------------------------------------------------------------- dữ kiện
def _dtbchk(dong, ct):
    tu = mau = 0.0
    for d in dong:
        hp = ct.get(d.get("ma"))
        if (hp and not d.get("mien") and d.get("chu") in CHU_4 and d.get("tc") is not None
                and hp["dieu_kien"] != "gdtc"):   # R-B08
            tu += CHU_4[d["chu"]] * d["tc"]
            mau += d["tc"]
    return tu / mau if mau else None


def sang_ho_so(doc, khai_bao=None, tau=None):
    """Kết quả OCR → (hồ sơ JSON theo student_fact_schema, ASP bổ sung, báo cáo)."""
    tau = TAU if tau is None else tau
    ct = ctdt()
    grades, mien, khong_chac = {}, [], []
    bc = {"tong_dong": 0, "nhan": 0, "loai": 0, "khong_chac": khong_chac, "hoc_ky_lech": [], "dong_an": 0,
          "can_xac_nhan": [], "ngoai_ctdt": [], "chi_tiet": []}
    for hk in doc["hoc_ky"]:
        dong = [d for d in hk["dong"] if d.get("ma") != "SHCVHT"]
        bc["tong_dong"] += len(dong)
        tc = sum(d.get("tc") or 0 for d in dong)
        tc_khong_mien = sum(d.get("tc") or 0 for d in dong if not d.get("mien"))
        doc_duoc = all(d.get("ma") and d.get("tc") is not None for d in dong)
        lech_tc = hk["tong_dk"] is None or hk["tong_dk"] not in (tc, tc_khong_mien) or not doc_duoc
        if lech_tc:
            bc["hoc_ky_lech"].append(hk["ten"])
            bc["dong_an"] += 1       # có thể có HP bị ẩn/không đọc được → không được kết luận "thiếu môn"
        tinh = _dtbchk(dong, ct)
        lech_dtb = (not lech_tc and hk["dtbchk"] is not None and tinh is not None
                    and abs(tinh - hk["dtbchk"]) > 0.006)
        if lech_dtb:
            bc["hoc_ky_lech"].append(hk["ten"] + " (ĐTBCHK)")
        for d in dong:
            dac_biet = anh_xa_dac_biet(d)
            if dac_biet and "duoc_mien" in dac_biet:
                if d.get("tc") == 10:
                    mien += dac_biet["duoc_mien"]
                    bc["can_xac_nhan"].append(dac_biet["can_xac_nhan"])
                    bc["nhan"] += 1
                else:
                    bc["loai"] += 1
                    bc["dong_an"] += 1
                continue
            kq = kiem_dong(d, ct, tau)
            bc["chi_tiet"].append({"hoc_ky": hk["ten"], "ma": d.get("ma"), "ly_do": kq["ly_do"],
                                   "conf": round(kq["conf"], 2), "ocr_raw": d.get("ocr_raw")})
            ma = d.get("ma")
            if ma is None:
                bc["loai"] += 1
                bc["dong_an"] += 1
            elif ma not in ct:
                bc["ngoai_ctdt"].append(ma)
            elif kq["hop_le"] and not lech_dtb:
                if d.get("mien"):
                    g = {"code": ma, "credits": d["tc"], "diem": "M", "status": "passed"}
                else:
                    g = {"code": ma, "credits": d["tc"], "thang10": round(d["thop"] * 10), "letter": d["chu"],
                         "status": "passed" if d["chu"] != "F" else "failed"}
                g.update(confidence=round(kq["conf"], 3), ocr_raw=d.get("ocr_raw"))
                cu = grades.get(ma)
                if cu is None or g.get("thang10", 0) > cu.get("thang10", 0):   # học lại: lấy điểm cao nhất (R-B13)
                    grades[ma] = g
                bc["nhan"] += 1
            else:
                for m in (ma, d.get("ma_khac")):
                    if m in ct and m not in khong_chac:
                        khong_chac.append(m)
    # mã đọc ra ngoài CTĐT nhưng chỉ lệch 1 ký tự với một HP CTĐT chưa có → có thể là HP đó đọc sai
    for ma in bc["ngoai_ctdt"]:
        for m in ct:
            if m not in grades and m not in khong_chac and len(m) == len(ma) and sum(a != b for a, b in zip(m, ma)) == 1:
                khong_chac.append(m)
    # mã có dù chỉ một dòng không chắc (vd. học lại đọc không ra) → cả mã là không chắc, kể cả khi
    # một lần học khác đọc chắc: điểm cuối là điểm cao nhất (R-B13) mà ta không biết
    for m in khong_chac:
        grades.pop(m, None)
    extra = lua_chon(khong_chac)
    # Dữ kiện ngoài bảng điểm chưa khai báo → để mở cả hai nhánh. KB Tuần 10 dùng giả định thế giới
    # đóng (thiếu xac_nhan_ky_luat_sach → FALSE, không phải UNKNOWN như chú thích của nó) — sửa ở Tuần 16.
    bc["khai_bao_thieu"] = [k for k in ("xac_nhan_ky_luat_sach",) if k not in (khai_bao or {})]
    extra += "".join(f"\n{{ {k} }}." for k in bc["khai_bao_thieu"])
    hs = {"student_id": "sv_ocr", "major": "cntt", "cohort": "K49", "ctdt": "cntt_k49", "grades": grades,
          "exemptions": [{"ma_hp": m, "chung_chi_ref": None, "quyet_dinh": True} for m in mien],
          "meta": {"nguon": "ocr", "tau": tau}}
    hs.update(khai_bao or {})
    return hs, extra, bc


# ---------------------------------------------------------------- kết luận
# Điểm đại diện cho HP không chắc: F (0), D (40 — đạt thấp nhất), A (100). tot_nghiep phụ thuộc điểm
# qua (đạt / không) và các trung bình (ĐTBCTL, TB GDQP) — đơn điệu trong miền đạt. Chỉ xét F và A là
# SAI: D đạt vẫn vào ĐTBCTL và kéo nó xuống (sv_du_hp: F→TRUE, A→TRUE, D→FALSE).
DIEM_DAI_DIEN = (0, 40, 100)


def lua_chon(khong_chac):
    return "\n".join("1 { " + "; ".join(f'g10("{m}",{v})' for v in DIEM_DAI_DIEN) + " } 1."
                     for m in khong_chac)


def _w7():
    import validate_student_facts
    return validate_student_facts


def ket_luan(hs, extra, bc, claim="tot_nghiep"):
    """Ba trị trên dữ kiện OCR. HP không chắc → solver xét F / D / A (DIEM_DAI_DIEN). Có dòng ẩn → UNKNOWN."""
    if bc["dong_an"] or len(bc["khong_chac"]) > MAX_KHONG_CHAC:
        return "UNKNOWN"
    import prototype
    return prototype.solve_verdict(claim, _w7().load_facts(hs) + "\n" + extra)[0]


def ket_luan_tu_json(j, claim="tot_nghiep"):
    import prototype
    return prototype.solve_verdict(claim, _w7().load_facts(j))[0]


def khai_bao_tu_json(j):
    return {k: j[k] for k in ("xac_nhan_ky_luat_sach", "khong_tinh_tich_luy", "che_do_sv_chon_tich_luy") if k in j}


def so_khop(hs, j):
    """So fact OCR ĐÃ NHẬN với đáp án. Trả (đúng, tổng, danh sách sai)."""
    dung, sai = 0, []
    for ma, g in hs["grades"].items():
        jg = j["grades"].get(ma)
        ok = jg is not None and jg["credits"] == g["credits"] and (
            g.get("diem") == "M" if jg.get("diem") == "M" else
            (jg.get("thang10") == g.get("thang10") and jg.get("letter") == g.get("letter")))
        dung += ok
        if not ok:
            sai.append(f"{ma}: OCR {g.get('thang10')}/{g.get('letter')} ≠ {jg and (jg.get('thang10'), jg.get('letter'))}")
    mien_dung = {e["ma_hp"] for e in j.get("exemptions", []) if e.get("quyet_dinh")}
    for e in hs["exemptions"]:
        ok = e["ma_hp"] in mien_dung
        dung += ok
        if not ok:
            sai.append(f"miễn {e['ma_hp']} không có trong đáp án")
    return dung, len(hs["grades"]) + len(hs["exemptions"]), sai


if __name__ == "__main__":
    anh = [Image.open(p) for p in sys.argv[1:]]
    hs, extra, bc = sang_ho_so(doc_bang_diem(anh))
    print(json.dumps({k: v for k, v in bc.items() if k != "chi_tiet"}, ensure_ascii=False, indent=1))
