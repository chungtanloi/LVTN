"""
muc_tieu.py — diễn giải ý định "mục tiêu hạng tốt nghiệp" (CPA2, Tuần 24).

Luật nằm ở muc_tieu_hang.lp (phép tính chính xác trên R-B10, R-F06, R-F07). Module này chỉ:
  - đọc kết quả của TỪNG thế giới (answer set) → kịch bản (kết quả, N, D, X, ngưỡng hiệu lực, có bị hạ một mức không);
  - ba trị: mọi thế giới cùng một kết quả → TRUE (đạt được) / FALSE (không thể); khác nhau → UNKNOWN, nêu từng kịch bản;
  - dựng lời giải thích tiếng Việt. Số hiển thị: ĐTBCTL hiện tại và mức tối đa CẮT xuống 2 chữ số (QD-14: không làm
    tròn lên), mức trung bình CẦN đạt LÀM TRÒN LÊN 2 chữ số (để con số nêu ra luôn đủ).
Ngưỡng hạng đọc từ atom nguong_mt/2 của solver (không chép tay hang/2). Không dự đoán điểm, không khuyên "nên".
"""
import re
from pathlib import Path

LP = Path(__file__).parent / "muc_tieu_hang.lp"
TEN = {"xuat_sac": "xuất sắc", "gioi": "giỏi", "kha": "khá", "trung_binh": "trung bình"}
CHU = [(10, "D"), (15, "D+"), (20, "C"), (25, "C+"), (30, "B"), (35, "B+"), (40, "A")]   # điểm thang 4 ×10 (band/4)
TRAN_TC_HK = 20                                                             # QĐ3266 Điều 14 khoản 1 (R-Formal)


def so(x100):
    """số nguyên ×100 → '3,70'"""
    return f"{x100 // 100},{x100 % 100:02d}"


def _gt(m, ten):
    for a in m:
        if a.startswith(ten + "("):
            return int(a[len(ten) + 1:-1])
    return None


def ket_qua(m, h):
    """Một thế giới → (atom kết quả, N, D, X, ngưỡng hiệu lực ×100 | None, bị hạ?)."""
    kq = next((a for a in m if a.startswith((f"mt_can({h},", f"mt_khong_the({h},"))
               or a in (f"mt_chi_can_qua({h})", f"mt_da_dat({h})")), None)
    l = next((int(a[:-1].split(",")[1]) for a in m if a.startswith(f"nguong_mt({h},")), None)
    return kq, _gt(m, "tl_tu"), _gt(m, "tl_mau"), _gt(m, "tc_xet"), l, "mt_ha" in m


def kich_ban(models, h):
    """Các kịch bản có KẾT QUẢ khác nhau (không bị hạ trước). Cờ 'bị hạ' không phải là kết quả: cùng một kết quả ở cả
    thế giới bị hạ và không bị hạ (vd. mục tiêu khá) là MỘT kịch bản — cờ None."""
    co = {}
    for m in models:
        k = ket_qua(m, h)
        co.setdefault(k[:5], set()).add(k[5])
    ds = [k + ((next(iter(f)) if len(f) == 1 else None),) for k, f in co.items()]
    return sorted(ds, key=lambda k: (bool(k[5]), k[0] or ""))


def kha_thi(atom):
    return bool(atom) and atom.startswith(("mt_can(", "mt_chi_can_qua(", "mt_da_dat("))


def mo_ta(h, kb, tc_noi):
    """Một kịch bản → câu tiếng Việt. tc_noi: True nếu X do câu hỏi nêu (học kỳ tới), False nếu là TC tối thiểu còn lại."""
    atom, n, d, x, l, ha = kb
    cur = so(n * 10 // d) if d else None
    ve_x = f"{x} TC sắp học" if tc_noi else f"{x} TC tối thiểu còn phải tích lũy (có tính điểm) để tốt nghiệp"
    if atom is None:
        return "chưa tính được (chưa có ĐTBCTL)"
    if atom.endswith(",ha_bac)"):
        return ("không thể đạt loại xuất sắc: hạng xuất sắc và giỏi bị giảm một mức khi khối lượng học phần bị điểm F vượt "
                "quá năm phần trăm tổng TC của CTĐT hoặc đã bị kỷ luật từ mức cảnh cáo cấp Trường (QĐ3266 Điều 34 khoản 2)")
    if atom.startswith("mt_can("):
        s = int(atom[:-1].split(",")[1])
        can = -(-s * 10 // x)                          # ⌈S/(10X)⌉ ×100 — làm tròn LÊN
        chu = next(c for p, c in CHU if p * x >= s)
        return (f"với {ve_x}, cần điểm trung bình (thang 4) tối thiểu {so(can)} trên {x} TC đó"
                f" (ĐTBCTL ≥ {so(l)}) — ví dụ mọi học phần đạt {chu} trở lên là đủ")
    if atom.startswith("mt_chi_can_qua("):
        return f"với {ve_x}, chỉ cần đạt mọi học phần (từ D trở lên) là ĐTBCTL vẫn ≥ {so(l)}"
    if atom.startswith("mt_da_dat("):
        return f"bạn đã tích lũy đủ TC tối thiểu và ĐTBCTL hiện tại {cur} đã ≥ {so(l)}"
    if atom.endswith(",het_tc)"):
        return (f"bạn đã tích lũy đủ TC tối thiểu; nếu không học thêm học phần nào thì ĐTBCTL giữ {cur} < {so(l)} — "
                "không thể đạt")
    toi_da = (n + 40 * x) * 10 // (d + x)              # cắt xuống
    return f"không thể: kể cả đạt A mọi học phần trong {ve_x}, ĐTBCTL tối đa chỉ {so(toi_da)} < {so(l)}"


def tong_hop(kbs, tc_noi):
    """Ba trị theo KHẢ THI trên mọi thế giới (review H1): mọi kịch bản đạt được → TRUE, không kịch bản nào → FALSE,
    lẫn lộn → UNKNOWN. Review H2: khi X là số TC TỐI THIỂU (câu hỏi không nêu số TC), 'không thể' vì điểm chỉ đúng với
    số TC tối thiểu — học thêm học phần thì khác → không kết luận FALSE, hỏi số TC dự định (can_tc). Riêng 'không thể vì
    bị hạ một mức' (ha_bac) thì học thêm cũng không đổi. Trả (verdict, can_tc)."""
    kt = [kha_thi(k[0]) for k in kbs]
    verdict = "TRUE" if all(kt) else "FALSE" if not any(kt) else "UNKNOWN"
    can_tc = (not tc_noi and verdict != "TRUE"
              and any(not kha_thi(k[0]) and not k[0].endswith(",ha_bac)") for k in kbs))
    return ("UNKNOWN" if can_tc else verdict), can_tc


def _nhan(k):
    """Nhãn kịch bản: theo cờ hạ bậc; kịch bản khác nhau vì lý do khác (tích lũy, tự chọn) → nêu ĐTBCTL của nó."""
    if k[5] is True:
        return "nếu bị hạ một mức (Đ34 k2): "
    if k[5] is False:
        return "nếu không bị hạ một mức: "
    return f"trường hợp ĐTBCTL {so(k[1] * 10 // k[2])} trên {k[2]} TC: " if k[2] else ""


def dien_giai(h, kbs, tc_noi, verdict, can_tc, hoi=()):
    """Danh sách kịch bản + kết luận → lời giải thích tiếng Việt."""
    _, n, d, _, _, _ = kbs[0]
    dau = f"Mục tiêu: tốt nghiệp từ loại {TEN[h]} trở lên."
    if len(kbs) == 1:
        than = mo_ta(h, kbs[0], tc_noi)
        than = than[0].upper() + than[1:] + "."
    else:
        mo = {"TRUE": "Đạt được, nhưng mức cần tùy dữ kiện: ", "FALSE": "Không thể trong mọi trường hợp: ",
              "UNKNOWN": "Chưa chắc — tùy dữ kiện: "}[verdict]
        than = mo + "; ".join(_nhan(k) + mo_ta(h, k, tc_noi) for k in kbs) + "."
    if can_tc:
        than += (" Kết quả trên chỉ tính số tín chỉ tối thiểu còn lại; nếu học thêm học phần ngoài mức tối thiểu thì kết quả "
                 "có thể khác — hãy hỏi theo số tín chỉ dự định, ví dụ: \"kỳ tới em học 18 tín chỉ thì cần trung bình bao "
                 f"nhiêu để tốt nghiệp loại {TEN[h]}\".")
    if hoi:
        than += " Còn thiếu: " + " ".join(hoi)
    hien = f" ĐTBCTL hiện tại: {so(n * 10 // d)} trên {d} TC." if d else ""
    gia_dinh = (" Giả định: đạt mọi học phần sắp học, không tính học cải thiện điểm. Đây là phép tính theo quy chế,"
                " không phải dự đoán.")
    return f"{dau} {than}{hien}{gia_dinh}"


def tach_claim(claim):
    """'muc_tieu_hang(gioi)' / 'muc_tieu_hang(gioi,18)' → ('gioi', None | 18)."""
    m = re.fullmatch(r"muc_tieu_hang\((\w+)(?:,(\d+))?\)", claim)
    return m.group(1), (int(m.group(2)) if m.group(2) else None)
