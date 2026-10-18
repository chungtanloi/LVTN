"""
eligibility.py — Eligibility module v1 (CPA2, Tuần 18)

  xet(ho_so, doi_tuong, them="") → {
      ket_qua:      ELIGIBLE | NOT_ELIGIBLE | UNKNOWN | DA_HOAN_THANH | MAU_THUAN
      ly_do:        atom lý do không đủ (thieu_tc/2, thieu_tien_quyet/2, dv_cong_bo_khac/1) — đúng trong MỌI thế giới
      chung_chi:    [{atom, rule_id, nguon}] — why/2 → catalog R-Formal (văn bản, điều, khoản)
      can_bo_sung:  dữ kiện mở QUYẾT ĐỊNH kết luận (engine w16) — vd. đơn vị đã công bố hình thức chưa
      mau_thuan:    bản ghi hồ sơ tự mâu thuẫn (loader chung, P17-1)
  }
  doi_tuong: lvtn · tltn · nien_luan · nien_luan_co_so · thuc_tap · tich_luy_tc · thay_the:<MÃ HP>

Ba trị như Tuần 16: chỉ ELIGIBLE / NOT_ELIGIBLE khi đúng trong mọi thế giới; còn lại UNKNOWN, không đoán.

Chạy:  python eligibility.py --student ../w7_student_facts/students/sv_lvtn.json --doi-tuong lvtn
"""
import argparse, json, re, sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "w16_abstention"))
import abstention as A

LP = HERE / "eligibility.lp"
CATALOG = ROOT / "w5_rformal" / "r_formal_v1.json"
DOI_TUONG = ("lvtn", "tltn", "nien_luan", "nien_luan_co_so", "thuc_tap", "tich_luy_tc")


_LP = LP.read_text(encoding="utf-8")
_MA = dict(re.findall(r'doi_tuong\((\w+),\s*("[^"]+")\)', _LP))       # đối tượng → mã HP (có ngoặc kép)
_CT = {h["ma"] for h in json.loads((ROOT / "w6_curriculum" / "curriculum_cntt_k49.json")
                                   .read_text(encoding="utf-8"))["hoc_phan"]}
_NGUON = None


def _atom(doi_tuong):
    if doi_tuong.startswith("thay_the:"):
        ma = doi_tuong.split(":", 1)[1]
        if ma not in _CT:
            raise ValueError(f"mã HP thay thế không có trong CTĐT K49: {ma!r}")
        return f'thay_the("{ma}")'
    if doi_tuong not in DOI_TUONG:
        raise ValueError(f"đối tượng lạ: {doi_tuong} (hợp lệ: {DOI_TUONG} hoặc thay_the:<MÃ>)")
    return doi_tuong


def _nguon():
    global _NGUON
    if _NGUON is None:
        cat = json.loads(CATALOG.read_text(encoding="utf-8"))
        _NGUON = {r["asp"]: r for r in cat["rules"] if r.get("asp")}
    return _NGUON


def xet(ho_so, doi_tuong, them=""):
    x = _atom(doi_tuong)
    asp, mt = A.sang_asp(ho_so)
    models = A.giai(asp + "\n" + _LP + f"\ndang_xet({x}).\n" + them)
    if not models:
        return {"doi_tuong": doi_tuong, "ket_qua": "MAU_THUAN", "ly_do": [], "chung_chi": [], "can_bo_sung": [],
                "mau_thuan": mt}
    claim = f"du_dk({x})"
    if A.ba_tri(f"da_hoan_thanh({x})", models) == "TRUE":
        kq = "DA_HOAN_THANH"
    else:
        kq = {"TRUE": "ELIGIBLE", "FALSE": "NOT_ELIGIBLE", "UNKNOWN": "UNKNOWN"}[A.ba_tri(claim, models)]
    chung = frozenset.intersection(*models)              # đúng trong MỌI thế giới
    ma = _MA.get(x)
    ly_do = sorted(a for a in chung if (ma and (a.startswith(f"thieu_tc({ma},") or a.startswith(f"thieu_tien_quyet({ma},")))
                   or a == f"dv_cong_bo_khac({x})")
    src = _nguon()
    dich = {claim, f"da_hoan_thanh({x})", *ly_do}
    chung_chi = []
    for a in sorted(chung):
        k = re.match(r"why\((.+),(\w+)\)$", a)
        if k and k.group(1) in dich and k.group(2) in src:
            r = src[k.group(2)]
            chung_chi.append({"atom": k.group(1), "rule_id": k.group(2),
                              "nguon": f"{r['van_ban']} Điều {r['dieu']}" + (f" khoản {r['khoan']}" if r.get("khoan") else "")})
    can = A.bang_chung_thieu(claim, models) if kq == "UNKNOWN" else []
    return {"doi_tuong": doi_tuong, "ket_qua": kq, "ly_do": ly_do, "chung_chi": chung_chi, "can_bo_sung": can,
            "mau_thuan": mt}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--student", required=True)
    ap.add_argument("--doi-tuong", default="lvtn")
    a = ap.parse_args()
    print(json.dumps(xet(json.loads(Path(a.student).read_text(encoding="utf-8")), a.doi_tuong),
                     ensure_ascii=False, indent=2))
