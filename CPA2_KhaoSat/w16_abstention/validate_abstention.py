"""
validate_abstention.py — kiểm chứng Abstention engine v1 Tuần 16 (CPA2)

Tiêu chí (Kế hoạch 24 tuần, dòng 16): "Không đoán khi thiếu dữ liệu".
  A. Dữ kiện ngoài thiếu → UNKNOWN (không phải FALSE/TRUE do giả định thế giới đóng)
  B. missing evidence: chỉ nêu dữ kiện QUYẾT ĐỊNH, kèm kết luận theo từng giá trị
  C. Chính sách từ chối: UNKNOWN thì không kết luận, kể cả khi đa số thế giới nghiêng một phía
  D. Tích hợp Prototype (Tuần 12) + 6 hồ sơ giả lập giữ nguyên kết luận

Chạy:  python validate_abstention.py
"""
import sys, json, copy, tempfile
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
STUDENTS = ROOT / "w7_student_facts" / "students"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "w12_integration"))
import abstention as A
import prototype

errors = []
OK, FAIL = "  [OK]  ", "  [FAIL]"


def check(cond, msg, note=""):
    print((OK if cond else FAIL) + " " + msg)
    if note:
        print("          ↳ " + note)
    if not cond:
        errors.append(msg)
    return cond


def hs(ten, **sua):
    """Hồ sơ giả lập + chỉnh sửa. Giá trị A.BO = xoá hẳn trường."""
    j = json.loads((STUDENTS / f"{ten}.json").read_text(encoding="utf-8"))
    for k, v in sua.items():
        if v is A.BO:
            j.pop(k, None)
        else:
            j[k] = v
    return j


def bien(res, ten):
    return next((b for b in res["can_bo_sung"] if b["bien"] == ten), None)


# =============================================================
def test_open_world():
    print("\nA. DỮ KIỆN NGOÀI THIẾU → UNKNOWN (P15-2)")
    r = A.tra_loi("tot_nghiep", hs("sv_lvtn"))
    check(r["verdict"] == "TRUE", f"A1 sv_lvtn khai báo đủ → TRUE (got {r['verdict']})")
    r = A.tra_loi("tot_nghiep", hs("sv_lvtn", xac_nhan_ky_luat_sach=None))
    check(r["verdict"] == "UNKNOWN", f"A2 kỷ luật = null → UNKNOWN (got {r['verdict']})",
          "HỒI QUY: luật Tuần 10 cho FALSE (thế giới đóng)")
    r = A.tra_loi("tot_nghiep", hs("sv_lvtn", xac_nhan_ky_luat_sach=A.BO))
    check(r["verdict"] == "UNKNOWN", f"A3 thiếu hẳn trường kỷ luật → UNKNOWN (got {r['verdict']})")
    r = A.tra_loi("tot_nghiep", hs("sv_lvtn", xac_nhan_ky_luat_sach=False))
    check(r["verdict"] == "FALSE", f"A4 kỷ luật = false (đã khai báo) → FALSE (got {r['verdict']})")
    r = A.tra_loi("tot_nghiep", hs("sv_tron_ngoai_ngu", xac_nhan_ky_luat_sach=None))
    check(r["verdict"] == "FALSE", f"A5 trộn AV/PV + kỷ luật null → vẫn FALSE (got {r['verdict']})",
          "dữ kiện mở không cứu được hồ sơ đã thiếu điều kiện học vụ")
    r = A.tra_loi("thieu_dk(thoi_gian)", hs("sv_lvtn", da_hoc_nam2=A.BO))
    check(r["verdict"] == "UNKNOWN", f"A6 thiếu da_hoc_nam2 → thieu_dk(thoi_gian) UNKNOWN (got {r['verdict']})",
          "HỒI QUY: luật Tuần 10 cho FALSE — coi như chưa quá hạn khi không biết đã học bao lâu")
    r = A.tra_loi("thieu_dk(thoi_gian)", hs("sv_lvtn", da_hoc_nam2=9))
    check(r["verdict"] == "FALSE", f"A7 da_hoc_nam2 = 9 (trần 18) → thieu_dk(thoi_gian) FALSE (got {r['verdict']})")
    r = A.tra_loi("thieu_dk(thoi_gian)", hs("sv_lvtn", da_hoc_nam2=20))
    check(r["verdict"] == "TRUE", f"A8 da_hoc_nam2 = 20 (trần 18) → thieu_dk(thoi_gian) TRUE (got {r['verdict']})")
    r = A.tra_loi("bi_xoa_ten", hs("sv_tron_ngoai_ngu", da_hoc_nam2=A.BO))
    check(r["verdict"] == "UNKNOWN", f"A9 chưa đủ ĐK + thiếu da_hoc_nam2 → bi_xoa_ten UNKNOWN (got {r['verdict']})",
          "HỒI QUY: luật cũ cho FALSE (R-F09/R-D08 — xoá tên khi quá hạn mà chưa đủ ĐK)")


def test_missing_evidence():
    print("\nB. MISSING EVIDENCE — chỉ nêu dữ kiện quyết định")
    r = A.tra_loi("tot_nghiep", hs("sv_lvtn", xac_nhan_ky_luat_sach=None))
    b = bien(r, "xac_nhan_ky_luat_sach")
    check(b is not None and b["quyet_dinh"], "B1 kỷ luật null → hỏi xac_nhan_ky_luat_sach (quyết định)")
    check(b is not None and b["theo_gia_tri"] == {"true": "TRUE", "false": "FALSE"},
          f"B2 true → TRUE, false → FALSE ({b and b['theo_gia_tri']})")
    check(b is not None and b["nguon"].startswith("R-F03") and b["hoi"],
          "B3 câu hỏi có nội dung + nguồn R-F03")
    r = A.tra_loi("tot_nghiep", hs("sv_tron_ngoai_ngu", xac_nhan_ky_luat_sach=None))
    check(r["can_bo_sung"] == [], f"B4 đã FALSE chắc chắn → không hỏi gì thêm ({[x['bien'] for x in r['can_bo_sung']]})")
    # CT550E không chắc (80 hoặc 30) quyết định; CT478 không chắc nhưng 80 hay 90 đều đạt → không hỏi
    j = hs("sv_lvtn")
    j["grades"].pop("CT550E")
    r = A.tra_loi("tot_nghiep", j, them='1 { g10("CT550E",80); g10("CT550E",30) } 1.\n'
                                        '1 { g10("CT478",80); g10("CT478",90) } 1.')
    ten = [x["bien"] for x in r["can_bo_sung"]]
    check(r["verdict"] == "UNKNOWN" and ten == ['g10("CT550E")'],
          f"B5 chỉ hỏi CT550E, không hỏi CT478 (không quyết định) ({r['verdict']}, {ten})")
    b = bien(r, 'g10("CT550E")')
    check(b is not None and b["theo_gia_tri"] == {"80": "TRUE", "30": "FALSE"},
          f"B6 CT550E: 80 → TRUE, 30 → FALSE ({b and b['theo_gia_tri']})")
    # Hai biến mở: không biến nào một mình đủ kết luận TRUE
    j = hs("sv_lvtn", xac_nhan_ky_luat_sach=None)
    j["grades"].pop("CT550E")
    r = A.tra_loi("tot_nghiep", j, them='1 { g10("CT550E",80); g10("CT550E",30) } 1.')
    ten = sorted(x["bien"] for x in r["can_bo_sung"])
    check(ten == sorted(['g10("CT550E")', "xac_nhan_ky_luat_sach"]), f"B7 hai biến mở đều được hỏi ({ten})")
    b = bien(r, "xac_nhan_ky_luat_sach")
    check(b is not None and b["theo_gia_tri"] == {"true": "UNKNOWN", "false": "FALSE"},
          f"B8 kỷ luật true → vẫn UNKNOWN (còn CT550E) ({b and b['theo_gia_tri']})")
    # Điểm OCR không chắc theo F/D/A (Tuần 15): D kéo ĐTBCTL xuống → không đơn điệu
    j = hs("sv_lvtn")
    j["grades"].pop("CT550E")
    r = A.tra_loi("tot_nghiep", j, them='1 { g10("CT550E",0); g10("CT550E",40); g10("CT550E",100) } 1.')
    b = bien(r, 'g10("CT550E")')
    check(b is not None and set(b["theo_gia_tri"]) == {"0", "40", "100"} and b["theo_gia_tri"]["0"] == "FALSE",
          f"B9 F/D/A: liệt kê đủ 3 giá trị, F → FALSE ({b and b['theo_gia_tri']})")
    # Quyết định miễn chưa rõ (QD-11): đủ ĐK xin miễn XH025 nhưng chưa biết đã có QĐ hay chưa
    j = hs("sv_mien_ielts")
    j["exemptions"] = [e for e in j["exemptions"] if e["ma_hp"] != "XH025"]
    r = A.tra_loi("tot_nghiep", j, them='{ duoc_mien("XH025") }.')
    b = bien(r, 'duoc_mien("XH025")')
    check(r["verdict"] == "UNKNOWN" and b is not None and b["theo_gia_tri"] == {"true": "TRUE", "false": "FALSE"}
          and b["nguon"].startswith("R-M16"),
          f"B10 QĐ miễn XH025 chưa rõ → hỏi duoc_mien(\"XH025\") ({r['verdict']}, {b and b['theo_gia_tri']})")


def test_policy():
    print("\nC. CHÍNH SÁCH TỪ CHỐI KẾT LUẬN")
    r = A.tra_loi("tot_nghiep", hs("sv_lvtn", xac_nhan_ky_luat_sach=None))
    check(r["ket_luan"] is None, "C1 UNKNOWN → ket_luan = None (không kết luận)")
    check("xac_nhan_ky_luat_sach" not in r["giai_thich"] and "kỷ luật" in r["giai_thich"],
          "C2 giải thích hỏi bằng tiếng Việt, không lộ tên atom")
    # 3 thế giới đạt, 1 thế giới rớt: đa số TRUE nhưng vẫn UNKNOWN
    j = hs("sv_lvtn")
    j["grades"].pop("CT550E")
    r = A.tra_loi("tot_nghiep", j, them='1 { g10("CT550E",80); g10("CT550E",90); g10("CT550E",100); g10("CT550E",30) } 1.')
    check(r["verdict"] == "UNKNOWN" and r["ket_luan"] is None,
          f"C3 đa số 3/4 thế giới TRUE → vẫn UNKNOWN, không kết luận ({r['verdict']})")
    r = A.tra_loi("tot_nghiep", hs("sv_lvtn"), them=':- tot_nghiep. :- not tot_nghiep.')
    check(r["verdict"] == "MAU_THUAN" and r["ket_luan"] is None,
          f"C4 KB mâu thuẫn (vô nghiệm) → MAU_THUAN, không kết luận ({r['verdict']})")
    r = A.tra_loi("tot_nghiep", hs("sv_lvtn"))
    check(r["ket_luan"] is True and r["can_bo_sung"] == [], "C5 TRUE chắc chắn → ket_luan True, không hỏi thêm")


def test_integration():
    print("\nD. TÍCH HỢP PROTOTYPE (Tuần 12) + 6 HỒ SƠ")
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "sv_lvtn_null.json"
        p.write_text(json.dumps(hs("sv_lvtn", xac_nhan_ky_luat_sach=None), ensure_ascii=False), encoding="utf-8")
        res = prototype.answer("em đủ điều kiện tốt nghiệp chưa?", str(p))
    check(res["verdict"] == "UNKNOWN", f"D1 prototype: kỷ luật null → UNKNOWN (got {res['verdict']})")
    check("xac_nhan_ky_luat_sach" in res["missing_facts"], f"D2 missing_facts = {res['missing_facts']}")
    mong = {"sv_5hp": "TRUE", "sv_du_hp": "FALSE", "sv_lvtn": "TRUE", "sv_mien_ielts": "TRUE",
            "sv_tltn": "TRUE", "sv_tron_ngoai_ngu": "FALSE"}
    thuc = {k: A.tra_loi("tot_nghiep", hs(k))["verdict"] for k in mong}
    check(thuc == mong, "D3 6 hồ sơ giả lập giữ nguyên kết luận Tuần 12", "" if thuc == mong else f"lệch: {thuc}")
    thuc = {k: A.tra_loi("thieu_dk(thoi_gian)", hs(k))["verdict"] for k in mong}
    check(all(v == "FALSE" for v in thuc.values()), f"D4 6 hồ sơ đã khai báo da_hoc_nam2 → thời gian xác định ({thuc})")


def main():
    print("=" * 78)
    print("VALIDATE ABSTENTION ENGINE v1 — Tuần 16 (CPA2)")
    print("Thiếu dữ kiện → UNKNOWN + danh sách dữ kiện quyết định; không đoán")
    print("=" * 78)
    test_open_world()
    test_missing_evidence()
    test_policy()
    test_integration()
    print("\n" + "=" * 78)
    if errors:
        print(f"KẾT LUẬN: CÓ {len(errors)} LỖI")
        for e in errors:
            print("  ·", e)
        return 1
    print("KẾT LUẬN: ĐẠT — Abstention engine không đoán khi thiếu dữ liệu")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
