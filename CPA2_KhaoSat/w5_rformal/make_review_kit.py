"""
make_review_kit.py — sinh bộ công cụ SOÁT CHÉO ĐỘC LẬP cho danh mục R-Formal.

Vì sao cần: toàn bộ nhãn F/P/N trong r_formal_v1.json hiện do MỘT người gán. Với một
bộ dữ liệu định công bố, đây là hạn chế phương pháp lớn nhất còn lại của RQ1, và nó
KHÔNG sửa được bằng cách thêm điều khoản — chỉ sửa được bằng một người gán nhãn thứ hai.

Sinh ra hai thứ:
  1. phieu_gan_nhan_mu.xlsx — phiếu gán nhãn MÙ: chỉ có trích nguyên văn + con trỏ
     nguồn, KHÔNG có nhãn của người thứ nhất, không có ghi chú, không có mã ASP.
     Người thứ hai điền cột "lop" (F/P/N) và "du_lieu" (co/khong).
  2. tinh_kappa.py — script tính Cohen's kappa giữa phiếu đã điền và danh mục gốc,
     kèm ma trận nhầm lẫn và danh sách các đơn vị bất đồng để hai người ngồi lại.

Cách dùng:
    python3 make_review_kit.py                  # sinh phiếu
    (gửi phieu_gan_nhan_mu.xlsx cho người thứ hai điền)
    python3 tinh_kappa.py phieu_da_dien.xlsx    # tính kappa

Cỡ mẫu: mặc định lấy TOÀN BỘ 71 đơn vị trong miền. Nếu người soát chỉ có thời gian cho
một phần, dùng --n 20 để lấy mẫu ngẫu nhiên có seed cố định (tái lập được), phân tầng
theo nhóm điều khoản để không dồn hết vào một nhóm dễ.
"""
import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

HERE = Path(__file__).parent
CAT = HERE / "r_formal_v1.json"
OUT = HERE / "phieu_gan_nhan_mu.xlsx"
SEED = 20260904


def lay_mau(rules, n):
    """Lấy mẫu phân tầng theo nhóm điều khoản, seed cố định để tái lập."""
    if n is None or n >= len(rules):
        return rules
    theo_nhom = defaultdict(list)
    for r in rules:
        theo_nhom[r["nhom"]].append(r)
    rng = random.Random(SEED)
    for v in theo_nhom.values():
        rng.shuffle(v)
    chon, i = [], 0
    nhom = sorted(theo_nhom)
    while len(chon) < n:                      # rút vòng tròn qua các nhóm
        tien = False
        for g in nhom:
            if i < len(theo_nhom[g]) and len(chon) < n:
                chon.append(theo_nhom[g][i]); tien = True
        if not tien:
            break
        i += 1
    return sorted(chon, key=lambda r: r["id"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=None,
                    help="số đơn vị đưa vào phiếu (mặc định: tất cả 71)")
    args = ap.parse_args()

    cat = json.loads(CAT.read_text(encoding="utf-8"))
    inm = [r for r in cat["rules"] if r["lop"] != "X"]
    mau = lay_mau(inm, args.n)

    wb = openpyxl.Workbook()

    # ---- Sheet 1: hướng dẫn ------------------------------------------------
    hd = wb.active
    hd.title = "Hướng dẫn"
    dong = [
        ("PHIẾU GÁN NHÃN ĐỘC LẬP — R-Formal (CPA², Tuần 5)", True),
        ("", False),
        (f"Số đơn vị cần gán nhãn: {len(mau)}", False),
        ("Người gán nhãn: ......................    Ngày: ......................", False),
        ("", False),
        ("MỤC ĐÍCH", True),
        ("Đo mức đồng thuận giữa hai người gán nhãn độc lập trên cùng một danh mục "
         "điều khoản.", False),
        ("Bạn KHÔNG được xem nhãn của người thứ nhất — phiếu này cố ý bỏ trống.", False),
        ("", False),
        ("CÁCH ĐIỀN — sang sheet 'Phiếu', điền hai cột:", True),
        ("", False),
        ("Cột 'lop' — khả năng hình thức hoá, chọn F / P / N:", True),
        ("   F = dịch trọn vẹn sang logic thực thi được, không mất thông tin.", False),
        ("   P = dịch được phần lõi, nhưng còn một tham số hoặc một cách hiểu phải do", False),
        ("       CON NGƯỜI quyết định mới chạy được.", False),
        ("   N = không dịch được: kết quả phụ thuộc quyết định hành chính của một người,", False),
        ("       hoặc điều khoản chỉ trỏ sang một văn bản khác, hoặc ngôn ngữ để mở.", False),
        ("", False),
        ("Cột 'du_lieu' — dữ kiện cần thiết có nằm trong phạm vi dữ liệu của hệ thống", True),
        ("(bảng điểm + chương trình đào tạo + hồ sơ sinh viên) hay không: co / khong.", False),
        ("   Đây là câu hỏi TÁCH BIỆT với cột 'lop'. Một điều khoản có thể vừa F vừa", False),
        ("   'khong' — ví dụ quy định về tỷ lệ dự lớp: ngưỡng rất rõ (nên là F) nhưng", False),
        ("   dữ liệu điểm danh không có trong bảng điểm (nên là 'khong').", False),
        ("", False),
        ("Cột 'ghi_chu' — tuỳ chọn, ghi lý do khi bạn thấy phân vân.", False),
        ("", False),
        ("LƯU Ý", True),
        ("Chỉ đọc cột 'trich' để quyết định. Nếu cần tra toàn văn, mở file PDF gốc theo", False),
        ("con trỏ (văn bản / điều / khoản / điểm) ở các cột bên trái.", False),
        ("Đừng trao đổi với người gán nhãn thứ nhất TRƯỚC khi điền xong — trao đổi làm", False),
        ("hỏng phép đo. Sau khi điền xong thì nên ngồi lại để giải quyết các chỗ lệch.", False),
    ]
    for i, (txt, dam) in enumerate(dong, start=1):
        c = hd.cell(i, 1, txt)
        if dam:
            c.font = Font(bold=True)
    hd.column_dimensions["A"].width = 100

    # ---- Sheet 2: phiếu ----------------------------------------------------
    ws = wb.create_sheet("Phiếu")
    header = ["id", "van_ban", "dieu", "khoan", "diem", "trich", "lop", "du_lieu", "ghi_chu"]
    fill = PatternFill("solid", fgColor="DDEBF7")
    vang = PatternFill("solid", fgColor="FFF2CC")
    for j, h in enumerate(header, start=1):
        c = ws.cell(1, j, h)
        c.font = Font(bold=True)
        c.fill = fill
    for i, r in enumerate(mau, start=2):
        ws.cell(i, 1, r["id"])
        ws.cell(i, 2, r["van_ban"])
        ws.cell(i, 3, r["dieu"] if r["dieu"] else "Phụ lục")
        ws.cell(i, 4, "" if r["khoan"] is None else r["khoan"])
        ws.cell(i, 5, "" if r["diem"] is None else r["diem"])
        c = ws.cell(i, 6, r["trich"])
        c.alignment = Alignment(wrap_text=True, vertical="top")
        ws.cell(i, 7).fill = vang          # lop  — để trống
        ws.cell(i, 8).fill = vang          # du_lieu — để trống
        ws.row_dimensions[i].height = 60

    dv_lop = DataValidation(type="list", formula1='"F,P,N"', allow_blank=True)
    dv_dl = DataValidation(type="list", formula1='"co,khong"', allow_blank=True)
    ws.add_data_validation(dv_lop); ws.add_data_validation(dv_dl)
    dv_lop.add(f"G2:G{len(mau)+1}")
    dv_dl.add(f"H2:H{len(mau)+1}")

    for col, w in zip("ABCDEFGHI", (10, 10, 8, 8, 8, 95, 8, 10, 40)):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A2"

    wb.save(OUT)
    print(f"Đã ghi {OUT} — {len(mau)} đơn vị cần gán nhãn.")
    print("Phiếu KHÔNG chứa nhãn của người thứ nhất (gán nhãn mù).")
    print("Bước tiếp theo: gửi phiếu cho người soát, rồi chạy  python3 tinh_kappa.py <file đã điền>")


if __name__ == "__main__":
    main()
