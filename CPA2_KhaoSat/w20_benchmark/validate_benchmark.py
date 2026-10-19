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
  B10 Q-Noise (TỔNG HỢP, không thay Q-Real): câu gốc = ca G-Truth đi qua parser; V0–V4 kế thừa gold; V1/V4 không
      dấu; giữ mã HP; sinh lại tất định; hash khớp qnoise_dong_bang.json (đóng băng trước lần chạy đầu)

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


TRUONG_KHOA = ("id", "nhom", "he", "claim", "cau_hoi", "dau_vao", "gold", "hk", "su_that", "can_hoi", "cham_diem",
               "split", "loai_gold", "oracle")       # mọi trường ảnh hưởng đầu vào hoặc cách chấm (review Tuần 20)
NGUON_DU_LIEU = ["w7_student_facts/students/" + n + ".json" for n in
                 ("sv_5hp", "sv_du_hp", "sv_lvtn", "sv_mien_ielts", "sv_tltn", "sv_tron_ngoai_ngu")] + \
                ["w6_curriculum/curriculum_cntt_k49.json"]


def hash_gold(cases):
    lo = [{k: c.get(k) for k in TRUONG_KHOA} for c in sorted(cases, key=lambda c: c["id"])]
    return hashlib.sha256(json.dumps(lo, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def hash_ca(cases):
    """Hash toàn bộ trường của mọi ca (Q-Noise: goc/bien_the/claim_ky_vong cũng quyết định cách chấm — review)."""
    lo = sorted(cases, key=lambda c: c["id"])
    return hashlib.sha256(json.dumps(lo, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def hash_nguon():
    return {f: hashlib.sha256((ROOT / f).read_bytes().replace(b"\r\n", b"\n")).hexdigest() for f in NGUON_DU_LIEU}


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
        for ma in re.findall(r"[A-Z]{2}\d{3}E?", cl):        # mã HP trong claim phải có trong CTĐT (trừ ca thiết kế ngoài KB)
            if ma not in oracle._CT and c.get("loai_gold") != "thiet_ke":
                sai.append((c["id"], ma))
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
              f"B6a hash gold (mọi trường ảnh hưởng đầu vào/chấm điểm) khớp bản đóng băng (commit {db.get('commit', '?')})")
        check(db.get("nguon_du_lieu") == hash_nguon(), "B6b hồ sơ gốc + CTĐT mà ca tham chiếu không đổi kể từ đóng băng")
    except FileNotFoundError:
        check(False, "B6 có gold_dong_bang.json")

    print("\nB7–B8. ĐẦU VÀO CPA² VÀ BASELINE")
    import baseline
    loi, lo = [], []
    for c in tat_ca:
        try:
            dau_vao.vat_lieu_hoa(c)
            b = json.dumps(baseline.dau_vao_baseline(c), ensure_ascii=False)
            if (re.search(r'"(gold|ly_do|nguon|su_that|oracle|can_hoi|nhom|loai_gold)"', b)
                    or re.search(r"sv_(lvtn|tltn|5hp|du_hp|mien_ielts|tron_ngoai_ngu)", b) or c["id"] in b):
                lo.append(c["id"])
        except Exception as e:  # noqa: BLE001
            loi.append((c["id"], f"{type(e).__name__}: {e}"))
    check(not loi, f"B7 mọi ca dựng được đầu vào ({loi[:3]})")
    check(not lo, f"B8 đầu vào baseline không lộ gold/lý do/nguồn/tên hồ sơ gốc ({lo[:5]})")

    print("\nB9. Q-REAL")
    import nhap_qreal as Q
    mau = ["Em  đăng ký CT180 được chưa ạ? MSSV B2306555", "em đăng ký ct180 được chưa ạ? mssv b2306555",
           "Liên hệ em qua loi@student.ctu.edu.vn hoặc 0912 345 678, em còn thiếu môn gì?", "",
           "Em lớp DI20V7A1, fb.com/nguyenvanan.99 và facebook.com/profile.php?id=100012345678, mã số sinh viên là B2306555, em tốt nghiệp được chưa?",
           "MSSV B 2306555 hỏi: em còn 0123456789 tín chỉ thì sao?"]
    ra = Q.chuan_hoa_danh_sach([{"cau_hoi": x, "nguon": "Nhóm FB Lớp DI20V7A1"} for x in mau])
    txt = json.dumps(ra, ensure_ascii=False)
    check(len(ra) == 4 and not re.search(r"2306555|@|0912|DI20V7A1|nguyenvanan|100012345678", txt, re.I)
          and "[MSSV] [MSSV" not in txt and "0123456789 tín chỉ" in txt and all(r["split"] in ("dev", "test") for r in ra),
          f"B9a nhập Q-Real: ẩn danh MSSV (cả có dấu cách)/email/SĐT/mã lớp/link FB, không nuốt số thường, khử trùng, chia split",
          txt[:300] if not len(ra) == 4 else "")
    check(Q.bo_qua_da_xoa([{"id": "QR-1"}, {"id": "QR-2"}], {"QR-2"}) == [{"id": "QR-1"}],
          "B9b câu đã xoá tay (meta.da_xoa) không bị nhập lại")
    qr = Q.doc_qreal()
    n_ = len(qr)
    print(f"     Q-Real hiện có {n_} câu thật — mục tiêu 400–600: {'ĐẠT' if n_ >= 400 else 'CHƯA ĐẠT'} ({n_}/400)")
    kiem_qnoise(gt)
    kiem_qelicit()
    return ket_thuc()


def kiem_qelicit():
    """B11 — Q-Elicit (kịch bản → sinh viên tự viết câu hỏi) + biểu mẫu thu Q-Real. Câu elicit KHÔNG tính vào Q-Real."""
    print("\nB11. Q-ELICIT + BIỂU MẪU (câu elicit báo riêng, KHÔNG tính vào chỉ tiêu 400 câu tự nhiên)")
    try:
        import build_bieu_mau as BM
        import nhap_qreal as Q
        import prototype
        kb = BM.doc_kich_ban()
    except (ImportError, FileNotFoundError, AttributeError) as e:
        check(False, f"B11 có build_bieu_mau.py, qreal/kich_ban_q_elicit.json và nhập biểu mẫu ({e})")
        return
    ds = kb["kich_ban"]
    thieu = [k.get("id") for k in ds if not all(k.get(t) not in (None, "") for t in ("id", "bo", "y_dinh", "tinh_huong", "split"))
             or k["y_dinh"] not in Q.Y_DINH or k["split"] not in ("dev", "test") or "can_ho_so" not in k]
    bo = Counter(k["bo"] for k in ds)
    check(len(ds) >= 20 and not thieu and len({k["id"] for k in ds}) == len(ds) and len(bo) == 4 and min(bo.values()) >= 5,
          f"B11a ≥ 20 kịch bản, 4 bộ × ≥ 5, đủ trường, ý định hợp lệ ({len(ds)}; bộ {dict(bo)}; lỗi {thieu[:4]})")
    phu = {k["y_dinh"] for k in ds}
    check(phu == set(Q.Y_DINH), f"B11b phủ MỌI ý định, có ngoài phạm vi (thiếu {sorted(set(Q.Y_DINH) - phu)})")
    mom = [(k["id"], m) for k in ds for m in BM.mom(k["tinh_huong"])]
    tu_nhan = [(k["id"], prototype.parse_question(k["tinh_huong"])) for k in ds]
    tu_nhan = [x for x in tu_nhan if x[1] != "khong_ro"]
    check(not mom and not tu_nhan,
          f"B11c chống mớm lời: tình huống không chứa cụm từ parser dựa vào, và parser KHÔNG tự nhận ra ý định từ chính "
          f"tình huống ({mom[:3]} {tu_nhan[:3]})")
    theo_y = defaultdict(set)
    for k in ds:
        theo_y[k["y_dinh"]].add(k["split"])
    lech = [y for y, v in theo_y.items() if sum(k["y_dinh"] == y for k in ds) >= 2 and v != {"dev", "test"}]
    n_test = sum(k["split"] == "test" for k in ds)
    check(not lech and 8 <= n_test <= len(ds) - 8,
          f"B11d chia dev/test THEO KỊCH BẢN; ý định có ≥ 2 kịch bản thì có ở cả hai phía ({lech}; test {n_test})")
    bm = (HERE / "qreal" / "bieu_mau.md").read_text(encoding="utf-8") if (HERE / "qreal" / "bieu_mau.md").exists() else ""
    tieu_de = re.findall(r"^#+ .*?(\[[A-Z_]+(?:-\d+)?\])", bm, re.M)
    vt = {t: i for i, t in enumerate(tieu_de)}
    check(bm == BM.sinh_bieu_mau(kb) and {f"[{k['id']}]" for k in ds} <= set(tieu_de)
          and {"[DONG_Y]", "[BO]", "[MA_RUT]", "[TU_DO-1]", "[TU_DO-2]", "[TU_DO-3]"} <= set(tieu_de)
          and not re.search(r"^#+ .*(?:mssv|mã số|\btên\b|email|điện thoại|tháng sinh|ngày sinh)", bm, re.I | re.M),
          "B11e bieu_mau.md sinh từ kịch bản (đồng bộ); đủ câu đồng ý/mã rút lại/chọn bộ/kịch bản/câu tự do; KHÔNG hỏi "
          "tên, MSSV, email, SĐT, ngày/tháng sinh")
    if {"[TU_DO-1]", "[BO]"} <= set(vt) and "## Tiêu đề" in bm:
        doc_truoc = bm[bm.index("## Tiêu đề"):bm.index("### [BO]")]   # chữ người trả lời THẬT SỰ đọc trước câu tự do
        check(vt["[TU_DO-1]"] < vt["[BO]"] < min(vt.get(f"[{k['id']}]", 10**6) for k in ds) and not BM.mom(doc_truoc),
              f"B11e2 câu tự do (Q-Real) hỏi TRƯỚC mọi kịch bản; chữ đọc trước nó không chứa cụm từ parser ({BM.mom(doc_truoc)})")
    dy = bm[bm.index("[DONG_Y]"):bm.index("### [MA_RUT]")] if "### [MA_RUT]" in bm and "[DONG_Y]" in bm else ""
    check(all(re.search(x, dy, re.I) for x in (r"<<ĐIỀN", r"liên hệ", r"github|công khai", r"dịch vụ AI|OpenAI|Gemini",
                                               r"bản thô[^.]*xo[áa]", r"mã rút", r"tự nguyện", r"không thể thu hồi",
                                               r"lịch sử")) and not re.search(r"mã hoá|mã hóa|mọi câu \(trừ câu này\)", bm),
          "B11e3 phần đồng ý (NĐ 13/2023) nói ĐÚNG: người thu + liên hệ (chỗ điền), mục đích, kho mã công khai + dịch vụ AI, "
          "thời hạn xoá bản thô, rút lại bằng mã tự đặt và GIỚI HẠN của việc rút (lịch sử git, dịch vụ AI), tự nguyện")
    import csv, tempfile
    k1, k2 = ds[0], ds[1]
    hang = [["Dấu thời gian", "2. [DONG_Y] Đồng ý ", "[MA_RUT] Mã", "[BO] Bộ", f" [{k1['id']}] …", f"[{k2['id']}] … (2)",
             "[KB-99] lạ", "[TU_DO-1] …", "[TU_DO-2] …"],
            ["1", "Tôi đồng ý.", "x7k2m9", "1", "e dk ct180 dc ko ad", "  ", "câu kịch bản lạ", "MSSV B2306555 hỏi: học phí kỳ hè tính sao ạ?", ""],
            ["2", "Không đồng ý", "", "1", "câu của người KHÔNG đồng ý phải bị loại", "", "", "người không đồng ý hỏi", ""],
            ["3", "Tôi đồng ý", "Q8w2Lp", "1", "E DK CT180 DC KO AD", "em muốn hỏi xíu về chuyện này nha", "", "",
             "câu một nè?\ncâu hai nữa?"],
            ["4", "Tôi đồng ý", "ab1", "2", "", "", "", "câu của người đặt mã quá ngắn nè", ""]]
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "_tho").mkdir()
        with open(d / "_tho" / "bieu_mau_xuat.csv", "w", encoding="utf-8-sig", newline="") as fh:
            csv.writer(fh).writerows(hang)
        (d / "_tho" / "ban_be.txt").write_text("em đăng ký ct180 được không ạ\n", encoding="utf-8")
        (d / "_tho" / "khong_dung_cot.csv").write_text("cau hoi\nmột câu sai tên cột\n", encoding="utf-8")
        (d / "_tho" / "bang.xlsx").write_bytes(b"x")
        out, el_f, th = d / "qreal.json", d / "qelicit.json", d / "_tho"
        n_tn, n_el, cb = Q.nhap(th, out, el_f)
        tn, el = Q.doc_qreal(out), Q.doc_elicit(el_f)
        cong_khai = out.read_text(encoding="utf-8") + el_f.read_text(encoding="utf-8")
        r1 = Q.rut("x7k2m9", out, el_f, th)
        tn1, el1 = Q.doc_qreal(out), Q.doc_elicit(el_f)
        r_hoa = Q.rut("X7K2M9", out, el_f, th)
        r2 = Q.rut("Q8w2Lp", out, el_f, th)
        tn2, el2 = Q.doc_qreal(out), Q.doc_elicit(el_f)
        Q.nhap(th, out, el_f)                     # nhập lại: câu đã rút KHÔNG quay lại
        tn3, el3 = Q.doc_qreal(out), Q.doc_elicit(el_f)
    txt = json.dumps([tn, el], ensure_ascii=False)
    theo = {k["id"]: k for k in ds}
    ok = (len(el) == 2 and {e["kich_ban"] for e in el} == {k1["id"], k2["id"]}
          and all(e["y_dinh_kich_ban"] == theo[e["kich_ban"]]["y_dinh"] and e["split"] == theo[e["kich_ban"]]["split"]
                  and e["id"].startswith("QE-") for e in el)
          and len(tn) == 4 and {x["nguon"] for x in tn} == {"bieu_mau", "ban_be"}
          and any("[MSSV]" in x["cau_hoi"] for x in tn) and any(x.get("nhieu_cau") for x in tn)
          and not any(x.get("kich_ban") for x in tn) and "e dk ct180" not in json.dumps(tn, ensure_ascii=False)
          and "học phí" not in json.dumps(el, ensure_ascii=False)
          and "KHÔNG đồng ý" not in txt and "không đồng ý hỏi" not in txt and "2306555" not in txt
          and not re.search(r'x7k2m9|Q8w2Lp|"ma_rut|"_chu"', cong_khai)
          and all(any(w in c for c in cb) for w in ("KB-99", "ab1", "khong_dung_cot.csv", "bang.xlsx")))
    check(ok, "B11f nhập đầu–cuối (mẫu GIẢ, thư mục tạm): tiêu đề có tiền tố, 'Tôi đồng ý.'; loại người không đồng ý; "
              "elicit → qelicit.json, tự do + .txt → qreal.json, KHÔNG lẫn hai nguồn; ẩn danh; đánh dấu ô nhiều câu; mã rút "
              "KHÔNG nằm trong file công khai; cảnh báo mã kịch bản lạ, mã rút quá ngắn, CSV sai cột, file lạ",
          "" if ok else txt[:300] + f" | cảnh báo {cb}")
    check(r1 == 1 and len(tn1) == 3 and len(el1) == 2 and r_hoa == 0 and r2 == 3 and len(tn2) == 2 and len(el2) == 0
          and len(tn3) == 2 and len(el3) == 0,
          f"B11g rút lại: mã phân biệt hoa/thường; câu TRÙNG của người khác vẫn giữ tới khi họ cũng rút; nhập lại không "
          f"thêm lại ({r1}, {r_hoa}, {r2}; {len(tn1)}/{len(el1)} → {len(tn2)}/{len(el2)} → {len(tn3)}/{len(el3)})")
    try:
        db = json.loads((HERE / "qreal" / "kich_ban_dong_bang.json").read_text(encoding="utf-8"))
        check(db.get("kich_ban") == BM.hash_kich_ban(kb), "B11h kịch bản ĐÓNG BĂNG trước khi mở biểu mẫu (hash khớp)")
    except FileNotFoundError:
        check(False, "B11h có qreal/kich_ban_dong_bang.json")
    print(f"     Q-Real (tự nhiên) {len(Q.doc_qreal())}/400 — Q-Elicit {len(Q.doc_elicit())} câu (báo riêng, không tính)")


VIET = re.compile(r"[^\x00-\x7f]")


def kiem_qnoise(gt):
    """B10 — Q-Noise v1: câu G-Truth gõ kiểu sinh viên (bỏ dấu, viết tắt, gõ vội). TỔNG HỢP, không phải Q-Real."""
    print("\nB10. Q-NOISE (tổng hợp — đo độ bền parser, KHÔNG thay Q-Real)")
    try:
        import build_qnoise as QN
        qn = json.loads((HERE / "qnoise.json").read_text(encoding="utf-8"))
    except (ImportError, FileNotFoundError) as e:
        check(False, f"B10 có build_qnoise.py và qnoise.json ({e})")
        return
    cs = qn["cases"]
    check(qn["meta"].get("loai") == "tong_hop" and "Q-Real" in qn["meta"].get("ghi_chu", ""),
          "B10a nhãn TỔNG HỢP, ghi rõ không thay Q-Real")
    goc = {c["id"]: c for c in gt}
    chon = {c["id"] for c in gt if QN.la_goc(c)}
    check(chon and chon == {c["goc"] for c in cs},
          f"B10b câu gốc = mọi ca G-Truth đi qua parser, không dữ kiện mở ({len(chon)} ca)")
    bt = defaultdict(set)
    for c in cs:
        bt[c["goc"]].add(c["bien_the"])
    check(all(v == set(QN.BIEN_THE) for v in bt.values()) and len({c["id"] for c in cs}) == len(cs),
          f"B10c mỗi câu gốc đủ biến thể {QN.BIEN_THE}, id không trùng ({len(cs)} câu)")
    ke = [c["id"] for c in cs if c["he"] != "nl" or any(c.get(k) != goc[c["goc"]].get(k) for k in QN.KE_THUA)
          or c["id"] != f"QN-{c['goc']}-{c['bien_the']}" or c["claim_goc"] != goc[c["goc"]]["claim"]]
    check(not ke, f"B10d gold/split/đầu vào KẾ THỪA nguyên từ ca gốc đã đóng băng; id = QN-gốc-biến thể ({ke[:4]})")
    yd = [c["id"] for c in cs if c.get("claim_ky_vong") != QN.y_dinh(goc[c["goc"]])
          or any(x in QN.TU_CHOI for x in c["claim_ky_vong"])]
    check(not yd and set(QN.Y_DINH_NL) == {i for i in chon if goc[i]["he"] == "nl"},
          f"B10h mỗi câu có ý định kỳ vọng (claim parser phải sinh; rỗng = phải từ chối), câu nl gán tay đủ ({yd[:4]})")
    v = {(c["goc"], c["bien_the"]): c["cau_hoi"] for c in cs}
    xau = []
    for c in cs:
        q0 = goc[c["goc"]]["cau_hoi"]
        q = c["cau_hoi"]
        ma0 = sorted(m.upper() for m in re.findall(r"[A-Za-z]{2}\d{3}[Ee]?", q0))
        if (c["bien_the"] == "V0") != (q == q0) or sorted(m.upper() for m in re.findall(r"[A-Za-z]{2}\d{3}[Ee]?", q)) != ma0:
            xau.append((c["id"], "V0/mã HP"))
        if c["bien_the"] in ("V1", "V4") and VIET.search(q):
            xau.append((c["id"], "còn dấu"))
        if c["bien_the"] == "V1" and QN.ma_thuong(QN.bo_dau(q0)) != q:
            xau.append((c["id"], "V1 phải chỉ bỏ dấu"))
        if c["bien_the"] == "V4" and QN.bo_dau(v[(c["goc"], "V2")]) != q:
            xau.append((c["id"], "V4 phải = V2 bỏ dấu"))
        if c["bien_the"] != "V0" and re.search(r"[A-Z]{2}\d{3}", q):
            xau.append((c["id"], "mã HP chưa viết thường"))
    check(not xau, f"B10e V0 = câu gốc; V1 = chỉ bỏ dấu; V4 = V2 bỏ dấu; giữ đúng mã HP (viết thường) ({xau[:4]})")
    check(QN.sinh(gt) == cs, "B10f sinh lại tất định (seed theo id) — trùng qnoise.json")
    try:
        db = json.loads((HERE / "qnoise_dong_bang.json").read_text(encoding="utf-8"))
        dbg = json.loads((HERE / "gold_dong_bang.json").read_text(encoding="utf-8"))
        check(db.get("qnoise") == hash_ca(cs) and db.get("gtruth_goc") == dbg["gtruth"] == hash_gold(gt),
              "B10g Q-Noise ĐÓNG BĂNG trước lần chạy đầu (hash TOÀN BỘ ca khớp; G-Truth gốc khớp bản đóng băng)")
    except FileNotFoundError:
        check(False, "B10g có qnoise_dong_bang.json")


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
