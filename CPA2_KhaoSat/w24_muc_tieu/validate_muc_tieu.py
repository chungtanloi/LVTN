"""
validate_muc_tieu.py — kiểm chứng ý định "mục tiêu hạng tốt nghiệp" (CPA2, Tuần 24).

Câu hỏi: "em cần trung bình bao nhiêu (ở các học phần còn lại / ở N tín chỉ kỳ tới) để tốt nghiệp (ít nhất) loại X?"
Phép tính CHÍNH XÁC trên định nghĩa có sẵn (R-B10 ĐTBCTL, R-F06 hạng, R-F07 hạ một mức) — không dự đoán:
  10·(N + S) ≥ L·(D + X)   N = tl_tu (điểm ×10 · TC), D = tl_mau, X = TC sẽ học, L = cận dưới hạng ×100 (QD-14)

  A. SỐ HỌC ASP trên dữ kiện tự dựng (giá trị kỳ vọng tính tay, ghi ở từng ca)
  B. PARSER: ca dương (có dấu / không dấu / tiền tố lời gọi / biến thể N tín chỉ) và ca ÂM (phải vẫn bị từ chối)
  C. HỒI QUY: không câu hỏi nào của G-Truth / OCR-Noise / Q-Noise bị bắt sang ý định mới
  D. TÍCH HỢP qua prototype.answer: ba trị khi chưa khai báo dữ kiện hạ bậc, chứng chỉ, hậu kiểm, trần 20 TC/HK

Chạy: python validate_muc_tieu.py
"""
import json, sys, tempfile
from pathlib import Path

import clingo

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "w12_integration"))
import prototype as P

W5 = ROOT / "w5_rformal"
LP = [W5 / "qd3266_r_formal_v1.lp", W5 / "qd5339_r_formal_v1.lp", HERE / "muc_tieu_hang.lp"]
SV = ROOT / "w7_student_facts" / "students" / "sv_lvtn.json"

ok_all = True


def check(cond, msg, note=""):
    global ok_all
    print(f"  [{'OK' if cond else 'FAIL'}] {msg}" + (f"\n         ↳ {note}" if note and not cond else ""))
    ok_all = ok_all and bool(cond)


def mo_hinh(facts):
    """Dữ kiện tự dựng + R-Formal + muc_tieu_hang.lp → tập atom của answer set duy nhất (không có nhánh mở)."""
    if not (HERE / "muc_tieu_hang.lp").exists():
        return set()
    ctl = clingo.Control(["--warn=none", "--models=0"])
    ctl.add("base", [], "\n".join(p.read_text(encoding="utf-8") for p in LP) + "\n" + facts)
    ctl.ground([("base", [])])
    ms = []
    with ctl.solve(yield_=True) as h:
        for m in h:
            ms.append({str(a) for a in m.symbols(atoms=True)})
    return ms[0] if len(ms) == 1 else set()


# CTĐT thu nhỏ: 1 học phần a 30 TC điểm 7,5 (B = 3,0) → N = 30·30 = 900, D = 30; ĐTBCTL 3,00
NEN = "course(a,30). g10(a,75). tc_toi_thieu_ctdt(60). tc_dk_ctdt(0).\n"


def phan_A():
    print("A. SỐ HỌC ASP (N = 900, D = 30 trừ khi ghi khác; S và X cùng thang ×10 · TC)")
    m = mo_hinh(NEN + "muc_tieu_hang(gioi).")
    # X = 60 − 0 − 30 = 30; L = 320: 10(900+S) ≥ 320·60 → S ≥ 1020 → TB 3,40 (10X = 300 < 1020 ≤ 40X = 1200)
    check("tc_xet(30)" in m and "mt_can(gioi,1020,30)" in m and "mt_kha_thi(gioi)" in m,
          "A1 giỏi, X mặc định = TC tối thiểu còn lại (60 − 0 − 30 = 30) → cần S = 1020 (TB 3,40)",
          f"{sorted(a for a in m if a.startswith(('tc_xet', 'mt_')))}")
    check("why(mt_can(gioi,1020,30),r_b10)" in m and "why(mt_can(gioi,1020,30),r_f06)" in m,
          "A1 chứng chỉ: R-B10 (ĐTBCTL) + R-F06 (ngưỡng hạng)")
    m = mo_hinh(NEN + "muc_tieu_hang(xuat_sac).")
    # L = 360: S ≥ 360·60/10 − 900 = 1260 > 40·30 = 1200 → không thể kể cả toàn A
    check("mt_khong_the(xuat_sac,diem)" in m and "mt_kha_thi(xuat_sac)" not in m,
          "A2 xuất sắc: cần S = 1260 > 1200 (toàn A) → không thể")
    m = mo_hinh(NEN + "muc_tieu_hang(trung_binh).")
    # L = 200: S ≥ 1200 − 900 = 300 = 10X → mọi HP đạt D là đủ (biên bằng)
    check("mt_chi_can_qua(trung_binh)" in m and not any(a.startswith("mt_can(trung_binh") for a in m),
          "A3 trung bình: S = 300 = 10·X (biên) → chỉ cần đạt mọi học phần (≥ D)")
    m = mo_hinh(NEN + "muc_tieu_hang(kha).")
    # L = 250: S ≥ 1500 − 900 = 600 > 300 → cần TB 2,00
    check("mt_can(kha,600,30)" in m, "A3b khá: S = 600 > 10X = 300 → cần TB 2,00 (không phải 'chỉ cần qua')")
    m = mo_hinh(NEN + "muc_tieu_hang(gioi). tc_du_kien(10).")
    # X = 10: 10(900+S) ≥ 320·40 → S ≥ 380 → TB 3,80
    check("tc_xet(10)" in m and "mt_can(gioi,380,10)" in m and "tc_xet(30)" not in m,
          "A4 X do câu hỏi nêu (10 TC) thay X mặc định → S = 380 (TB 3,80)")
    m7 = mo_hinh(NEN + "muc_tieu_hang(gioi). tc_du_kien(7).")
    m8 = mo_hinh(NEN + "muc_tieu_hang(gioi). tc_du_kien(8).")
    # X = 7: S ≥ 320·37/10 − 900 = 284 > 280 → không thể; X = 8: S ≥ 316 ≤ 320 → cần TB 3,95
    check("mt_khong_the(gioi,diem)" in m7 and "mt_can(gioi,316,8)" in m8,
          "A5 biên toàn A: 7 TC cần 284 > 280 → không thể; 8 TC cần 316 ≤ 320 → TB 3,95")
    nen0 = "course(a,30). g10(a,75). tc_toi_thieu_ctdt(30). tc_dk_ctdt(0).\n"
    m_k = mo_hinh(nen0 + "muc_tieu_hang(kha).")
    m_g = mo_hinh(nen0 + "muc_tieu_hang(gioi).")
    check("tc_xet(0)" in m_k and "mt_da_dat(kha)" in m_k and "mt_khong_the(gioi,het_tc)" in m_g,
          "A6 đã đủ TC tối thiểu (X = 0): ĐTBCTL 3,00 ≥ 2,50 → đã đạt khá; giỏi → không thể (không còn TC tối thiểu)")
    nen_dk = NEN.replace("tc_dk_ctdt(0)", "tc_dk_ctdt(10)") + "course(q,10). loai_hp(q,gdqp). g10(q,80).\n"
    m = mo_hinh(nen_dk + "muc_tieu_hang(gioi).")
    # HP điều kiện không vào ĐTBCTL; X = 60 − 10 − 30 = 20: S ≥ 320·50/10 − 900 = 700 → TB 3,50
    check("tc_xet(20)" in m and "mt_can(gioi,700,20)" in m,
          "A7 HP điều kiện: không vào N/D, và trừ khỏi TC tối thiểu (X = 60 − 10 − 30 = 20) → S = 700 (TB 3,50)")
    ha = NEN + "tc_diem_f(10).\n"          # 100·10 > 5·60 → vuot_5_chac → ha_mot_muc (Đ34 k2 a)
    m_g = mo_hinh(ha + "muc_tieu_hang(gioi). tc_du_kien(60).")
    m_g0 = mo_hinh(NEN + "muc_tieu_hang(gioi). tc_du_kien(60).")
    m_x = mo_hinh(ha + "muc_tieu_hang(xuat_sac). tc_du_kien(60).")
    m_k = mo_hinh(ha + "muc_tieu_hang(kha). tc_du_kien(60).")
    # bị hạ: giỏi phải có hạng gốc xuất sắc (L = 360): S ≥ 360·90/10 − 900 = 2340; không hạ: 320·90/10 − 900 = 1980
    check("mt_can(gioi,2340,60)" in m_g and "mt_can(gioi,1980,60)" in m_g0,
          "A8 hạ một mức (F > 5%): ít nhất giỏi cần hạng gốc xuất sắc → S = 2340 (không hạ: 1980)")
    check("why(mt_can(gioi,2340,60),r_f07)" in m_g, "A8 chứng chỉ ca bị hạ có R-F07")
    check("mt_khong_the(xuat_sac,ha_bac)" in m_x and "mt_kha_thi(xuat_sac)" not in m_x,
          "A9 bị hạ một mức → xuất sắc không thể đạt dù điểm (lý do ha_bac)")
    # khá: hạ chỉ áp xuất sắc/giỏi; giỏi gốc bị hạ vẫn là khá → ngưỡng giữ 2,50: S ≥ 250·90/10 − 900 = 1350
    check("mt_can(kha,1350,60)" in m_k, "A10 khá khi bị hạ: ngưỡng vẫn 2,50 → S = 1350")
    m = mo_hinh("tc_toi_thieu_ctdt(0). tc_dk_ctdt(0). muc_tieu_hang(xuat_sac).")
    # review M1: chưa có HP nào tính ĐTBCTL (D = 0) và X = 0 → V = 0 nhưng KHÔNG được kết luận "đã đạt"
    check("tl_mau(0)" in m and "mt_da_dat(xuat_sac)" not in m and "mt_kha_thi(xuat_sac)" not in m,
          "A11 (review M1) D = 0, X = 0 → không suy 'đã đạt' xuất sắc từ V = 0")


def phan_B():
    print("B. PARSER (prototype.parse_question)")
    duong = [
        ("Em cần đạt trung bình bao nhiêu để tốt nghiệp loại giỏi?", "muc_tieu_hang(gioi)"),
        ("em can trung binh bao nhieu de tot nghiep loai xuat sac", "muc_tieu_hang(xuat_sac)"),
        ("Để tốt nghiệp loại giỏi thì em cần đạt điểm trung bình bao nhiêu ở các học phần còn lại?", "muc_tieu_hang(gioi)"),
        ("Cho em hỏi em cần bao nhiêu điểm để ra trường bằng khá ạ", "muc_tieu_hang(kha)"),
        ("Kỳ tới em học 18 tín chỉ thì cần trung bình bao nhiêu để tốt nghiệp loại giỏi?", "muc_tieu_hang(gioi,18)"),
        ("kỳ sau em học 15 tc thì cần đạt trung bình bao nhiêu để tốt nghiệp loại xuất sắc", "muc_tieu_hang(xuat_sac,15)"),
        ("Em cần đạt điểm trung bình tích lũy bao nhiêu để tốt nghiệp loại giỏi?", "muc_tieu_hang(gioi)"),   # review L1
    ]
    for q, kv in duong:
        v = P.parse_question(q)
        check(v == kv, f"B+ '{q}' → {kv} ({v})")
    am = [
        ("Điểm bao nhiêu thì qua môn?", None),
        ("Em có đạt loại giỏi khi tốt nghiệp không?", "hang_cuoi(gioi)"),   # ý định xếp loại sẵn có (C12) giữ nguyên
        ("Bạn em cần bao nhiêu để tốt nghiệp loại giỏi?", None),
        ("Em cần bao nhiêu tín chỉ để tốt nghiệp?", None),
        ("Em cần bao nhiêu để tốt nghiệp loại giỏi hay xuất sắc?", None),
        ("Em không cần bao nhiêu để tốt nghiệp loại giỏi", None),
        ("Em cần bao nhiêu để được học bổng loại giỏi?", None),
        ("Nếu em rớt CT177 thì trễ mấy kỳ?", "counterfactual"),
        ("Em cần trung bình bao nhiêu để tốt nghiệp?", None),
        ("Nếu em học 18 tín chỉ thì cần bao nhiêu để tốt nghiệp loại giỏi?", "counterfactual"),          # review L2
        ("Em cần bao nhiêu để tốt nghiệp loại giỏi nếu rớt CT177?", "counterfactual"),
    ]
    for q, kv in am:
        v = P.parse_question(q)
        check(not v.startswith("muc_tieu_hang") and (kv is None or v == kv),
              f"B− '{q}' → KHÔNG phải mục tiêu hạng{' (' + kv + ')' if kv else ''} ({v})")


def phan_C():
    print("C. HỒI QUY: câu hỏi của benchmark không bị bắt sang ý định mới")
    bat = []
    n = 0
    for ten in ("gtruth.json", "ocr_noise.json", "qnoise.json"):
        for c in json.loads((ROOT / "w20_benchmark" / ten).read_text(encoding="utf-8"))["cases"]:
            q = c.get("cau_hoi") or ""
            if q:
                n += 1
                if P.parse_question(q).startswith("muc_tieu_hang"):
                    bat.append(c["id"])
    check(not bat, f"C1 {n} câu hỏi G-Truth/OCR-Noise/Q-Noise: không câu nào thành muc_tieu_hang ({bat[:5]})")


def _ho_so(d, ten, bo=(), them=None):
    j = json.loads(SV.read_text(encoding="utf-8"))
    for c in bo:
        j["grades"].pop(c)
    j.update(them or {})
    f = Path(d) / ten
    f.write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")
    return str(f)


SACH = {"tc_diem_f": 0, "ky_luat_canh_cao_cap_truong": False}
BO30 = ("CT550E", "CT467", "CT293", "CT275", "CT223", "CT222")      # 15 + 5·3 = 30 TC không điều kiện


def phan_D():
    print("D. TÍCH HỢP (prototype.answer)")
    q18 = "Kỳ tới em học 18 tín chỉ thì cần trung bình bao nhiêu để tốt nghiệp loại giỏi?"
    tat_ca = []
    with tempfile.TemporaryDirectory() as d:
        # sv_lvtn: N = 4390, D = 140 (ĐTBCTL 3,13). X = 18: không hạ → S ≥ 320·158/10 − 4390 = 666 → TB 3,70;
        # bị hạ → L = 360: S ≥ 1298 > 720 → không thể. Chưa khai báo tc_diem_f / kỷ luật → hai kịch bản → UNKNOWN
        r = P.answer(q18, str(SV))
        tat_ca.append(r)
        check(r["verdict"] == "UNKNOWN" and "3,70" in r["explanation_vi"]
              and {"f_ngoai_ho_so_vuot_5", "ky_luat_canh_cao_cap_truong"} & set(r.get("missing_facts", [])),
              f"D1 chưa khai báo dữ kiện hạ bậc → UNKNOWN, nêu 3,70 (nếu không bị hạ) và hỏi dữ kiện "
              f"({r['verdict']}, {r.get('missing_facts')}, {r['explanation_vi'][:160]})")
        f = _ho_so(d, "sach.json", them=SACH)
        r = P.answer(q18, f)
        tat_ca.append(r)
        ids = {s_["rule_id"] for s_ in r["certificate"]["proof"]["steps"]}
        check(r["verdict"] == "TRUE" and "3,70" in r["explanation_vi"] and {"r_b10", "r_f06"} <= ids
              and r.get("claim") == "mt_can(gioi,666,18)",
              f"D2 khai báo sạch → TRUE, cần TB 3,70 trên 18 TC, chứng chỉ R-B10 + R-F06 "
              f"({r['verdict']}, {r.get('claim')}, {sorted(ids)}, {r['explanation_vi'][:160]})")
        check(ids <= {"r_b10", "r_f06", "r_f07", "r_f07b"} and r["certificate"]["proof"]["steps"][0]["atom"] == "mt_can(gioi,666,18)",
              f"D2b chứng chỉ CHỈ gồm bước của phép tính mục tiêu (ĐTBCTL, hạng, hạ bậc), bước đầu là kết quả ({sorted(ids)})")
        r = P.answer(q18.replace("giỏi", "xuất sắc"), f)
        tat_ca.append(r)
        check(r["verdict"] == "FALSE" and "không thể" in r["explanation_vi"].lower(),
              f"D3 xuất sắc với 18 TC: cần 1298 > 720 → FALSE 'không thể' ({r['verdict']}, {r['explanation_vi'][:140]})")
        r = P.answer(q18.replace("giỏi", "khá"), str(SV))
        tat_ca.append(r)
        check(r["verdict"] == "TRUE" and "chỉ cần" in r["explanation_vi"] and "trở lên" in r["explanation_vi"],
              f"D4 khá: ĐTBCTL 3,13 ≥ 2,50, hạ bậc không đổi ngưỡng khá → TRUE 'chỉ cần' đạt mọi HP, dù chưa khai báo "
              f"({r['verdict']}, {r['explanation_vi'][:140]})")
        f30 = _ho_so(d, "con30.json", bo=BO30, them=SACH)
        ex, _, _ = P.load_student(f30)
        ctl = clingo.Control(["--warn=none", "--models=1"])
        ctl.add("base", [], P.kb(ex))
        ctl.ground([("base", [])])
        with ctl.solve(yield_=True) as h:
            at = {str(a) for a in next(iter(h)).symbols(atoms=True)}
        N = next(int(a[6:-1]) for a in at if a.startswith("tl_tu("))
        D = next(int(a[7:-1]) for a in at if a.startswith("tl_mau("))
        S = -(-(320 * (D + 30) - 10 * N) // 10)          # oracle độc lập với muc_tieu_hang.lp
        r = P.answer("Em cần đạt trung bình bao nhiêu để tốt nghiệp loại giỏi?", f30)
        tat_ca.append(r)
        check(r["verdict"] == "TRUE" and r.get("claim") == f"mt_can(gioi,{S},30)" and "30" in r["explanation_vi"],
              f"D5 bỏ 30 TC: X mặc định = 30 TC còn lại; S = ⌈(320·{D + 30} − 10·{N})/10⌉ = {S} "
              f"({r['verdict']}, {r.get('claim')}, {r['explanation_vi'][:140]})")
        r = P.answer(q18.replace("18", "21"), f)
        tat_ca.append(r)
        check(r["verdict"] == "UNKNOWN" and "20" in r["explanation_vi"],
              f"D6 21 TC trong một kỳ vượt trần 20 TC/HK (QĐ3266 Đ14 k1) → không tính, hỏi lại ({r['verdict']}, {r['explanation_vi'][:140]})")
        # review H1: KHÔNG THỂ ở mọi thế giới (không hạ: cần 1190 > 600; bị hạ: xuất sắc không đạt được) → FALSE, không hỏi
        # dữ kiện vô ích. sv_lvtn chưa khai báo: X = 15, L = 360: S ≥ (360·155 − 43900)/10 = 1190 > 40·15 = 600
        r = P.answer("Kỳ tới em học 15 tín chỉ thì cần trung bình bao nhiêu để tốt nghiệp loại xuất sắc?", str(SV))
        tat_ca.append(r)
        check(r["verdict"] == "FALSE" and not r.get("missing_facts"),
              f"D9 (review H1) không thể ở MỌI thế giới → FALSE, không hỏi dữ kiện ({r['verdict']}, {r.get('missing_facts')})")
        # review H2: X mặc định = TC tối thiểu còn lại (sv_lvtn: 0) → 'không thể' chỉ đúng với số TC tối thiểu; học thêm
        # thì khác (câu 18 TC ở D2 cần 3,70) → không kết luận FALSE, hỏi số TC dự định
        r = P.answer("Em cần đạt trung bình bao nhiêu để tốt nghiệp loại giỏi?", f)
        tat_ca.append(r)
        check(r["verdict"] == "UNKNOWN" and "tc_du_kien" in r.get("missing_facts", []) and "tối thiểu" in r["explanation_vi"],
              f"D10 (review H2) X mặc định không đạt → UNKNOWN, hỏi số TC dự định, không 'không thể' ({r['verdict']}, "
              f"{r.get('missing_facts')}, {r['explanation_vi'][:160]})")
        f0 = _ho_so(d, "rong.json", bo=tuple(json.loads(SV.read_text(encoding="utf-8"))["grades"]), them=SACH)
        r = P.answer("Kỳ tới em học 18 tín chỉ thì cần trung bình bao nhiêu để tốt nghiệp loại khá?", f0)
        tat_ca.append(r)
        check(r["verdict"] == "UNKNOWN" and "None" not in r["explanation_vi"] and "diem_hoc_phan" in r.get("missing_facts", []),
              f"D11 (review M1) chưa có ĐTBCTL → UNKNOWN 'chưa tính được', không in 'None' ({r['verdict']}, {r['explanation_vi'][:120]})")
        r = P.answer(q18, None)
        tat_ca.append(r)
        check(r["verdict"] == "UNKNOWN" and "ho_so" in r.get("missing_facts", []), "D7 không có hồ sơ → UNKNOWN, cần hồ sơ")
    check(all(x["verdict"] != "BLOCKED" for x in tat_ca), "D8 không câu trả lời nào bị hậu kiểm chặn")


def main():
    for p in (phan_A, phan_B, phan_C, phan_D):
        p()
    print("\nKẾT LUẬN:", "ĐẠT" if ok_all else "CHƯA ĐẠT")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
