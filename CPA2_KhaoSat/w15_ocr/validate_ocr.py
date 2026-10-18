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
    return json.loads((STUDENTS / f"{ten}.json").read_text(encoding="utf-8"))


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


def _doc_hoan_hao(j):
    """Hồ sơ → tài liệu OCR đọc hoàn hảo (mức tài liệu, không cần Tesseract)."""
    ct = O.ctdt()
    doc = {"hoc_ky": []}
    for i, ds in enumerate(RT.chia_hoc_ky(j, RT._ctdt())):
        dong = [{"ma": m, "tc": ct[m]["tc"], "thi": j["grades"][m]["thang10"] / 10, "thop": j["grades"][m]["thang10"] / 10,
                 "chu": j["grades"][m]["letter"], "mien": False,
                 "conf": {"ma": .99, "tc": .99, "thi": .99, "thop": .99, "chu": .99}} for m in ds if m != "CC004"]
        v = O._dtbchk(dong, ct)
        doc["hoc_ky"].append({"ten": f"HK{i + 1}", "dong": dong, "tong_dk": sum(d["tc"] for d in dong),
                              "dtbchk": round(v, 2) if v is not None else None})
    return doc


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


def main():
    nhanh = "--nhanh" in sys.argv
    phan_A()
    phan_B(nhanh)
    phan_C()
    phan_E()
    phan_F()
    if not nhanh:
        phan_D()
    print("\nKẾT LUẬN:", "ĐẠT — fact OCR có confidence, kiểm chéo chặn fact sai, không sinh kết luận sai" if ok_all else "CHƯA ĐẠT")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
