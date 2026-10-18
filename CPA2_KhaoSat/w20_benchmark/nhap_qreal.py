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

Chạy:  python nhap_qreal.py [--thu-muc qreal/_tho]
"""
import argparse, csv, hashlib, json, re, unicodedata
from pathlib import Path

HERE = Path(__file__).parent
QDIR = HERE / "qreal"
OUT = QDIR / "qreal.json"
Y_DINH = ["tot_nghiep", "dang_ky", "du_dk_luan_van", "mien", "thieu_mon", "thieu_tc", "de_xuat", "xep_loai",
          "counterfactual", "ngoai_pham_vi", "tra_cuu_quy_che"]

AN_DANH = [      # thứ tự quan trọng: cụm "mã số sinh viên …" trước mẫu MSSV trần (tránh "[MSSV] [MSSV")
    (re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+"), "[EMAIL]"),
    (re.compile(r"(?:https?://)?(?:www\.|m\.)?(?:facebook\.com|fb\.com|fb\.me|zalo\.me)/\S+", re.I), "[LINK]"),
    (re.compile(r"\b(mssv|mã số sinh viên|mã sv)\s*(?:là|:|-)?\s*[A-Za-z]?\s?\d{7}\b", re.I), r"\1 [MSSV]"),
    (re.compile(r"\b[A-Za-z]\s?\d{7}\b"), "[MSSV]"),              # MSSV ĐHCT, vd. B2306555 / B 2306555
    (re.compile(r"\b[A-Z]{2}\d{2}[A-Z]\d[A-Z]\d\b"), "[LỚP]"),       # mã lớp ĐHCT, vd. DI20V7A1
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
    for k in ("fb", "facebook", "zalo", "dien_dan", "diễn đàn", "ban", "bạn", "log"):
        if k in s:
            return {"facebook": "fb", "diễn đàn": "dien_dan", "bạn": "ban_be", "ban": "ban_be"}.get(k, k)
    return "khac"


def bo_qua_da_xoa(ds, da_xoa):
    return [x for x in ds if x["id"] not in da_xoa]


def chuan_hoa_danh_sach(ds):
    ra, thay = [], set()
    for x in ds:
        q = an_danh(chuan(x.get("cau_hoi")))
        if len(q) < 8:
            continue
        k = khoa_trung(q)
        if k in thay:
            continue
        thay.add(k)
        h = hashlib.sha1(k.encode("utf-8")).hexdigest()
        ra.append({"id": f"QR-{h[:8]}", "cau_hoi": q, "nguon": loai_nguon(x.get("nguon")),
                   "y_dinh": None, "can_ho_so": None, "ma_hp": None, "split": "dev" if int(h, 16) % 2 == 0 else "test"})
    return ra


def doc_tho(thu_muc):
    ds = []
    for f in sorted(Path(thu_muc).glob("*")):
        if f.suffix == ".txt":
            ds += [{"cau_hoi": l, "nguon": f.stem} for l in f.read_text(encoding="utf-8").splitlines()]
        elif f.suffix == ".csv":
            with open(f, encoding="utf-8-sig", newline="") as fh:
                ds += [{"cau_hoi": r.get("cau_hoi"), "nguon": r.get("nguon") or f.stem} for r in csv.DictReader(fh)]
        elif f.suffix == ".json":
            for x in json.loads(f.read_text(encoding="utf-8")):
                ds.append(x if isinstance(x, dict) else {"cau_hoi": x, "nguon": f.stem})
    return ds


def doc_qreal():
    return json.loads(OUT.read_text(encoding="utf-8"))["cau_hoi"] if OUT.exists() else []


def doc_da_xoa():
    """Id câu đã xoá tay (lộ thông tin / không phải câu học vụ) — ghi ở meta.da_xoa để lần nhập sau không thêm lại."""
    return set(json.loads(OUT.read_text(encoding="utf-8"))["meta"].get("da_xoa", [])) if OUT.exists() else set()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--thu-muc", default=str(QDIR / "_tho"))
    a = ap.parse_args()
    cu = {x["id"]: x for x in doc_qreal()}                  # giữ nhãn đã gán
    da_xoa = doc_da_xoa()
    moi = bo_qua_da_xoa(chuan_hoa_danh_sach(doc_tho(a.thu_muc)), da_xoa)
    for x in moi:
        cu.setdefault(x["id"], x)
    ds = sorted(cu.values(), key=lambda x: x["id"])
    QDIR.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({"meta": {"ten": "Q-Real (câu hỏi thật, đã ẩn danh)", "y_dinh_hop_le": Y_DINH,
                                        "da_xoa": sorted(da_xoa)},
                               "cau_hoi": ds}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Q-Real: {len(ds)} câu ({sum(x['y_dinh'] is not None for x in ds)} đã gán nhãn) → {OUT.relative_to(HERE)}")
    print("NHỚ: rà tay qreal.json (tên người, lớp, chi tiết nhận diện) trước khi commit.")


if __name__ == "__main__":
    main()
