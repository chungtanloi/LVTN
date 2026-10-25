"""
nhap_qreal.py — nhập Q-Real: câu hỏi THẬT của sinh viên (CPA2, Tuần 20)

Nguồn do Loi cung cấp (nhóm/diễn đàn SV, câu hỏi bạn bè, log hỏi đáp…). Quy trình:
  1. Đặt file thô vào qreal/_tho/ (KHÔNG commit — .gitignore): .txt (mỗi dòng một câu), .csv (cột cau_hoi[,nguon]),
     .json (danh sách chuỗi hoặc {cau_hoi, nguon}).
  2. python nhap_qreal.py   → chuẩn hoá NFC, gộp khoảng trắng, ẨN DANH (MSSV, email, số điện thoại → [MSSV]/[EMAIL]/[SĐT]),
     bỏ câu rỗng/quá ngắn, khử trùng (không phân biệt hoa thường, dấu câu), gán id + split dev/test theo hash (ổn định).
  3. Rà tay qreal/qreal.json trước khi commit: còn tên người, lớp, chi tiết nhận diện được → sửa câu, hoặc xoá câu và
     thêm id vào meta.da_xoa (lần nhập sau không thêm lại). Chỉ commit câu đã ẩn danh. Script KHÔNG bắt được tên người.
  4. Gán nhãn (tay, TRƯỚC khi chạy hệ thống): y_dinh ∈ {tot_nghiep, dang_ky, du_dk_luan_van, mien, thieu_mon, thieu_tc,
     de_xuat, xep_loai, counterfactual, ngoai_pham_vi, tra_cuu_quy_che}; can_ho_so (câu hỏi cá nhân hoá?);
     ma_hp (nếu có). Gold là nhãn ý định + claim mong đợi — dùng đánh giá parser (B2) và độ phủ (Tuần 22).

Biểu mẫu (Google Form, nội dung ở qreal/bieu_mau.md): CSV xuất từ Google Sheets đặt vào qreal/_tho/ được nhận ra nhờ
cột chứa "[DONG_Y]". Chỉ lấy dòng "Tôi đồng ý". Cột [TU_DO-n] → Q-Real (nguồn bieu_mau). Cột [KB-xx] → Q-Elicit, ghi
RIÊNG ở qreal/qelicit.json, kèm kịch bản + ý định gán trước + split theo kịch bản. Câu elicit KHÔNG tính vào chỉ tiêu
400 câu tự nhiên (Loi 19/10/2026). Mã rút lại [MA_RUT] (≥ 6 ký tự, phân biệt hoa/thường) KHÔNG vào file công khai: bảng
băm mã → id nằm ở qreal/_tho/_noi_bo/ma_rut.json (gitignore, xoá cùng bản thô). "--rut <mã>" xoá câu của người đó ở cả hai
file (câu TRÙNG của người khác giữ tới khi họ cũng rút) và ghi id vào meta.da_xoa. Ô nhiều câu → nhieu_cau=true.

Chạy:  python nhap_qreal.py [--thu-muc qreal/_tho]      ·      python nhap_qreal.py --rut <mã tự đặt>
"""
import argparse, csv, hashlib, json, re, unicodedata
from pathlib import Path

HERE = Path(__file__).parent
QDIR = HERE / "qreal"
OUT = QDIR / "qreal.json"
ELICIT = QDIR / "qelicit.json"
Y_DINH = ["tot_nghiep", "dang_ky", "du_dk_luan_van", "mien", "thieu_mon", "thieu_tc", "de_xuat", "xep_loai",
          "counterfactual", "ngoai_pham_vi", "tra_cuu_quy_che"]

AN_DANH = [      # thứ tự quan trọng: cụm "mã số sinh viên …" trước mẫu MSSV trần (tránh "[MSSV] [MSSV")
    (re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+"), "[EMAIL]"),
    (re.compile(r"(?:https?://)?(?:www\.|m\.)?(?:facebook\.com|fb\.com|fb\.me|zalo\.me)/\S+", re.I), "[LINK]"),
    (re.compile(r"\b(mssv|mã số sinh viên|mã sv)\s*(?:là|:|-)?\s*[A-Za-z]?\s?\d{7}\b", re.I), r"\1 [MSSV]"),
    (re.compile(r"\b[A-Za-z]\s?\d{7}\b"), "[MSSV]"),              # MSSV ĐHCT, vd. B2306555 / B 2306555
    (re.compile(r"\b[A-Z]{2}\d{2}[A-Z]\d[A-Z]\d\b", re.I), "[LỚP]"),   # mã lớp ĐHCT, vd. DI20V7A1 / di23v7a1
    (re.compile(r"(?<![\w])(?:\+84|0)[35789](?:[\s.-]?\d){8}(?![\w])"), "[SĐT]"),   # di động VN 03/05/07/08/09
]


def an_danh(s):
    for re_, thay in AN_DANH:
        s = re_.sub(thay, s)
    return s


def chuan(s):
    s = unicodedata.normalize("NFC", s or "")
    return re.sub(r"\s+", " ", s).strip()


def khoa_trung(s):
    return re.sub(r"[^\w]+", " ", s.lower()).strip()


def loai_nguon(s):
    """Chỉ giữ LOẠI nguồn (nhom_fb, ban_be, dien_dan, log…), bỏ tên nhóm/lớp có thể nhận diện."""
    s = (s or "").lower()
    for k in ("bieu_mau", "fb", "facebook", "zalo", "dien_dan", "diễn đàn", "ban", "bạn", "log"):
        if k in s:
            return {"facebook": "fb", "diễn đàn": "dien_dan", "bạn": "ban_be", "ban": "ban_be"}.get(k, k)
    return "khac"


def bo_qua_da_xoa(ds, da_xoa):
    return [x for x in ds if x["id"] not in da_xoa]


def nhieu_cau(raw):
    """Ô trả lời có vẻ chứa nhiều câu hỏi (xuống dòng, ≥ 2 dấu "?") → rà tay tách."""
    raw = (raw or "").strip()
    return "\n" in raw or raw.count("?") >= 2


MA_RUT_TOI_THIEU = 6


def bam_ma_rut(ma):
    """Mã rút lại → băm (phân biệt hoa/thường). Mã ngắn hơn MA_RUT_TOI_THIEU → None (dễ trùng giữa người trả lời)."""
    ma = chuan(ma)
    return hashlib.sha256(("cpa2-rut|" + ma).encode("utf-8")).hexdigest()[:16] if len(ma) >= MA_RUT_TOI_THIEU else None


def _them_chu(ban_ghi, x):
    """Gộp người sở hữu (băm mã rút) của câu trùng vào bản ghi đã giữ — rút lại phải tính cả người trùng câu."""
    if x.get("ma_rut_bam"):
        ban_ghi["_chu"] = set(ban_ghi["_chu"]) | {x["ma_rut_bam"]}


def chuan_hoa_danh_sach(ds):
    ra, thay = [], {}
    for x in ds:
        q = an_danh(chuan(x.get("cau_hoi")))
        if len(q) < 8:
            continue
        k = khoa_trung(q)
        if k in thay:
            _them_chu(thay[k], x)
            continue
        h = hashlib.sha1(k.encode("utf-8")).hexdigest()
        thay[k] = {"id": f"QR-{h[:8]}", "cau_hoi": q, "nguon": loai_nguon(x.get("nguon")),
                   "y_dinh": None, "can_ho_so": None, "ma_hp": None, "split": "dev" if int(h, 16) % 2 == 0 else "test",
                   "nhieu_cau": nhieu_cau(x.get("cau_hoi")), "_chu": set()}
        _them_chu(thay[k], x)
        ra.append(thay[k])
    for r in ra:
        r["_chu"] = sorted(r["_chu"])
    return ra


MA_COT = re.compile(r"\[(DONG_Y|MA_RUT|BO|KB-\d+|TU_DO-\d+)\]")
DONG_Y = ("tôi đồng ý", "đồng ý")


def la_bieu_mau(f):
    """CSV xuất từ Google Form của bieu_mau.md (có cột chứa [DONG_Y], kể cả khi Google thêm tiền tố "2. ")."""
    with open(f, encoding="utf-8-sig", newline="") as fh:
        return any((MA_COT.search(h) or [None, None])[1] == "DONG_Y" for h in next(csv.reader(fh), []))


def doc_bieu_mau(f, canh_bao=None):
    """CSV biểu mẫu → (câu tự do cho Q-Real, câu elicit {cau_hoi, kich_ban}). Chỉ dòng ĐỒNG Ý; bỏ ô trống.
    Giá trị đồng ý lạ / file không còn dòng nào → ghi vào canh_bao (không im lặng bỏ cả file)."""
    canh_bao = [] if canh_bao is None else canh_bao
    tu_nhien, elicit, n = [], [], 0
    with open(f, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            cot = {MA_COT.search(h).group(1): v for h, v in r.items() if h and MA_COT.search(h)}
            dy = chuan(cot.get("DONG_Y")).lower().strip(" .!")
            if dy not in DONG_Y:
                if dy != "không đồng ý":
                    canh_bao.append(f"{Path(f).name}: giá trị đồng ý lạ {dy!r} → bỏ dòng")
                continue
            n += 1
            rut = bam_ma_rut(cot.get("MA_RUT"))
            if chuan(cot.get("MA_RUT")) and not rut:
                canh_bao.append(f"{Path(f).name}: mã rút {chuan(cot.get('MA_RUT'))!r} ngắn hơn {MA_RUT_TOI_THIEU} ký tự "
                                "→ không lưu (người này không rút lại được)")
            for ma, v in cot.items():
                if not chuan(v) or not (ma.startswith("KB-") or ma.startswith("TU_DO-")):
                    continue
                if ma.startswith("KB-"):
                    elicit.append({"cau_hoi": v, "kich_ban": ma, "ma_rut_bam": rut})
                else:
                    tu_nhien.append({"cau_hoi": v, "nguon": "bieu_mau", "ma_rut_bam": rut})
    if not n:
        canh_bao.append(f"{Path(f).name}: KHÔNG có dòng đồng ý nào")
    return tu_nhien, elicit


def chuan_hoa_elicit(ds, kb, canh_bao=None):
    """Câu elicit → bản ghi Q-Elicit: ẩn danh, bỏ câu ngắn, khử trùng TRONG từng kịch bản; ý định gán trước + split theo
    kịch bản (cả kịch bản một phía). y_dinh để trống — rà tay ghi khi sinh viên hỏi lệch kịch bản."""
    canh_bao = [] if canh_bao is None else canh_bao
    theo = {k["id"]: k for k in kb["kich_ban"]}
    ra, thay = [], {}
    for x in ds:
        k = theo.get(x.get("kich_ban"))
        if not k:
            canh_bao.append(f"mã kịch bản lạ {x.get('kich_ban')} → bỏ câu")
            continue
        q = an_danh(chuan(x.get("cau_hoi")))
        if len(q) < 8:
            continue
        khoa = k["id"] + "|" + khoa_trung(q)
        if khoa in thay:
            _them_chu(thay[khoa], x)
            continue
        thay[khoa] = {"id": "QE-" + hashlib.sha1(khoa.encode("utf-8")).hexdigest()[:8], "kich_ban": k["id"],
                      "y_dinh_kich_ban": k["y_dinh"], "can_ho_so": k["can_ho_so"], "ma_hp": k["ma_hp"], "cau_hoi": q,
                      "y_dinh": None, "split": k["split"], "nhieu_cau": nhieu_cau(x.get("cau_hoi")), "_chu": set()}
        _them_chu(thay[khoa], x)
        ra.append(thay[khoa])
    for r in ra:
        r["_chu"] = sorted(r["_chu"])
    return ra


def doc_tho(thu_muc, canh_bao=None):
    """Đọc file thô (bỏ qua thư mục con, vd. _noi_bo/). File không đọc được câu nào / định dạng lạ → cảnh báo."""
    canh_bao = [] if canh_bao is None else canh_bao
    ds = []
    for f in sorted(Path(thu_muc).glob("*")):
        if f.is_dir():
            continue
        truoc = len(ds)
        if f.suffix == ".csv" and la_bieu_mau(f):
            ds += doc_bieu_mau(f, canh_bao)[0]
            continue                                   # biểu mẫu tự cảnh báo (có thể chỉ có câu elicit)
        if f.suffix == ".txt":
            ds += [{"cau_hoi": l, "nguon": f.stem} for l in f.read_text(encoding="utf-8").splitlines()]
        elif f.suffix == ".csv":
            with open(f, encoding="utf-8-sig", newline="") as fh:
                ds += [{"cau_hoi": r.get("cau_hoi"), "nguon": r.get("nguon") or f.stem} for r in csv.DictReader(fh)
                       if chuan(r.get("cau_hoi"))]
        elif f.suffix == ".json":
            for x in json.loads(f.read_text(encoding="utf-8")):
                ds.append(x if isinstance(x, dict) else {"cau_hoi": x, "nguon": f.stem})
        else:
            canh_bao.append(f"{f.name}: định dạng không hỗ trợ (.txt/.csv/.json) → bỏ qua; .xlsx hãy xuất CSV")
            continue
        if len(ds) == truoc:
            canh_bao.append(f"{f.name}: không đọc được câu nào (CSV cần cột 'cau_hoi')")
    return ds


def _doc(path):
    return json.loads(Path(path).read_text(encoding="utf-8")) if Path(path).exists() else None


def doc_qreal(path=OUT):
    d = _doc(path)
    return d["cau_hoi"] if d else []


def doc_elicit(path=ELICIT):
    d = _doc(path)
    return d["cau_hoi"] if d else []


def doc_da_xoa(path=OUT):
    """Id câu đã xoá tay / rút lại — ghi ở meta.da_xoa để lần nhập sau không thêm lại."""
    d = _doc(path)
    return set(d["meta"].get("da_xoa", [])) if d else set()


def _ghi(path, ten, ds, da_xoa, ghi_chu=None):
    meta = {"ten": ten, "y_dinh_hop_le": Y_DINH, "da_xoa": sorted(da_xoa)}
    if ghi_chu:
        meta["ghi_chu"] = ghi_chu
    Path(path).parent.mkdir(exist_ok=True)
    Path(path).write_text(json.dumps({"meta": meta, "cau_hoi": sorted(ds, key=lambda x: x["id"])}, ensure_ascii=False,
                                     indent=1), encoding="utf-8")


TEN_QR = "Q-Real (câu hỏi thật, đã ẩn danh)"
TEN_QE = "Q-Elicit (sinh viên tự viết theo kịch bản, đã ẩn danh)"
GHI_QE = "Chủ đề do kịch bản đặt — báo cáo RIÊNG, KHÔNG tính vào chỉ tiêu Q-Real."


def _bang_rut(thu_muc):
    return Path(thu_muc) / "_noi_bo" / "ma_rut.json"      # trong _tho/ (gitignore) — xoá cùng bản thô


def _gop_chu(bang, moi):
    """Ghi người sở hữu (băm mã rút) của các bản ghi mới vào bảng {băm: [id]}, rồi bỏ trường nội bộ _chu."""
    for x in moi:
        for h in x.pop("_chu", []):
            bang[h] = sorted(set(bang.get(h, [])) | {x["id"]})


def nhap(thu_muc, out=OUT, elicit=ELICIT):
    """Nhập mọi file thô → Q-Real (out) + Q-Elicit (elicit, chỉ khi có CSV biểu mẫu). Giữ nhãn đã gán, tôn trọng
    meta.da_xoa. Mã rút chỉ vào bảng nội bộ trong thu_muc. Trả (số câu Q-Real, số câu Q-Elicit, cảnh báo)."""
    import build_bieu_mau
    cb = []
    bang = _doc(_bang_rut(thu_muc)) or {}
    cu = {x["id"]: x for x in doc_qreal(out)}
    da_xoa = doc_da_xoa(out)
    moi = bo_qua_da_xoa(chuan_hoa_danh_sach(doc_tho(thu_muc, cb)), da_xoa)
    _gop_chu(bang, moi)
    for x in moi:
        cu.setdefault(x["id"], x)
    _ghi(out, TEN_QR, cu.values(), da_xoa)
    bm = [f for f in sorted(Path(thu_muc).glob("*.csv")) if la_bieu_mau(f)]
    cu_e = {x["id"]: x for x in doc_elicit(elicit)}
    if bm or cu_e:
        da_xoa_e = doc_da_xoa(elicit)
        tho = [e for f in bm for e in doc_bieu_mau(f)[1]]
        moi_e = bo_qua_da_xoa(chuan_hoa_elicit(tho, build_bieu_mau.doc_kich_ban(), cb), da_xoa_e)
        _gop_chu(bang, moi_e)
        for x in moi_e:
            cu_e.setdefault(x["id"], x)
        _ghi(elicit, TEN_QE, cu_e.values(), da_xoa_e, GHI_QE)
    if bang:
        _bang_rut(thu_muc).parent.mkdir(parents=True, exist_ok=True)
        _bang_rut(thu_muc).write_text(json.dumps(bang, indent=1), encoding="utf-8")
    return len(cu), len(cu_e), cb


def rut(ma, out=OUT, elicit=ELICIT, thu_muc=QDIR / "_tho"):
    """Người trả lời rút lại bằng mã tự đặt: xoá các câu CHỈ thuộc mã này ở cả hai file (câu trùng của người khác giữ
    lại tới khi họ cũng rút), ghi id vào meta.da_xoa. Trả số câu đã xoá."""
    h, bang = bam_ma_rut(ma), _doc(_bang_rut(thu_muc)) or {}
    if not h or h not in bang:
        return 0
    ids = set(bang.pop(h))
    con_chu = {i for v in bang.values() for i in v}
    xoa = ids - con_chu
    n = 0
    for path, ten, gc in ((out, TEN_QR, None), (elicit, TEN_QE, GHI_QE)):
        d = _doc(path)
        if not d:
            continue
        bo = [x for x in d["cau_hoi"] if x["id"] in xoa]
        n += len(bo)
        _ghi(path, ten, [x for x in d["cau_hoi"] if x["id"] not in xoa],
             set(d["meta"].get("da_xoa", [])) | {x["id"] for x in bo}, gc)
    _bang_rut(thu_muc).write_text(json.dumps(bang, indent=1), encoding="utf-8")
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--thu-muc", default=str(QDIR / "_tho"))
    ap.add_argument("--rut", help="mã rút lại người trả lời tự đặt → xoá mọi câu của họ")
    a = ap.parse_args()
    if a.rut:
        print(f"đã rút {rut(a.rut)} câu (id ghi vào meta.da_xoa — không nhập lại)")
        return
    n_qr, n_qe, cb = nhap(a.thu_muc)
    for c in cb:
        print("  CẢNH BÁO:", c)
    print(f"Q-Real: {n_qr} câu tự nhiên → {OUT.relative_to(HERE)}  ·  Q-Elicit: {n_qe} câu → {ELICIT.relative_to(HERE)} "
          "(báo riêng, KHÔNG tính vào chỉ tiêu 400)")
    print("NHỚ: rà tay qreal.json và qelicit.json (tên người, lớp, chi tiết nhận diện; tách ô nhieu_cau) trước khi commit.")


if __name__ == "__main__":
    main()
