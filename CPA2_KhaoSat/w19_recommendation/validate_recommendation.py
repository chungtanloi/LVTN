"""
validate_recommendation.py — kiểm chứng Recommendation v1 Tuần 19 (CPA2)

Tiêu chí (Kế hoạch 24 tuần, dòng 19): "Không recommend Not Eligible" — và không đề xuất điều chưa chắc (UNKNOWN →
danh sách cần xác minh). Gold viết tay TRƯỚC khi cài đặt, theo:
  QĐ3266 Đ7 k4 (R-A03) tiên quyết = đã tích lũy · Đ14 k1 (R-C01) ≤ 20 TC/HK · CTĐT K49: lịch mở HK, nhóm tự chọn,
  nhóm một nhánh (AV hoặc PV; CN1/CN2/CN3) · QĐ5339 Đ2 k6 + QD-11 (đủ điều kiện xin miễn ≠ đã miễn) · w18 eligibility
  (QD-12) · R-A04 QĐ3266 Đ7 k5: song hành phải học trước hoặc cùng lúc — 'học' = có học, kể cả F (QD-13 rút lại 18/10/2026)
Thứ tự ưu tiên chọn HP là CHÍNH SÁCH TƯ VẤN (không phải quy chế): bắt buộc → mở khóa nhiều HP → hoàn thành nhóm → TC.

Chạy:  python validate_recommendation.py
"""
import sys, json, re, tempfile
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
STUDENTS = ROOT / "w7_student_facts" / "students"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "w12_integration"))
sys.path.insert(0, str(ROOT / "w16_abstention"))
sys.path.insert(0, str(ROOT / "w18_eligibility"))

errors = []
OK, FAIL = "  [OK]  ", "  [FAIL]"
CT = {h["ma"]: h for h in json.loads((ROOT / "w6_curriculum" / "curriculum_cntt_k49.json").read_text(encoding="utf-8"))["hoc_phan"]}
HK = {1: "I", 2: "II", 3: "III"}


def check(cond, msg, note=""):
    print((OK if cond else FAIL) + " " + msg)
    if note:
        print("          ↳ " + note)
    if not cond:
        errors.append(msg)
    return cond


def goc(ten="sv_lvtn"):
    return json.loads((STUDENTS / f"{ten}.json").read_text(encoding="utf-8"))


def chi_giu(ma_giu, **truong):
    j = goc()
    j["grades"] = {m: g for m, g in j["grades"].items() if m in ma_giu}
    j.update(truong)
    return j


NAM2 = ["ML014", "KL001E", "TN001", "TN010", "TN012", "CT100", "CT200", "CT101", "CT172", "CT173", "CT190",
        "QP010E", "QP011E", "QP012", "QP013", "TC100", "XH023"]


def ma(r):
    return [x["ma"] for x in r["dang_ky"]]


def main():
    print("=" * 78)
    print("VALIDATE RECOMMENDATION v1 — Tuần 19 (CPA2)")
    print("=" * 78)
    import recommendation as R
    import abstention as A
    import eligibility as E

    print("\nA. ĐĂNG KÝ HỌC KỲ TỚI — sinh viên năm 2 (đã học AV1, CT101, CT173, TN001 …)")
    r = R.de_xuat(chi_giu(NAM2), hk=1)
    m = ma(r)
    check(m and r["tong_tc"] <= 20, f"A1 có phương án, tổng {r['tong_tc']} TC ≤ 20 (Đ14 k1) ({m})")
    check(not {"CT174", "CT175", "CT180", "CT112", "ML018", "CT271E"} & set(m),
          "A2 không đề xuất HP thiếu tiên quyết (CT174/175/180 cần CT177; CT112 cần CT178; ML018 cần ML016)")
    check(not set(m) & set(NAM2), "A3 không đề xuất HP đã tích lũy")
    check(not any(x.startswith("FL") for x in m), "A4 đã học AV → không đề xuất Pháp văn (nhóm một nhánh)")
    check(not any(x.startswith("QP") for x in m), "A5 không đề xuất GDQP (trường bố trí riêng)")
    check(all(CT[x]["cot"] == "BB" for x in m), f"A6 còn đủ HP bắt buộc lấp 20 TC → chỉ chọn bắt buộc ({m})")
    check({"CT177", "CT176"} <= set(m), "A7 ưu tiên HP mở khóa nhiều HP sau (CT177 → CT174/175/180; CT176 → CT182/271E/300)")
    check(all(HK[1] in CT[x]["hk"] for x in m), "A8 mọi HP đề xuất có mở ở HK1")
    check(all(x["chung_chi"] for x in r["dang_ky"]), "A9 mỗi HP đề xuất có chứng chỉ (tiên quyết R-A03 …)")

    print("\nB. HỌC KỲ 3")
    r = R.de_xuat(chi_giu(NAM2), hk=3)
    m = ma(r)
    check(m and all(HK[3] in CT[x]["hk"] for x in m) and "CT177" not in m,
          f"B1 HK3 chỉ chọn HP mở ở HK3 (CT177 chỉ mở HK1/HK2) ({m})")

    check(not ({"XH031", "XH032", "XH033"} & set(m)) and {"XH024", "XH025"} <= set(m),
          f"B2 nhóm AV: AV căn bản 2–3 trước AV tăng cường (song hành Đ7 k5) ({m})")

    print("\nC. KHÔNG CHẮC → CẦN XÁC MINH, KHÔNG ĐỀ XUẤT")
    j = chi_giu([x for x in NAM2 if x != "CT101"])
    r = R.de_xuat(j, hk=1, them='1 { g10("CT101",80); g10("CT101",30) } 1.')
    m = ma(r)
    xm = [x["ma"] for x in r["can_xac_minh"]]
    check(not {"CT177", "CT176"} & set(m) and {"CT177", "CT176"} <= set(xm),
          f"C1 điểm CT101 chưa rõ → CT177, CT176 vào 'cần xác minh', không vào phương án ({m} | {xm})")

    print("\nD. GIAI ĐOẠN CUỐI — 146 TC, chưa làm LVTN")
    r = R.de_xuat(goc() | {"grades": {k: v for k, v in goc()["grades"].items() if k != "CT550E"}}, hk=1)
    m = ma(r)
    nhom_tn = {k for k, h in CT.items() if h["cot"] == "g_tot_nghiep"}
    check(m and set(m) <= nhom_tn and not {"CT550E", "CT501E"} <= set(m) and r["tong_tc"] <= 20,
          f"D1 chỉ chọn trong nhóm tốt nghiệp, không cùng lúc LVTN + TLTN ({m})")
    ht = {x["doi_tuong"] for x in r["hinh_thuc_tot_nghiep"]}
    check(ht == {"lvtn", "tltn", "tich_luy_tc"}, f"D2 hình thức tốt nghiệp đủ điều kiện: lvtn, tltn, tich_luy_tc ({ht})")
    j = goc() | {"grades": {k: v for k, v in goc()["grades"].items() if k != "CT550E"}, "hinh_thuc_cuoi_khoa": "tltn"}
    r = R.de_xuat(j, hk=1)
    check("CT550E" not in ma(r) and "lvtn" not in {x["doi_tuong"] for x in r["hinh_thuc_tot_nghiep"]},
          f"D3 đã công bố hình thức TLTN → không đề xuất LVTN ({ma(r)})")
    r = R.de_xuat(goc(), hk=1)
    check(ma(r) == [] and r["hinh_thuc_tot_nghiep"] == [], "D4 đã đủ CTĐT → không đề xuất gì thêm")

    print("\nE. XIN MIỄN (QD-11) VÀ THAY THẾ")
    j = chi_giu([x for x in NAM2 if x != "XH023"], certificates=[{"loai": "ielts", "diem": 6.0}])
    r = R.de_xuat(j, hk=1)
    xin = {x["ma"] for x in r["xin_mien"]}
    check({"XH023", "XH024", "XH025"} <= xin and not xin & {"FL001"}, f"E1 IELTS 6.0 → đề xuất NỘP ĐƠN xin miễn AV 1–3 ({sorted(xin)})")
    check(not {"XH023", "XH024", "XH025"} & set(ma(r)), "E2 HP đủ điều kiện xin miễn không bị đề xuất học")
    check(all("nộp đơn" in x["hanh_dong"] for x in r["xin_mien"]), "E3 diễn đạt 'nộp đơn xin miễn', không phải 'đã miễn'")
    r = R.de_xuat(goc("sv_mien_ielts"), hk=1)
    check(not r["xin_mien"], "E4 đã có quyết định miễn → không đề xuất xin miễn nữa")
    j = chi_giu([x for x in NAM2 if x != "ML014"] + ["ML009"])
    j["grades"]["ML009"] = {"code": "ML009", "credits": 2, "thang10": 80, "letter": "B+", "status": "passed"}
    r = R.de_xuat(j, hk=1)
    check("ML014" in {x["ma"] for x in r["thay_the"]} and "ML014" not in ma(r),
          f"E5 đạt ML009 → ML014 được công nhận thay thế, không đề xuất học ML014 ({ma(r)})")

    print("\nF. SONG HÀNH — QĐ3266 Đ7 k5: 'phải học trước hoặc học cùng lúc' (QD-13 rút lại; 'học' = có học, kể cả F)")
    j = chi_giu(NAM2 + ["CT176"])
    r = R.de_xuat(j, hk=1)
    sh = {x["ma"]: x for x in r.get("khong_du_song_hanh", [])}
    check("CT182" not in ma(r) and "CT180" in sh.get("CT182", {}).get("song_hanh", [])
          and "Điều 7 khoản 5" in sh.get("CT182", {}).get("nguon", ""),
          f"F1 chưa học CT180 và CT180 không thể học cùng kỳ (thiếu CT177) → KHÔNG đề xuất CT182, nêu Đ7 k5 ({ma(r)})")
    j = chi_giu(NAM2 + ["CT176"])
    j["grades"]["CT180"] = {"code": "CT180", "credits": 3, "thang10": 30, "letter": "F", "status": "failed"}
    r = R.de_xuat(j, hk=1)
    check("CT182" not in {x["ma"] for x in r.get("khong_du_song_hanh", [])}
          and "CT182" in ma(r) + [x["ma"] for x in r["ung_vien_khong_chon"]],
          f"F2 đã học CT180 (dù bị F) → song hành thoả, CT182 hợp lệ (quyết định (a): 'học' ≠ 'tích lũy') ({ma(r)})")
    j = chi_giu(NAM2 + ["CT176"])
    j["grades"]["CT180"] = {"code": "CT180", "credits": 3, "thang10": None, "letter": "W", "diem": "W", "status": "failed"}
    r = R.de_xuat(j, hk=1)
    check("CT182" not in ma(r) and "CT182" in {x["ma"] for x in r.get("khong_du_song_hanh", [])},
          "F3 CT180 điểm W (đã rút) → không tính là đã học → CT182 không đề xuất")
    j = chi_giu(NAM2 + ["CT176"])
    j["grades"]["CT177"] = {"code": "CT177", "credits": 3, "thang10": 30, "letter": "A", "status": "passed"}
    r = R.de_xuat(j, hk=1)
    xm = {x["ma"] for x in r["can_xac_minh"]}
    check("CT182" in xm and "CT182" not in {x["ma"] for x in r.get("khong_du_song_hanh", [])},
          f"F5 HP song hành CT180 chưa chắc (CT177 mâu thuẫn) → CT182 'cần xác minh', không kết luận chắc 'không đủ' (review)")
    j = chi_giu(NAM2 + ["CT176"])
    j["grades"]["CT180"] = {"code": "CT180", "credits": 3, "thang10": None, "letter": None, "diem": "I", "status": "unknown"}
    check(R._da_hoc(j, {}, "CT180") == "co", "F6 CT180 điểm I (status unknown) → đã học (đã dự học, chờ bổ sung điểm)")
    r = R.de_xuat(chi_giu(NAM2), hk=3)
    m = ma(r)
    bad = [x for x in m for p_ in CT[x]["song_hanh"] if p_ not in m and p_ not in NAM2]
    check(not bad, f"F4 HK3: mọi HP đề xuất có song hành đã học hoặc cùng kỳ (XH025 cùng XH024; không XH031 khi chưa có XH025) ({m})")

    print("\nG. BẤT BIẾN AN TOÀN — kiểm lại độc lập mọi đề xuất (6 hồ sơ × 3 học kỳ + biến thể)")
    ca = [(goc(n), k) for n in ("sv_5hp", "sv_du_hp", "sv_lvtn", "sv_mien_ielts", "sv_tltn", "sv_tron_ngoai_ngu")
          for k in (1, 2, 3)] + [(chi_giu(NAM2), k) for k in (1, 2, 3)]
    sai = []
    for j, k in ca:
        r = R.de_xuat(j, hk=k)
        for x in r["dang_ky"]:
            v = A.tra_loi(f'du_dk_dang_ky("{x["ma"]}")', j)["verdict"]
            d = A.tra_loi(f'tich_luy("{x["ma"]}")', j)["verdict"]
            if v != "TRUE" or d != "FALSE" or HK[k] not in (CT[x["ma"]]["hk"] or []):
                sai.append((x["ma"], k, v, d))
        m_ = {x["ma"] for x in r["dang_ky"]}
        for x in r["dang_ky"]:      # Đ7 k5: song hành phải đã học (có bản ghi, không W) hoặc cùng kỳ
            for p_ in CT[x["ma"]]["song_hanh"]:
                g_ = j["grades"].get(p_)
                if p_ not in m_ and not (g_ and g_.get("diem") != "W" and g_.get("letter") != "W"):
                    sai.append((x["ma"], "song_hanh", p_, k))
        for x in r["hinh_thuc_tot_nghiep"]:
            if E.xet(j, x["doi_tuong"])["ket_qua"] != "ELIGIBLE":
                sai.append((x["doi_tuong"], k))
        if r["tong_tc"] > 20:
            sai.append(("tong_tc", k, r["tong_tc"]))
    check(not sai, f"G1 {len(ca)} lần đề xuất: mọi mục kiểm lại đều TRUE/ELIGIBLE, song hành thoả Đ7 k5, không vượt 20 TC", f"sai: {sai[:5]}" if sai else "")

    print("\nH. PROTOTYPE (Tuần 12)")
    import prototype
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "sv.json"
        p.write_text(json.dumps(chi_giu(NAM2), ensure_ascii=False), encoding="utf-8")
        res = prototype.answer("kỳ này em nên đăng ký môn gì", str(p))
        check(res.get("claim") == "de_xuat" and res.get("de_xuat", {}).get("dang_ky"),
              f"H1 'kỳ này em nên đăng ký môn gì' → Recommendation ({res.get('claim')})")
        # hồi quy review Tuần 19
        import unicodedata
        for q, hk in [("học kì 2 em nên đăng ký gì", 2), ("kỳ 3 em nên đăng ký môn gì", 3),
                      ("HK III em nên đăng ký gì", 3), ("học hè em nên đăng ký gì", 3)]:
            res = prototype.answer(q, str(p))
            check(res.get("de_xuat", {}).get("hk") == hk, f"H2 '{q}' → HK{hk} ({res.get('de_xuat', {}).get('hk')})")
        res = prototype.answer("em nên đăng ký gì cho học kỳ 4", str(p))
        check(res.get("verdict") == "UNKNOWN" and not res.get("de_xuat"),
              f"H3 'học kỳ 4' không tồn tại (Đ6 k1: 3 HK) → hỏi lại, không lặng lẽ dùng HK1 ({res.get('verdict')})")
        check(prototype.parse_question("em nên đăng ký CT180 được chưa") != "de_xuat",
              "H4 câu hỏi về MỘT học phần không bị nhánh đề xuất chiếm")
        check(prototype.parse_question("kỳ này em có nên đăng ký môn gì") == "de_xuat",
              "H5 'em có nên đăng ký môn gì' → đề xuất (không rơi về tot_nghiep mặc định — P18-1)")
        check(prototype.parse_question(unicodedata.normalize("NFD", "kỳ này em nên đăng ký môn gì")) == "de_xuat",
              "H6 câu hỏi Unicode tổ hợp (NFD) vẫn nhận đúng ý định")

    print("\nI. HỒI QUY REVIEW")
    j = chi_giu([x for x in NAM2 if x != "XH023"] + ["FL001"])
    j["grades"]["FL001"] = {"code": "FL001", "credits": 4, "thang10": 80, "letter": "B+", "status": "passed"}
    j["grades"]["XH024"] = {"code": "XH024", "credits": 3, "thang10": 80, "letter": "B+", "status": "passed"}
    r = R.de_xuat(j, hk=1)
    ly = {x["ly_do"] for x in r["can_xac_minh"] if x["ma"] and x["ma"][:2] in ("XH", "FL")}
    check(ly and all("cả hai nhánh" in l for l in ly),
          f"I1 đã học cả AV lẫn PV → cần xác minh với lý do 'cả hai nhánh', không phải 'chưa xác định thiếu bao nhiêu' ({ly})")
    src = (HERE / "recommendation.py").read_text(encoding="utf-8")
    check(not re.search(r"^\s*assert\b", src, re.M), "I2 bất biến kiểm lại phương án không dùng assert (bị bỏ khi chạy python -O)")

    print("\n" + "=" * 78)
    if errors:
        print(f"KẾT LUẬN: CÓ {len(errors)} LỖI")
        for e in errors:
            print("  ·", e)
        return 1
    print("KẾT LUẬN: ĐẠT — chỉ đề xuất phương án đã chứng minh hợp lệ; không đề xuất Not Eligible/Unknown")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
