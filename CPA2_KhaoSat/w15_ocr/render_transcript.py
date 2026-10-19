"""
render_transcript.py — vẽ bảng điểm tổng hợp theo bố cục "Mẫu In D5050A0" của ĐHCT (CPA2, Tuần 15)

Từ một hồ sơ JSON Tuần 7 (đáp án đã biết) → danh sách ảnh trang bảng điểm. Dùng để đo OCR có
đáp án tuyệt đối. Bố cục (cột, cỡ chữ, khổ 1105×1430) chép theo bảng điểm in từ dkmh.ctu.edu.vn;
họ tên / mã số là GIẢ, không lấy từ bảng điểm thật.

Quy ước in (đối chiếu bảng điểm thật + quy chế):
  - học phần điều kiện có "(*)" sau tên; dòng "SHCVHT" 0 TC mỗi học kỳ
  - ĐTBCHK: mọi HP đã học kể cả điểm F và HP điều kiện, TRỪ GDTC (R-B08); không tính điểm M
  - ĐTBCTL: HP đã tích lũy, không gồm F và HP điều kiện (R-B10)
  - miễn ngoại ngữ bằng chứng chỉ in thành dòng CC004 "Miễn M" 10 TC (như bảng điểm thật)

Chạy: python render_transcript.py ../w7_student_facts/students/sv_lvtn.json   → _anh/sv_lvtn_*.png
"""
import io, json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
CURRICULUM = HERE.parent / "w6_curriculum" / "curriculum_cntt_k49.json"
def _tim_font(bien_moi_truong, *ung_vien):
    """Font đầu tiên tồn tại: biến môi trường → Times New Roman (Windows) → Liberation Serif (cùng số đo với
    Times, Linux) → DejaVu Serif. Số liệu OCR phụ thuộc font — chỉ so trước/sau trên CÙNG font (Tuần 16)."""
    import os
    for f in (os.environ.get(bien_moi_truong), *ung_vien):
        if f and Path(f).exists():
            return f
    raise FileNotFoundError(f"không tìm thấy font — đặt biến môi trường {bien_moi_truong}")


_FONT = {}


def font(dam=False):
    """Đường dẫn font, chỉ tìm khi thật sự vẽ (import module không cần font — w17 dùng chia_hoc_ky)."""
    if dam not in _FONT:
        _FONT[dam] = (_tim_font("CPA2_FONT_DAM", "C:/Windows/Fonts/timesbd.ttf",
                                "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
                                "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf") if dam else
                      _tim_font("CPA2_FONT", "C:/Windows/Fonts/times.ttf",
                                "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
                                "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"))
    return _FONT[dam]

W, H = 1105, 1430
CO = 21                      # cỡ chữ (px) ~ bảng điểm in từ trình duyệt
DONG = 30                    # khoảng cách dòng
X = {"ma": 67, "ten": 159, "nhom": 531, "tc": 610, "thi": 646, "l2": 708, "thop": 760, "qd": 822, "sao": 884}
TEN_MAX = X["nhom"] - X["ten"] - 12
TC_HK_MAX = 20
CHU_4 = {"A": 4.0, "B+": 3.5, "B": 3.0, "C+": 2.5, "C": 2.0, "D+": 1.5, "D": 1.0, "F": 0.0}
NAM_HOC = ["23-24", "24-25", "25-26", "26-27", "27-28"]


def _ctdt():
    cur = json.loads(CURRICULUM.read_text(encoding="utf-8"))
    return {h["ma"]: h for h in cur["hoc_phan"]}


def chia_hoc_ky(j, ctdt):
    """Xếp học phần của hồ sơ thành học kỳ theo thứ tự CTĐT, ≤ 20 TC/HK (QĐ3266 Đ14 k1)."""
    thu_tu = {m: i for i, m in enumerate(ctdt)}
    ma = sorted(j["grades"], key=lambda m: thu_tu.get(m, 999))
    hk, cur, tc = [], [], 0
    for m in ma:
        c = j["grades"][m]["credits"]
        if cur and tc + c > TC_HK_MAX:
            hk.append(cur)
            cur, tc = [], 0
        cur.append(m)
        tc += c
    if cur:
        hk.append(cur)
    mien = [e["ma_hp"] for e in j.get("exemptions", []) if e.get("quyet_dinh")]
    if mien:   # bảng điểm thật: chứng chỉ ngoại ngữ in thành một dòng CC004 ở học kỳ 2
        (hk[1] if len(hk) > 1 else hk[0]).insert(0, "CC004")
    return hk


class Trang:
    def __init__(self):
        self.anh = []
        self.f = ImageFont.truetype(font(), CO)
        self.fd = ImageFont.truetype(font(dam=True), CO)
        self.moi()

    def moi(self):
        self.im = Image.new("L", (W, H), 255)
        self.d = ImageDraw.Draw(self.im)
        self.anh.append(self.im)
        self.y = 60
        self.d.text((40, 28), "Hệ thống quản lý đào tạo - Trường Đại học Cần Thơ (bản giả lập)", font=ImageFont.truetype(font(), 14), fill=0)

    def can(self, h):
        if self.y + h > H - 60:
            self.moi()

    def chu(self, x, s, dam=False, dy=0):
        self.d.text((x, self.y + dy), s, font=self.fd if dam else self.f, fill=0)

    def xuong(self, n=1):
        self.y += DONG * n


def _ngat(f, s, rong):
    """Ngắt tên dài thành hai dòng như trình duyệt."""
    if f.getlength(s) <= rong:
        return [s]
    tu, a = s.split(), ""
    for i, t in enumerate(tu):
        if f.getlength((a + " " + t).strip()) > rong:
            return [a, " ".join(tu[i:])]
        a = (a + " " + t).strip()
    return [s]


def render(j, bien_the="sach"):
    ctdt = _ctdt()
    p = Trang()
    p.chu(X["ma"], "Trường Đại Học Cần Thơ"); p.chu(785, "Mẫu In D5050A0"); p.xuong()
    p.chu(X["ma"], "Bảng Ghi Điểm Thi Học Kỳ"); p.xuong()
    p.chu(X["ma"], "Họ Và Tên"); p.chu(218, "Sinh Viên Giả Lập", dam=True); p.chu(400, "- Mã Số:"); p.chu(480, "B0000000", dam=True); p.xuong()
    p.chu(X["ma"], "Ngành"); p.chu(218, "Công nghệ thông tin (DI00V7A1)"); p.xuong(2)

    tl_diem = tl_tc = tl_tong = 0.0
    for i, ds in enumerate(chia_hoc_ky(j, ctdt)):
        p.can(DONG * 5)
        p.chu(X["ma"], f"Học Kỳ {i % 2 + 1} - Năm Học {NAM_HOC[i // 2]} (DI00V7A1)"); p.xuong(2)
        for k, s in [("ma", "Mã HP"), ("ten", "Tên Học Phần"), ("nhom", "Nhóm"), ("tc", "TC"), ("thi", "Thi"),
                     ("l2", "L2"), ("thop", "T.Hợp"), ("qd", "Q/Đổi"), ("sao", "*")]:
            p.chu(X[k], s)
        p.xuong()
        dk = hk_diem = hk_tc = tl_hk = 0
        for n, m in enumerate(ds):
            if m == "CC004":
                ten, tc = "Chứng chỉ trình độ Tiếng Anh - Bậc 3 (B1)", 10
                dong = {"tc": "10", "thi": "-2.0", "thop": "Miễn", "qd": "M", "sao": "*(BL)"}
                dk += tc
                tl_hk += tc
                tl_tong += tc          # C14: 10 TC miễn vào TC tích lũy của MỌI học kỳ sau (trước chỉ cộng ở học kỳ này)
            else:
                g = j["grades"][m]
                hp = ctdt.get(m, {"ten": f"Học phần {m}", "dieu_kien": None})
                ten = hp["ten"] + (" (*)" if hp.get("dieu_kien") else "")
                tc = g["credits"]
                diem = f"{g['thang10'] / 10:.1f}"
                dong = {"nhom": f"{(n * 7) % 40 + 1:02d}", "tc": str(tc), "thi": diem, "thop": diem,
                        "qd": g["letter"], "sao": "*" if g["letter"] != "F" else ""}
                dk += tc
                if hp.get("dieu_kien") != "gdtc":                       # R-B08
                    hk_diem += CHU_4[g["letter"]] * tc
                    hk_tc += tc
                if g["letter"] != "F":
                    tl_hk += tc
                    tl_tong += tc
                    if not hp.get("dieu_kien"):                       # R-B10
                        tl_diem += CHU_4[g["letter"]] * tc
                        tl_tc += tc
            dong_ten = _ngat(p.f, ten, TEN_MAX)
            cao = DONG * len(dong_ten)
            p.can(cao)
            dy = (cao - DONG) // 2
            p.chu(X["ma"], m, dy=dy)
            for t, s in enumerate(dong_ten):
                p.chu(X["ten"], s, dy=t * DONG)
            for k, s in dong.items():
                p.chu(X[k], s, dy=dy)
            p.y += cao
        p.can(DONG * 5)
        p.chu(X["ma"], "SHCVHT Cố vấn học tập sinh hoạt lớp"); p.chu(X["nhom"], f"D{i + 10}"); p.chu(X["tc"], "0"); p.xuong()
        p.chu(X["ma"], "Tổng Số Tín Chỉ Đăng Ký"); p.chu(400, str(dk)); p.xuong()
        p.chu(X["ma"], "Tổng Số Tín Chỉ Tích Lũy Học Kỳ"); p.chu(400, str(tl_hk))
        p.chu(X["nhom"], "Điểm T.Bình chung học kỳ (hệ 4)"); p.chu(870, f"{hk_diem / hk_tc if hk_tc else 0:.2f}"); p.xuong()
        p.chu(X["ma"], "Tổng Số Tín Chỉ Tích Lũy"); p.chu(400, str(int(tl_tong)))
        p.chu(X["nhom"], "Điểm T.Bình chung tích lũy (hệ 4)"); p.chu(870, f"{tl_diem / tl_tc if tl_tc else 0:.2f}"); p.xuong()
        p.chu(X["ma"], "Điểm Rèn Luyện"); p.chu(218, "80", dam=True); p.chu(400, "Tốt"); p.xuong(2)
    return [bien_doi(a, bien_the) for a in p.anh]


def bien_doi(im, bien_the):
    if bien_the == "sach":
        return im
    if bien_the == "mo_jpeg":   # ảnh chụp/scan chất lượng thấp
        b = io.BytesIO()
        im.filter(ImageFilter.GaussianBlur(0.8)).save(b, "JPEG", quality=35)
        return Image.open(io.BytesIO(b.getvalue())).convert("L")
    if bien_the == "nghieng":   # scan lệch
        return im.rotate(0.8, resample=Image.BICUBIC, expand=True, fillcolor=255)
    raise ValueError(bien_the)


if __name__ == "__main__":
    p = Path(sys.argv[1])
    out = HERE / "_anh"
    out.mkdir(exist_ok=True)
    for bt in ("sach", "mo_jpeg", "nghieng"):
        for i, a in enumerate(render(json.loads(p.read_text(encoding="utf-8")), bt), 1):
            a.save(out / f"{p.stem}_{bt}_{i}.png")
    print("đã ghi", out)
