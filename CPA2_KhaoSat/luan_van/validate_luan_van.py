"""
validate_luan_van.py — kiểm tra đề cương luận văn (CPA², giai đoạn 2).

Kiểm:
  L1  De_cuong_LVTN.docx tồn tại, mọi phần XML đọc được
  L2  phần thân: A4, lề trên 3 cm, dưới 3 cm, trái 3,5 cm, phải 2 cm (mẫu Trường CNTT&TT)
  L3  phần thân (từ bookmark CPA2_BAT_DAU): Times New Roman, cỡ 13, giãn dòng 1,2
  L4  đủ đề mục theo bố cục mẫu, đúng thứ tự
  L5  không còn chữ hướng dẫn hay chỗ giữ chỗ của mẫu ("Trình bày luận văn", "Nguyễn Văn A", "XX/202")
  L6  tóm lược tiếng Việt và tiếng Anh, mỗi bản ≤ 500 từ
  L7  ĐỐI CHIẾU SỐ LIỆU: mỗi con số trong đề cương phải có trong báo cáo nguồn hoặc tính lại được từ mã
  L8  .docx khớp bản sinh lại từ De_cuong_LVTN.md (không sửa tay .docx)
Ô "<<...>>" chưa điền chỉ CẢNH BÁO, không làm trượt.

Chạy:  python validate_luan_van.py   (mã thoát 0 = ĐẠT)
"""
import json
import re
import sys
import unicodedata
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

HERE = Path(__file__).parent
ROOT = HERE.parent
MD = HERE / "De_cuong_LVTN.md"
DOCX = HERE / "De_cuong_LVTN.docx"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

ket_qua = []


def ca(ma, dat, mo_ta):
    ket_qua.append((ma, bool(dat), mo_ta))
    print(f"[{'ĐẠT' if dat else 'TRƯỢT'}] {ma}: {mo_ta}")


def nfc(s):
    return unicodedata.normalize("NFC", s)


def chu(p):
    return "".join(t.text or "" for t in p.iter(W + "t"))


def doan_than(body):
    """Các đoạn từ bookmark CPA2_BAT_DAU trở đi (kể cả trong bảng)."""
    ra, bat_dau = [], False
    for p in body.iter(W + "p"):
        if not bat_dau and any(b.get(W + "name") == "CPA2_BAT_DAU" for b in p.iter(W + "bookmarkStart")):
            bat_dau = True
        if bat_dau:
            ra.append(p)
    return ra


def kiem_docx():
    if not DOCX.exists():
        ca("L1", False, f"chưa có {DOCX.name}")
        return None
    try:
        z = zipfile.ZipFile(DOCX)
        for n in z.namelist():
            if n.endswith(".xml") or n.endswith(".rels"):
                ET.fromstring(z.read(n))
    except Exception as e:                                  # noqa: BLE001 — báo lỗi đọc file, không dừng
        ca("L1", False, f"không đọc được {DOCX.name}: {e}")
        return None
    ca("L1", True, f"{DOCX.name} đọc được ({len(z.namelist())} phần)")
    return z


def kiem_le(body):
    sect = body.findall(W + "sectPr")
    if not sect:
        ca("L2", False, "không có sectPr cuối thân")
        return
    pg, mar = sect[-1].find(W + "pgSz"), sect[-1].find(W + "pgMar")
    gt = {k: int(mar.get(W + k)) for k in ("top", "bottom", "left", "right")}
    can = {"top": 1701, "bottom": 1701, "left": 1985, "right": 1134}     # 3 / 3 / 3,5 / 2 cm (twip)
    a4 = pg.get(W + "w") == "11906" and pg.get(W + "h") == "16838"
    ca("L2", a4 and all(abs(gt[k] - v) <= 2 for k, v in can.items()), f"A4={a4}, lề={gt}, cần={can}")


def kiem_dinh_dang(doan):
    sai = []
    for p in doan:
        sp = p.find(f"{W}pPr/{W}spacing")
        if chu(p).strip() and (sp is None or sp.get(W + "line") != "288" or sp.get(W + "lineRule") != "auto"):
            sai.append(("giãn dòng", chu(p)[:40]))
        for r in p.iter(W + "r"):
            if not "".join(t.text or "" for t in r.iter(W + "t")).strip():
                continue
            rp = r.find(W + "rPr")
            sz = rp.find(W + "sz") if rp is not None else None
            f = rp.find(W + "rFonts") if rp is not None else None
            if sz is None or sz.get(W + "val") not in ("26", "28"):          # 13 pt; tiêu đề phần 14 pt
                sai.append(("cỡ chữ", chu(p)[:40]))
            if f is None or f.get(W + "ascii") != "Times New Roman":
                sai.append(("font", chu(p)[:40]))
    ca("L3", not sai and len(doan) > 20, f"{len(doan)} đoạn thân, {len(sai)} lỗi định dạng" +
       (f"; ví dụ {sai[:3]}" if sai else ""))


CAN_CO = ["MỤC LỤC", "TÓM LƯỢC", "PHẦN GIỚI THIỆU", "Đặt vấn đề", "Những nghiên cứu liên quan", "Mục tiêu đề tài",
          "Đối tượng và phạm vi nghiên cứu", "Phương pháp nghiên cứu", "Nội dung nghiên cứu",
          "Bố cục của quyển luận văn", "CHƯƠNG 1", "CHƯƠNG 2", "CHƯƠNG 3", "CHƯƠNG 4", "PHẦN KẾT LUẬN",
          "Kết quả đạt được", "Hướng phát triển", "KẾ HOẠCH THỰC HIỆN", "TÀI LIỆU THAM KHẢO"]


def kiem_de_muc(doan):
    tieu_de = [nfc(chu(p)) for p in doan if p.find(f"{W}pPr/{W}outlineLvl") is not None]
    vi_tri, thieu = -1, []
    for m in CAN_CO:
        k = next((i for i, t in enumerate(tieu_de) if i > vi_tri and nfc(m) in t), None)
        if k is None:
            thieu.append(m)
        else:
            vi_tri = k
    ca("L4", not thieu, f"{len(tieu_de)} đề mục; thiếu hoặc sai thứ tự: {thieu}" if thieu
       else f"{len(tieu_de)} đề mục, đủ và đúng thứ tự")


def kiem_cho_giu(z):
    x = nfc(z.read("word/document.xml").decode("utf-8"))
    van_ban = nfc("".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", x)))
    con = [s for s in ("Trình bày luận văn", "Bố cục nội dung gồm", "Nguyễn Văn A", "XX/202", "TÊN ĐỀ TÀI",
                       "123453454", "[[MUC_LUC]]") if nfc(s) in van_ban]
    ca("L5", not con, f"còn chữ của mẫu: {con}" if con else "không còn chữ hướng dẫn của mẫu")
    o = sorted(set(re.findall(r"&lt;&lt;([^&]+)&gt;&gt;", x)))
    if o:
        print(f"[CẢNH BÁO] còn {len(o)} ô chưa điền trên bìa: {o}")


def doc_md():
    s = nfc(MD.read_text(encoding="utf-8")).replace("\r\n", "\n")
    m = re.match(r"---\n(.*?)\n---\n", s, re.S)
    return dict(l.split(": ", 1) for l in m.group(1).splitlines()), s[m.end():]


def kiem_tom_luoc():
    _, than = doc_md()
    k = re.search(r"# TÓM LƯỢC\n(.*?)\n# ", than, re.S).group(1)
    vi, en = k.split("**Abstract.**")
    dem = (len(vi.split()), len(en.split()))
    ca("L6", 0 < dem[0] <= 500 and 0 < dem[1] <= 500, f"tóm lược VI {dem[0]} từ, EN {dem[1]} từ (tối đa 500)")


def so_r_formal():
    r = json.loads((ROOT / "w5_rformal" / "r_formal_v1.json").read_text(encoding="utf-8"))["rules"]
    lop = [e.get("lop") for e in r]
    mien = sum(lop.count(x) for x in "FPN")
    f_dl = sum(1 for e in r if e.get("lop") == "F" and e.get("du_lieu") == "co")

    def pt(a, b):
        return f"{100 * a / b:.1f}".replace(".", ",") + "%"
    return [f"{len(r)} đơn vị", f"F = {lop.count('F')}, P = {lop.count('P')}, N = {lop.count('N')}",
            f"{lop.count('X')} đơn vị ngoài miền", f"{lop.count('F')}/{mien} = {pt(lop.count('F'), mien)}",
            f"{f_dl}/{mien} = {pt(f_dl, mien)}"]


# (chuỗi trong đề cương, file nguồn, chuỗi phải có trong nguồn)
DOI_CHIEU = [
    ("Soundness 91,1% (5 kết luận sai trên 56 ca)", "Tuan22_Danh_gia_CPA2.md", "91,1% (5 kết luận sai / 56 ca)"),
    ("Soundness 100%, Coverage 25%", "Tuan22_Danh_gia_CPA2.md", "Soundness 100%, Coverage thấp (25%)"),
    ("19/19 bộ kiểm thử", "Tuan22_Danh_gia_CPA2.md", "19/19 `validate_*.py` ĐẠT"),
    ("Soundness 91,9%, Coverage 78,4%", "Tuan17_Adversarial_Set.md", "| Coverage | 78,4% |"),
    ("Soundness 91,9%", "Tuan17_Adversarial_Set.md", "**91,9%**"),
    ("bộ đối kháng 80 ca", "Tuan17_Adversarial_Set.md", "**80 ca chấm điểm**"),
    ("CPA² đúng đáp án chuẩn 58 ca, hệ đối chứng tốt nhất 44 ca", "Tuan23_So_sanh_baseline.md",
     "nhiều ca đúng gold nhất (58; baseline cao nhất 44)"),
    ("CPA² đúng đáp án chuẩn ở 58 ca", "Tuan23_So_sanh_baseline.md", "(58; baseline cao nhất 44)"),
    ("hơn 5/6 hệ có ý nghĩa thống kê", "Tuan23_So_sanh_baseline.md", "CPA² hơn 5/6 baseline qua ngưỡng"),
    ("2 kết luận sai với Coverage 54,0%", "Tuan23_So_sanh_baseline.md", "| **2** | **54,0%** |"),
    ("(Coverage 2–28%)", "Tuan23_So_sanh_baseline.md", "(Coverage 2–28%)"),
    ("Recall@1 = 0,67, Recall@5 = 0,92", "Tuan14_RAG_Grounding.md", "Recall@1 = 0,67, Recall@5 = 0,92"),
    ("hiện 0/400", "Tuan20_Benchmark.md", "(0/400)"),
    ("Q-Noise (240 câu", "Tuan20_Benchmark.md", "240 câu (48 câu gốc × 5 kiểu gõ)"),
]


def kiem_so_lieu():
    _, than = doc_md()
    loi = []
    r_formal = so_r_formal()
    for chuoi in r_formal:
        if nfc(chuoi) not in than:
            loi.append(f"R-Formal tính lại: '{chuoi}' không có trong đề cương")
    for trong_md, nguon, trong_nguon in DOI_CHIEU:
        src = nfc((ROOT / nguon).read_text(encoding="utf-8"))
        if nfc(trong_md) not in than:
            loi.append(f"đề cương thiếu '{trong_md}'")
        if nfc(trong_nguon) not in src:
            loi.append(f"{nguon} không có '{trong_nguon}'")
    ca("L7", not loi, f"{len(r_formal) + len(DOI_CHIEU)} con số đối chiếu với nguồn" + (f"; lỗi: {loi}" if loi else ""))


def kiem_dong_bo(z):
    sys.path.insert(0, str(HERE))
    try:
        import md_sang_docx                                     # noqa: PLC0415 — chỉ cần khi kiểm L8
    except ImportError as e:
        ca("L8", False, f"không nạp được md_sang_docx: {e}")
        return
    ca("L8", md_sang_docx.sinh_document_xml() == z.read("word/document.xml"),
       ".docx khớp bản sinh lại từ De_cuong_LVTN.md")


def main():
    z = kiem_docx()
    if z is not None:
        body = ET.fromstring(z.read("word/document.xml")).find(W + "body")
        doan = doan_than(body)
        kiem_le(body)
        kiem_dinh_dang(doan)
        kiem_de_muc(doan)
        kiem_cho_giu(z)
        kiem_dong_bo(z)
    kiem_tom_luoc()
    kiem_so_lieu()
    tong = 8
    dat = sum(d for _, d, _ in ket_qua)
    print(f"\n{dat}/{tong} ca ĐẠT")
    ok = dat == tong and len(ket_qua) == tong
    print("KẾT LUẬN: " + ("ĐẠT" if ok else "CHƯA ĐẠT"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
