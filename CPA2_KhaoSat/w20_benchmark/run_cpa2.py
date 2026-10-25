"""
run_cpa2.py — chạy CPA² trên G-Truth v1 / OCR-Noise v1 và chấm điểm (CPA2, Tuần 20)

Chấm như w17 (run_adversarial.cham / tong_hop — dùng chung với baseline Tuần 21):
  Soundness = 1 − #kết luận TRUE/FALSE sai / n · Coverage · Selective Acc · Đúng gold · Từ chối thừa · Hỏi đúng
  LOI (ngoại lệ, nhãn lạ) tính là SAI, không phải từ chối.

Đường chạy theo "he":
  kb    w16 abstention.tra_loi(claim, hồ sơ, dữ kiện mở)
  elig  w18 eligibility.xet → ELIGIBLE TRUE · NOT_ELIGIBLE / DA_HOAN_THANH FALSE · UNKNOWN · MAU_THUAN
  rec   w19 recommendation.de_xuat(hồ sơ, hk) → khong_de_xuat:X TRUE nếu X không trong phương án; tong_tc_le_20 TRUE nếu ≤ 20
  nl    w12 prototype.answer(câu hỏi, hồ sơ tạm) → verdict (BLOCKED/UNSAT → UNKNOWN/MAU_THUAN)
  ocr   w15 sang_ho_so → ket_luan(claim)

Q-Noise (tổng hợp): mọi câu đi đường nl. CHẤM CHẶT theo ý định: claim parser phải thuộc claim_ky_vong (rỗng → phải
là khong_ro/counterfactual); kết luận TRUE/FALSE từ claim khác = UNSOUND dù trùng gold (chứng chỉ chứng minh câu khác).
Báo thêm theo biến thể V0–V4: đúng ý định, cùng verdict / cùng claim với V0 của cùng câu gốc. Không thay Q-Real.

Errata (<bo>_errata.json, gold phát hiện sai SAU khi đóng băng — vd. C15 hạ bậc HG): in THÊM dòng "[theo errata]", số
chính thức vẫn theo gold đóng băng.

Tuần 20: CHỈ chạy dev (kiểm đường ống). Test để Tuần 22 (chạy một lần, báo cáo).
Chạy:  python run_cpa2.py --bo gtruth --split dev [--hau-to _x]      (--bo: gtruth | ocr_noise | qnoise)
"""
import argparse, json, sys, tempfile, time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
for d in ("w17_adversarial", "w16_abstention", "w15_ocr", "w18_eligibility", "w19_recommendation", "w12_integration"):
    sys.path.insert(0, str(ROOT / d))
import dau_vao
from run_adversarial import cham, tong_hop, pct


def chay(c):
    try:
        return _chay(c)
    except Exception as e:  # noqa: BLE001 — một ca lỗi không làm mất các ca khác
        return "LOI", [f"{type(e).__name__}: {e}"]


def _chay(c):
    v = dau_vao.vat_lieu_hoa(c)
    he = c["he"]
    if he == "kb":
        import abstention
        r = abstention.tra_loi(c["claim"], v["ho_so"], v["them_asp"])
        return r["verdict"], [b["bien"] for b in r["can_bo_sung"]]
    if he == "elig":
        import eligibility
        r = eligibility.xet(v["ho_so"], c["claim"], v["them_asp"])
        return ({"ELIGIBLE": "TRUE", "NOT_ELIGIBLE": "FALSE", "DA_HOAN_THANH": "FALSE"}.get(r["ket_qua"], r["ket_qua"]),
                [b["bien"] for b in r["can_bo_sung"]])
    if he == "rec":
        import recommendation
        r = recommendation.de_xuat(v["ho_so"], c["hk"], v["them_asp"])
        ma = [x["ma"] for x in r["dang_ky"]]
        if not ma:      # không có phương án (vô nghiệm / hồ sơ mâu thuẫn) → không chứng minh được gì: từ chối, không tính TRUE
            return "UNKNOWN", ["phuong_an_rong"]
        if c["claim"].startswith("tong_tc_le_20"):
            return ("TRUE" if r["tong_tc"] <= 20 else "FALSE"), []
        x = c["claim"].split(":")[1].split("@")[0]
        return ("FALSE" if x in ma else "TRUE"), []
    if he == "nl":
        import prototype
        if v["them_asp"]:
            return "LOI", ["ca nl không hỗ trợ dữ kiện mở"]
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "sv.json"
            f.write_text(json.dumps(v["ho_so"], ensure_ascii=False), encoding="utf-8")
            r = prototype.answer(c["cau_hoi"], str(f))
        vd = r["verdict"]       # BLOCKED = hậu kiểm chặn → coi là từ chối (đếm riêng qua claim_parser)
        return ({"BLOCKED": "UNKNOWN", "UNSAT": "MAU_THUAN", "DA_HOAN_THANH": "FALSE"}.get(vd, vd),
                [f"claim_parser={r.get('claim')}", f"verdict_goc={vd}"] + list(r.get("missing_facts") or []))
    if he == "ocr":
        import ocr_transcript as O
        hs, extra, bc = O.sang_ho_so(v["doc"], khai_bao=v["khai_bao"])
        out = O.ket_luan(hs, extra, bc, claim=c["claim"])
        return ("MAU_THUAN" if out == "UNSAT" else out), bc["can_hoi"]     # P20-4: hỏi 1 số ĐTBCHK thay cả học kỳ
    raise ValueError(he)


TU_CHOI = ("khong_ro", "counterfactual")


def claim_cua(r):
    """claim parser của một lần chạy nl; None nếu ca lỗi (LOI) — None không bao giờ được tính là trùng."""
    h = next((h for h in r["hoi"] if h.startswith("claim_parser=")), None)
    return h.split("=", 1)[1] if h and r["tra_loi"] != "LOI" else None


def nhat_quan(kq):
    """Q-Noise: tổng hợp theo biến thể + đúng ý định + cùng verdict / cùng claim với V0 của cùng câu gốc."""
    v0 = {r["goc"]: r for r in kq if r["bien_the"] == "V0"}
    out = {}
    for bt in sorted({r["bien_the"] for r in kq}):
        con = [r for r in kq if r["bien_the"] == bt]
        s = tong_hop(con)
        s["dung_y_dinh"] = f"{sum(r['dung_y_dinh'] for r in con)}/{len(con)}"
        s["sai_y_dinh_ket_luan"] = sum(bool(r.get("sai_y_dinh")) for r in con)
        s["cung_verdict_V0"] = f"{sum(r['tra_loi'] != 'LOI' and r['tra_loi'] == v0[r['goc']]['tra_loi'] for r in con)}/{len(con)}"
        s["cung_claim_V0"] = f"{sum(claim_cua(r) is not None and claim_cua(r) == claim_cua(v0[r['goc']]) for r in con)}/{len(con)}"
        out[f"[{bt}]"] = s
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bo", choices=["gtruth", "ocr_noise", "qnoise"], required=True)
    ap.add_argument("--split", choices=["dev", "test"], required=True)
    ap.add_argument("--hau-to", default="")
    a = ap.parse_args()
    ds = [c for c in json.loads((HERE / f"{a.bo}.json").read_text(encoding="utf-8"))["cases"]
          if c["cham_diem"] and c["split"] == a.split]
    print(f"CPA² trên {a.bo} — split {a.split} ({len(ds)} ca)\n")
    kq = []
    for c in ds:
        t = time.time()
        tl, hoi = chay(c)
        r = {"id": c["id"], "nhom": c["nhom"], "he": c["he"], "claim": c["claim"], "gold": c["gold"],
             "su_that": c.get("su_that"), "loai_gold": c["loai_gold"], "tra_loi": tl, "hoi": hoi, "giay": round(time.time() - t, 2)}
        if a.bo == "qnoise":
            r.update(goc=c["goc"], bien_the=c["bien_the"], claim_ky_vong=c["claim_ky_vong"])
        r.update(cham(c, tl, hoi))
        if a.bo == "qnoise":
            cl = claim_cua(r)
            r["dung_y_dinh"] = cl in c["claim_ky_vong"] if c["claim_ky_vong"] else cl in TU_CHOI
            if r["ket_luan"] and not r["dung_y_dinh"]:      # đúng gold nhờ may — không được tính đúng
                r.update(unsound=True, dung_gold=False, sai_y_dinh=True)
        kq.append(r)
        dau = "✗ UNSOUND" if r["unsound"] else ("✓" if r["dung_gold"] else "· từ chối thừa" if r["tu_choi_thua"] else "·")
        print(f"  {c['id']:8} {c['nhom']:14} gold={c['gold']:7} → {tl:9} {dau}" + (f"   {hoi}" if tl == "LOI" or c["he"] == "nl" else ""))
    tg = {"tong": tong_hop(kq)}
    for lg in ("quy_che", "thiet_ke"):      # gold theo câu chữ quy chế vs theo nguyên tắc thiết kế — báo cáo tách riêng
        con = [r for r in kq if r["loai_gold"] == lg]
        if con:
            tg[f"[{lg}]"] = tong_hop(con)
    if a.bo == "qnoise":
        tg.update(nhat_quan(kq))
    ef = HERE / f"{a.bo}_errata.json"                  # errata: gold phát hiện sai SAU khi đóng băng — chấm THÊM, không thay
    if ef.exists():
        sua = json.loads(ef.read_text(encoding="utf-8"))["sua"]
        ds_e = []
        for c, r in zip(ds, kq):
            ce = {**c, "gold": sua[c["id"]]["gold_errata"]} if c["id"] in sua else c
            ds_e.append({**r, **cham(ce, r["tra_loi"], r["hoi"])})
        tg["[theo errata]"] = tong_hop(ds_e)
    nhom = defaultdict(list)
    for r in kq:
        nhom[r["nhom"]].append(r)
    for k, v in sorted(nhom.items()):
        tg[k] = tong_hop(v)
    print(f"\n{'nhóm':15} {'n':>3} {'Sound':>7} {'Cover':>7} {'SelAcc':>7} {'đúng':>5} {'unsound':>8} {'từ chối thừa':>13} {'hỏi đúng':>9}")
    for k, s in tg.items():
        print(f"{k:15} {s['n']:>3} {pct(s['soundness']):>7} {pct(s['coverage']):>7} {pct(s['selective_acc']):>7} "
              f"{s['dung_gold']:>5} {s['unsound']:>8} {s['tu_choi_thua']:>13} {s['hoi_dung']:>9}"
              + (f"   đúng ý định {s['dung_y_dinh']} (kết luận sai ý định {s['sai_y_dinh_ket_luan']}) · cùng verdict V0 "
                 f"{s['cung_verdict_V0']} · cùng claim V0 {s['cung_claim_V0']}" if "cung_verdict_V0" in s else ""))
    (HERE / f"ket_qua_{a.bo}_{a.split}{a.hau_to}.json").write_text(
        json.dumps({"bo": a.bo, "split": a.split, "tong_hop": tg, "ca": kq}, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
