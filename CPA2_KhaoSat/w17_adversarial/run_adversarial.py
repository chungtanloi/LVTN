"""
run_adversarial.py — chạy CPA² trên Adversarial set v1 và chấm điểm (CPA2, Tuần 17)

Hệ thống được chấm:
  - ca hồ sơ:    w16 abstention.tra_loi (KB w5–w10 + thế giới mở + missing evidence)
  - ca OCR doc:  w15 sang_ho_so → ket_luan (pipeline OCR từ sau bước nhận dạng)
  - ca OCR ảnh:  chỉ khi --anh (cần Tesseract + font), không tính vào số đo

Số đo (n = số ca chấm điểm của split):
  Soundness     = 1 − (#kết luận TRUE/FALSE sai) / n. Kết luận "sai" khi: gold UNKNOWN; hoặc ≠ gold;
                  hoặc ≠ su_that (nếu có). UNKNOWN/MAU_THUAN không bao giờ unsound.
  Coverage      = #kết luận TRUE/FALSE / n
  Selective Acc = #kết luận đúng / #kết luận TRUE/FALSE
  Đúng gold     = #trả lời == gold (MAU_THUAN tính như UNKNOWN)
  Từ chối thừa  = gold TRUE/FALSE mà trả UNKNOWN
  Hỏi đúng      = ca hồ sơ gold UNKNOWN, hệ thống UNKNOWN và hỏi đủ mọi can_hoi
  LOI           = hệ thống ném lỗi hoặc trả nhãn lạ — tính là SAI (unsound), không phải từ chối

Ca khong_phat_hien_duoc (lỗi OCR nhất quán, gold = sự thật mà đầu vào không cho thấy) KHÔNG tính vào các số
đo trên — chúng trái định nghĩa gold "đúng với thông tin đầu vào"; báo riêng ở dòng "rủi ro OCR ẩn".

Chạy:  python run_adversarial.py --split dev      (tinh chỉnh chỉ dựa trên dev)
       python run_adversarial.py --split test     (chạy để báo cáo)
"""
import argparse, json, sys, time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "w16_abstention"))
sys.path.insert(0, str(ROOT / "w15_ocr"))
import dau_vao
import abstention


def chay(ca):
    try:
        return _chay(ca)
    except Exception as e:  # noqa: BLE001 — một ca lỗi không được làm mất kết quả các ca khác
        return "LOI", [f"{type(e).__name__}: {e}"]


def _chay(ca):
    v = dau_vao.vat_lieu_hoa(ca)
    loai = ca["dau_vao"]["loai"]
    if loai == "ho_so":
        r = abstention.tra_loi(ca["claim"], v["ho_so"], v["them_asp"])
        return r["verdict"], [b["bien"] for b in r["can_bo_sung"]]
    import ocr_transcript as O
    if loai == "ocr_anh":
        import render_transcript as RT
        goc, bt = v["anh"]
        doc = O.doc_bang_diem(RT.render(dau_vao.ho_so_goc(goc), bien_the=bt))
        kb = O.khai_bao_tu_json(dau_vao.ho_so_goc(goc))
    else:
        doc, kb = v["doc"], v["khai_bao"]
    hs, extra, bc = O.sang_ho_so(doc, khai_bao=kb)
    out = O.ket_luan(hs, extra, bc, claim=ca["claim"])
    return ("MAU_THUAN" if out == "UNSAT" else out), sorted(bc["khong_chac"])


def cham(ca, tra_loi, hoi):
    ket = tra_loi in ("TRUE", "FALSE")
    tu_choi = tra_loi in ("UNKNOWN", "MAU_THUAN")
    gold = ca["gold"]
    sai = (not ket and not tu_choi) or (ket and bool(gold == "UNKNOWN" or tra_loi != gold
                                                     or (ca.get("su_that") and tra_loi != ca["su_that"])))
    return {"ket_luan": ket, "unsound": sai, "dung_gold": (tra_loi if ket else "UNKNOWN" if tu_choi else None) == gold,
            "tu_choi_thua": tu_choi and gold in ("TRUE", "FALSE"),
            "hoi_dung": (set(ca.get("can_hoi") or []) <= set(hoi)) if (gold == "UNKNOWN" and not ket and ca.get("can_hoi")) else None}


def tong_hop(ds):
    n = len(ds)
    k = sum(r["ket_luan"] for r in ds)
    us = sum(r["unsound"] for r in ds)
    hd = [r["hoi_dung"] for r in ds if r["hoi_dung"] is not None]
    return {"n": n, "soundness": 1 - us / n if n else None, "unsound": us, "coverage": k / n if n else None,
            "selective_acc": (k - us) / k if k else None, "dung_gold": sum(r["dung_gold"] for r in ds),
            "tu_choi_thua": sum(r["tu_choi_thua"] for r in ds), "hoi_dung": f"{sum(hd)}/{len(hd)}"}


def pct(x):
    return "—" if x is None else f"{100 * x:.1f}%"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "test"], required=True)
    ap.add_argument("--anh", action="store_true", help="chạy thêm ca mức ảnh (không chấm)")
    a = ap.parse_args()
    ds = json.loads((HERE / "adversarial_set.json").read_text(encoding="utf-8"))["cases"]
    chon = [c for c in ds if c["cham_diem"] and c["split"] == a.split]
    kq = []
    print(f"CPA² trên Adversarial set v1 — split {a.split} ({len(chon)} ca)\n")
    for c in chon:
        t = time.time()
        tl, hoi = chay(c)
        r = {"id": c["id"], "nhom": c["nhom"], "gold": c["gold"], "su_that": c.get("su_that"), "tra_loi": tl,
             "hoi": hoi, "khong_phat_hien_duoc": bool(c.get("khong_phat_hien_duoc")), "giay": round(time.time() - t, 2)}
        r.update(cham(c, tl, hoi))
        kq.append(r)
        dau = "✗ UNSOUND" if r["unsound"] else ("✓" if r["dung_gold"] else "· từ chối thừa" if r["tu_choi_thua"] else "·")
        print(f"  {c['id']:6} {c['nhom']:14} gold={c['gold']:7} → {tl:9} {dau}"
              + (f"   hỏi={hoi}" if hoi and tl == "UNKNOWN" else ""))
    if a.anh:
        print("\nMức ảnh (không chấm):")
        for c in (c for c in ds if c["dau_vao"]["loai"] == "ocr_anh"):
            print(f"  {c['id']} gold={c['gold']} → {chay(c)[0]}")
    chinh = [r for r in kq if not r["khong_phat_hien_duoc"]]
    an = [r for r in kq if r["khong_phat_hien_duoc"]]
    tg = {"tong": tong_hop(chinh)}
    nhom = defaultdict(list)
    for r in chinh:
        nhom[r["nhom"]].append(r)
    for k, v in sorted(nhom.items()):
        tg[k] = tong_hop(v)
    print(f"\nSố đo chính: {len(chinh)} ca (bỏ {len(an)} ca khong_phat_hien_duoc)")
    print(f"\n{'nhóm':15} {'n':>3} {'Sound':>7} {'Cover':>7} {'SelAcc':>7} {'đúng':>5} {'unsound':>8} {'từ chối thừa':>13} {'hỏi đúng':>9}")
    for k, s in tg.items():
        print(f"{k:15} {s['n']:>3} {pct(s['soundness']):>7} {pct(s['coverage']):>7} {pct(s['selective_acc']):>7} "
              f"{s['dung_gold']:>5} {s['unsound']:>8} {s['tu_choi_thua']:>13} {s['hoi_dung']:>9}")
    if an:
        print(f"\nRủi ro OCR ẩn (khong_phat_hien_duoc): {sum(r['unsound'] for r in an)}/{len(an)} ca kết luận trái sự thật "
              f"({', '.join(r['id'] + '→' + r['tra_loi'] for r in an)})")
        tg["rui_ro_ocr_an"] = {"n": len(an), "trai_su_that": sum(r["unsound"] for r in an)}
    (HERE / f"ket_qua_{a.split}.json").write_text(
        json.dumps({"split": a.split, "tong_hop": tg, "ca": kq}, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
