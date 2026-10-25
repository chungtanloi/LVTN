"""
validate_ocr.py — kiểm chứng OCR pipeline v1 (CPA2, Tuần 15)

  A. Hàm chuẩn hoá (không cần OCR): sửa mã HP, đọc điểm thang 10, điểm chữ theo R-B02,
     kiểm dòng, ánh xạ CC004
  B. Bảng điểm tổng hợp (vẽ từ 6 hồ sơ Tuần 7, có đáp án) × biến thể nhiễu:
       - fact được chấp nhận (confidence ≥ τ, qua kiểm chéo) đúng ≥ 99%       [cổng]
       - kết luận tot_nghiep từ OCR ∈ {kết luận từ JSON gốc, UNKNOWN}         [cổng]
       - độ phủ (tỉ lệ kết luận không phải UNKNOWN)                            [báo cáo]
  C. Tiêm lỗi vào kết quả OCR: đọc sai điểm chữ / mất một dòng → bị bắt, không sinh kết luận sai
  D. Bảng điểm thật (chỉ chạy nếu có ảnh ở máy; kết quả ghi vào _rieng/, không commit)  [báo cáo]
  F. Lỗi OCR nhất quán ở mức tài liệu (P17-2): ĐTBCHK không đọc được, mã bắt buộc đọc thành mã tự chọn
  G. C14: kiểm chéo bằng TC tích lũy + ĐTBCTL in sau mỗi học kỳ (cứu học kỳ mất ĐTBCHK; bắt lỗi GDTC F→D)

Chạy: python validate_ocr.py           (đủ A–D)
      python validate_ocr.py --nhanh   (A, C và một biến thể của B)
"""
import copy, json, sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import ocr_transcript as O
import render_transcript as RT

STUDENTS = ROOT / "w7_student_facts" / "students"
import jsonschema
SCHEMA = jsonschema.Draft202012Validator(json.loads((ROOT / "w7_student_facts" / "student_fact_schema.json").read_text(encoding="utf-8")))
HO_SO = ["sv_lvtn", "sv_tltn", "sv_5hp", "sv_tron_ngoai_ngu", "sv_du_hp", "sv_mien_ielts"]
BIEN_THE = ["sach", "mo_jpeg", "nghieng"]
THAT = ROOT.parent / "NiênLuan" / "tmp" / "bangdiem_review"
RIENG = HERE / "_rieng"

ok_all = True


def check(cond, msg, cong=True):
    global ok_all
    print(f"  [{'OK' if cond else ('FAIL' if cong else 'GHI NHẬN')}] {msg}")
    if cong:
        ok_all = ok_all and cond
    return cond


def phan_A():
    print("A. CHUẨN HOÁ")
    for raw, mong in [("CTI00", "CT100"), ("QP0IIE", "QP011E"), ("KL00IE", "KL001E"),
                      ("TN010_", "TN010"), ("QP0I0E", "QP010E"), ("CT550E", "CT550E")]:
        check(O.sua_ma(raw) == mong, f"sua_ma({raw!r}) = {O.sua_ma(raw)!r}, mong {mong!r}")
    for raw, mong in [("97", 9.7), ("9.7", 9.7), ("100", 10.0), ("10.0", 10.0), ("80", 8.0),
                      ("4.5", 4.5), ("45", 4.5), ("9/7", 9.7), ("", None), ("975", None)]:
        check(O.so_thang10(raw) == mong, f"so_thang10({raw!r}) = {O.so_thang10(raw)!r}, mong {mong!r}")
    for x, mong in [(9.7, "A"), (9.0, "A"), (8.9, "B+"), (8.0, "B+"), (7.1, "B"), (6.5, "C+"),
                    (5.5, "C"), (5.0, "D+"), (4.5, "D"), (4.0, "D"), (3.9, "F")]:
        check(O.chu_tu_diem(x) == mong, f"chu_tu_diem({x}) = {O.chu_tu_diem(x)!r}, mong {mong!r} (R-B02)")
    dong = {"ma": "CT100", "tc": 2, "thi": 9.2, "thop": 9.2, "chu": "A", "conf": {"ma": .9, "tc": .9, "thop": .9, "chu": .9}}
    check(O.kiem_dong(dong, O.ctdt())["hop_le"], "dòng nhất quán (9.2 ↔ A, CT100 2 TC) → hợp lệ")
    sai = dict(dong, chu="B")
    check(not O.kiem_dong(sai, O.ctdt())["hop_le"], "điểm chữ không khớp T.Hợp (9.2 ↔ B) → loại")
    sai_tc = dict(dong, tc=3)
    check(not O.kiem_dong(sai_tc, O.ctdt())["hop_le"], "TC không khớp CTĐT (CT100 3 TC) → loại")
    m = O.anh_xa_dac_biet({"ma": "CC004", "tc": 10, "mien": True})
    check(m and sorted(m["duoc_mien"]) == ["XH023", "XH024", "XH025"] and m["can_xac_nhan"],
          "CC004 (10 TC, Miễn M) → miễn XH023–025, gắn cờ cần Phòng Đào tạo xác nhận")
    check(O.anh_xa_dac_biet({"ma": "SHCVHT", "tc": 0}) == {"bo_qua": True}, "SHCVHT 0 TC → bỏ qua")


def ho_so(ten):
    profile = json.loads((STUDENTS / f"{ten}.json").read_text(encoding="utf-8"))
    profile['tc_cong_nhan'] = 0  # declared only in this synthetic OCR scenario
    return profile


def phan_B(nhanh):
    print("B. BẢNG ĐIỂM TỔNG HỢP")
    dung = tong = khong_unknown = so_ca = 0
    for ten in HO_SO:
        j = ho_so(ten)
        truth = O.ket_luan_tu_json(j)
        for bt in (BIEN_THE[:1] if nhanh else BIEN_THE):
            anh = RT.render(j, bien_the=bt)
            doc = O.doc_bang_diem(anh)
            hs, extra, bc = O.sang_ho_so(doc, khai_bao=O.khai_bao_tu_json(j))
            loi = list(SCHEMA.iter_errors(hs))
            check(not loi, f"{ten}/{bt}: hồ sơ OCR hợp lệ theo student_fact_schema ({[e.message for e in loi[:2]]})")
            d, t, sai = O.so_khop(hs, j)
            dung += d
            tong += t
            v = O.ket_luan(hs, extra, bc)
            so_ca += 1
            khong_unknown += v != "UNKNOWN"
            check(v in (truth, "UNKNOWN"),
                  f"{ten}/{bt}: OCR → {v}, JSON → {truth} · fact nhận {bc['nhan']}/{bc['tong_dong']}, "
                  f"loại {bc['loai']}, khác đáp án {sai[:3]}")
    acc = dung / tong if tong else 0
    check(acc >= 0.99, f"fact được chấp nhận đúng {dung}/{tong} = {acc:.3f} (cổng ≥ 0,99)")
    print(f"     độ phủ: {khong_unknown}/{so_ca} ca có kết luận TRUE/FALSE (còn lại UNKNOWN)")


def phan_C():
    print("C. TIÊM LỖI")
    j = ho_so("sv_lvtn")
    doc = O.doc_bang_diem(RT.render(j, bien_the="sach"))
    # 1) đọc sai điểm chữ một dòng đạt (→ F): kiểm chéo R-B02 phải bắt
    d1 = copy.deepcopy(doc)
    dong = next(r for k in d1["hoc_ky"] for r in k["dong"]
                if r.get("chu") not in (None, "F") and r.get("ma") in O.ctdt())
    cu, dong["chu"] = dong["chu"], "F"
    hs, extra, bc = O.sang_ho_so(d1, khai_bao=O.khai_bao_tu_json(j))
    check(dong["ma"] not in hs["grades"] and dong["ma"] in bc["khong_chac"],
          f"{dong['ma']} đọc nhầm {cu}→F → không vào grades, thành dữ kiện không chắc")
    check(O.ket_luan(hs, extra, bc) in ("TRUE", "UNKNOWN"), "kết luận không thành FALSE sai")
    # 2) mất hẳn một dòng (OCR bỏ sót): tổng TC học kỳ lệch → cả học kỳ bị nghi ngờ
    d2 = copy.deepcopy(doc)
    hk = next(k for k in d2["hoc_ky"] if len(k["dong"]) > 3)
    mat = hk["dong"].pop(1)
    hs, extra, bc = O.sang_ho_so(d2, khai_bao=O.khai_bao_tu_json(j))
    check(hk["ten"] in bc["hoc_ky_lech"], f"mất dòng {mat['ma']} → học kỳ '{hk['ten']}' lệch tổng TC")
    check(O.ket_luan(hs, extra, bc) == "UNKNOWN", "mất dòng → UNKNOWN (không phải FALSE vì 'thiếu môn')")
    # 3) không có khai báo kỷ luật (bảng điểm không ghi) → không thể TRUE
    hs, extra, bc = O.sang_ho_so(doc, khai_bao={})
    check(O.ket_luan(hs, extra, bc) == "UNKNOWN", "thiếu xác nhận kỷ luật (R-F03, không có trên bảng điểm) → UNKNOWN")


def phan_E():
    print("E. TÍNH ĐÚNG CỦA LỰA CHỌN CHO HP KHÔNG CHẮC (hồi quy review)")
    # 1) không đơn điệu: sv_du_hp không tốt nghiệp vì CT478 điểm D kéo ĐTBCTL < 2,0. Nếu CT478 đọc không
    #    chắc, chỉ xét F (bị loại khỏi ĐTBCTL) và A thì cả hai nhánh đều TRUE → TRUE sai. Phải có nhánh D.
    j = ho_so("sv_du_hp")
    hs = copy.deepcopy(j)
    hs["grades"].pop("CT478")
    bc = {"dong_an": 0, "khong_chac": ["CT478"]}
    v = O.ket_luan(hs, O.lua_chon(["CT478"]), bc)
    check(v == "UNKNOWN", f"sv_du_hp, CT478 không chắc → {v} (đáp án FALSE; TRUE là sai)")
    # 2) học lại: lần 1 đọc chắc là F, lần 2 đọc không chắc → HP vẫn phải là không chắc, không phải F
    doc = {"hoc_ky": [
        {"ten": "HK1", "tong_dk": 3, "dtbchk": 0.0, "dong": [
            {"ma": "CT177", "tc": 3, "thi": 3.0, "thop": 3.0, "chu": "F", "mien": False,
             "conf": {"ma": .99, "tc": .99, "thi": .99, "thop": .99, "chu": .99}}]},
        {"ten": "HK2", "tong_dk": 3, "dtbchk": None, "dong": [
            {"ma": "CT177", "tc": 3, "thi": None, "thop": None, "chu": None, "mien": False,
             "conf": {"ma": .99, "tc": .99}}]}]}
    hs, extra, bc = O.sang_ho_so(doc, khai_bao={"xac_nhan_ky_luat_sach": True})
    check("CT177" in bc["khong_chac"] and "CT177" not in hs["grades"],
          f"CT177 F rồi học lại đọc không chắc → không chắc (grades: {hs['grades'].get('CT177', {}).get('letter')})")


def phan_D():
    print("D. BẢNG ĐIỂM THẬT (chỉ ở máy)")
    anh = sorted(THAT.glob("page-*.png")) if THAT.exists() else []
    if not anh:
        print("     bỏ qua — không có ảnh")
        return
    from PIL import Image
    doc = O.doc_bang_diem([Image.open(p) for p in anh])
    hs, extra, bc = O.sang_ho_so(doc, khai_bao={})
    RIENG.mkdir(exist_ok=True)
    (RIENG / "ket_qua_that.json").write_text(json.dumps({"ho_so": hs, "bao_cao": bc}, ensure_ascii=False, indent=1),
                                             encoding="utf-8")
    check(bc["tong_dong"] > 0, f"đọc {bc['tong_dong']} dòng HP, nhận {bc['nhan']}, không chắc {len(bc['khong_chac'])}, "
          f"loại {bc['loai']}, học kỳ lệch {bc['hoc_ky_lech']}, cần xác nhận {bc['can_xac_nhan']}", cong=False)


def _ghi_tich_luy(doc):
    """Ghi số tích lũy IN sau mỗi học kỳ, cài ĐỘC LẬP với ocr_transcript: TC tích lũy gồm HP điều kiện và dòng miễn;
    ĐTBCTL bỏ điểm F và HP điều kiện (R-B10); học lại lấy điểm cao nhất (R-B13)."""
    ct = RT._ctdt()
    tot, mien = {}, 0
    for hk in doc["hoc_ky"]:
        for d in hk["dong"]:
            if d.get("mien"):
                mien += d["tc"]
            elif d["ma"] not in tot or RT.CHU_4[d["chu"]] > RT.CHU_4[tot[d["ma"]]["chu"]]:
                tot[d["ma"]] = dict(d)
        dat = [d for d in tot.values() if d["chu"] != "F"]
        diem = [d for d in dat if not ct.get(d["ma"], {}).get("dieu_kien")]
        mau = sum(d["tc"] for d in diem)
        hk["tc_tich_luy"] = sum(d["tc"] for d in dat) + mien
        hk["dtbctl"] = round(sum(RT.CHU_4[d["chu"]] * d["tc"] for d in diem) / mau, 2) if mau else 0.0
    return doc


def _doc_hoan_hao(j, tich_luy=False):
    """Hồ sơ → tài liệu OCR đọc hoàn hảo (mức tài liệu, không cần Tesseract). tich_luy=True: có cả hai số tích lũy
    in sau mỗi học kỳ (C14); mặc định không có — các ca F (P17-2, P20-4) mô tả lúc OCR chưa đọc dòng tích lũy."""
    ct = O.ctdt()
    doc = {"hoc_ky": []}
    for i, ds in enumerate(RT.chia_hoc_ky(j, RT._ctdt())):
        dong = [{"ma": m, "tc": ct[m]["tc"], "thi": j["grades"][m]["thang10"] / 10, "thop": j["grades"][m]["thang10"] / 10,
                 "chu": j["grades"][m]["letter"], "mien": False,
                 "conf": {"ma": .99, "tc": .99, "thi": .99, "thop": .99, "chu": .99}} for m in ds if m != "CC004"]
        v = O._dtbchk(dong, ct)
        doc["hoc_ky"].append({"ten": f"HK{i + 1}", "dong": dong, "tong_dk": sum(d["tc"] for d in dong),
                              "dtbchk": round(v, 2) if v is not None else None})
    return _ghi_tich_luy(doc) if tich_luy else doc


def _dong(doc, ma):
    return next((hk, d) for hk in doc["hoc_ky"] for d in hk["dong"] if d["ma"] == ma)


def phan_F():
    print("F. LỖI OCR NHẤT QUÁN (P17-2, sau Tuần 17) — mức tài liệu")
    j = ho_so("sv_lvtn")
    kb = O.khai_bao_tu_json(j)
    # 1) không đọc được ĐTBCHK → học kỳ không kiểm chéo được → điểm trong học kỳ không chắc
    jf = copy.deepcopy(j)
    jf["grades"]["CT177"].update(thang10=30, letter="F", status="failed")        # sự thật: CT177 = F
    doc = _doc_hoan_hao(jf)
    hk, d = _dong(doc, "CT177")
    d.update(thi=4.5, thop=4.5, chu="D")                                          # OCR đọc nhất quán thành D
    hk["dtbchk"] = None                                                          # và không đọc được ĐTBCHK
    hs, extra, bc = O.sang_ho_so(doc, khai_bao=kb)
    v = O.ket_luan(hs, extra, bc)
    check(hk["ten"] + " (ĐTBCHK)" in bc["hoc_ky_lech"] and v != "TRUE",
          f"F1 CT177 F đọc thành D + ĐTBCHK không đọc được → học kỳ nghi ngờ, không TRUE sai ({v})")
    # 2) mã HP bắt buộc đọc nhất quán thành mã tự chọn lệch 1 ký tự, cùng TC (CT178 → CT478)
    doc = _doc_hoan_hao(j)
    _dong(doc, "CT178")[1]["ma"] = "CT478"
    hs, extra, bc = O.sang_ho_so(doc, khai_bao=kb)
    v = O.ket_luan(hs, extra, bc)
    check({"CT178", "CT478"} <= set(bc["khong_chac"]) and v != "FALSE",
          f"F2 CT178 (bắt buộc) đọc thành CT478 → cả hai không chắc, không FALSE sai ({v}, {bc['khong_chac']})")
    # 2b) đọc thành một mã BẮT BUỘC khác (CT178 → CT177): CT177 xuất hiện hai dòng
    doc = _doc_hoan_hao(j)
    _dong(doc, "CT178")[1]["ma"] = "CT177"
    hs, extra, bc = O.sang_ho_so(doc, khai_bao=kb)
    v = O.ket_luan(hs, extra, bc)
    check({"CT178", "CT177"} <= set(bc["khong_chac"]) and v != "FALSE",
          f"F4 CT178 đọc thành CT177 (bắt buộc, thành 2 dòng) → cả hai không chắc, không FALSE sai ({v}, {bc['khong_chac']})")
    # 3) không báo nhầm: bảng điểm đọc hoàn hảo vẫn kết luận được
    hs, extra, bc = O.sang_ho_so(_doc_hoan_hao(j), khai_bao=kb)
    check(not bc["khong_chac"] and O.ket_luan(hs, extra, bc) == "TRUE", "F3 bảng điểm đọc hoàn hảo → TRUE, không HP nào bị nghi")
    # P20-4 (Tuần 20): mất ĐTBCHK vẫn KHÔNG tin điểm (M2 không phân biệt được với F1), nhưng hỏi đúng MỘT con số
    # (ĐTBCHK in trên bảng điểm) thay vì cả học kỳ; sinh viên khai báo số in → khôi phục kiểm chéo
    doc = _doc_hoan_hao(j)
    hk, _ = _dong(doc, "CT177")
    so_in, hk["dtbchk"] = hk["dtbchk"], None
    hs, extra, bc = O.sang_ho_so(doc, khai_bao=kb)
    check(bc.get("can_hoi") == [f"dtbchk:{hk['ten']}"] and O.ket_luan(hs, extra, bc) != "TRUE",
          f"F5 mất ĐTBCHK → vẫn không kết luận, nhưng chỉ hỏi ĐTBCHK của {hk['ten']} ({bc.get('can_hoi')})")
    hs, extra, bc = O.sang_ho_so(doc, khai_bao={**kb, "dtbchk_khai_bao": {hk["ten"]: so_in}})
    v = O.ket_luan(hs, extra, bc)
    check(v == "TRUE" and not bc["khong_chac"] and not bc.get("can_hoi") and bc.get("dtbchk_khai_bao") == [hk["ten"]]
          and "dtbchk_khai_bao" not in hs,
          f"F6 sinh viên khai báo ĐTBCHK in ({so_in}) khớp số tính lại → tin điểm học kỳ → TRUE, ghi nguồn khai báo ({v})")
    jf = copy.deepcopy(j)
    jf["grades"]["CT177"].update(thang10=30, letter="F", status="failed")
    doc = _doc_hoan_hao(jf)
    hk, d = _dong(doc, "CT177")
    so_in_that = hk["dtbchk"]                                                   # số in thật (CT177 = F)
    d.update(thi=4.5, thop=4.5, chu="D")
    hk["dtbchk"] = None
    hs, extra, bc = O.sang_ho_so(doc, khai_bao={**kb, "dtbchk_khai_bao": {hk["ten"]: so_in_that}})
    v = O.ket_luan(hs, extra, bc)
    check(v != "TRUE" and hk["ten"] + " (ĐTBCHK)" in bc["hoc_ky_lech"],
          f"F7 như F1 + khai báo đúng số in thật → số tính từ điểm đọc nhầm LỆCH → vẫn không TRUE sai ({v})")
    hs, extra, bc = O.sang_ho_so(_doc_hoan_hao(j), khai_bao={**kb, "dtbchk_khai_bao": {"HK1": 0.5}})
    check(O.ket_luan(hs, extra, bc) == "TRUE" and not bc.get("dtbchk_khai_bao"),
          "F8 ĐTBCHK đã đọc được thì số in thắng khai báo (khai báo chỉ dùng khi OCR mất số)")
    # review P20-4: khai báo phải là SỐ HỮU HẠN trong [0, 4] — "NaN" làm |tính − NaN| > ε luôn False → tin học kỳ (F1 thành TRUE)
    jf = copy.deepcopy(j)
    jf["grades"]["CT177"].update(thang10=30, letter="F", status="failed")
    doc = _doc_hoan_hao(jf)
    hk, d = _dong(doc, "CT177")
    d.update(thi=4.5, thop=4.5, chu="D")
    hk["dtbchk"] = None
    kq = {}
    for x in ("nan", float("nan"), float("inf"), "abc", None, True, 5.0, -1):
        try:
            hs, extra, bc = O.sang_ho_so(doc, khai_bao={**kb, "dtbchk_khai_bao": {hk["ten"]: x}})
            kq[repr(x)] = (O.ket_luan(hs, extra, bc), bc.get("can_hoi"), bool(bc.get("khai_bao_loi")))
        except Exception as e:  # noqa: BLE001
            kq[repr(x)] = (type(e).__name__,)
    check(all(v[0] != "TRUE" and v[0] in ("UNKNOWN", "FALSE") and v[1] == [f"dtbchk:{hk['ten']}"] and v[2] for v in kq.values()),
          f"F9 khai báo không phải số hợp lệ (NaN, inf, chữ, None, True, ngoài [0,4]) → bỏ, báo lỗi, vẫn hỏi; không crash, không TRUE sai ({kq})")
    doc = _doc_hoan_hao(j)
    hk, _ = _dong(doc, "CT177")
    so_in, hk["dtbchk"] = hk["dtbchk"], None
    hs, extra, bc = O.sang_ho_so(doc, khai_bao={**kb, "dtbchk_khai_bao": {" " + hk["ten"] + " ": f"{so_in:.2f}".replace(".", ","), "HK99": 3.0}})
    check(O.ket_luan(hs, extra, bc) == "TRUE" and bc["dtbchk_khai_bao"] == [hk["ten"]]
          and any("HK99" in x for x in bc.get("khai_bao_loi", [])),
          f"F10 khai báo dạng '3,16' và tên học kỳ có khoảng trắng vẫn nhận; tên học kỳ không có trên bảng điểm → báo ({bc.get('khai_bao_loi')})")
    doc = _doc_hoan_hao(j)
    hk, d = _dong(doc, "CT177")
    hk["dtbchk"], hk["tong_dk"] = None, hk["tong_dk"] + 3                          # lệch tổng TC: không kiểm chéo ĐTBCHK
    hs, extra, bc = O.sang_ho_so(doc, khai_bao={**kb, "dtbchk_khai_bao": {hk["ten"]: so_in}})
    check(not bc["dtbchk_khai_bao"] and O.ket_luan(hs, extra, bc) != "TRUE",
          f"F11 học kỳ lệch tổng TC → khai báo ĐTBCHK KHÔNG được dùng và không ghi là nguồn ({bc['dtbchk_khai_bao']})")


def _do_phan_giai(doc, i):
    """0,5 × TC nhỏ nhất của HP không điều kiện trong học kỳ i / TC tính ĐTBCTL sau học kỳ i (tính độc lập)."""
    ct = RT._ctdt()
    tot = {d["ma"]: d for hk in doc["hoc_ky"][: i + 1] for d in hk["dong"]}
    mau = sum(d["tc"] for d in tot.values() if d["chu"] != "F" and not ct[d["ma"]].get("dieu_kien"))
    tc = [d["tc"] for d in doc["hoc_ky"][i]["dong"] if not ct[d["ma"]].get("dieu_kien")]
    return 0.5 * min(tc) / mau if tc and mau else None


def phan_G():
    print("G. C14 — KIỂM CHÉO BẰNG SỐ TÍCH LŨY IN SAU MỖI HỌC KỲ (Tuần 20) — mức tài liệu")
    j = ho_so("sv_lvtn")
    kb = O.khai_bao_tu_json(j)

    def chay(doc, ho=j, them=None):
        hs, extra, bc = O.sang_ho_so(doc, khai_bao={**O.khai_bao_tu_json(ho), **(them or {})})
        return hs, bc, O.ket_luan(hs, extra, bc)

    def khong_dong(doc, hk):      # sửa một học kỳ (sự thật) → tính lại tổng TC đăng ký + ĐTBCHK in
        hk["tong_dk"] = sum(d["tc"] for d in hk["dong"])
        hk["dtbchk"] = round(O._dtbchk(hk["dong"], O.ctdt()), 2)

    # G0 bảng điểm sạch có số tích lũy → không báo nhầm (TC tích lũy luôn được kiểm khi đọc được)
    hs, bc, v = chay(_doc_hoan_hao(j, tich_luy=True))
    check(v == "TRUE" and not bc["hoc_ky_lech"] and not bc["khong_chac"] and not bc.get("tich_luy_kiem_cheo"),
          f"G0 bảng điểm sạch có số tích lũy → TRUE, không học kỳ nào bị nghi ({bc['hoc_ky_lech']})")
    # G1 (= OCR-Noise M2) mất ĐTBCHK, số tích lũy đọc được và khớp → tin học kỳ, không cần hỏi
    doc = _doc_hoan_hao(j, tich_luy=True)
    hk, _ = _dong(doc, "CT177")
    hk["dtbchk"] = None
    hs, bc, v = chay(doc)
    check(v == "TRUE" and not bc["khong_chac"] and not bc.get("can_hoi") and bc.get("tich_luy_kiem_cheo") == [hk["ten"]],
          f"G1 mất ĐTBCHK {hk['ten']}, số tích lũy khớp → tin điểm học kỳ → TRUE, không hỏi, ghi nguồn "
          f"({v}, hỏi {bc.get('can_hoi')}, nguồn {bc.get('tich_luy_kiem_cheo')})")
    # G2 (= F1) sự thật CT177 = F, OCR đọc nhất quán thành D + mất ĐTBCHK; số tích lũy in theo sự thật → TC lệch
    jf = copy.deepcopy(j)
    jf["grades"]["CT177"].update(thang10=30, letter="F", status="failed")
    doc = _doc_hoan_hao(jf, tich_luy=True)
    hk, d = _dong(doc, "CT177")
    d.update(thi=4.5, thop=4.5, chu="D")
    hk["dtbchk"] = None
    hs, bc, v = chay(doc)
    check(v != "TRUE" and hk["ten"] + " (TC tích lũy)" in bc["hoc_ky_lech"] and not bc.get("tich_luy_kiem_cheo"),
          f"G2 CT177 F đọc thành D + mất ĐTBCHK → TC tích lũy lệch → không tin, không TRUE sai ({v}, {bc['hoc_ky_lech']})")
    # G3 đạt → đạt: CT177 (B) đọc nhất quán thành A + mất ĐTBCHK → TC tích lũy khớp nhưng ĐTBCTL lệch → không tin
    doc = _doc_hoan_hao(j, tich_luy=True)
    hk, d = _dong(doc, "CT177")
    d.update(thi=9.5, thop=9.5, chu="A")
    hk["dtbchk"] = None
    hs, bc, v = chay(doc)
    check("CT177" in bc["khong_chac"] and not bc.get("tich_luy_kiem_cheo") and bc.get("can_hoi") == [f"dtbchk:{hk['ten']}"],
          f"G3 CT177 B đọc thành A + mất ĐTBCHK → ĐTBCTL lệch → không tin, vẫn hỏi ĐTBCHK ({bc.get('can_hoi')})")
    # G4 độ phân giải không đủ: học kỳ cuối của sv_tltn (TC tính ĐTBCTL lớn) — lệch một bậc của HP 3 TC chỉ đổi
    #    ĐTBCTL ≈ 0,0107 < 0,011 (sai số làm tròn 0,005 + dung sai 0,006) → không được tin dù số tích lũy khớp
    jt = ho_so("sv_tltn")
    doc = _doc_hoan_hao(jt, tich_luy=True)
    hk, _ = _dong(doc, "CT501E")
    i = doc["hoc_ky"].index(hk)
    pg = _do_phan_giai(doc, i)
    hk["dtbchk"] = None
    hs, bc, v = chay(doc, ho=jt)
    check(pg < 0.011 and not bc.get("tich_luy_kiem_cheo") and bc.get("can_hoi") == [f"dtbchk:{hk['ten']}"] and v != "TRUE",
          f"G4 {hk['ten']} sv_tltn độ phân giải {pg:.4f} < 0,011 → không tin bằng số tích lũy, vẫn hỏi ĐTBCHK ({v})")
    # G5 học kỳ TRƯỚC chưa được tin (lệch tổng TC) → không cứu học kỳ sau bằng số tích lũy
    doc = _doc_hoan_hao(j, tich_luy=True)
    hk, _ = _dong(doc, "CT177")
    hk["dtbchk"] = None
    doc["hoc_ky"][0]["tong_dk"] += 3
    hs, bc, v = chay(doc)
    check("CT177" in bc["khong_chac"] and not bc.get("tich_luy_kiem_cheo"),
          f"G5 học kỳ trước lệch tổng TC → {hk['ten']} không được cứu bằng số tích lũy ({bc.get('tich_luy_kiem_cheo')})")
    # G6 HP GDQP: số tích lũy chỉ xác nhận đạt/không đạt, không xác nhận mức điểm (TB GDQP cần mức) → GDQP vẫn không
    #    chắc; HP điều kiện khác (chỉ cần đạt) được tin
    doc = _doc_hoan_hao(j, tich_luy=True)
    hk = doc["hoc_ky"][0]
    hk["dtbchk"] = None
    hs, bc, v = chay(doc)
    qp = sorted(d["ma"] for d in hk["dong"] if O.ctdt()[d["ma"]]["dieu_kien"] == "gdqp")
    check(bc.get("tich_luy_kiem_cheo") == [hk["ten"]] and sorted(bc["khong_chac"]) == qp and "TC100" in hs["grades"]
          and "XH023" in hs["grades"] and bc.get("can_hoi") == [f"dtbchk:{hk['ten']}"],
          f"G6 {hk['ten']} toàn HP điều kiện, mất ĐTBCHK → tin TC100/XH023, GDQP {qp} vẫn không chắc, hỏi ĐTBCHK "
          f"({bc['khong_chac']}, {bc.get('can_hoi')})")
    # G7 dòng miễn CC004 (10 TC): TC tích lũy in CÓ hoặc KHÔNG cộng 10 TC miễn đều nhận (chưa biết bảng điểm thật)
    kq = []
    for cong in (True, False):
        doc = _doc_hoan_hao(j, tich_luy=True)
        doc["hoc_ky"][1]["dong"].insert(0, {"ma": "CC004", "tc": 10, "thi": None, "thop": None, "chu": "M", "mien": True,
                                           "conf": {"ma": .99, "tc": .99}})
        doc["hoc_ky"][1]["tong_dk"] += 10
        _ghi_tich_luy(doc)
        if not cong:
            for hk in doc["hoc_ky"][1:]:
                hk["tc_tich_luy"] -= 10
        hk, _ = _dong(doc, "CT177")
        hk["dtbchk"] = None
        hs, bc, v = chay(doc)
        kq.append((bc.get("tich_luy_kiem_cheo"), [x for x in bc["hoc_ky_lech"] if "tích lũy" in x]))
    check(all(not a and not b for a, b in kq),
          f"G7 có dòng miễn CC004: TC tích lũy in có / không cộng 10 TC miễn → không báo lệch nhầm, nhưng KHÔNG cứu "
          f"{hk['ten']} khi chưa biết quy ước của trường (review C14) ({kq})")
    # G8 học lại: CT177 học lần đầu D ở học kỳ trước, học lại B ở học kỳ 4 → số tích lũy tính MỘT lần, điểm cao nhất
    doc = _doc_hoan_hao(j, tich_luy=True)
    hk, d = _dong(doc, "CT177")
    i = doc["hoc_ky"].index(hk)
    truoc = doc["hoc_ky"][i - 1]
    truoc["dong"].insert(0, dict(d, thi=4.5, thop=4.5, chu="D", conf=dict(d["conf"])))
    khong_dong(doc, truoc)
    _ghi_tich_luy(doc)
    hk["dtbchk"] = None
    hs, bc, v = chay(doc)
    check(v == "TRUE" and bc.get("tich_luy_kiem_cheo") == [hk["ten"]] and hs["grades"]["CT177"]["letter"] == "B"
          and not [x for x in bc["hoc_ky_lech"] if "tích lũy" in x],
          f"G8 CT177 D rồi học lại B → số tích lũy tính một lần theo điểm cao nhất → khớp, cứu {hk['ten']} ({v}, {bc['hoc_ky_lech']})")
    # G9 lỗ hổng cũ: GDTC (TC100) thật F, OCR đọc nhất quán thành D. ĐTBCHK KHÔNG tính GDTC (R-B08) nên vẫn khớp →
    #    trước C14 hệ thống nhận TC100 đạt → TRUE sai. TC tích lũy in theo sự thật lệch 1 TC → không tin
    jf = copy.deepcopy(j)
    jf["grades"]["TC100"].update(thang10=30, letter="F", status="failed")
    doc = _doc_hoan_hao(jf, tich_luy=True)
    hk, d = _dong(doc, "TC100")
    d.update(thi=4.5, thop=4.5, chu="D")
    hs, bc, v = chay(doc, ho=jf)
    that = O.ket_luan_tu_json(jf)
    check(v != "TRUE" and hk["ten"] + " (TC tích lũy)" in bc["hoc_ky_lech"] and "TC100" not in hs["grades"],
          f"G9 TC100 F đọc thành D (ĐTBCHK không tính GDTC nên vẫn khớp) → TC tích lũy lệch → không TRUE sai "
          f"({v}, sự thật {that})")
    # G10 không đọc được số tích lũy → như trước C14 (P20-4: hỏi ĐTBCHK)
    doc = _doc_hoan_hao(j, tich_luy=True)
    hk, _ = _dong(doc, "CT177")
    hk["dtbchk"] = hk["dtbctl"] = None
    hs, bc, v = chay(doc)
    check(v != "TRUE" and bc.get("can_hoi") == [f"dtbchk:{hk['ten']}"] and not bc.get("tich_luy_kiem_cheo"),
          f"G10 mất cả ĐTBCHK lẫn ĐTBCTL của {hk['ten']} → không cứu, hỏi ĐTBCHK ({bc.get('can_hoi')})")

    # review C14 (HIGH): "TC tích lũy in có HOẶC không cộng TC miễn" là độ chùng — lệch đạt ↔ F của HP có TC đúng bằng
    # tổng TC miễn bị che. Dòng miễn 3 TC ở HK1 (mã ngoài CTĐT ZZ999 — _tich_luy cộng mọi dòng "Miễn" bất kể mã).
    def them_mien(doc):
        doc["hoc_ky"][0]["dong"].insert(0, {"ma": "ZZ999", "tc": 3, "thi": None, "thop": None, "chu": "M", "mien": True,
                                           "conf": {"ma": .99, "tc": .99}})
        doc["hoc_ky"][0]["tong_dk"] += 3
        return _ghi_tich_luy(doc)
    # G12 nhánh cứu: số in KHÔNG cộng TC miễn; CT179 (B, 3 TC) đọc nhất quán thành F + mất ĐTBCHK → khớp qua phương án
    #      "có miễn" và ĐTBCTL vẫn khớp → trước khi sửa: cứu học kỳ → FALSE sai (sự thật TRUE)
    doc = them_mien(_doc_hoan_hao(j, tich_luy=True))
    for h in doc["hoc_ky"]:
        h["tc_tich_luy"] -= 3
    hk, d = _dong(doc, "CT179")
    d.update(thi=3.5, thop=3.5, chu="F")
    hk["dtbchk"] = None
    hs, bc, v = chay(doc)
    check(v != "FALSE" and not bc.get("tich_luy_kiem_cheo"),
          f"G12 có dòng miễn 3 TC, CT179 B đọc thành F + mất ĐTBCHK → không cứu bằng số tích lũy, không FALSE sai ({v})")
    # G13 nhánh luôn kiểm: số in CÓ cộng TC miễn; TC100 (GDTC, 3 TC) thật F đọc thành D, ĐTBCHK có (không tính GDTC)
    #      → khớp qua phương án "không miễn" → trước khi sửa: TRUE sai (như G9)
    doc = them_mien(_doc_hoan_hao(jf, tich_luy=True))
    hk, d = _dong(doc, "TC100")
    d.update(thi=4.5, thop=4.5, chu="D")
    hs, bc, v = chay(doc, ho=jf)
    check(v != "TRUE" and "TC100" not in hs["grades"],
          f"G13 có dòng miễn 3 TC, TC100 F đọc thành D → lỗi bị độ chùng che → TC100 không chắc, không TRUE sai ({v})")
    # G14 (review MEDIUM) bảng điểm thật in GDTC là TC025–027 (ngoài KB K49, Bài học CLAUDE.md): ĐTBCTL của trường bỏ GDTC
    #      → số tính lại cũng phải bỏ, nếu không mọi học kỳ sau đều lệch ĐTBCTL và không cứu được
    doc = _doc_hoan_hao(j, tich_luy=True)                     # số in tính khi dòng còn là TC100 (GDTC)
    _dong(doc, "TC100")[1]["ma"] = "TC025"
    hk, _ = _dong(doc, "CT177")
    hk["dtbchk"] = None
    hs, bc, v = chay(doc)
    check(bc.get("tich_luy_kiem_cheo") == [hk["ten"]] and not [x for x in bc["hoc_ky_lech"] if "tích lũy" in x],
          f"G14 GDTC in mã TC025 (ngoài CTĐT) → vẫn coi là GDTC khi tính ĐTBCTL → cứu được {hk['ten']} ({bc['hoc_ky_lech']})")
    # G15 (review lượt 2, MEDIUM) độ chùng thứ hai: dòng KHÔNG đọc được điểm cũng làm TC tích lũy tính lại có hai giá trị.
    #      Dòng ngoài CTĐT XX999 (3 TC, thật đạt) không đọc được điểm ở HK1 + TC100 (3 TC) thật F đọc thành D: số in
    #      khớp qua nhánh "XX999 rớt" ở mọi học kỳ, ĐTBCHK bỏ cả hai dòng → trước khi sửa: TRUE sai
    doc = _doc_hoan_hao(jf)
    hk1 = doc["hoc_ky"][0]
    hk1["dong"].append({"ma": "XX999", "tc": 3, "thi": 7.0, "thop": 7.0, "chu": "B", "mien": False,
                        "conf": {"ma": .99, "tc": .99, "thop": .99, "chu": .99}})
    hk1["tong_dk"] += 3
    _ghi_tich_luy(doc)
    hk1["dong"][-1].update(thi=None, thop=None, chu=None)
    _dong(doc, "TC100")[1].update(thi=4.5, thop=4.5, chu="D")
    hs, bc, v = chay(doc, ho=jf)
    check(v != "TRUE" and "TC100" not in hs["grades"],
          f"G15 dòng không đọc được điểm cùng TC với TC100 (F đọc thành D) → lỗi bị che → TC100 không chắc, không TRUE sai ({v})")


def phan_G_anh():
    print("G'. C14 — OCR ĐỌC DÒNG TÍCH LŨY TRÊN ẢNH TỔNG HỢP")
    for ten in ("sv_lvtn", "sv_mien_ielts"):
        j = ho_so(ten)
        doc = O.doc_bang_diem(RT.render(j, bien_the="sach"))
        tl = [hk.get("tc_tich_luy") for hk in doc["hoc_ky"]]
        dtb = [hk.get("dtbctl") for hk in doc["hoc_ky"]]
        hs, extra, bc = O.sang_ho_so(doc, khai_bao=O.khai_bao_tu_json(j))
        lech = [x for x in bc["hoc_ky_lech"] if "tích lũy" in x]
        check(None not in tl and None not in dtb and tl == sorted(tl) and not lech,
              f"G11 {ten}/sach: đọc đủ TC tích lũy {tl} (không giảm) + ĐTBCTL mọi học kỳ, khớp số tính lại ({lech})")


def phan_H():
    import prototype
    for extra, claim in [('', 'tot_nghiep'), ('{audit_choice}.', 'audit_choice'), ('', 'audit_absent'), (':-.', 'tot_nghiep')]:
        old = prototype.solve_verdict(claim, extra)[0]
        check(prototype.solve_truth(claim, extra) == old, f'H verdict-only tương đương liệt kê: {claim} / {old}')
    # 2^25 thế giới độc lập: vẫn chỉ cần tìm một thế giới có claim và một thế giới không có claim.
    check(prototype.solve_truth('audit_choice(1)', '{audit_choice(1..25)}.') == 'UNKNOWN',
          'H 33 triệu thế giới tiềm năng → UNKNOWN mà không liệt kê/lưu toàn bộ')


def main():
    nhanh = "--nhanh" in sys.argv
    try:   # số liệu OCR phụ thuộc font + phiên bản Tesseract → ghi lại để chỉ so trên CÙNG môi trường
        tv = O.pytesseract.get_tesseract_version()
    except Exception as e:  # noqa: BLE001
        tv = f"không chạy được ({type(e).__name__})"
    print(f"Môi trường: font={RT.font()} · tesseract={O.pytesseract.pytesseract.tesseract_cmd} {tv}\n")
    phan_A()
    phan_H()
    phan_B(nhanh)
    phan_C()
    phan_E()
    phan_F()
    phan_G()
    phan_G_anh()
    if not nhanh:
        phan_D()
    print("\nKẾT LUẬN:", "ĐẠT — fact OCR có confidence, kiểm chéo chặn fact sai, không sinh kết luận sai" if ok_all else "CHƯA ĐẠT")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
