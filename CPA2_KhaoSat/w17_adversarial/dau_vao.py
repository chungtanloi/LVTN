"""
dau_vao.py — dựng đầu vào của một ca đối kháng (CPA2, Tuần 17)

Ca mô tả đầu vào ở dạng TRUNG LẬP với hệ thống: hồ sơ gốc (6 hồ sơ giả lập Tuần 7) + danh sách phép
biến đổi. Từ đó dựng:
  - "ho_so": hồ sơ student_fact_schema đưa cho hệ thống (HP không chắc đã bị bỏ ra)
  - "khong_chac" / "mien_chua_ro": dữ kiện mở, mỗi hệ thống tự diễn đạt (CPA² → lựa chọn ASP;
    baseline LLM → câu chữ trong mo_ta_cho_nguoi)
  - "ho_so_that": hồ sơ thật phía sau (dùng cho oracle và cho su_that của ca OCR)
  - "doc": tài liệu OCR (định dạng doc_bang_diem của Tuần 15) cho ca mức tài liệu — không cần Tesseract

Phép biến đổi hồ sơ:
  ["dat", k, v] · ["xoa", k] · ["diem", ma, t10] · ["xoa_diem", ma] · ["diem_tho", ma, {bản ghi}]
  ["diem_dac_biet", ma, "I"|"W"] · ["chung_chi", loai, diem] · ["mien", ma, quyet_dinh] · ["bo_mien", ma]
  ["khong_chac", ma, [t10, ...]] · ["mien_chua_ro", ma] · ["tat_ca_khong_dk", t10]
Phép biến đổi tài liệu OCR (sau khi dựng doc từ hồ sơ thật):
  ["doi_chu", ma, chu] · ["doi_diem", ma, t10] (đọc nhất quán: Thi, T.Hợp, chữ cùng sai) · ["mat_dong", ma]
  ["doi_ma", ma, ma_moi|None] · ["conf", ma, truong, gia_tri] · ["doi_tc", ma, tc]
  ["doi_tong_dk", i_hk, v] · ["doi_dtbchk", i_hk, v|None] · ["hoc_lai", ma, t10_lan_dau, i_hk_lan_dau, doc_duoc]
"""
import copy, json, sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
STUDENTS = ROOT / "w7_student_facts" / "students"
sys.path.insert(0, str(HERE))
import oracle

CONF = {"ma": .99, "tc": .99, "thi": .99, "thop": .99, "chu": .99}


def ho_so_goc(ten):
    return json.loads((STUDENTS / f"{ten}.json").read_text(encoding="utf-8"))


def ban_ghi(ma, t10):
    return {"code": ma, "credits": oracle._CT[ma]["tin_chi"], "thang10": t10, "letter": oracle.chu(t10),
            "status": "passed" if t10 >= 40 else "failed"}


def _ap_ho_so(j, ops):
    khong_chac, mien_chua_ro = {}, []
    for op in ops:
        k = op[0]
        if k == "dat":
            j[op[1]] = op[2]
        elif k == "xoa":
            j.pop(op[1], None)
        elif k == "diem":
            j["grades"][op[1]] = ban_ghi(op[1], op[2])
        elif k == "xoa_diem":
            for m in (op[1] if isinstance(op[1], list) else [op[1]]):
                j["grades"].pop(m)
        elif k == "diem_tho":
            j["grades"][op[1]] = dict(op[2], code=op[1])
        elif k == "diem_dac_biet":
            j["grades"][op[1]] = {"code": op[1], "credits": oracle._CT[op[1]]["tin_chi"], "thang10": None,
                                  "letter": op[2], "diem": op[2], "status": "in_progress" if op[2] == "I" else "unknown"}
        elif k == "chung_chi":
            j.setdefault("certificates", []).append({"loai": op[1], "diem": op[2]})
        elif k == "mien":
            j.setdefault("exemptions", []).append({"ma_hp": op[1], "chung_chi_ref": 0, "quyet_dinh": op[2]})
        elif k == "bo_mien":
            j["exemptions"] = [e for e in j.get("exemptions", []) if e["ma_hp"] != op[1]]
        elif k == "khong_chac":
            khong_chac[op[1]] = op[2]
        elif k == "mien_chua_ro":
            mien_chua_ro.append(op[1])
        elif k == "tat_ca_khong_dk":
            for m, g in j["grades"].items():
                if g.get("thang10") is not None and not oracle.dieu_kien(m):
                    j["grades"][m] = ban_ghi(m, op[1])
        else:
            raise ValueError(f"phép biến đổi lạ: {op}")
    return j, khong_chac, mien_chua_ro


def asp_mo(khong_chac, mien_chua_ro):
    """Dữ kiện mở → ASP cho CPA²."""
    s = [f'1 {{ {"; ".join(f"g10(\"{m}\",{v})" for v in vs)} }} 1.' for m, vs in khong_chac.items()]
    s += [f'{{ duoc_mien("{m}") }}.' for m in mien_chua_ro]
    return "\n".join(s)


# ---------------------------------------------------------------- tài liệu OCR
def _dong(ma, t10):
    return {"ma": ma, "tc": oracle._CT[ma]["tin_chi"], "thi": t10 / 10, "thop": t10 / 10, "chu": oracle.chu(t10),
            "mien": False, "conf": dict(CONF), "ocr_raw": None}


def _O():
    sys.path.insert(0, str(ROOT / "w15_ocr"))
    import ocr_transcript
    return ocr_transcript


def _tong(hk):
    O = _O()
    hk["tong_dk"] = sum(d["tc"] for d in hk["dong"])
    v = O._dtbchk(hk["dong"], O.ctdt())
    hk["dtbchk"] = round(v, 2) if v is not None else None


def doc_tu_ho_so(j):
    """Hồ sơ → bảng điểm đọc HOÀN HẢO (định dạng doc_bang_diem). Chia học kỳ như render_transcript."""
    sys.path.insert(0, str(ROOT / "w15_ocr"))
    import render_transcript as RT
    doc = {"hoc_ky": []}
    for i, ds in enumerate(RT.chia_hoc_ky(j, RT._ctdt())):
        hk = {"ten": f"HK{i + 1}", "dong": [_dong(m, j["grades"][m]["thang10"]) for m in ds if m != "CC004"]}
        _tong(hk)
        doc["hoc_ky"].append(hk)
    return doc


def _tim(doc, ma):
    for hk in doc["hoc_ky"]:
        for d in hk["dong"]:
            if d["ma"] == ma:
                return hk, d
    raise KeyError(ma)


def _ap_doc(doc, ops):
    for op in ops:
        k = op[0]
        if k == "doi_chu":
            _tim(doc, op[1])[1]["chu"] = op[2]
        elif k == "doi_diem":
            d = _tim(doc, op[1])[1]
            d.update(thi=op[2] / 10, thop=op[2] / 10, chu=oracle.chu(op[2]))
        elif k == "mat_dong":
            hk, d = _tim(doc, op[1])
            hk["dong"].remove(d)
        elif k == "doi_ma":          # ["doi_ma", ma, ma_doc_duoc, ma_khac?] — ma_khac: lần đọc thứ hai của mã
            d = _tim(doc, op[1])[1]
            d["ma"] = op[2]
            if len(op) > 3:
                d["ma_khac"] = op[3]
        elif k == "conf":
            _tim(doc, op[1])[1]["conf"][op[2]] = op[3]
        elif k == "doi_tc":
            _tim(doc, op[1])[1]["tc"] = op[2]
        elif k == "doi_tong_dk":
            doc["hoc_ky"][op[1]]["tong_dk"] = op[2]
        elif k == "doi_dtbchk":
            doc["hoc_ky"][op[1]]["dtbchk"] = op[2]
        elif k == "hoc_lai":          # lần học đầu ở học kỳ i (được in đầy đủ, tổng học kỳ nhất quán)
            _, ma, t10, i, doc_duoc = op
            hk = doc["hoc_ky"][i]
            d = _dong(ma, t10)
            hk["dong"].insert(0, d)
            _tong(hk)
            if not doc_duoc:          # lần học SAU (dòng hiện có) đọc không ra điểm
                _, sau = next((h, x) for h in doc["hoc_ky"] if h is not hk for x in h["dong"] if x["ma"] == ma)
                sau.update(thi=None, thop=None, chu=None, conf={"ma": .99, "tc": .99})
        else:
            raise ValueError(f"phép biến đổi OCR lạ: {op}")
    return doc


# ---------------------------------------------------------------- giao diện
def vat_lieu_hoa(ca):
    dv = ca["dau_vao"]
    j = ho_so_goc(dv["goc"])
    if dv["loai"] == "ho_so":
        hs, kc, mcr = _ap_ho_so(j, dv.get("bien_doi", []))
        that = copy.deepcopy(hs)
        for m in kc:
            hs["grades"].pop(m, None)
        for m in mcr:
            hs["exemptions"] = [e for e in hs.get("exemptions", []) if e["ma_hp"] != m]
        return {"ho_so": hs, "khong_chac": kc, "mien_chua_ro": mcr, "them_asp": asp_mo(kc, mcr), "ho_so_that": that}
    if dv["loai"] == "ocr_doc":
        that, _, _ = _ap_ho_so(j, dv.get("that", []))
        doc = _ap_doc(doc_tu_ho_so(that), dv.get("bien_doi", []))
        kb = {k: that[k] for k in ("xac_nhan_ky_luat_sach", "da_hoc_nam2") if k in that}
        for k in dv.get("khai_bao_bo", []):
            kb.pop(k, None)
        return {"doc": doc, "khai_bao": kb, "ho_so_that": that}
    if dv["loai"] == "ocr_anh":       # mức ảnh: render + Tesseract lúc chạy (Tuần 15), không chấm điểm
        return {"anh": (dv["goc"], dv["bien_the"]), "ho_so_that": j}
    raise ValueError(dv["loai"])


def mo_ta_cho_nguoi(ca):
    """Mô tả tiếng Việt của đầu vào (cho baseline không đọc được ASP/JSON biến đổi)."""
    dv = ca["dau_vao"]
    if dv["loai"] != "ho_so":
        return f"Bảng điểm OCR của hồ sơ {dv['goc']} (xem tài liệu OCR đính kèm)."
    v = vat_lieu_hoa(ca)
    s = [f"Hồ sơ {dv['goc']} (CTĐT CNTT K49) sau các thay đổi:"]
    for op in dv.get("bien_doi", []):
        s.append("  - " + json.dumps(op, ensure_ascii=False))
    for m, vs in v["khong_chac"].items():
        s.append(f"  - điểm {m} CHƯA RÕ, có thể là một trong: {', '.join(f'{x / 10:.1f}' for x in vs)}")
    for m in v["mien_chua_ro"]:
        s.append(f"  - CHƯA RÕ học phần {m} đã có quyết định miễn hay chưa")
    return "\n".join(s)
