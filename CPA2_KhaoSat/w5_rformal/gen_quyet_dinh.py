"""
gen_quyet_dinh.py — sinh phụ lục QUYẾT ĐỊNH DIỄN GIẢI từ r_formal_v1.json.

Vì sao phải sinh bằng máy: danh sách này đã sai lệch một lần giữa tài liệu và danh mục.
Sinh từ nguồn duy nhất (JSON) thì tài liệu không thể trôi khỏi KB.

Taxonomy Tuần 2 yêu cầu: mọi điều khoản lớp P phải "ghi rõ quyết định diễn giải trong KB
và hiển thị cho người dùng". Đây là bản hiện thực của yêu cầu đó — và là phụ lục cần đưa
vào luận văn, ở phần GIẢ ĐỊNH VÀ HẠN CHẾ, không phải phần kết quả: mỗi mục dưới đây là
điều tác giả QUYẾT, không phải điều tìm thấy trong văn bản.
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "PhuLuc_Quyet_dinh_dien_giai.md"

# Nguồn xác nhận của từng quyết định — trường duy nhất phải khai bằng tay, vì nó nói về
# một sự kiện ngoài văn bản. Để trống nghĩa là CHƯA có ai xác nhận.
NGUON = {
    "QD-01": "Câu chữ QĐ3266 Điều 22 k.5 đ.a + QĐ5339 Điều 3 k.11 (suy trực tiếp từ văn bản)",
    "QD-02": "Câu chữ QĐ3266 Điều 17 k.3; phần 'chọn phương án tối ưu' là quyết định của tác giả",
    "QD-03": "",
    "QD-04": "Quyết định của tác giả (nguyên tắc thận trọng), chưa hỏi ai",
    "QD-05": "",
    "QD-06": "Đã giải quyết bằng việc thu thập QĐ5339",
    "QD-07": "Câu chữ QĐ3266 Điều 31 k.3 (suy trực tiếp từ văn bản)",
    "QD-08": "Câu chữ QĐ5339 Điều 2 (chỉ rõ Tổ Xét miễn là người quyết định)",
    "QD-09": "XÁC NHẬN NGOÀI VĂN BẢN — CHƯA GHI RÕ NGƯỜI XÁC NHẬN VÀ NGÀY",
    "QD-10": "Câu chữ QĐ5339 Điều 3 k.3 (suy trực tiếp từ văn bản)",
    "QD-11": "Câu chữ QĐ5339 Điều 2 k.6 (suy trực tiếp từ văn bản)",
    "QD-12": "XÁC NHẬN NGOÀI VĂN BẢN — Loi, 18/10/2026 (trong phiên làm việc Tuần 18): chỉ có quy định số TC",
    "QD-13": "Câu chữ QĐ3266 Điều 7 k.5 (PDF gốc tr.5) — bản xác nhận cũ trái câu chữ (Loi 18/10/2026: học sau cũng được) ĐÃ RÚT; phần F vẫn thoả là diễn giải (Loi chọn (a), 18/10/2026)",
    "QD-14": "Quyết định của tác giả (Tuần 20, P20-1): QĐ3266 không quy định làm tròn ĐTBCTL — xếp hạng theo cận dưới, so hữu tỉ; chưa hỏi Phòng Đào tạo",
}

TRANG_THAI = [
    ("ĐÃ ĐÓNG", "đóng"), ("ĐÓNG THEO HƯỚNG", "đóng"), ("ĐÓNG MỘT PHẦN", "đóng một phần"),
    ("ĐÓNG LẠI Ở PHẠM VI HẸP HƠN", "đã sửa"), ("ĐÃ ĐÓNG (xác nhận", "đóng"),
    ("ĐÓNG TẠM", "đóng tạm"), ("SỬA", "đã sửa"), ("ĐÓNG", "đóng"), ("MỞ", "mở"),
]
BIEU_TUONG = {"đóng": "✅", "đóng một phần": "🟡", "đã sửa": "🔄", "mở": "🔴",
              "đóng tạm": "🟠", "KHÔNG RÕ": "⚠️"}


def trang_thai(text):
    sau_ma = text.split(":", 1)[0]
    for khoa, nhan in TRANG_THAI:
        if khoa in sau_ma:
            return nhan
    # không nhận ra từ khoá trạng thái → báo ra thay vì im lặng coi là "mở",
    # vì im lặng đúng là cách bảng này từng sai một lần.
    return "KHÔNG RÕ"


def main():
    cat = json.loads((HERE / "r_formal_v1.json").read_text(encoding="utf-8"))
    muc = {}
    for r in cat["rules"]:
        qd = r.get("quyet_dinh")
        if not qd:
            continue
        m = re.match(r"(QD-\d+)", qd)
        if not m:
            continue
        muc[m.group(1)] = {
            "ma": m.group(1), "noi_dung": qd, "rule": r["id"],
            "van_ban": r["van_ban"], "dieu": r["dieu"], "khoan": r["khoan"],
            "diem": r["diem"], "lop": r["lop"], "trich": r["trich"],
            "tt": trang_thai(qd),
        }

    ds = [muc[k] for k in sorted(muc)]
    dem = {}
    for d in ds:
        dem[d["tt"]] = dem.get(d["tt"], 0) + 1

    L = []
    L.append("# PHỤ LỤC — QUYẾT ĐỊNH DIỄN GIẢI TRONG R-FORMAL\n")
    L.append(f"**Sinh tự động từ** `r_formal_v1.json` (R-Formal v{cat['meta']['phien_ban']}) "
             "bằng `gen_quyet_dinh.py`. Không sửa tay file này — sửa danh mục rồi sinh lại.\n")
    L.append("> **Vị trí trong luận văn:** phụ lục này thuộc phần **giả định và hạn chế**, "
             "không thuộc phần kết quả. Mỗi mục dưới đây là điều tác giả **quyết định**, "
             "không phải điều **tìm thấy** trong văn bản quy phạm. Trộn hai loại vào nhau "
             "là cách nhanh nhất để một luận văn hình thức hoá bị bác ở phần phương pháp.\n")
    L.append(f"**Tổng: {len(ds)} quyết định** — "
             + ", ".join(f"{BIEU_TUONG[k]} {v} {k}" for k, v in sorted(dem.items())) + "\n")
    L.append("---\n")

    L.append("## Bảng tổng quan\n")
    L.append("| Mã | Trạng thái | Điều khoản liên quan | Nguồn xác nhận |")
    L.append("|---|---|---|---|")
    for d in ds:
        ct = f"{d['van_ban'].upper()} Điều {d['dieu']}"
        if d["khoan"]: ct += f" k.{d['khoan']}"
        if d["diem"]:  ct += f" đ.{d['diem']}"
        ng = NGUON.get(d["ma"]) or "**CHƯA CÓ**"
        L.append(f"| **{d['ma']}** | {BIEU_TUONG[d['tt']]} {d['tt']} | {ct} ({d['rule']}) | {ng} |")
    L.append("")

    chua = [d["ma"] for d in ds if not NGUON.get(d["ma"])]
    mau_thuan = [d["ma"] for d in ds
                 if d["tt"] == "đóng" and not NGUON.get(d["ma"])]
    if mau_thuan:
        L.append(f"> ⚠️ **Mâu thuẫn nội tại:** {', '.join(mau_thuan)} ghi là ĐÓNG nhưng "
                 "không có nguồn xác nhận. Một quyết định không thể vừa đóng vừa không có "
                 "ai đứng sau — sửa trạng thái trong `build_catalog.py` hoặc bổ sung nguồn.\n")
    ngoai = [d["ma"] for d in ds
             if NGUON.get(d["ma"]) and "ngoài văn bản" in NGUON[d["ma"]].lower()]
    L.append("### Hai nhóm cần chú ý\n")
    L.append(f"- **Chưa có nguồn xác nhận** ({len(chua)}): "
             + (", ".join(f"`{m}`" for m in chua) if chua else "không có")
             + " — đây là các quyết định treo, phải hỏi người có thẩm quyền.")
    L.append(f"- **Xác nhận NGOÀI văn bản** ({len(ngoai)}): "
             + (", ".join(f"`{m}`" for m in ngoai) if ngoai else "không có")
             + " — hợp lệ, nhưng **bắt buộc ghi rõ ai xác nhận và ngày nào**; "
               "nếu là trao đổi miệng thì nên xin email hoặc ghi biên bản.\n")
    L.append("---\n")

    L.append("## Chi tiết từng quyết định\n")
    for d in ds:
        ct = f"{d['van_ban'].upper()} Điều {d['dieu']}"
        if d["khoan"]: ct += f" khoản {d['khoan']}"
        if d["diem"]:  ct += f" điểm {d['diem']}"
        L.append(f"### {BIEU_TUONG[d['tt']]} {d['ma']} — {d['tt']}\n")
        L.append(f"**Điều khoản:** {ct} · bản ghi `{d['rule']}` · lớp **{d['lop']}**\n")
        L.append(f"**Trích nguyên văn:**\n")
        L.append(f"> *{d['trich']}*\n")
        L.append(f"**Quyết định:** {d['noi_dung']}\n")
        ng = NGUON.get(d["ma"])
        L.append(f"**Nguồn xác nhận:** {ng if ng else '**CHƯA CÓ — cần hỏi người có thẩm quyền**'}\n")
        L.append("")

    L.append("---\n")
    L.append("## Ghi chú phương pháp\n")
    L.append("Ba loại quyết định trong bảng này khác hẳn nhau về mức độ chắc chắn, và "
             "luận văn nên trình bày tách bạch:\n")
    L.append("1. **Suy trực tiếp từ câu chữ** (QD-01, QD-07, QD-10, QD-11 …) — thực chất "
             "không phải \"quyết định\" mà là kết quả đọc kỹ. Độ chắc chắn cao nhất.")
    L.append("2. **Phân giải một chỗ văn bản để mở, có người xác nhận** (QD-09) — hợp lệ, "
             "nhưng phụ thuộc lời của một người, nên phải ghi nguồn.")
    L.append("3. **Tác giả tự quyết vì không có ai để hỏi** (QD-04) — yếu nhất; phải nêu rõ "
             "là lựa chọn của tác giả và nêu phương án thay thế đã cân nhắc.\n")
    L.append("Không phải mục nào chưa \"đóng gọn\" cũng là việc làm dở. Cần tách hai loại:\n")
    L.append("- **QD-03** (*định nghĩa \"TC nợ đọng\"*) là thiếu thông tin thật: hỏi Phòng Đào "
             "tạo một câu là xong. Đây là hạng mục tồn đọng.")
    L.append("- **QD-05** (*thời hạn bổ sung điểm I do giảng viên quy định*) và **QD-08** "
             "(*tiêu chí \"tương đương\" do Tổ Xét miễn quyết*) là **thẩm quyền mở thật sự**: "
             "quy chế CỐ Ý để cho một con người quyết, nên đọc thêm bao nhiêu văn bản cũng "
             "không làm chúng biến mất. QD-08 đã \"đóng\" theo nghĩa đã xác định được AI quyết, "
             "chứ không theo nghĩa hệ thống tự tính được. Cả hai là **kết quả của RQ1** — bằng "
             "chứng cho luận điểm rằng một phần quy chế học vụ không thể tự động hoá — và nên "
             "được báo cáo như phát hiện, không như hạng mục tồn đọng.\n")

    OUT.write_text("\n".join(L), encoding="utf-8")
    print(f"Đã ghi {OUT} — {len(ds)} quyết định.")
    print(f"  chưa có nguồn xác nhận: {chua}")
    print(f"  xác nhận ngoài văn bản: {ngoai}")
    if mau_thuan:
        print(f"  ⚠️  MÂU THUẪN (đóng nhưng không nguồn): {mau_thuan}")


if __name__ == "__main__":
    main()
