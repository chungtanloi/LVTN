"""
validate_benchmark.py — kiểm chứng bộ đánh giá Tuần 20 (CPA2): G-Truth v1, OCR-Noise v1, Q-Real, đầu vào baseline

Tiêu chí (Kế hoạch 24 tuần, dòng 20): "Có ground truth". Kiểm:
  B1  đủ số ca (G-Truth ≥ 110, OCR-Noise ≥ 40) · mỗi ca đủ trường, gold ∈ {TRUE, FALSE, UNKNOWN}, có lý do + nguồn
  B2  claim tồn tại: vị từ có đầu luật trong KB (chống P18-1: claim không ai suy ra → luôn FALSE im lặng);
      đối tượng eligibility / recommendation / câu tự nhiên đúng định dạng
  B3  tiền đề số học (trường "oracle") khớp oracle Python độc lập (w17/oracle.py — không clingo, không đọc .lp)
  B4  dev/test: không giao, mỗi nhóm có cả hai, lệch ≤ 1
  B5  không trùng: không trùng ca nào của w17 (cùng claim + cùng đầu vào), không trùng nội bộ
  B6  gold ĐÓNG BĂNG: hash gold khớp gold_dong_bang.json (commit trước lần chạy đầu)
  B7  mọi ca dựng được đầu vào (hồ sơ / tài liệu OCR)
  B8  đầu vào baseline KHÔNG lộ đáp án (không gold/lý do/nguồn/sự thật, không tên hồ sơ gốc)
  B9  Q-Real: pipeline nhập (NFC, ẩn danh MSSV/email/SĐT, khử trùng, chia split) chạy đúng trên mẫu; báo số câu
      thật hiện có so với mục tiêu 400 (không chặn KẾT LUẬN — dữ liệu do Loi cung cấp)

Chạy:  python validate_benchmark.py
"""
import hashlib, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "w17_adversarial"))

errors = []
OK, FAIL = "  [OK]  ", "  [FAIL]"


def check(cond, msg, note=""):
    print((OK if cond else FAIL) + " " + msg)
    if note:
        print("          ↳ " + note)
    if not cond:
        errors.append(msg)
    return cond


KB = [ROOT / "w5_rformal" / "qd3266_r_formal_v1.lp", ROOT / "w5_rformal" / "qd5339_r_formal_v1.lp",
      ROOT / "w6_curriculum" / "curriculum_schema.lp", ROOT / "w8_elective" / "elective_solver.lp",
      ROOT / "w9_exemption" / "exemption_substitution_solver.lp", ROOT / "w10_graduation" / "graduation_solver.lp"]
HE = {"kb", "elig", "rec", "nl", "ocr"}
ELIG = {"lvtn", "tltn", "nien_luan", "nien_luan_co_so", "thuc_tap", "tich_luy_tc"}


def dau_luat():
    s = "\n".join(p.read_text(encoding="utf-8") for p in KB)
    return set(re.findall(r"^\s*([a-z_][a-z0-9_]*)\s*(?:\(|:-)", s, re.M))


def hash_gold(cases):
    lo = [[c["id"], c["he"], c["claim"], c["dau_vao"], c["gold"]] for c in sorted(cases, key=lambda c: c["id"])]
    return hashlib.sha256(json.dumps(lo, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def main():
    print("=" * 78)
    print("VALIDATE BENCHMARK — Tuần 20 (CPA2): G-Truth v1 · OCR-Noise v1 · Q-Real · baseline")
    print("=" * 78)
    try:
        gt = json.loads((HERE / "gtruth.json").read_text(encoding="utf-8"))["cases"]
        on = json.loads((HERE / "ocr_noise.json").read_text(encoding="utf-8"))["cases"]
    except FileNotFoundError as e:
        check(False, f"B0 có gtruth.json và ocr_noise.json ({e.filename})")
        return ket_thuc()
    import oracle, dau_vao
    tat_ca = gt + on

    print("\nB1. SỐ LƯỢNG VÀ TRƯỜNG")
    check(len(gt) >= 110, f"B1a G-Truth ≥ 110 ca ({len(gt)})")
    check(len(on) >= 40, f"B1b OCR-Noise ≥ 40 ca ({len(on)})")
    thieu = [c.get("id") for c in tat_ca if not all(c.get(k) for k in ("id", "nhom", "he", "claim", "gold", "ly_do", "nguon", "split"))
             or c["gold"] not in ("TRUE", "FALSE", "UNKNOWN") or c["he"] not in HE]
    check(not thieu, f"B1c mỗi ca đủ id/nhóm/hệ/claim/gold/lý do/nguồn/split, gold ba trị ({thieu[:5]})")
    check(len({c["id"] for c in tat_ca}) == len(tat_ca), "B1d id không trùng")
    check(all(c.get("loai_gold") in ("quy_che", "thiet_ke") for c in tat_ca),
          "B1e mỗi ca ghi loại gold: theo quy chế hay theo nguyên tắc thiết kế (báo cáo tách riêng)")
    print("     phân bố G-Truth:", dict(Counter(c["nhom"] for c in gt)), "· gold:", dict(Counter(c["gold"] for c in gt)))

    print("\nB2. CLAIM TỒN TẠI (chống P18-1)")
    dau = dau_luat()
    sai = []
    for c in tat_ca:
        cl = c["claim"]
        if c["he"] in ("kb", "ocr"):
            if cl.split("(")[0] not in dau:
                sai.append((c["id"], cl))
        elif c["he"] == "elig":
            if not (cl in ELIG or re.fullmatch(r"thay_the:[A-Z]{2}\d{3}E?", cl)):
                sai.append((c["id"], cl))
        elif c["he"] == "rec":
            if not re.fullmatch(r"(khong_de_xuat:[A-Z]{2}\d{3}E?|tong_tc_le_20)@[123]", cl):
                sai.append((c["id"], cl))
        elif c["he"] == "nl" and not c.get("cau_hoi"):
            sai.append((c["id"], "thiếu câu hỏi"))
    check(not sai, f"B2 mọi claim có vị từ đầu luật trong KB / đúng định dạng ({sai[:5]})")

    print("\nB3. TIỀN ĐỀ SỐ HỌC — oracle độc lập")
    lech, n = [], 0
    for c in tat_ca:
        if not c.get("oracle"):
            continue
        that = dau_vao.vat_lieu_hoa(c)["ho_so_that"]
        t = oracle.tinh(that)
        for k, v in c["oracle"].items():
            n += 1
            tv = t[k]
            if (str(tv) if not isinstance(tv, bool) and tv is not None else tv) != v:
                lech.append((c["id"], k, v, str(tv)))
    check(n >= 25 and not lech, f"B3 {n} tiền đề khớp oracle (≥ 25)", f"lệch: {lech[:4]}" if lech else "")

    print("\nB4. DEV / TEST")
    for ten, bo in (("G-Truth", gt), ("OCR-Noise", on)):
        theo = defaultdict(Counter)
        for c in bo:
            theo[c["nhom"]][c["split"]] += 1
        xau = {k: dict(v) for k, v in theo.items() if not (v["dev"] and v["test"]) or abs(v["dev"] - v["test"]) > 1}
        check(not xau and set(c["split"] for c in bo) == {"dev", "test"},
              f"B4 {ten}: mỗi nhóm có dev và test, lệch ≤ 1 ({xau})")

    print("\nB5. KHÔNG TRÙNG")
    def khoa(c):
        v = dau_vao.vat_lieu_hoa(c)
        return c["claim"] + "|" + json.dumps({k: v.get(k) for k in ("ho_so", "doc", "khong_chac", "mien_chua_ro", "khai_bao")},
                                             ensure_ascii=False, sort_keys=True) + "|" + str(c.get("hk", "")) + "|" + c.get("cau_hoi", "") * (c.get("he") == "nl")
    w17 = json.loads((ROOT / "w17_adversarial" / "adversarial_set.json").read_text(encoding="utf-8"))["cases"]
    k17 = {khoa(c) for c in w17 if c["dau_vao"]["loai"] in ("ho_so", "ocr_doc")}
    kk = [khoa(c) for c in tat_ca]
    check(not [c["id"] for c, k in zip(tat_ca, kk) if k in k17], "B5a không trùng ca nào của w17 (bộ đối kháng đã nhiễm)")
    dup = [k for k, n_ in Counter(kk).items() if n_ > 1]
    check(not dup, f"B5b không trùng nội bộ ({len(dup)} cặp)")

    print("\nB6. GOLD ĐÓNG BĂNG")
    try:
        db = json.loads((HERE / "gold_dong_bang.json").read_text(encoding="utf-8"))
        check(db["gtruth"] == hash_gold(gt) and db["ocr_noise"] == hash_gold(on),
              f"B6 hash gold khớp bản đóng băng (commit {db.get('commit', '?')})")
    except FileNotFoundError:
        check(False, "B6 có gold_dong_bang.json")

    print("\nB7–B8. ĐẦU VÀO CPA² VÀ BASELINE")
    import baseline
    loi, lo = [], []
    for c in tat_ca:
        try:
            dau_vao.vat_lieu_hoa(c)
            b = json.dumps(baseline.dau_vao_baseline(c), ensure_ascii=False)
            if re.search(r'"(gold|ly_do|nguon|su_that|oracle|can_hoi)"', b) or re.search(r"sv_(lvtn|tltn|5hp|du_hp|mien_ielts|tron_ngoai_ngu)", b):
                lo.append(c["id"])
        except Exception as e:  # noqa: BLE001
            loi.append((c["id"], f"{type(e).__name__}: {e}"))
    check(not loi, f"B7 mọi ca dựng được đầu vào ({loi[:3]})")
    check(not lo, f"B8 đầu vào baseline không lộ gold/lý do/nguồn/tên hồ sơ gốc ({lo[:5]})")

    print("\nB9. Q-REAL")
    import nhap_qreal as Q
    mau = ["Em  đăng ký CT180 được chưa ạ? MSSV B2306555", "em đăng ký ct180 được chưa ạ? mssv b2306555",
           "Liên hệ em qua loi@student.ctu.edu.vn hoặc 0912345678, em còn thiếu môn gì?", ""]
    ra = Q.chuan_hoa_danh_sach([{"cau_hoi": x, "nguon": "mau"} for x in mau])
    txt = json.dumps(ra, ensure_ascii=False)
    check(len(ra) == 2 and not re.search(r"B2306555|@|0912345678", txt, re.I) and all(r["split"] in ("dev", "test") for r in ra),
          f"B9a nhập Q-Real: ẩn danh MSSV/email/SĐT, khử trùng, bỏ câu rỗng, chia split ({len(ra)} câu)")
    qr = Q.doc_qreal()
    n_ = len(qr)
    print(f"     Q-Real hiện có {n_} câu thật — mục tiêu 400–600: {'ĐẠT' if n_ >= 400 else 'CHƯA ĐẠT'} ({n_}/400)")
    return ket_thuc()


def ket_thuc():
    print("\n" + "=" * 78)
    if errors:
        print(f"KẾT LUẬN: CÓ {len(errors)} LỖI")
        for e in errors:
            print("  ·", e)
        return 1
    print("KẾT LUẬN: ĐẠT — có ground truth đóng băng, nguồn, oracle, dev/test; đầu vào baseline trung lập")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
