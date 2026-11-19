"""
md_sang_docx.py — sinh De_cuong_LVTN.docx từ De_cuong_LVTN.md trên mẫu MauLuanVan-NienLuan.docx (Trường CNTT&TT).

Chỉ dùng thư viện chuẩn (zipfile + chuỗi XML), giữ nguyên style, ảnh và hai trang bìa của mẫu:
  - bìa: thay chỗ giữ chỗ (tên đề tài, sinh viên, mã số, khóa, GVHD, thời gian) bằng khối đầu của .md;
  - bỏ trang hướng dẫn của mẫu, chèn phần thân sinh từ .md;
  - phần thân: Times New Roman 13, giãn dòng 1,2, lề 3 / 3 / 3,5 / 2 cm (theo hướng dẫn của mẫu), số trang ở chân trang;
  - mục lục là trường TOC: Word cập nhật khi mở file (settings updateFields).
.md là NGUỒN DUY NHẤT; không sửa tay .docx (validate_luan_van.py L8 kiểm).

Markdown hỗ trợ: khối đầu `---`, `#`/`##`/`###`, đoạn văn, `- ` gạch đầu dòng, bảng `|`, **đậm**, [[MUC_LUC]].

Chạy:  python md_sang_docx.py   → De_cuong_LVTN.docx
"""
import re
import sys
import unicodedata
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).parent
MAU = HERE / "MauLuanVan-NienLuan.docx"
MD = HERE / "De_cuong_LVTN.md"
RA = HERE / "De_cuong_LVTN.docx"

LE = {"top": 1701, "bottom": 1701, "left": 1985, "right": 1134}     # 3 / 3 / 3,5 / 2 cm (twip)
FONT = ('<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman" '
        'w:eastAsia="Times New Roman"/>')
DONG = 'w:line="288" w:lineRule="auto"'                              # 1,2 dòng = 240 × 1,2
FOOTER_TRANG = "word/footer4.xml"                                    # footer mặc định của section thân trong mẫu
NGAY_ZIP = (2026, 12, 1, 0, 0, 0)                                    # cố định để file sinh ra ổn định


def nfc(s):
    return unicodedata.normalize("NFC", s)


# ----------------------------------------------------------------------------- đọc .md
def doc_md():
    s = nfc(MD.read_text(encoding="utf-8")).replace("\r\n", "\n")
    m = re.match(r"---\n(.*?)\n---\n", s, re.S)
    if not m:
        raise ValueError("De_cuong_LVTN.md thiếu khối đầu ---")
    bia = dict(l.split(": ", 1) for l in m.group(1).splitlines())
    return bia, s[m.end():]


def khoi(than):
    """Tách thân .md thành các khối (loai, noi_dung)."""
    ra, dong = [], than.split("\n")
    i = 0
    while i < len(dong):
        d = dong[i].rstrip()
        if not d:
            i += 1
        elif d.startswith("|"):
            bang_ = []
            while i < len(dong) and dong[i].startswith("|"):
                if not re.match(r"^\|[\s\-|:]+\|$", dong[i].strip()):
                    bang_.append([c.strip() for c in dong[i].strip().strip("|").split("|")])
                i += 1
            ra.append(("bang", bang_))
        elif d.startswith("### "):
            ra.append(("h3", d[4:]))
            i += 1
        elif d.startswith("## "):
            ra.append(("h2", d[3:]))
            i += 1
        elif d.startswith("# "):
            ra.append(("h1", d[2:]))
            i += 1
        elif d.startswith("- "):
            ra.append(("gach", d[2:]))
            i += 1
        elif d == "[[MUC_LUC]]":
            ra.append(("muc_luc", ""))
            i += 1
        else:
            doan_ = [d]
            i += 1
            while i < len(dong) and dong[i].strip() and not re.match(r"^(#|- |\||\[\[)", dong[i]):
                doan_.append(dong[i].rstrip())
                i += 1
            ra.append(("doan", " ".join(doan_)))
    return ra


# ----------------------------------------------------------------------------- dựng XML
def run(text, dam=False, nghieng=False, co=26):
    rpr = FONT + ("<w:b/><w:bCs/>" if dam else "") + ("<w:i/><w:iCs/>" if nghieng else "") + \
        f'<w:sz w:val="{co}"/><w:szCs w:val="{co}"/>'
    return f'<w:r><w:rPr>{rpr}</w:rPr><w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


def runs(text, nghieng=False, co=26, dam_tat_ca=False):
    """**đậm** trong dòng."""
    return "".join(run(phan, dam=dam_tat_ca or k % 2 == 1, nghieng=nghieng, co=co)
                   for k, phan in enumerate(re.split(r"\*\*", text)) if phan)


def doan(noi_dung, jc="both", truoc=0, sau=120, thut_dau=567, bookmark=""):
    ind = f'<w:ind w:firstLine="{thut_dau}"/>' if thut_dau else ""
    ppr = f'<w:pPr><w:spacing w:before="{truoc}" w:after="{sau}" {DONG}/>{ind}<w:jc w:val="{jc}"/></w:pPr>'
    return f"<w:p>{ppr}{bookmark}{noi_dung}</w:p>"


def tieu_de(cap, text, ngat_trang, bookmark=""):
    """cap 1: phần/chương (14 pt, giữa, sang trang mới); cap 2: đậm; cap 3: đậm nghiêng. Có outlineLvl cho mục lục."""
    co = 28 if cap == 1 else 26
    jc = "center" if cap == 1 else "left"
    truoc, sau = (0, 240) if cap == 1 else (240, 120)
    them = ("<w:pageBreakBefore/>" if ngat_trang else "") + "<w:keepNext/>"
    noi = runs(text, co=co, dam_tat_ca=True, nghieng=(cap == 3))
    ppr = (f'<w:pPr>{them}<w:spacing w:before="{truoc}" w:after="{sau}" {DONG}/>'
           f'<w:jc w:val="{jc}"/><w:outlineLvl w:val="{cap - 1}"/></w:pPr>')
    return f"<w:p>{ppr}{bookmark}{noi}</w:p>"


def gach(text):
    ppr = (f'<w:pPr><w:spacing w:before="0" w:after="60" {DONG}/>'
           f'<w:ind w:left="567" w:hanging="284"/><w:jc w:val="both"/></w:pPr>')
    return f"<w:p>{ppr}{run('– ')}{runs(text)}</w:p>"


def bang(hang):
    vien = "".join(f'<w:{b} w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
                   for b in ("top", "left", "bottom", "right", "insideH", "insideV"))
    tblpr = f'<w:tblPr><w:tblW w:w="5000" w:type="pct"/><w:tblBorders>{vien}</w:tblBorders></w:tblPr>'
    so_cot = max(len(h) for h in hang)
    grid = "<w:tblGrid>" + "".join('<w:gridCol w:w="2900"/>' for _ in range(so_cot)) + "</w:tblGrid>"
    xml = []
    for k, h in enumerate(hang):
        o = []
        for c in h + [""] * (so_cot - len(h)):
            p = (f'<w:p><w:pPr><w:spacing w:before="40" w:after="40" {DONG}/></w:pPr>'
                 f"{runs(c, dam_tat_ca=(k == 0))}</w:p>")
            o.append(f'<w:tc><w:tcPr><w:tcW w:w="0" w:type="auto"/></w:tcPr>{p}</w:tc>')
        xml.append(("<w:tr><w:trPr><w:tblHeader/></w:trPr>" if k == 0 else "<w:tr>") + "".join(o) + "</w:tr>")
    return f"<w:tbl>{tblpr}{grid}{''.join(xml)}</w:tbl>" + doan("", sau=0, thut_dau=0)


def muc_luc():
    goi_y = "(Mục lục tự cập nhật khi mở bằng Microsoft Word; nếu chưa, nhấn chuột phải vào đây và chọn Update Field.)"
    rpr = f'<w:rPr>{FONT}<w:sz w:val="26"/><w:szCs w:val="26"/></w:rPr>'
    noi = (f'<w:r>{rpr}<w:fldChar w:fldCharType="begin" w:dirty="true"/></w:r>'
           f'<w:r>{rpr}<w:instrText xml:space="preserve"> TOC \\o "1-3" \\h \\z \\u </w:instrText></w:r>'
           f'<w:r>{rpr}<w:fldChar w:fldCharType="separate"/></w:r>'
           f"{run(goi_y, nghieng=True)}"
           f'<w:r>{rpr}<w:fldChar w:fldCharType="end"/></w:r>')
    return doan(noi, jc="left", thut_dau=0)


def sinh_than(than):
    xml, dau = [], True
    bm = '<w:bookmarkStart w:id="9001" w:name="CPA2_BAT_DAU"/><w:bookmarkEnd w:id="9001"/>'
    for loai, nd in khoi(than):
        b = bm if dau else ""
        if loai in ("h1", "h2", "h3"):
            xml.append(tieu_de(int(loai[1]), nd, ngat_trang=(loai == "h1" and not dau), bookmark=b))
        elif loai == "doan":
            xml.append(doan(runs(nd), bookmark=b))
        elif loai == "gach":
            xml.append(gach(nd))
        elif loai == "bang":
            xml.append(bang(nd))
        elif loai == "muc_luc":
            xml.append(muc_luc())
        dau = False
    return "".join(xml)


# ----------------------------------------------------------------------------- ghép vào mẫu
def thay_bia(x, bia):
    """Thay chỗ giữ chỗ trên hai trang bìa (chỉ phần trước điểm cắt). Chữ của đoạn dồn vào run đầu."""
    thay = [("LUẬN VĂN TỐT NGHIỆP ĐẠI HỌC/NIÊN LUẬN/TIỂU LUẬN", bia["loai"]),
            ("TÊN ĐỀ TÀI (TIẾNG VIỆT)", bia["ten_vi"]), ("TÊN ĐỀ TÀI (TIẾNG ANH)", bia["ten_en"]),
            ("ThS/TS. Nguyễn Văn A", bia["gvhd"]), ("Họ và tên", bia["sinh_vien"]),
            ("123453454", bia["mssv"]), ("123456", bia["mssv"]), ("Kxy", bia["khoa"]),
            ("Cần Thơ, XX/202Y", bia["thoi_gian"])]

    def sua_doan(m):
        p = m.group(0)
        ts = list(re.finditer(r"(<w:t(?: [^>]*)?>)([^<]*)(</w:t>)", p))
        if not ts:
            return p
        cu = "".join(t.group(2) for t in ts)
        moi = cu
        for a, b in thay:
            moi = moi.replace(escape(nfc(a)), escape(nfc(b)))
        if moi == cu:
            return p
        ra, vt = [], 0
        for k, t in enumerate(ts):
            ra.append(p[vt:t.start()])
            ra.append('<w:t xml:space="preserve">' + (moi if k == 0 else "") + "</w:t>")
            vt = t.end()
        ra.append(p[vt:])
        return "".join(ra)

    return re.sub(r"<w:p[ >](?:(?!<w:p[ >]).)*?</w:p>", sua_doan, x, flags=re.S)


def sinh_document_xml():
    bia, than = doc_md()
    with zipfile.ZipFile(MAU) as z:
        x = nfc(z.read("word/document.xml").decode("utf-8"))
    i = x.find(nfc("1. Trình bày luận văn"))
    if i < 0:
        raise ValueError("mẫu không có trang hướng dẫn '1. Trình bày luận văn' — mẫu đã đổi?")
    cat = x.rfind("<w:p ", 0, i)
    truoc = x.rfind("<w:p ", 0, cat)
    if "pageBreakBefore" in x[truoc:cat] and "<w:t" not in x[truoc:cat]:
        cat = truoc
    s0 = x.rfind("<w:sectPr")
    s1 = x.find("</w:sectPr>", s0) + len("</w:sectPr>")
    sect = x[s0:s1]
    # section bìa phụ: bỏ header/footer riêng → kế thừa bìa chính (trống), bìa không đánh số trang
    sect_bia = re.sub(r"<w:(header|footer)Reference [^>]*/>", "", sect)
    # section thân: lề theo hướng dẫn của mẫu, đánh số trang từ 1
    sect_than = re.sub(r"<w:pgMar [^>]*/>", ('<w:pgMar w:top="{top}" w:right="{right}" w:bottom="{bottom}" '
                                             'w:left="{left}" w:header="720" w:footer="720" w:gutter="0"/>').format(**LE),
                       sect)
    sect_than = sect_than.replace("<w:cols ", '<w:pgNumType w:start="1"/><w:cols ', 1)
    ngat = f"<w:p><w:pPr>{sect_bia}</w:pPr></w:p>"
    moi = thay_bia(x[:cat], bia) + ngat + sinh_than(than) + sect_than + x[s1:]
    return moi.encode("utf-8")


FOOTER = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
          '<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
          '<w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
          f'<w:r><w:rPr>{FONT}<w:sz w:val="26"/></w:rPr><w:fldChar w:fldCharType="begin"/></w:r>'
          f'<w:r><w:rPr>{FONT}<w:sz w:val="26"/></w:rPr><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
          f'<w:r><w:rPr>{FONT}<w:sz w:val="26"/></w:rPr><w:fldChar w:fldCharType="separate"/></w:r>'
          f'<w:r><w:rPr>{FONT}<w:sz w:val="26"/></w:rPr><w:t>1</w:t></w:r>'
          f'<w:r><w:rPr>{FONT}<w:sz w:val="26"/></w:rPr><w:fldChar w:fldCharType="end"/></w:r></w:p></w:ftr>')


def sua_settings(s):
    if "<w:updateFields" in s:
        return s
    for moc in ("<w:hdrShapeDefaults", "<w:footnotePr", "<w:endnotePr", "<w:compat", "<w:docVars", "<w:rsids"):
        k = s.find(moc)
        if k >= 0:
            return s[:k] + '<w:updateFields w:val="true"/>' + s[k:]
    return s.replace("</w:settings>", '<w:updateFields w:val="true"/></w:settings>')


def main():
    doc = sinh_document_xml()
    with zipfile.ZipFile(MAU) as zin, zipfile.ZipFile(RA, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                data = doc
            elif item.filename == FOOTER_TRANG:
                data = FOOTER.encode("utf-8")
            elif item.filename == "word/settings.xml":
                data = sua_settings(data.decode("utf-8")).encode("utf-8")
            zout.writestr(zipfile.ZipInfo(item.filename, NGAY_ZIP), data, zipfile.ZIP_DEFLATED)
    print(f"Đã sinh {RA.name} ({RA.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
