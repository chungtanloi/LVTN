"""
build_bieu_mau.py — nội dung Google Form thu câu hỏi học vụ: Q-Elicit (kịch bản) + Q-Real (câu tự do) (CPA2, Tuần 20)

Nguồn: qreal/kich_ban_q_elicit.json (viết tay). Sinh qreal/bieu_mau.md để Loi dán vào Google Form — tiêu đề từng câu
hỏi giữ NGUYÊN mã trong ngoặc vuông ([DONG_Y], [BO], [KB-xx], [TU_DO-n]) vì nhap_qreal.doc_bieu_mau đọc CSV xuất từ
Google Sheets theo các mã này.

Dữ liệu cá nhân (Nghị định 13/2023/NĐ-CP): biểu mẫu KHÔNG hỏi tên, MSSV, email, SĐT, ngày/tháng sinh; bộ kịch bản do
người trả lời tự chọn một số 1–4. Phần đồng ý nêu người thu + liên hệ (chỗ <<ĐIỀN>> — Loi điền trước khi mở form), mục
đích, nơi lưu (kho mã GitHub, có thể công khai) + dịch vụ AI dùng để so sánh, thời hạn xoá bản thô, quyền rút lại bằng
mã tự đặt. Người không đồng ý → kết thúc biểu mẫu (nhap_qreal vẫn loại dòng không đồng ý).

Thứ tự (review): câu TỰ DO (Q-Real) hỏi TRƯỚC mọi kịch bản; mọi chữ đứng trước nó không chứa cụm từ parser (B11e2).

Chống mớm lời (B11c): tình huống không được chứa cụm từ mà parser dựa vào — `mom()` kiểm trên câu đã chuẩn hoá bằng
chính prototype.chuan_hoa (bỏ dấu từ khoá + mở viết tắt), nên bắt được cả dạng không dấu.

Chạy:  python build_bieu_mau.py      → qreal/bieu_mau.md
"""
import hashlib, json, re, sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "w12_integration"))
KICH_BAN = HERE / "qreal" / "kich_ban_q_elicit.json"
BIEU_MAU = HERE / "qreal" / "bieu_mau.md"

# cụm từ parser (w12 prototype.parse_question) dựa vào để nhận ý định — trên dạng đã chuẩn hoá
MOM = [r"dieu kien", r"dang ky", r"tot nghiep", r"ra truong", r"luan van", r"tieu luan", r"duoc khong", r"duoc chua",
       r"\bmien\b", r"con thieu", r"xep loai", r"xep hang", r"\bneu\b", r"\bnen\b", r"de xuat", r"dtbctl",
       r"nhan de tai"]


def doc_kich_ban():
    return json.loads(KICH_BAN.read_text(encoding="utf-8"))


def hash_kich_ban(kb):
    """Hash nội dung kịch bản (đóng băng TRƯỚC khi mở biểu mẫu — B11h)."""
    return hashlib.sha256(json.dumps(kb["kich_ban"], ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def mom(tinh_huong):
    """Các cụm từ mớm lời có trong tình huống (rỗng = đạt)."""
    import prototype
    s = prototype.chuan_hoa(tinh_huong)
    return [m for m in MOM if re.search(m, s)]


def sinh_bieu_mau(kb):
    ds = kb["kich_ban"]
    bo = sorted({k["bo"] for k in ds})
    L = [
        "# Biểu mẫu thu câu hỏi học vụ — nội dung để dán vào Google Form",
        "",
        "<!-- SINH TỰ ĐỘNG bởi build_bieu_mau.py từ qreal/kich_ban_q_elicit.json — sửa kịch bản rồi chạy lại, không sửa tay. -->",
        "",
        "> **Cho người tạo form.** Mỗi tiêu đề `###` bên dưới là MỘT câu hỏi trên Google Form: chép NGUYÊN tiêu đề, "
        "kể cả mã trong ngoặc vuông, vì bộ nhập đọc CSV theo các mã này.",
        ">",
        "> **Trước khi mở form:** thay mọi chỗ `<<ĐIỀN: …>>` bằng thông tin thật.",
        ">",
        "> **Cài đặt Google Form:**",
        "> - Tắt *Thu thập địa chỉ email*.",
        "> - Không bật *Giới hạn 1 câu trả lời*, vì tuỳ chọn này bắt đăng nhập.",
        "> - Tắt *Cho phép chỉnh sửa sau khi gửi*.",
        ">",
        "> Dùng *Chuyển đến phần dựa trên câu trả lời* cho `[DONG_Y]` và `[BO]`. Google Form luôn có nút *Quay lại*, nên "
        "câu tự do vẫn có thể bị sửa sau khi đọc kịch bản (đã nhắc người trả lời; ghi là hạn chế).",
        ">",
        "> **Sau khi đóng form:**",
        "> 1. Tải CSV từ Trang tính.",
        "> 2. Đặt file vào `w20_benchmark/qreal/_tho/` (gitignore).",
        "> 3. Chạy `python nhap_qreal.py`.",
        "> 4. Rà tay `qreal.json` và `qelicit.json` trước khi commit.",
        "> 5. Xoá bản thô (Trang tính + CSV) đúng hạn đã ghi ở phần đồng ý.",
        ">",
        "> Người trả lời muốn rút lại thì chạy `python nhap_qreal.py --rut <mã>`.",
        "",
        "## Tiêu đề và mô tả form",
        "",
        "**Tiêu đề:** Bạn thường hỏi gì về chuyện học ở trường? (khảo sát khoảng 5 phút)",
        "",
        "**Mô tả:** Mình là sinh viên ĐH Cần Thơ, đang làm đề tài nghiên cứu cuối khoá về một trợ lý trả lời câu hỏi "
        "học vụ. Mình cần biết sinh viên THẬT SỰ hỏi như thế nào, vì vậy bạn cứ viết đúng như khi nhắn cho bạn bè hay "
        "cố vấn học tập: không dấu, viết tắt, sai chính tả đều ổn.",
        "",
        "## Phần 0 — Đồng ý tham gia",
        "",
        "### [DONG_Y] Bạn có đồng ý cho dùng câu hỏi bạn viết cho đề tài này không?",
        "",
        "*Trắc nghiệm, bắt buộc.* Nội dung giải thích (đặt trong phần mô tả của câu hỏi):",
        "",
        "- **Người thu dữ liệu:** <<ĐIỀN: họ tên>>, sinh viên ĐH Cần Thơ. Liên hệ: <<ĐIỀN: email liên hệ>>.",
        "- **Mục đích:** đánh giá trợ lý trả lời câu hỏi học vụ trong đề tài nghiên cứu cuối khoá. Một số câu có thể "
        "được trích nguyên văn trong báo cáo.",
        "- **Ẩn danh:** biểu mẫu không hỏi tên, mã số sinh viên, email, số điện thoại hay ngày sinh. Xin đừng ghi các "
        "thông tin này vào câu trả lời. Lỡ ghi thì mình sẽ xoá khi rà tay.",
        "- **Nơi lưu:** câu trả lời đã ẩn danh và rà tay được lưu trong kho mã nguồn của đề tài trên GitHub (có thể "
        "công khai). Câu trả lời cũng có thể được gửi tới dịch vụ AI (OpenAI, Google Gemini) để so sánh với trợ lý. "
        "Dữ liệu không dùng cho mục đích khác.",
        "- **Thời hạn:** bản thô (Trang tính, file CSV, cùng mã rút) được xoá ngay sau khi nhập và rà, chậm nhất "
        "<<ĐIỀN: ngày>>.",
        "- **Rút lại:** bạn có thể tự đặt một mã rút ở câu tiếp theo. Muốn rút, gửi mã đó qua liên hệ ở trên trước "
        "<<ĐIỀN: ngày>> (ngày xoá bản thô); mình sẽ xoá các câu đi kèm mã khỏi dữ liệu và các lần cập nhật sau. Không đặt "
        "mã, hoặc sau ngày đó, thì mình không thể biết câu nào là của bạn.",
        "- **Giới hạn của việc rút lại:** phần đã nằm trong lịch sử kho mã (các phiên bản cũ trên GitHub), đã đưa vào "
        "báo cáo, hoặc đã gửi tới dịch vụ AI thì mình không thể thu hồi.",
        "- **Tự nguyện:** tham gia là tự nguyện. Ngoài câu đồng ý và câu chọn bộ, mọi câu đều không bắt buộc.",
        "",
        "Lựa chọn:",
        "- `Tôi đồng ý` → chuyển đến câu tiếp theo",
        "- `Không đồng ý` → *Gửi biểu mẫu* (kết thúc)",
        "",
        "### [MA_RUT] Mã rút lại do bạn tự đặt (không bắt buộc)",
        "",
        "*Trả lời ngắn.* Tối thiểu 6 ký tự ngẫu nhiên, phân biệt hoa/thường, ví dụ `k7Mq2x`. Đừng dùng ngày sinh, "
        "mã số sinh viên, số điện thoại hay mật khẩu. Mã chỉ dùng để tìm câu của bạn khi bạn muốn rút, không đưa lên kho "
        "mã và được xoá cùng bản thô.",
        "",
        "## Phần 1 — Câu hỏi của chính bạn",
        "",
        "*Mô tả phần:* Bạn đã từng thật sự muốn hỏi gì về chuyện học ở trường? Mỗi ô một câu, viết đúng như bạn đã hỏi "
        "hoặc định hỏi. Không nghĩ ra thì bỏ trống.",
        "",
    ]
    for n in (1, 2, 3):
        L += [f"### [TU_DO-{n}] Câu hỏi {n}", "", "*Đoạn văn, không bắt buộc.*", ""]
    L += ["## Phần 2 — Chọn bộ tình huống", "",
          "### [BO] Chọn một số bất kỳ từ 1 đến 4", "",
          "*Trắc nghiệm, bắt buộc. Chỉ dùng để chia bạn vào một bộ tình huống.* Mô tả phần: sau bước này, xin đừng "
          "quay lại sửa câu ở Phần 1.", ""]
    L += [f"- `{b}` → chuyển đến *Bộ tình huống {b}*" for b in bo]
    for b in bo:
        L += ["", f"## Bộ tình huống {b}", "",
              "*Mô tả phần:* Đọc từng tình huống, rồi viết câu bạn sẽ hỏi (nhắn cho bạn bè, cố vấn học tập hay "
              "trợ lý ảo) trong tình huống đó. Viết bằng lời của bạn, không cần giống tình huống. Không biết hỏi gì thì "
              "bỏ trống. Cuối phần → *Gửi biểu mẫu*.", ""]
        for k in [k for k in ds if k["bo"] == b]:
            L += [f"### [{k['id']}] {k['tinh_huong']}", "", "*Đoạn văn (trả lời dài), không bắt buộc.*", ""]
    L += ["## Lời cảm ơn (thông báo xác nhận)", "", "Cảm ơn bạn đã giúp! Câu hỏi của bạn giúp trợ lý hiểu sinh viên "
          "hỏi thật như thế nào.", ""]
    return "\n".join(L)


def main():
    kb = doc_kich_ban()
    loi = [(k["id"], m) for k in kb["kich_ban"] for m in mom(k["tinh_huong"])]
    if loi:
        print("MỚM LỜI — sửa tình huống trước:", loi)
        return 1
    BIEU_MAU.write_text(sinh_bieu_mau(kb), encoding="utf-8")
    print(f"đã ghi {BIEU_MAU.relative_to(HERE)} ({len(kb['kich_ban'])} kịch bản)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
