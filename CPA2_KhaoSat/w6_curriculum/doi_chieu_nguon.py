"""
doi_chieu_nguon.py — đối chiếu bản chép tay (build_curriculum.py) với PDF gốc.

Hai nguồn độc lập, hai cách đối chiếu:
  Trang 3 (dòng 1–41) có LỚP VĂN BẢN → so khớp CHÍNH XÁC mã, số TC, các mã tham chiếu
          (tiên quyết + song hành) trên cùng dòng, với pdftotext -layout.
  Trang 4 (dòng 42–78) là ẢNH QUÉT     → OCR tesseract (eng) rồi chuẩn hoá lỗi OCR hay
          gặp của mã học phần (I→1, O→0, S→5, 'C1'→'CT'); chỉ kết luận KHỚP/LỆCH khi đọc
          được, dòng OCR hỏng thì báo KHÔNG ĐỌC ĐƯỢC chứ không đoán.

Cần: poppler-utils (pdftotext, pdftoppm) và tesseract. Thiếu thì báo BỎ QUA, mã thoát 2.
Chạy: python3 doi_chieu_nguon.py [đường_dẫn_pdf]
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_curriculum import ROWS, META  # noqa: E402

# Dòng OCR đọc lệch đã được SOÁT TAY trên ảnh trang và xác nhận bản chép đúng.
# Chỉ được thêm vào đây sau khi nhìn ảnh — không dùng để "tắt" một lệch chưa soát.
DA_SOAT_TAY = {
    75: "ảnh 200 dpi đọc rõ 'CT482 Xử lý dữ liệu lớn'; OCR nhầm 8→s ('cr4s2')",
}

PDF_MAC_DINH = Path(__file__).resolve().parents[2] / "NiênLuan/ctdt/K49/69_7480201_CongNgheThongTin.pdf"


def trang3(pdf):
    txt = subprocess.run(["pdftotext", "-f", "3", "-l", "3", "-layout", str(pdf), "-"],
                         capture_output=True, text=True).stdout
    dong = {}
    for ln in txt.splitlines():
        m = re.match(r"\s*(\d{1,2})\s+([A-Z]{2}\d{3}E?)\s+(.*)$", ln)
        if m:
            dong[int(m.group(1))] = (m.group(2), m.group(3))
    kq = []
    for r in ROWS:
        tt, ma, ten, tc = r[0], r[1], r[2], r[3]
        if tt > 41:
            continue
        if tt not in dong:
            kq.append((tt, ma, "KHÔNG ĐỌC ĐƯỢC", "dòng không có trong lớp văn bản"))
            continue
        ma_pdf, phan_con = dong[tt]
        ref_pdf = set(re.findall(r"\b[A-Z]{2}\d{3}E?\b", phan_con))
        ref_ta = set((r[7] if isinstance(r[7], list) else []) + r[8])
        # tên học phần chỉ chứa khoảng trắng đơn; cột đầu tiên sau ≥2 khoảng trắng là Số TC
        so = re.match(r"(.*?\S)\s{2,}(\S+)", phan_con)
        tok = so.group(2) if so else None
        tc_pdf = tok if tok == "1+1+1" else (int(tok) if tok and tok.isdigit() else tok)
        tc_ok = (tc_pdf == "1+1+1" and tc == 3) or tc_pdf == tc
        loi = []
        if ma_pdf != ma:
            loi.append(f"mã {ma_pdf}≠{ma}")
        if not tc_ok:
            loi.append(f"TC {tc_pdf}≠{tc}")
        if ref_pdf != ref_ta:
            loi.append(f"tham chiếu {sorted(ref_pdf)}≠{sorted(ref_ta)}")
        kq.append((tt, ma, "LỆCH" if loi else "KHỚP", "; ".join(loi)))
    return kq


def chuan_hoa_ma(s):
    s = s.upper().strip("[|(/")
    if len(s) < 5 or s[0] != "C":
        return None
    s = "CT" + s[2:] if s[1] != "T" else s
    than = s[2:].replace("I", "1").replace("O", "0").replace("S", "5").replace("L", "1")
    return "CT" + than


def trang4(pdf):
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["pdftoppm", "-r", "300", "-f", "4", "-l", "4", "-gray", "-png",
                        str(pdf), f"{d}/p"], check=True)
        png = next(Path(d).glob("p*.png"))
        txt = subprocess.run(["tesseract", str(png), "-", "--psm", "6"],
                             capture_output=True, text=True).stdout
    doc = {}
    for ln in txt.splitlines():
        m = re.match(r"\W*[A-Za-z]?\W*(\d{2})\s*[\[|(/]?\s*\|?\s*([A-Za-z0-9]{5,6})", ln)
        if m and 42 <= int(m.group(1)) <= 78:
            doc[int(m.group(1))] = chuan_hoa_ma(m.group(2))
    kq = []
    for r in ROWS:
        tt, ma = r[0], r[1]
        if tt < 42:
            continue
        o = doc.get(tt)
        if not o or not re.fullmatch(r"CT\d{3}E?", o):
            kq.append((tt, ma, "KHÔNG ĐỌC ĐƯỢC", f"OCR: {o}"))
        elif o == ma:
            kq.append((tt, ma, "KHỚP", ""))
        elif tt in DA_SOAT_TAY:
            kq.append((tt, ma, "KHỚP (soát tay)", f"OCR đọc {o} — {DA_SOAT_TAY[tt]}"))
        else:
            kq.append((tt, ma, "LỆCH", f"OCR đọc {o}"))
    return kq


def main():
    pdf = Path(sys.argv[1]) if len(sys.argv) > 1 else PDF_MAC_DINH
    if not pdf.exists():
        print(f"BỎ QUA — không thấy PDF: {pdf}")
        return 2
    thieu = [t for t in ("pdftotext", "pdftoppm", "tesseract") if not shutil.which(t)]
    print(f"Đối chiếu bản chép với {META['file_pdf']}")
    kq = trang3(pdf) if "pdftotext" not in thieu else []
    if not ("pdftoppm" in thieu or "tesseract" in thieu):
        kq += trang4(pdf)
    else:
        print(f"  (trang 4 BỎ QUA — thiếu {thieu})")
    dem = {}
    for tt, ma, st, gc in kq:
        dem[st] = dem.get(st, 0) + 1
        if st != "KHỚP":
            print(f"  dòng {tt:2d} {ma:7s} {st:15s} {gc}")
    print("  Tổng:", ", ".join(f"{k} {v}" for k, v in sorted(dem.items())))
    return 1 if dem.get("LỆCH") else (2 if thieu else 0)


if __name__ == "__main__":
    sys.exit(main())
