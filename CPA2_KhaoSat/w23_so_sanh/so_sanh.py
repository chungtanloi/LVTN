"""
so_sanh.py — bảng so sánh CPA² vs baseline LLM/RAG/tool-calling (CPA2, Tuần 23).

Đọc kết quả ĐÃ CÓ, không chạy hệ thống nào, không gọi API:
  CPA²     w20_benchmark/ket_qua_{gtruth,ocr_noise}_<split>.json   (run_cpa2; --cpa2-hau-to thêm một dòng SAU SỬA, riêng)
  baseline ket_qua_baseline_<b1|b2|b3>_<openai|gemini>_<split>[hậu tố].json   (run_baseline; thư mục CPA2_BASELINE_OUT
           hoặc w21_baseline/)

Công bằng:
  - mọi hệ chấm LẠI bằng CÙNG hàm run_adversarial.cham / tong_hop, trên TẬP CA CHUNG của mọi hệ đã có kết quả
    (ca thiếu ở hệ nào được liệt kê, không bỏ lặng lẽ); LOI tính là SAI
  - nhóm như Tuần 21: tong · [cau_hoi_ro] (run_baseline.cau_hoi_kem) · [quy_che]/[thiet_ke] · [theo errata] (chỉ THÊM dòng)
  - số CHÍNH THỨC: CPA² không hậu tố; baseline meta.dong_bang_khop = true và không hậu tố. Còn lại gắn [không chính thức]
  - 'hỏi đúng' chỉ đo được với CPA² (baseline trả lời tự do, không có danh sách dữ kiện cần hỏi) → None
  - McNemar chính xác hai phía (nhị thức) cho CPA² vs từng baseline, trên 'đúng gold' và trên 'unsound'. Tập nhỏ → lực
    kiểm định thấp: p lớn KHÔNG có nghĩa là hai hệ như nhau.

Chạy:  python so_sanh.py --split dev [--cpa2-hau-to _sau_A17] [--ra]
"""
import argparse, json, math, os, re, sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
for d in (ROOT / "w21_baseline", ROOT / "w17_adversarial", ROOT / "w20_benchmark"):
    sys.path.insert(0, str(d))
import run_baseline as R                       # tai_ca, cau_hoi_kem, _errata — cùng định nghĩa với Tuần 21
from run_adversarial import cham, tong_hop, pct

BL = ("b1", "b2", "b3")
NHA = ("openai", "gemini")
BO = ("gtruth", "ocr_noise")


def mcnemar(b, c):
    """p hai phía chính xác cho b, c cặp bất đồng: 2·P(X ≤ min(b,c)), X ~ Bin(b+c, 1/2); tối đa 1."""
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


def _doc_cpa2(w20_dir, split, hau_to):
    out = {}
    for bo in BO:
        f = Path(w20_dir) / f"ket_qua_{bo}_{split}{hau_to}.json"
        if not f.exists():
            raise FileNotFoundError(f"thiếu kết quả CPA² {f.name} — chạy w20_benchmark/run_cpa2.py --bo {bo} --split {split}"
                                    + (f" --hau-to {hau_to}" if hau_to else ""))
        j = json.loads(f.read_text(encoding="utf-8"))
        if j.get("split", split) != split:
            raise ValueError(f"{f.name}: split {j.get('split')} ≠ {split}")
        for r in j["ca"]:
            out[r["id"]] = {"tra_loi": r["tra_loi"], "hoi": r.get("hoi") or [], "nhan_thieu": False}
    return out


def _doc_bl(f, split):
    j = json.loads(Path(f).read_text(encoding="utf-8"))
    m = j.get("meta", {})
    if m.get("split") != split:
        raise ValueError(f"{Path(f).name}: meta.split = {m.get('split')!r} ≠ split {split!r} đang so")
    tho = {r["id"]: r for r in j.get("tra_loi_tho", [])}
    out = {r["id_goc"]: {"tra_loi": r["tra_loi"], "hoi": None, "nhan_thieu": bool(tho.get(r["id"], {}).get("nhan_thieu"))}
           for r in j["ca"]}
    return m, out


def _cham(ca, tra):
    """Một dòng chấm cho mỗi ca (cùng hàm cho mọi hệ). hoi None = hệ không có khái niệm 'hỏi' → hoi_dung None."""
    x = cham(ca, tra["tra_loi"], tra["hoi"] or [])
    if tra["hoi"] is None:
        x["hoi_dung"] = None
    return x


def _tong(xs, tra_cua):
    t = tong_hop([x for _, x in xs])
    if xs and all(tra_cua[i]["hoi"] is None for i, _ in xs):
        t["hoi_dung"] = None
    t["loi"] = sum(tra_cua[i]["tra_loi"] == "LOI" for i, _ in xs)
    t["nhan_thieu"] = sum(tra_cua[i]["nhan_thieu"] for i, _ in xs)
    return t


def _nhom(ids, ca, tra, errata):
    xs = [(i, _cham(ca[i]["goc"], tra[i])) for i in ids]
    g = {"tong": _tong(xs, tra)}
    g["[cau_hoi_ro]"] = _tong([(i, x) for i, x in xs if R.cau_hoi_kem(ca[i]["goc"]) is None], tra)
    for lg in ("quy_che", "thiet_ke"):
        con = [(i, x) for i, x in xs if ca[i]["goc"].get("loai_gold") == lg]
        if con:
            g[f"[{lg}]"] = _tong(con, tra)
    if any(i in errata and ca[i]["bo"] == "gtruth" for i in ids):
        xe = [(i, _cham({**ca[i]["goc"], "gold": errata[i]} if i in errata and ca[i]["bo"] == "gtruth" else ca[i]["goc"], tra[i]))
              for i in ids]
        g["[theo errata]"] = _tong(xe, tra)
    return g, dict(xs)


def so_sanh(split, w20_dir=ROOT / "w20_benchmark", bl_dir=None, cpa2_hau_to=""):
    bl_dir = Path(bl_dir or os.environ.get("CPA2_BASELINE_OUT") or ROOT / "w21_baseline")
    ca = {v["goc"]["id"]: v for v in R.tai_ca(split).values()}
    errata = R._errata()
    he = [{"ten": "CPA²", "chinh_thuc": True, "meta": {"model": "clingo (CPA²)", "usd": 0}, "tra": _doc_cpa2(w20_dir, split, "")}]
    if cpa2_hau_to:
        he.append({"ten": f"CPA² [{cpa2_hau_to}]", "chinh_thuc": False, "meta": {"model": "clingo (CPA²)", "usd": 0},
                   "tra": _doc_cpa2(w20_dir, split, cpa2_hau_to)})
    for bl in BL:
        for nha in NHA:
            ten = f"{bl}_{nha}"
            goc = bl_dir / f"ket_qua_baseline_{ten}_{split}.json"
            if goc.exists():
                m, tra = _doc_bl(goc, split)
                he.append({"ten": ten, "chinh_thuc": m.get("dong_bang_khop") is True and not m.get("hau_to"), "meta": m, "tra": tra})
            else:
                he.append({"ten": ten, "trang_thai": "chua_chay", "chinh_thuc": False})
            # mọi hậu tố run_baseline cho phép ([A-Za-z0-9_-]*), kể cả không bắt đầu bằng '_' (review M2); bỏ đúng tên chính thức
            for f in sorted(bl_dir.glob(f"ket_qua_baseline_{ten}_{split}*.json")):
                if f.name == goc.name:
                    continue
                m, tra = _doc_bl(f, split)
                ht = m.get("hau_to") or f.stem[len(f"ket_qua_baseline_{ten}_{split}"):]
                he.append({"ten": f"{ten} [{ht}]", "chinh_thuc": False, "meta": m, "tra": tra})
    co = [h for h in he if "tra" in h]
    # Tập chung CHỈ theo hệ chính thức (review M1): một file thử nghiệm thiếu ca không được kéo n của dòng chính thức.
    # Hệ không chính thức chấm trên (tập chung ∩ ca của nó), n riêng.
    chung = sorted(set(ca).intersection(*(h["tra"] for h in co if h["chinh_thuc"])))
    thieu = {h["ten"]: sorted(set(ca) - set(h["tra"])) for h in co if set(ca) - set(h["tra"])}
    for h in co:
        h["ids"] = [i for i in chung if i in h["tra"]]
        h["nhom"], h["_x"] = _nhom(h["ids"], ca, h["tra"], errata)
        h.setdefault("trang_thai", "co_ket_qua")
    c = he[0]
    mc, bd = {}, {}
    for h in co[1:]:
        if h["ten"].startswith("CPA²"):
            continue
        a, b_ = c["_x"], h["_x"]
        cap = h["ids"]                                                       # cặp: ca có ở cả CPA² chính thức và hệ này
        nhan = h["ten"] + ("" if h["chinh_thuc"] else " [không chính thức]")   # review M3
        mc[nhan] = {}
        for k in ("dung_gold", "unsound"):
            tot = (lambda x: x["dung_gold"]) if k == "dung_gold" else (lambda x: not x["unsound"])
            b = sum(1 for i in cap if not tot(a[i]) and tot(b_[i]))         # CPA² kém hơn ở ca này
            cc = sum(1 for i in cap if tot(a[i]) and not tot(b_[i]))        # CPA² tốt hơn ở ca này
            mc[nhan][k] = {"n": len(cap), "b": b, "c": cc, "p": mcnemar(b, cc)}
        bd[nhan] = {"cpa2_dung_bl_unsound": [i for i in cap if a[i]["dung_gold"] and b_[i]["unsound"]],
                    "bl_dung_cpa2_unsound": [i for i in cap if b_[i]["dung_gold"] and a[i]["unsound"]]}
    for h in he:
        h.pop("tra", None)
        h.pop("_x", None)
        h.pop("ids", None)
    return {"split": split, "n_gold": len(ca), "n_chung": len(chung), "thieu": thieu, "he": he, "mcnemar": mc, "bat_dong": bd}


def bang_md(kq, nhom="tong"):
    L = ["| Hệ | n | Soundness | unsound | Coverage | Selective Acc | đúng gold | từ chối thừa | hỏi đúng | LOI | nhãn thiếu | USD | model |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for h in kq["he"]:
        if h.get("trang_thai") == "chua_chay":
            L.append(f"| {h['ten']} | — | chưa chạy | | | | | | | | | | |")
            continue
        s = h["nhom"].get(nhom)
        if not s:
            continue
        m = h.get("meta", {})
        ten = h["ten"] + ("" if h["chinh_thuc"] else " [không chính thức]")
        mo = (m.get("model") or "") + (" qua " + m["qua"] if m.get("qua") else "")
        usd = "—" if m.get("usd") is None else f"{m['usd']:.4f}"
        hd = s["hoi_dung"] if s["hoi_dung"] and not str(s["hoi_dung"]).endswith("/0") else "—"
        L.append(f"| {ten} | {s['n']} | {pct(s['soundness'])} | {s['unsound']} | {pct(s['coverage'])} | {pct(s['selective_acc'])} | "
                 f"{s['dung_gold']} | {s['tu_choi_thua']} | {hd} | {s['loi']} | {s['nhan_thieu']} | {usd} | {mo} |")
    return "\n".join(L)


def bao_cao(kq):
    L = [f"# So sánh CPA² vs baseline — split {kq['split']}\n",
         f"Tập ca chung của các hệ CHÍNH THỨC: **{kq['n_chung']}/{kq['n_gold']}** ca được chấm (G-Truth + OCR-Noise). "
         "Hệ không chính thức chấm trên phần giao của tập này với ca của nó (xem cột n)."]
    for t, ids in kq["thieu"].items():
        L.append(f"- {t} thiếu {len(ids)} ca: {', '.join(ids)}")
    nhom = []
    for h in kq["he"]:
        for k in h.get("nhom", {}):
            if k not in nhom:
                nhom.append(k)
    for k in nhom:
        L += [f"\n## Nhóm `{k}`\n", bang_md(kq, k)]
    if kq["mcnemar"]:
        L += ["\n## McNemar chính xác (CPA² vs baseline, cặp bất đồng)\n",
              "b = ca CPA² kém hơn, c = ca CPA² tốt hơn. Tập nhỏ: p lớn không chứng minh hai hệ như nhau.\n",
              "| Baseline | n cặp | đúng gold (b / c / p) | không unsound (b / c / p) |", "|---|---|---|---|"]
        for t, v in kq["mcnemar"].items():
            d, u = v["dung_gold"], v["unsound"]
            L.append(f"| {t} | {d['n']} | {d['b']} / {d['c']} / {d['p']:.4f} | {u['b']} / {u['c']} / {u['p']:.4f} |")
        L += ["\n## Ca bất đồng (đầu vào phân tích ca sai)\n"]
        for t, v in kq["bat_dong"].items():
            L.append(f"- **{t}** — CPA² đúng / baseline unsound ({len(v['cpa2_dung_bl_unsound'])}): "
                     f"{', '.join(v['cpa2_dung_bl_unsound']) or '—'}; baseline đúng / CPA² unsound ({len(v['bl_dung_cpa2_unsound'])}): "
                     f"{', '.join(v['bl_dung_cpa2_unsound']) or '—'}")
    return "\n".join(L) + "\n"


def _hau_to(x):
    if not re.fullmatch(r"[A-Za-z0-9_-]*", x):
        raise argparse.ArgumentTypeError("hậu tố chỉ gồm chữ, số, _ và -")
    return x


def main():
    ap = argparse.ArgumentParser(description="Bảng so sánh CPA² vs baseline (Tuần 23)")
    ap.add_argument("--split", choices=["dev", "test"], required=True)
    ap.add_argument("--cpa2-hau-to", default="", type=_hau_to)
    ap.add_argument("--ra", action="store_true", help="ghi bang_so_sanh_<split>.md/.json vào w23_so_sanh/")
    a = ap.parse_args()
    try:
        kq = so_sanh(a.split, cpa2_hau_to=a.cpa2_hau_to)
    except (ValueError, FileNotFoundError) as e:
        print(f"Dừng: {e}")
        return 2
    md = bao_cao(kq)
    print(md)
    if a.ra:
        (HERE / f"bang_so_sanh_{a.split}.md").write_bytes(md.encode("utf-8"))
        (HERE / f"bang_so_sanh_{a.split}.json").write_bytes(json.dumps(kq, ensure_ascii=False, indent=1).encode("utf-8"))
        print(f"Đã ghi bang_so_sanh_{a.split}.md/.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
