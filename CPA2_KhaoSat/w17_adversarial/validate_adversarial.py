"""
validate_adversarial.py — kiểm chứng Adversarial set v1 Tuần 17 (CPA2)

Tiêu chí (Kế hoạch 24 tuần, dòng 17): "≥ 60 case đối kháng".
Test này kiểm BỘ DỮ LIỆU, không chấm CPA² (chấm ở run_adversarial.py, báo cáo trung thực):
  A. Đủ số lượng + đủ 5 nhóm
  B. Mỗi ca có gold, nguồn, lý do, câu hỏi tiếng Việt; id duy nhất
  C. Tách dev/test phân tầng theo nhóm
  D. Đầu vào dựng được: hồ sơ hợp lệ theo schema (trừ nhóm hồ sơ lỗi), tài liệu OCR dựng được
  E. Oracle độc lập (Python thuần, không clingo) khớp tiền đề số học của gold
  F. Ca phụ thuộc diễn giải chưa chốt → không chấm điểm (can_xac_nhan)
  G. Gold đóng băng: file khớp build_adversarial.tao() và khớp gold_dong_bang.json (commit 200b860)

Chạy:  python validate_adversarial.py
"""
import sys, json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

errors = []
OK, FAIL = "  [OK]  ", "  [FAIL]"
NHOM = {"thieu_du_lieu", "sat_nguong", "ocr_sai", "bay_quy_che", "ho_so_loi"}
GOLD = {"TRUE", "FALSE", "UNKNOWN"}


def check(cond, msg, note=""):
    print((OK if cond else FAIL) + " " + msg)
    if note:
        print("          ↳ " + note)
    if not cond:
        errors.append(msg)
    return cond


def main():
    print("=" * 78)
    print("VALIDATE ADVERSARIAL SET v1 — Tuần 17 (CPA2)")
    print("=" * 78)
    p = HERE / "adversarial_set.json"
    if not check(p.exists(), "adversarial_set.json tồn tại (sinh bằng build_adversarial.py)"):
        return ket_thuc()
    ds = json.loads(p.read_text(encoding="utf-8"))
    ca = ds["cases"]
    cham = [c for c in ca if c["cham_diem"]]

    print("\nA. SỐ LƯỢNG")
    check(len(cham) >= 60, f"A1 ≥ 60 ca chấm điểm ({len(cham)})")
    dem = Counter(c["nhom"] for c in cham)
    check(set(dem) == NHOM, f"A2 đủ 5 nhóm ({dict(dem)})")
    check(Counter(c["gold"] for c in cham).keys() == GOLD, f"A3 gold có cả TRUE/FALSE/UNKNOWN ({dict(Counter(c['gold'] for c in cham))})")

    print("\nB. TRƯỜNG BẮT BUỘC")
    ids = [c["id"] for c in ca]
    check(len(ids) == len(set(ids)), "B1 id duy nhất")
    thieu = [c["id"] for c in ca if not all(c.get(k) for k in ("cau_hoi", "claim", "ly_do", "nguon", "dau_vao"))]
    check(not thieu, f"B2 mọi ca có câu hỏi/claim/lý do/nguồn/đầu vào", f"thiếu: {thieu}" if thieu else "")
    sai = [c["id"] for c in ca if c["gold"] not in GOLD or c["nhom"] not in NHOM]
    check(not sai, "B3 gold ∈ {TRUE,FALSE,UNKNOWN}, nhóm hợp lệ", f"{sai}" if sai else "")
    sai = [c["id"] for c in cham if c["gold"] == "UNKNOWN" and c["nhom"] != "ho_so_loi" and c["dau_vao"]["loai"] == "ho_so"
           and not c.get("can_hoi")]
    check(not sai, "B4 ca gold UNKNOWN (hồ sơ) nêu dữ kiện quyết định kỳ vọng (can_hoi)", f"{sai}" if sai else "")
    sai = [c["id"] for c in cham if c.get("su_that") not in (None, "TRUE", "FALSE")
           or (c.get("su_that") and c["gold"] in ("TRUE", "FALSE") and c["su_that"] != c["gold"] and not c.get("khong_phat_hien_duoc"))]
    check(not sai, "B5 su_that nhất quán với gold (trừ ca khong_phat_hien_duoc)", f"{sai}" if sai else "")

    print("\nC. TÁCH DEV/TEST")
    check(all(c["split"] in ("dev", "test") for c in cham), "C1 mọi ca chấm điểm có split dev/test")
    lech = {n: (sum(1 for c in cham if c["nhom"] == n and c["split"] == "dev"),
                sum(1 for c in cham if c["nhom"] == n and c["split"] == "test")) for n in NHOM}
    check(all(d >= 1 and t >= 1 and abs(d - t) <= 1 for d, t in lech.values()),
          f"C2 phân tầng: mỗi nhóm có ở cả dev và test, lệch ≤ 1 ({lech})")

    print("\nD. ĐẦU VÀO DỰNG ĐƯỢC")
    import dau_vao
    import jsonschema
    schema = jsonschema.Draft202012Validator(json.loads(
        (ROOT / "w7_student_facts" / "student_fact_schema.json").read_text(encoding="utf-8")))
    loi_dung, loi_schema = [], []
    for c in ca:
        try:
            v = dau_vao.vat_lieu_hoa(c)
        except Exception as e:  # noqa: BLE001
            loi_dung.append(f"{c['id']}: {e}")
            continue
        if c["dau_vao"]["loai"] == "ho_so" and c["nhom"] != "ho_so_loi":
            if list(schema.iter_errors(v["ho_so"])):
                loi_schema.append(c["id"])
    check(not loi_dung, "D1 dựng được đầu vào của mọi ca", "; ".join(loi_dung[:3]))
    check(not loi_schema, "D2 hồ sơ (ngoài nhóm hồ sơ lỗi) hợp lệ theo student_fact_schema", f"{loi_schema}" if loi_schema else "")
    dien = [c["id"] for c in ca if c["dau_vao"]["loai"] == "ho_so" and not dau_vao.mo_ta_cho_nguoi(c)]
    check(not dien, "D3 mọi ca hồ sơ có mô tả tiếng Việt (để chạy baseline LLM Tuần 21)", f"{dien}" if dien else "")

    print("\nE. ORACLE ĐỘC LẬP ↔ TIỀN ĐỀ CỦA GOLD")
    import oracle
    co = [c for c in ca if c.get("oracle")]
    lech = []
    for c in co:
        thuc = oracle.tinh(dau_vao.vat_lieu_hoa(c)["ho_so_that"])
        for k, v in c["oracle"].items():
            if str(thuc[k]) != str(v):
                lech.append(f"{c['id']}.{k}: gold ghi {v}, oracle tính {thuc[k]}")
    check(len(co) >= 15, f"E1 ≥ 15 ca có tiền đề số học kiểm bằng oracle ({len(co)})")
    check(not lech, "E2 oracle khớp mọi tiền đề", "; ".join(lech[:4]))
    bq05 = next(c for c in ca if c["id"] == "BQ-05")
    f = oracle.tinh(dau_vao.vat_lieu_hoa(bq05)["ho_so_that"])["dtbctl_tinh_ca_F"]
    check(f < 2, f"E3 BQ-05 là bẫy thật: tính cả điểm F thì ĐTBCTL = {float(f):.3f} < 2 (đúng là 2,00)")

    print("\nF. CA KHÔNG CHẤM ĐIỂM")
    kc = [c for c in ca if not c["cham_diem"]]
    check(all(c.get("ly_do_khong_cham") for c in kc), f"F1 {len(kc)} ca không chấm đều ghi lý do")

    print("\nG. GOLD ĐÓNG BĂNG")
    import build_adversarial
    check(build_adversarial.tao() == ds, "G1 adversarial_set.json khớp đúng đầu ra build_adversarial.py (không sửa tay)")
    db = json.loads((HERE / "gold_dong_bang.json").read_text(encoding="utf-8"))
    khac = [i for i, g in db["gold"].items()
            if {k: next(c for c in ca if c["id"] == i).get(k) for k in g} != g] + [c["id"] for c in ca if c["id"] not in db["gold"]]
    check(not khac, f"G2 gold/su_that/cham_diem/split/can_hoi khớp bản đóng băng commit {db['commit']}",
          f"khác: {khac}" if khac else "")
    return ket_thuc()


def ket_thuc():
    print("\n" + "=" * 78)
    if errors:
        print(f"KẾT LUẬN: CÓ {len(errors)} LỖI")
        for e in errors:
            print("  ·", e)
        return 1
    print("KẾT LUẬN: ĐẠT — Adversarial set đủ ≥ 60 ca, có gold + nguồn + dev/test, oracle khớp")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
