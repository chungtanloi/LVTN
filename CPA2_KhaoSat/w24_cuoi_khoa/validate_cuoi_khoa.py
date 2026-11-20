"""
validate_cuoi_khoa.py — kiểm chứng ý định "so sánh luận văn / tiểu luận" (CPA2, Tuần 24).

Trình bày HAI phương án hoàn thành nhóm học phần tốt nghiệp (CTĐT CNTT K49: g_tot_nghiep, tối thiểu 15 TC):
  luận văn   CT550E (15 TC)
  tiểu luận  CT501E (6 TC) + ≥ 9 TC học phần thay thế trong nhóm
cho TỪNG hồ sơ: đủ điều kiện nhận đề tài (w18, QD-12: chỉ ngưỡng TC), học phần thay thế đã đạt / còn thiếu, học phần
đăng ký được ngay (duoc_dang_ky: tiên quyết + song hành). KHÔNG khuyên "nên" — lựa chọn là của sinh viên.

  B. PARSER: ca dương / ca âm
  C. HỒI QUY: câu hỏi G-Truth / OCR-Noise / Q-Noise không bị bắt sang ý định mới
  D. TÍCH HỢP qua prototype.answer — oracle độc lập: CTĐT JSON (w6) + hồ sơ JSON, không đọc KB

Chạy: python validate_cuoi_khoa.py
"""
import json, re, sys, tempfile
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "w12_integration"))
import prototype as P

SV = ROOT / "w7_student_facts" / "students" / "sv_lvtn.json"
CTDT = json.loads((ROOT / "w6_curriculum" / "curriculum_cntt_k49.json").read_text(encoding="utf-8"))
NHOM = {h["ma"]: h for h in CTDT["hoc_phan"] if h["cot"] == "g_tot_nghiep"}
THAY_THE = sorted(c for c in NHOM if c not in ("CT550E", "CT501E"))
KHONG_DK = sorted(c for c in THAY_THE if not NHOM[c]["tien_quyet"] and not NHOM[c]["tien_quyet_tc"] and not NHOM[c]["song_hanh"])
Q = "Em nên làm luận văn hay tiểu luận?"

ok_all = True


def check(cond, msg):
    global ok_all
    print(f"  [{'OK' if cond else 'FAIL'}] {msg}")
    ok_all = ok_all and bool(cond)


def phan_B():
    print("B. PARSER")
    duong = ["Em nên làm luận văn hay tiểu luận?", "em nen lam tieu luan hay luan van",
             "Cho em hỏi em nên chọn luận văn hay tiểu luận tốt nghiệp ạ", "Em có nên làm luận văn không?",
             "So sánh luận văn và tiểu luận cho em", "Làm luận văn với tiểu luận khác nhau gì?"]
    for q in duong:
        v = P.parse_question(q)
        check(v == "so_sanh_cuoi_khoa", f"B+ '{q}' → so_sanh_cuoi_khoa ({v})")
    am = [("Em đủ điều kiện làm luận văn chưa?", "du_dk_tc"), ("Bạn em nên làm luận văn hay tiểu luận?", None),
          ("Em nên làm luận văn nhóm hay cá nhân?", None), ("Nếu em làm luận văn thì sao?", "counterfactual"),
          ("Luận văn tốt nghiệp bao nhiêu tín chỉ?", None), ("Em không nên làm luận văn à?", None),
          ("Em nên đăng ký CT550E không?", "de_xuat"),
          ("Em nên làm luận văn hay tiểu luận hay thực tập?", None),            # review L3
          ("Em nên làm luận văn hay luận văn?", None),
          ("Em nên làm luận văn hay tiểu luận ở học kỳ 1?", None)]
    for q, kv in am:
        v = P.parse_question(q)
        check(v != "so_sanh_cuoi_khoa" and (kv is None or v == kv), f"B− '{q}' → không phải so sánh{' (' + kv + ')' if kv else ''} ({v})")


def phan_C():
    print("C. HỒI QUY: câu hỏi benchmark không bị bắt sang ý định mới")
    bat, n = [], 0
    for ten in ("gtruth.json", "ocr_noise.json", "qnoise.json"):
        for c in json.loads((ROOT / "w20_benchmark" / ten).read_text(encoding="utf-8"))["cases"]:
            if c.get("cau_hoi"):
                n += 1
                if P.parse_question(c["cau_hoi"]) == "so_sanh_cuoi_khoa":
                    bat.append(c["id"])
    check(not bat, f"C1 {n} câu hỏi benchmark: không câu nào thành so_sanh_cuoi_khoa ({bat[:5]})")


def _ho_so(d, ten, bo=(), them=()):
    j = json.loads(SV.read_text(encoding="utf-8"))
    mau = j["grades"]["CT467"]
    for c in bo:
        j["grades"].pop(c)
    for c in them:                                  # học phần thay thế đạt điểm B (7,5)
        j["grades"][c] = {**mau, "code": c, "credits": NHOM[c]["tin_chi"], "thang10": 75, "letter": "B", "status": "passed"}
    f = Path(d) / ten
    f.write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")
    return str(f)


def _ho_so_them(d, ten, truong, bo=()):
    f = _ho_so(d, ten, bo=bo)
    j = json.loads(Path(f).read_text(encoding="utf-8"))
    j.update(truong)
    Path(f).write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")
    return f


def _ma_trong(text):
    return set(re.findall(r"[A-Z]{1,3}\d{2,3}E?", text))


def phan_D():
    print(f"D. TÍCH HỢP (oracle CTĐT: nhóm tốt nghiệp {len(NHOM)} HP, thay thế {THAY_THE}, không điều kiện {KHONG_DK})")
    kq = []
    with tempfile.TemporaryDirectory() as d:
        r = P.answer(Q, str(SV))
        kq.append(r)
        pa = r.get("phuong_an", {})
        check(r["verdict"] == "TRUE" and pa.get("luan_van", {}).get("da_dat") is True
              and r.get("nhom", {}).get("da_du") is True and "đã đạt CT550E" in r["explanation_vi"],
              f"D1 sv_lvtn đã đạt CT550E → luận văn ĐÃ HOÀN THÀNH, nhóm tốt nghiệp đã đủ 15 TC ({r['verdict']}, "
              f"{pa.get('luan_van', {}).get('du_dk')}, {r['explanation_vi'][:140]})")
        f2 = _ho_so(d, "chua_lv.json", bo=("CT550E",))            # 161 − 15 = 146 TC ≥ 120
        r = P.answer(Q, f2)
        kq.append(r)
        lv, tl = r.get("phuong_an", {}).get("luan_van", {}), r.get("phuong_an", {}).get("tieu_luan", {})
        check(lv.get("du_dk") == "ELIGIBLE" and tl.get("du_dk") == "ELIGIBLE",
              f"D2 146 TC (≥ 120) → đủ điều kiện nhận đề tài cả luận văn lẫn tiểu luận ({lv.get('du_dk')}, {tl.get('du_dk')})")
        check(tl.get("thay_the_da_dat") == [] and tl.get("tc_con_thieu") == 9
              and set(KHONG_DK) <= set(tl.get("dang_ky_duoc", [])),
              f"D2 chưa có HP thay thế → tiểu luận còn thiếu 9 TC; đủ điều kiện đăng ký mọi HP thay thế không tiên quyết "
              f"({tl.get('thay_the_da_dat')}, {tl.get('tc_con_thieu')}, {tl.get('dang_ky_duoc')})")
        f3 = _ho_so(d, "co_tt.json", bo=("CT550E",), them=("CT478", "CT283"))
        r = P.answer(Q, f3)
        kq.append(r)
        tl = r.get("phuong_an", {}).get("tieu_luan", {})
        kh = r.get("phuong_an", {}).get("khong_lv_tl", {})
        check(tl.get("thay_the_da_dat") == ["CT283", "CT478"] and tl.get("tc_con_thieu") == 3 and kh.get("tc_con_thieu") == 9
              and r.get("nhom", {}).get("tc_da_dat") == 6 and "CT478" not in tl.get("dang_ky_duoc", []),
              f"D3 đã đạt CT478, CT283 (6 TC) → tiểu luận còn thiếu 3 TC, phương án (3) còn thiếu 9 TC; nhóm có 6 TC; "
              f"HP đã đạt không nằm trong 'đăng ký được' ({tl.get('thay_the_da_dat')}, {tl.get('tc_con_thieu')}, "
              f"{kh.get('tc_con_thieu')}, {r.get('nhom')})")
        bo4 = ("CT550E", "CT467", "CT293", "CT275", "CT223", "CT222", "CT300", "CT449", "CT484", "CT466E")   # 146 − 27 = 119
        r = P.answer(Q, _ho_so(d, "duoi120.json", bo=bo4))
        kq.append(r)
        lv, tl = r.get("phuong_an", {}).get("luan_van", {}), r.get("phuong_an", {}).get("tieu_luan", {})
        check(lv.get("du_dk") == "NOT_ELIGIBLE" and tl.get("du_dk") == "NOT_ELIGIBLE" and "120" in r["explanation_vi"],
              f"D4 119 TC (< 120) → chưa đủ điều kiện nhận đề tài cả hai, nêu ngưỡng 120 TC ({lv.get('du_dk')}, {tl.get('du_dk')})")
        r = P.answer(Q, None)
        kq.append(r)
        check(r["verdict"] == "UNKNOWN" and "ho_so" in r.get("missing_facts", []), "D5 không có hồ sơ → UNKNOWN, cần hồ sơ")
        # review H2: chỉ đạt CT501E (tiểu luận) → KHÔNG được nói luận văn "đã hoàn thành"
        r = P.answer(Q, _ho_so(d, "chi_tl.json", bo=("CT550E",), them=("CT501E",)))
        kq.append(r)
        pa = r.get("phuong_an", {})
        lv_dong = r["explanation_vi"].split("(1)")[1].split("(2)")[0] if "(1)" in r["explanation_vi"] else ""
        # Đ31 (eligibility.lp mục 4): thực hiện MỘT trong ba hình thức → luận văn không còn cần VÌ đã đạt tiểu luận —
        # không được nói "nhóm đã đủ" khi nhóm mới có 6/15 TC
        check(pa.get("luan_van", {}).get("da_dat") is False and pa.get("tieu_luan", {}).get("da_dat") is True
              and "đã hoàn thành" not in lv_dong and "đã đạt CT550E" not in lv_dong
              and "nhóm tốt nghiệp đã đủ" not in lv_dong and "CT501E" in lv_dong,
              f"D8 (review H2) chỉ đạt CT501E → luận văn KHÔNG 'đã hoàn thành'; tiểu luận đã đạt ({lv_dong[:120]})")
        # review H1: R-F05 (QĐ3266 Đ31 k3) — không làm LVTN/TLTN, học 5 HP thay thế (15 TC) → nhóm đủ
        r = P.answer(Q, _ho_so(d, "chi_tt.json", bo=("CT550E",), them=("CT478", "CT283", "CT233", "CT482", "CT210")))
        kq.append(r)
        pa = r.get("phuong_an", {})
        check(r.get("nhom", {}).get("da_du") is True and pa.get("khong_lv_tl", {}).get("tc_con_thieu") == 0
              and pa.get("luan_van", {}).get("da_dat") is False and "Điều 31 khoản 3" in r["explanation_vi"],
              f"D9 (review H1) chỉ học HP thay thế 15 TC → phương án (3) đã đủ, nhóm đủ; luận văn chưa đạt "
              f"({pa.get('khong_lv_tl')}, {r.get('nhom')})")
        r = P.answer(Q, f2)
        pa = r.get("phuong_an", {})
        check(set(pa) == {"luan_van", "tieu_luan", "khong_lv_tl"} and pa["khong_lv_tl"]["tc_con_thieu"] == 15
              and "ba phương án" in r["explanation_vi"] and "đăng ký được ngay" not in r["explanation_vi"]
              and "chưa xét học kỳ mở" in r["explanation_vi"],
              f"D10 (review H1, M1) nêu đủ BA phương án; phương án (3) còn thiếu 15 TC; không nói 'đăng ký được ngay' "
              f"({sorted(pa)}, {r['explanation_vi'][:120]})")
        # review M2: đã khai báo hình thức cuối khoá khác (tiểu luận) → lý do không phải "thiếu 120 TC"
        r = P.answer(Q, _ho_so_them(d, "kb_tl.json", {"hinh_thuc_cuoi_khoa": "tltn"}, bo=("CT550E",)))
        kq.append(r)
        lv_dong = r["explanation_vi"].split("(1)")[1].split("(2)")[0] if "(1)" in r["explanation_vi"] else ""
        check(r.get("phuong_an", {}).get("luan_van", {}).get("du_dk") == "NOT_ELIGIBLE" and "120" not in lv_dong
              and "khai báo" in lv_dong,
              f"D11 (review M2) đã khai báo tiểu luận → luận văn chưa đủ điều kiện vì hình thức đã khai báo, không vì 120 TC "
              f"({lv_dong[:140]})")
    co = [x for x in kq if x.get("phuong_an")]
    check(all("nên chọn" not in x["explanation_vi"] and "lựa chọn là của bạn" in x["explanation_vi"].lower() for x in co),
          "D6 không khuyên 'nên chọn'; nêu rõ lựa chọn là của sinh viên")
    check(all(x["verdict"] != "BLOCKED" for x in kq)
          and all(_ma_trong(x["explanation_vi"]) <= _ma_trong(" ".join(s_["atom"] for s_ in x["certificate"]["proof"]["steps"]))
                  for x in co),
          "D7 không bị hậu kiểm chặn; mọi mã HP trong lời giải thích có trong chứng chỉ")


def main():
    for p in (phan_B, phan_C, phan_D):
        p()
    print("\nKẾT LUẬN:", "ĐẠT" if ok_all else "CHƯA ĐẠT")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
