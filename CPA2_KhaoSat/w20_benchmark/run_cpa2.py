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

Tuần 20: CHỈ chạy dev (kiểm đường ống). Test để Tuần 22 (chạy một lần, báo cáo).
Chạy:  python run_cpa2.py --bo gtruth --split dev [--hau-to _x]
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
        vd = r["verdict"]
        return {"BLOCKED": "UNKNOWN", "UNSAT": "MAU_THUAN"}.get(vd, vd), list(r.get("missing_facts") or [])
    if he == "ocr":
        import ocr_transcript as O
        hs, extra, bc = O.sang_ho_so(v["doc"], khai_bao=v["khai_bao"])
        out = O.ket_luan(hs, extra, bc, claim=c["claim"])
        return ("MAU_THUAN" if out == "UNSAT" else out), sorted(bc["khong_chac"])
    raise ValueError(he)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bo", choices=["gtruth", "ocr_noise"], required=True)
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
        r.update(cham(c, tl, hoi))
        kq.append(r)
        dau = "✗ UNSOUND" if r["unsound"] else ("✓" if r["dung_gold"] else "· từ chối thừa" if r["tu_choi_thua"] else "·")
        print(f"  {c['id']:8} {c['nhom']:14} gold={c['gold']:7} → {tl:9} {dau}" + (f"   {hoi}" if tl == "LOI" else ""))
    tg = {"tong": tong_hop(kq)}
    for lg in ("quy_che", "thiet_ke"):      # gold theo câu chữ quy chế vs theo nguyên tắc thiết kế — báo cáo tách riêng
        con = [r for r in kq if r["loai_gold"] == lg]
        if con:
            tg[f"[{lg}]"] = tong_hop(con)
    nhom = defaultdict(list)
    for r in kq:
        nhom[r["nhom"]].append(r)
    for k, v in sorted(nhom.items()):
        tg[k] = tong_hop(v)
    print(f"\n{'nhóm':15} {'n':>3} {'Sound':>7} {'Cover':>7} {'SelAcc':>7} {'đúng':>5} {'unsound':>8} {'từ chối thừa':>13} {'hỏi đúng':>9}")
    for k, s in tg.items():
        print(f"{k:15} {s['n']:>3} {pct(s['soundness']):>7} {pct(s['coverage']):>7} {pct(s['selective_acc']):>7} "
              f"{s['dung_gold']:>5} {s['unsound']:>8} {s['tu_choi_thua']:>13} {s['hoi_dung']:>9}")
    (HERE / f"ket_qua_{a.bo}_{a.split}{a.hau_to}.json").write_text(
        json.dumps({"bo": a.bo, "split": a.split, "tong_hop": tg, "ca": kq}, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
