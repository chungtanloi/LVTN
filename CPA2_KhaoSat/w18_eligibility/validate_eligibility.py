"""
validate_eligibility.py — kiểm chứng Eligibility module v1 Tuần 18 (CPA2)

Tiêu chí (Kế hoạch 24 tuần, dòng 18): "Eligible / Not Eligible / Unknown" cho luận văn, niên luận, học phần thay thế.
Gold viết tay TRƯỚC khi cài đặt, theo:
  CTĐT CNTT K49 (tr.3–4): CT550E LVTN & CT501E TLTN ≥ 120 TC · CT466E Niên luận ≥ 80 TC · CT518E Thực tập ≥ 125 TC ·
                          CT271E Niên luận cơ sở: tiên quyết CT174, CT176                       (R-A03, QĐ3266 Đ7 k4)
  QĐ3266 Đ31 (tr.19): nhận đề tài LVTN/TLTN cần điều kiện DO ĐƠN VỊ ĐÀO TẠO quy định (R-F04). QD-12 (xác nhận ngoài
                      văn bản, Loi 18/10/2026): điều kiện đó CHỈ là ngưỡng TC của CTĐT. `hinh_thuc_cuoi_khoa` chỉ dùng
                      khi có khai báo (đã công bố hình thức khác → NOT); k3: SV có thể chọn tích lũy TC thay LVTN/TLTN;
                      F của LVTN/TLTN → làm lại hoặc học phần thay thế
  QĐ5339 Đ3 k9: ML009→ML014, ML010→ML016+ML018 (một → nhiều)

Chạy:  python validate_eligibility.py
"""
import sys, json, tempfile
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
STUDENTS = ROOT / "w7_student_facts" / "students"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "w12_integration"))

errors = []
OK, FAIL = "  [OK]  ", "  [FAIL]"


def check(cond, msg, note=""):
    print((OK if cond else FAIL) + " " + msg)
    if note:
        print("          ↳ " + note)
    if not cond:
        errors.append(msg)
    return cond


CT = {h["ma"]: h for h in json.loads((ROOT / "w6_curriculum" / "curriculum_cntt_k49.json").read_text(encoding="utf-8"))["hoc_phan"]}
CHU = [(90, "A"), (80, "B+"), (70, "B"), (65, "C+"), (55, "C"), (50, "D+"), (40, "D"), (0, "F")]


def bg(ma, t10, tc=None):
    return {"code": ma, "credits": tc or CT[ma]["tin_chi"], "thang10": t10,
            "letter": next(c for lo, c in CHU if t10 >= lo), "status": "passed" if t10 >= 40 else "failed"}


def hs(ten="sv_lvtn", xoa=(), diem=None, **truong):
    j = json.loads((STUDENTS / f"{ten}.json").read_text(encoding="utf-8"))
    for m in xoa:
        j["grades"].pop(m)
    for m, t in (diem or {}).items():
        j["grades"][m] = bg(m, t, tc=2 if m not in CT else None)
    for k, v in truong.items():
        j[k] = v
    return j


def ho_so_tc(muc_tieu, bo):
    """sv_lvtn bỏ `bo`, rồi bỏ thêm HP (không phải điều kiện) cho tới đúng `muc_tieu` TC — tổng con (subset-sum)."""
    j = hs(xoa=bo)
    con = sum(g["credits"] for g in j["grades"].values())
    du = con - muc_tieu
    ung = [m for m in j["grades"] if not CT.get(m, {}).get("dieu_kien") and m not in ("CT174", "CT176")]
    kq = {0: []}
    for m in ung:
        for s, ds in list(kq.items()):
            t = s + j["grades"][m]["credits"]
            if t <= du and t not in kq:
                kq[t] = ds + [m]
    assert du in kq, (muc_tieu, du)
    for m in kq[du]:
        j["grades"].pop(m)
    assert sum(g["credits"] for g in j["grades"].values()) == muc_tieu
    return j


def main():
    print("=" * 78)
    print("VALIDATE ELIGIBILITY MODULE v1 — Tuần 18 (CPA2)")
    print("=" * 78)
    import eligibility as E

    def xet(j, dt, them=""):
        return E.xet(j, dt, them)

    print("\nA. LUẬN VĂN / TIỂU LUẬN (CTĐT ≥ 120 TC — Đ31 R-F04 + QD-12)")
    r = xet(hs(xoa=["CT550E"]), "lvtn")
    check(r["ket_qua"] == "ELIGIBLE" and r["can_bo_sung"] == [],
          f"A1 146 TC, không khai báo hình thức → ELIGIBLE, không hỏi thêm ({r['ket_qua']}, {[b['bien'] for b in r['can_bo_sung']]})",
          "HỒI QUY QD-12: bản trước (chưa có xác nhận) cho UNKNOWN + hỏi đơn vị đã công bố chưa")
    r = xet(hs(xoa=["CT550E"], hinh_thuc_cuoi_khoa="lvtn"), "lvtn")
    check(r["ket_qua"] == "ELIGIBLE", f"A2 146 TC + đơn vị công bố hình thức LVTN → ELIGIBLE ({r['ket_qua']})")
    check(any(s["rule_id"] == "r_f04" for s in r["chung_chi"]) and any(s["rule_id"] == "r_a03" for s in r["chung_chi"]),
          f"A3 chứng chỉ trích cả R-A03 (tiên quyết TC) và R-F04 (đơn vị xét) ({sorted({s['rule_id'] for s in r['chung_chi']})})")
    r = xet(hs(xoa=["CT550E"], hinh_thuc_cuoi_khoa="tltn"), "lvtn")
    check(r["ket_qua"] == "NOT_ELIGIBLE", f"A4 đơn vị công bố hình thức TLTN → LVTN NOT_ELIGIBLE ({r['ket_qua']})")
    r = xet(hs(xoa=["CT550E"], hinh_thuc_cuoi_khoa="tltn"), "tltn")
    check(r["ket_qua"] == "ELIGIBLE", f"A5 … → TLTN ELIGIBLE ({r['ket_qua']})")
    r = xet(ho_so_tc(120, ["CT550E"]) | {"hinh_thuc_cuoi_khoa": "lvtn"}, "lvtn")
    check(r["ket_qua"] == "ELIGIBLE", f"A6 đúng 120 TC + công bố LVTN → ELIGIBLE ({r['ket_qua']})")
    r = xet(ho_so_tc(119, ["CT550E"]) | {"hinh_thuc_cuoi_khoa": "lvtn"}, "lvtn")
    check(r["ket_qua"] == "NOT_ELIGIBLE" and 'thieu_tc("CT550E",1)' in r["ly_do"],
          f"A7 119 TC → NOT_ELIGIBLE, lý do thiếu 1 TC ({r['ket_qua']}, {r['ly_do']})")
    r = xet(ho_so_tc(119, ["CT550E"]), "lvtn")
    check(r["ket_qua"] == "NOT_ELIGIBLE", f"A8 119 TC, không khai báo hình thức → NOT_ELIGIBLE ({r['ket_qua']})")
    r = xet(hs(), "lvtn")
    check(r["ket_qua"] == "DA_HOAN_THANH", f"A9 LVTN đã đạt → DA_HOAN_THANH, không báo Eligible ({r['ket_qua']})")
    r = xet(hs(diem={"CT550E": 30}, hinh_thuc_cuoi_khoa="lvtn"), "lvtn")
    check(r["ket_qua"] == "ELIGIBLE", f"A10 LVTN bị F, đơn vị cho làm lại → ELIGIBLE (Đ31: đăng ký làm lại) ({r['ket_qua']})")

    print("\nB. TÍCH LŨY TC THAY LVTN/TLTN (Đ31 k3 — SV tự chọn)")
    r = xet(hs(xoa=["CT550E"]), "tich_luy_tc")
    check(r["ket_qua"] == "ELIGIBLE", f"B1 chưa làm LVTN → được chọn tích lũy TC, không cần đơn vị công bố ({r['ket_qua']})")
    r = xet(hs(diem={"CT550E": 30}), "tich_luy_tc")
    check(r["ket_qua"] == "ELIGIBLE", f"B2 LVTN bị F → được học HP thay thế (Đ31) ({r['ket_qua']})")
    r = xet(hs(), "tich_luy_tc")
    check(r["ket_qua"] == "DA_HOAN_THANH", f"B3 nhóm tốt nghiệp đã đủ → DA_HOAN_THANH ({r['ket_qua']})")

    print("\nC. NIÊN LUẬN / THỰC TẬP (ngưỡng TC của CTĐT)")
    r = xet(ho_so_tc(80, ["CT466E", "CT518E", "CT550E"]), "nien_luan")
    check(r["ket_qua"] == "ELIGIBLE", f"C1 đúng 80 TC → Niên luận CT466E ELIGIBLE ({r['ket_qua']})")
    r = xet(ho_so_tc(79, ["CT466E", "CT518E", "CT550E"]), "nien_luan")
    check(r["ket_qua"] == "NOT_ELIGIBLE" and 'thieu_tc("CT466E",1)' in r["ly_do"],
          f"C2 79 TC → NOT_ELIGIBLE, thiếu 1 TC ({r['ket_qua']}, {r['ly_do']})")
    r = xet(ho_so_tc(125, ["CT518E", "CT550E"]), "thuc_tap")
    check(r["ket_qua"] == "ELIGIBLE", f"C3 đúng 125 TC → Thực tập CT518E ELIGIBLE ({r['ket_qua']})")
    r = xet(ho_so_tc(124, ["CT518E", "CT550E"]), "thuc_tap")
    check(r["ket_qua"] == "NOT_ELIGIBLE", f"C4 124 TC → Thực tập NOT_ELIGIBLE ({r['ket_qua']})")

    print("\nD. NIÊN LUẬN CƠ SỞ (tiên quyết CT174, CT176)")
    r = xet(hs(xoa=["CT271E"]), "nien_luan_co_so")
    check(r["ket_qua"] == "ELIGIBLE", f"D1 đã đạt CT174, CT176 → ELIGIBLE ({r['ket_qua']})")
    r = xet(hs(xoa=["CT271E", "CT176"]), "nien_luan_co_so")
    check(r["ket_qua"] == "NOT_ELIGIBLE" and 'thieu_tien_quyet("CT271E","CT176")' in r["ly_do"],
          f"D2 chưa học CT176 → NOT_ELIGIBLE, nêu tiên quyết thiếu ({r['ket_qua']}, {r['ly_do']})")
    r = xet(hs(xoa=["CT271E"], diem={"CT176": 30}), "nien_luan_co_so")
    check(r["ket_qua"] == "NOT_ELIGIBLE", f"D3 CT176 bị F (tiên quyết = đã tích lũy) → NOT_ELIGIBLE ({r['ket_qua']})")
    j = hs(xoa=["CT271E", "CT176"])
    r = xet(j, "nien_luan_co_so", '1 { g10("CT176",80); g10("CT176",30) } 1.')
    check(r["ket_qua"] == "UNKNOWN" and 'g10("CT176")' in [b["bien"] for b in r["can_bo_sung"]],
          f"D4 điểm CT176 chưa rõ (8,0 / 3,0) → UNKNOWN + hỏi CT176 ({r['ket_qua']})")
    j = hs(xoa=["CT271E"])
    j["grades"]["CT174"].update(thang10=80, letter="F", status="failed")
    r = xet(j, "nien_luan_co_so")
    check(r["ket_qua"] == "UNKNOWN" and r["mau_thuan"], f"D5 bản ghi CT174 mâu thuẫn (8,0 ghi F) → UNKNOWN ({r['ket_qua']})")

    print("\nE. HỌC PHẦN THAY THẾ (QĐ5339 Đ3 k9)")
    r = xet(hs(xoa=["ML014"], diem={"ML009": 80}), "thay_the:ML014")
    check(r["ket_qua"] == "ELIGIBLE", f"E1 đạt ML009 → được công nhận thay ML014 ({r['ket_qua']})")
    r = xet(hs(xoa=["ML014"], diem={"ML009": 30}), "thay_the:ML014")
    check(r["ket_qua"] == "NOT_ELIGIBLE", f"E2 ML009 bị F → không thay được ML014 ({r['ket_qua']})")
    r = xet(hs(xoa=["ML016", "ML018"], diem={"ML010": 75}), "thay_the:ML018")
    check(r["ket_qua"] == "ELIGIBLE", f"E3 ML010 → cả ML016 và ML018 (một → nhiều): ML018 ELIGIBLE ({r['ket_qua']})")

    print("\nF. TÍCH HỢP PROTOTYPE (Tuần 12): câu hỏi 'đủ điều kiện làm luận văn'")
    import prototype
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "sv.json"
        p.write_text(json.dumps(hs(xoa=["CT550E"]), ensure_ascii=False), encoding="utf-8")
        res = prototype.answer("em đủ điều kiện làm luận văn chưa", str(p))
        check(res["verdict"] == "TRUE", f"F1 146 TC → TRUE ({res['verdict']})",
              "HỒI QUY P18-1: prototype ánh xạ sang claim 'du_dk_tc' không đối số → luôn FALSE")
        p.write_text(json.dumps(hs(xoa=["CT550E"], hinh_thuc_cuoi_khoa="lvtn"), ensure_ascii=False), encoding="utf-8")
        res = prototype.answer("em đủ điều kiện làm luận văn chưa", str(p))
        check(res["verdict"] == "TRUE", f"F2 … + đơn vị công bố LVTN → TRUE ({res['verdict']})")

    print("\nH. HỒI QUY REVIEW")
    r = xet(hs(xoa=["CT550E"], diem={"CT501E": 75}, hinh_thuc_cuoi_khoa="lvtn"), "lvtn")
    check(r["ket_qua"] == "DA_HOAN_THANH", f"H1 đã đạt TLTN (hình thức khác, Đ31 'một trong ba') → LVTN DA_HOAN_THANH ({r['ket_qua']})")
    r = xet(hs(), "tltn")
    check(r["ket_qua"] == "DA_HOAN_THANH", f"H2 đã đạt LVTN → hỏi TLTN: DA_HOAN_THANH, không hỏi đơn vị ({r['ket_qua']})")
    r = xet(hs(diem={"ML009": 80}), "thay_the:ML014")
    check(r["ket_qua"] == "DA_HOAN_THANH", f"H3 ML014 đã đạt bằng điểm của chính nó → DA_HOAN_THANH ({r['ket_qua']})")
    try:
        xet(hs(), "thay_the:XX999")
        loi = False
    except ValueError:
        loi = True
    check(loi, "H4 mã HP thay thế không có trong CTĐT → báo lỗi, không im lặng NOT_ELIGIBLE")
    r = xet(hs(xoa=["CT550E"], hinh_thuc_cuoi_khoa="LVTN"), "lvtn")
    check(r["ket_qua"] == "ELIGIBLE" and r["mau_thuan"],
          f"H6 giá trị hình thức sai ('LVTN' hoa) → báo mâu thuẫn, coi như chưa khai báo → xét theo TC: ELIGIBLE ({r['ket_qua']})")
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "sv.json"
        p.write_text(json.dumps(hs(xoa=["CT550E"], hinh_thuc_cuoi_khoa="tltn"), ensure_ascii=False), encoding="utf-8")
        res = prototype.answer("em đủ điều kiện làm tiểu luận chưa", str(p))
        check(res["claim"] == "du_dk(tltn)" and res["verdict"] == "TRUE",
              f"H7 câu hỏi 'tiểu luận' → nhánh TLTN ({res['claim']}, {res['verdict']})")
    res = prototype.answer("em đủ điều kiện làm luận văn chưa", None)
    check(res["verdict"] == "UNKNOWN", f"H8 không có hồ sơ → UNKNOWN, không kết luận về SV ({res['verdict']})")

    print("\nG. SCHEMA")
    import jsonschema
    sc = jsonschema.Draft202012Validator(json.loads((ROOT / "w7_student_facts" / "student_fact_schema.json").read_text(encoding="utf-8")))
    check("hinh_thuc_cuoi_khoa" in sc.schema["properties"] and not list(sc.iter_errors(hs(hinh_thuc_cuoi_khoa="lvtn")))
          and list(sc.iter_errors(hs(hinh_thuc_cuoi_khoa="khac"))),
          "G1 schema có trường hinh_thuc_cuoi_khoa ∈ {lvtn, tltn, tich_luy_tc, null}")
    cat = json.loads((ROOT / "w5_rformal" / "r_formal_v1.json").read_text(encoding="utf-8"))
    f04 = next(r for r in cat["rules"] if r["id"] == "R-F04")
    check(f04["lop"] == "F" and (f04.get("quyet_dinh") or "").startswith("QD-12"),
          f"G2 R-F04 lớp F với quyết định QD-12 (xác nhận ngoài văn bản) ({f04['lop']}, {(f04.get('quyet_dinh') or '')[:20]})")

    print("\n" + "=" * 78)
    if errors:
        print(f"KẾT LUẬN: CÓ {len(errors)} LỖI")
        for e in errors:
            print("  ·", e)
        return 1
    print("KẾT LUẬN: ĐẠT — Eligible / Not Eligible / Unknown có chứng chỉ và câu hỏi bổ sung")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
