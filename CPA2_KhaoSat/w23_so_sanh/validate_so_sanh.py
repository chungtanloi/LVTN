"""
validate_so_sanh.py — kiểm chứng bảng so sánh CPA² vs baseline (CPA2, Tuần 23).

Chỉ dùng file kết quả GIẢ trong thư mục tạm (ca thật của G-Truth/OCR-Noise, câu trả lời dựng tay) — không gọi API,
không đọc .env, không chạm file kết quả thật.

  S1  ghép theo id_goc, chỉ chấm trên TẬP CA CHUNG; ca thiếu ở một bên được liệt kê
  S2  số liệu = run_adversarial.cham/tong_hop gốc tính độc lập (cùng hàm chấm cho mọi hệ)
  S3  LOI tính là SAI (unsound), không phải từ chối
  S4  baseline khác split → dừng (ValueError / exit ≠ 0)
  S5  baseline không khớp bản đóng băng hoặc có hậu tố → KHÔNG chính thức
  S6  thiếu file baseline → 'chua_chay', không có số
  S7  McNemar chính xác hai phía khớp giá trị tính tay
  S8  dòng CPA² có hậu tố tách khỏi dòng chính thức
  S9  errata chỉ thêm nhóm '[theo errata]', không đổi 'tong'
  S10 nhóm [cau_hoi_ro] = ca có run_baseline.cau_hoi_kem(c) is None
  S11 danh sách bất đồng: CPA² đúng gold mà baseline unsound (và ngược lại)
  S12 CLI trên repo thật khi chưa có file baseline → exit 0, in 'chưa chạy'

Chạy: python validate_so_sanh.py
"""
import json, math, os, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
for d in (HERE, ROOT / "w21_baseline", ROOT / "w17_adversarial", ROOT / "w20_benchmark"):
    sys.path.insert(0, str(d))
import run_baseline as R
from run_adversarial import cham, tong_hop

ok_all = True


def check(cond, msg):
    global ok_all
    print(f"  [{'OK' if cond else 'FAIL'}] {msg}")
    ok_all = ok_all and bool(cond)


try:
    import so_sanh as S
except ImportError as e:            # bước TDD đỏ: chưa có module
    print(f"  [FAIL] import so_sanh: {e}")
    print("\nKẾT LUẬN: CHƯA ĐẠT")
    sys.exit(1)

CA = {v["goc"]["id"]: v for v in R.tai_ca("dev").values()}         # id_goc → {goc, vao, bo}
ERRATA = R._errata()


def ghi_cpa2(d, tra, hau_to=""):
    """tra: {id_goc: (tra_loi, hoi)} → ket_qua_{gtruth,ocr_noise}_dev<hau_to>.json theo định dạng run_cpa2."""
    for bo in ("gtruth", "ocr_noise"):
        ca = [{"id": i, "tra_loi": t, "hoi": h} for i, (t, h) in tra.items() if CA[i]["bo"] == bo]
        (Path(d) / f"ket_qua_{bo}_dev{hau_to}.json").write_text(
            json.dumps({"bo": bo, "split": "dev", "tong_hop": {}, "ca": ca}, ensure_ascii=False), encoding="utf-8")


def ghi_bl(d, ten, tra, meta=None):
    """tra: {id_goc: tra_loi} → ket_qua_baseline_<ten>_dev.json theo định dạng run_baseline (ca + tra_loi_tho)."""
    m = {"bl": ten.split("_")[0], "nha": ten.split("_")[1], "model": "gia-1", "split": "dev", "dong_bang_khop": True,
         "hau_to": "", "usd": 0.12, "qua": None}
    m.update(meta or {})
    ca = [{"id": f"X{k}", "id_goc": i, "tra_loi": t} for k, (i, t) in enumerate(tra.items())]
    tho = [{"id": f"X{k}", "tra_loi": t, "nhan_thieu": False} for k, (i, t) in enumerate(tra.items())]
    f = Path(d) / f"ket_qua_baseline_{ten}_dev{m['hau_to']}.json"
    f.write_text(json.dumps({"meta": m, "tong_hop": {}, "ca": ca, "tra_loi_tho": tho}, ensure_ascii=False), encoding="utf-8")
    return f


def dung_gold(i):
    g = CA[i]["goc"]["gold"]
    return g if g in ("TRUE", "FALSE") else "UNKNOWN"


def sai_gold(i):
    g = CA[i]["goc"]["gold"]
    return "FALSE" if g == "TRUE" else "TRUE"


def tim(kq, ten):
    return next((h for h in kq["he"] if h["ten"] == ten), None)


def main():
    ids = sorted(CA)
    print(f"Tập dev: {len(ids)} ca (G-Truth + OCR-Noise được chấm)")
    with tempfile.TemporaryDirectory() as w20, tempfile.TemporaryDirectory() as bl:
        cpa2 = {i: (dung_gold(i), []) for i in ids}
        ghi_cpa2(w20, cpa2)
        thieu = ids[:2]
        b_tra = {i: dung_gold(i) for i in ids if i not in thieu}
        b_tra[ids[3]] = sai_gold(ids[3])                           # một ca unsound
        b_tra[ids[4]] = "LOI"                                      # một ca LOI
        ghi_bl(bl, "b1_openai", b_tra)
        kq = S.so_sanh("dev", w20_dir=Path(w20), bl_dir=Path(bl))
        c, b = tim(kq, "CPA²"), tim(kq, "b1_openai")
        chung = [i for i in ids if i not in thieu]
        check(c and b and c["nhom"]["tong"]["n"] == b["nhom"]["tong"]["n"] == len(chung),
              f"S1 cả hai hệ chấm trên cùng {len(chung)} ca chung ({c and c['nhom']['tong']['n']}, {b and b['nhom']['tong']['n']})")
        check(sorted(kq["thieu"].get("b1_openai", [])) == sorted(thieu), f"S1 liệt kê ca baseline thiếu ({kq['thieu'].get('b1_openai')})")
        tu_lam = tong_hop([cham(CA[i]["goc"], b_tra[i], []) for i in chung])
        check({k: b["nhom"]["tong"][k] for k in tu_lam if k != "hoi_dung"} == {k: v for k, v in tu_lam.items() if k != "hoi_dung"}
              and b["nhom"]["tong"]["hoi_dung"] is None,
              f"S2 tổng baseline = cham/tong_hop gốc; 'hỏi đúng' không đo được với câu trả lời tự do → None ({b['nhom']['tong']['unsound']} unsound)")
        tu_lam_c = tong_hop([cham(CA[i]["goc"], cpa2[i][0], []) for i in chung])
        check(all(c["nhom"]["tong"][k] == tu_lam_c[k] for k in ("n", "soundness", "unsound", "coverage", "dung_gold", "tu_choi_thua")),
              "S2 tổng CPA² = cham/tong_hop gốc")
        check(b["nhom"]["tong"]["unsound"] == 2 and b["nhom"]["tong"]["loi"] == 1,
              f"S3 LOI tính là unsound: 1 sai gold + 1 LOI = 2 unsound, loi=1 ({b['nhom']['tong']['unsound']}, {b['nhom']['tong'].get('loi')})")
        check(b["chinh_thuc"] is True and c["chinh_thuc"] is True and b["meta"]["model"] == "gia-1" and b["meta"]["usd"] == 0.12,
              "S5 baseline khớp đóng băng, không hậu tố → chính thức; giữ model + USD")
        check(tim(kq, "b2_gemini") and tim(kq, "b2_gemini")["trang_thai"] == "chua_chay" and "nhom" not in tim(kq, "b2_gemini"),
              "S6 thiếu file baseline → 'chua_chay', không có số")
        ro = [i for i in chung if R.cau_hoi_kem(CA[i]["goc"]) is None]
        check(b["nhom"]["[cau_hoi_ro]"]["n"] == len(ro), f"S10 [cau_hoi_ro] = {len(ro)} ca câu hỏi rõ nghĩa ({b['nhom']['[cau_hoi_ro]']['n']})")
        bd = kq["bat_dong"]["b1_openai"]
        check(ids[3] in bd["cpa2_dung_bl_unsound"] and ids[4] in bd["cpa2_dung_bl_unsound"] and not bd["bl_dung_cpa2_unsound"],
              f"S11 bất đồng: 2 ca CPA² đúng / baseline unsound ({bd['cpa2_dung_bl_unsound']})")
        mc = kq["mcnemar"]["b1_openai"]["dung_gold"]
        check(mc["b"] == 0 and mc["c"] == 2 and math.isclose(mc["p"], 0.5), f"S7 McNemar đúng gold trên dữ liệu: b=0, c=2 → p=0,5 ({mc})")

        # S5 không chính thức (review M1–M4)
        ghi_bl(bl, "b2_gemini", {i: dung_gold(i) for i in ids if i not in ids[5:10]}, {"dong_bang_khop": False})
        ghi_bl(bl, "b3_openai", {i: dung_gold(i) for i in ids}, {"hau_to": "_thu"})
        ghi_bl(bl, "b1_gemini", {i: dung_gold(i) for i in ids}, {"hau_to": "sau"})           # hậu tố KHÔNG có '_' (run_baseline cho phép)
        kq = S.so_sanh("dev", w20_dir=Path(w20), bl_dir=Path(bl))
        check(tim(kq, "b2_gemini")["chinh_thuc"] is False, "S5 dong_bang_khop=False → không chính thức")
        h3 = tim(kq, "b3_openai [_thu]")
        check(h3 is not None and h3["chinh_thuc"] is False and h3.get("nhom"), "S5 baseline hậu tố '_thu' → có dòng RIÊNG, không chính thức")
        h1 = tim(kq, "b1_gemini [sau]")
        check(h1 is not None and h1["chinh_thuc"] is False, f"S5b hậu tố không có '_' ('sau') vẫn được đọc, không bị bỏ lặng lẽ ({[h['ten'] for h in kq['he']]})")
        check(tim(kq, "CPA²")["nhom"]["tong"]["n"] == len(chung) and tim(kq, "b2_gemini")["nhom"]["tong"]["n"] == len(chung) - 5,
              f"S1b tập chung chỉ theo hệ CHÍNH THỨC: baseline không chính thức thiếu 5 ca không kéo n của CPA² "
              f"({tim(kq, 'CPA²')['nhom']['tong']['n']}, {tim(kq, 'b2_gemini')['nhom']['tong']['n']})")
        check("b2_gemini [không chính thức]" in kq["mcnemar"] and "b2_gemini" not in kq["mcnemar"]
              and "b2_gemini [không chính thức]" in kq["bat_dong"] and "b1_openai" in kq["mcnemar"],
              f"S5c McNemar / bất đồng gắn nhãn không chính thức ({list(kq['mcnemar'])})")
        (Path(bl) / "ket_qua_baseline_b1_gemini_devsau.json").unlink()

        # S8 dòng CPA² có hậu tố
        ghi_cpa2(w20, {i: ("UNKNOWN", []) for i in ids}, hau_to="_sau_X")
        kq = S.so_sanh("dev", w20_dir=Path(w20), bl_dir=Path(bl), cpa2_hau_to="_sau_X")
        c0, c1 = tim(kq, "CPA²"), tim(kq, "CPA² [_sau_X]")
        check(c0 and c1 and c0["chinh_thuc"] and not c1["chinh_thuc"] and c0["nhom"]["tong"]["coverage"] != c1["nhom"]["tong"]["coverage"],
              "S8 CPA² hậu tố là dòng RIÊNG, không chính thức; dòng chính thức giữ số cũ")

        # S9 errata
        e_ids = [i for i in chung if i in ERRATA]                  # ca errata phải nằm trong tập chung
        if e_ids:
            i = e_ids[0]
            tra = {k: (dung_gold(k), []) for k in ids}
            tra[i] = (ERRATA[i], [])
            ghi_cpa2(w20, tra)
            kq = S.so_sanh("dev", w20_dir=Path(w20), bl_dir=Path(bl))
            c = tim(kq, "CPA²")
            dg_goc = tong_hop([cham(CA[k]["goc"], tra[k][0], []) for k in chung])["dung_gold"]   # b1_openai vẫn thiếu 2 ca → tập chung
            check(c["nhom"]["tong"]["dung_gold"] == dg_goc and "[theo errata]" in c["nhom"]
                  and c["nhom"]["[theo errata]"]["dung_gold"] != dg_goc,
                  f"S9 errata ({i}): 'tong' theo gold đóng băng, '[theo errata]' là dòng thêm")
        else:
            check(False, "S9 tập dev không có ca errata nào để kiểm — đổi ca kiểm")

        # S4 lệch split
        f = ghi_bl(bl, "b1_gemini", {i: dung_gold(i) for i in ids}, {"split": "test"})
        try:
            S.so_sanh("dev", w20_dir=Path(w20), bl_dir=Path(bl))
            loi = None
        except ValueError as e:
            loi = str(e)
        check(loi and "split" in loi, f"S4 file baseline của split khác → ValueError ({loi})")
        f.unlink()

    # S7 McNemar tính tay
    check(math.isclose(S.mcnemar(1, 6), 2 * (1 + 7) / 2 ** 7) and S.mcnemar(0, 0) == 1.0
          and math.isclose(S.mcnemar(10, 0), 2 / 2 ** 10) and S.mcnemar(5, 5) == 1.0,
          f"S7 McNemar chính xác: (1,6)=0,125 · (0,0)=1 · (10,0)≈0,00195 · (5,5)=1 ({S.mcnemar(1, 6)}, {S.mcnemar(10, 0)})")

    # S12 CLI trên repo thật, thư mục baseline rỗng
    with tempfile.TemporaryDirectory() as rong:
        env = {k: v for k, v in os.environ.items() if not k.endswith("_API_KEY")}
        env.update(CPA2_BASELINE_OUT=rong, PYTHONIOENCODING="utf-8", CPA2_ENV_FILE=os.devnull)
        p = subprocess.run([sys.executable, str(HERE / "so_sanh.py"), "--split", "dev"], capture_output=True, text=True,
                           encoding="utf-8", env=env, timeout=600)
        check(p.returncode == 0 and "chưa chạy" in p.stdout and "CPA²" in p.stdout,
              f"S12 CLI không có file baseline → exit 0, in 'chưa chạy' (exit {p.returncode}; {p.stderr[-200:]})")

    print("\nKẾT LUẬN:", "ĐẠT" if ok_all else "CHƯA ĐẠT")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
