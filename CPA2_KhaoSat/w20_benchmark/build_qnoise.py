"""
build_qnoise.py — Q-Noise v1: câu hỏi G-Truth gõ kiểu sinh viên (CPA2, Tuần 20)

TỔNG HỢP — đo ĐỘ BỀN parser trước cách gõ (bỏ dấu, viết tắt, gõ vội). KHÔNG đo sinh viên hỏi GÌ, KHÔNG thay Q-Real
(Q-Real vẫn chưa đạt). Gold KẾ THỪA nguyên từ ca G-Truth đã đóng băng (312b7ff): biến đổi chỉ đổi cách viết, giữ
nghĩa và giữ mã HP → đáp án đúng không đổi.

Câu gốc: mọi ca G-Truth đi qua parser (hệ nl; đăng ký một HP; tốt nghiệp; đủ điều kiện làm LVTN/TLTN), trừ ca có
dữ kiện mở (prototype chưa nhận dữ kiện mở). Chọn theo claim/đầu vào — KHÔNG theo kết quả chạy hệ thống.

Ý định kỳ vọng (claim_ky_vong, gán tay TRƯỚC khi chạy — review): claim parser phải sinh. Kết luận TRUE/FALSE
từ claim KHÁC không được tính đúng dù trùng gold (chứng chỉ chứng minh câu khác). Rỗng = chưa hỗ trợ → phải từ chối.

Biến thể (tất định — seed theo id ca gốc + biến thể):
  V0  câu gốc (mốc so sánh)
  V1  bỏ dấu ("em du dieu kien tot nghiep chua")
  V2  viết tắt (đk, tn, hp, đc, ko, e, lv, tl, hk, kì)
  V3  gõ vội: chữ thường, lời gọi đầu câu ("ad ơi cho e hỏi"), thiếu dấu một từ, bỏ/nhân đôi "?"
  V4  bỏ dấu của V2 (cùng cách viết tắt → so V2/V4 tách được ảnh hưởng của dấu)
Mã HP viết thường ở V1–V4.

Chạy:  python build_qnoise.py      → qnoise.json
"""
import json, random, re, sys, unicodedata
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "w17_adversarial"))

BIEN_THE = ("V0", "V1", "V2", "V3", "V4")
KE_THUA = ("gold", "loai_gold", "split", "dau_vao", "su_that", "can_hoi", "cham_diem", "nhom")
# câu tự nhiên (hệ nl): ý định gán tay theo câu chữ. Rỗng = prototype chưa có claim cho câu này (học phí, học bổng,
# cảnh báo, chuyển ngành, phản thực tế; xếp loại — C12) → đúng là từ chối (khong_ro / counterfactual)
Y_DINH_NL = {
    "NL-01": ['duoc_dang_ky("CT182")'], "NL-02": ['duoc_dang_ky("CT182")'], "NL-03": ["du_dk(lvtn)"],
    "NL-04": ["tot_nghiep"], "NL-05": [], "NL-06": [], "NL-07": [], "NL-08": [], "NL-09": [], "NL-10": [],
    "NL-11": ['duoc_dang_ky("CT466E")'], "NL-12": ["tot_nghiep"],
}
TU_CHOI = ("khong_ro", "counterfactual")
MA_HP = re.compile(r"\b[A-Za-z]{2}\d{3}[Ee]?\b")

# viết tắt thường gặp khi sinh viên nhắn tin — cụm dài trước; giá trị là các cách viết (chọn theo seed)
VIET_TAT = [
    ("điều kiện", ["đk", "dk"]),
    ("đăng ký", ["đk", "đki", "dky"]),
    ("tốt nghiệp", ["tn"]),
    ("học phần", ["hp"]),
    ("luận văn", ["lv"]),
    ("tiểu luận", ["tl"]),
    ("học kỳ", ["hk"]),
    ("kỳ", ["kì"]),
    ("được", ["đc", "dc"]),
    ("không", ["ko", "k"]),
    ("em", ["e"]),
]
LOI_GOI = ["ad ơi cho e hỏi", "anh chị ơi", "cho em hỏi xíu", "mn ơi"]


def la_goc(c):
    """Ca G-Truth có câu hỏi đi qua parser và không có dữ kiện mở."""
    import dau_vao
    qua_parser = (c["he"] == "nl" or c["claim"].startswith("duoc_dang_ky(") or c["claim"] == "tot_nghiep"
                  or (c["he"] == "elig" and c["claim"] in ("lvtn", "tltn")))
    return bool(qua_parser and c.get("cau_hoi") and c["cham_diem"] and not dau_vao.vat_lieu_hoa(c)["them_asp"])


def y_dinh(c):
    """claim parser phải sinh cho câu gốc c (ca hệ nl: bảng tay; còn lại: suy từ claim G-Truth)."""
    if c["he"] == "nl":
        return Y_DINH_NL[c["id"]]
    if c["he"] == "elig":
        return [f"du_dk({c['claim']})"]
    return [c["claim"]]


def bo_dau(s):
    s = unicodedata.normalize("NFD", unicodedata.normalize("NFC", s).replace("đ", "d").replace("Đ", "D"))
    return unicodedata.normalize("NFC", "".join(ch for ch in s if unicodedata.category(ch) != "Mn"))


def ma_thuong(s):
    return MA_HP.sub(lambda m: m.group(0).lower(), s)


def viet_tat(s, rd):
    s = unicodedata.normalize("NFC", s)
    for cum, cach in VIET_TAT:
        s = re.sub(rf"(?<!\w){cum}(?!\w)", lambda m: rd.choice(cach), s, flags=re.I)
    return s


def go_voi(s, rd):
    s = unicodedata.normalize("NFC", s).lower()
    tu = s.split()
    co_dau = [i for i, t in enumerate(tu) if bo_dau(t) != t and not MA_HP.fullmatch(t.strip("?.,!"))]
    if co_dau:
        i = rd.choice(co_dau)
        tu[i] = bo_dau(tu[i])
    s = " ".join(tu).rstrip("?").rstrip()
    s = re.sub(r"\s*ạ$", "", s) if rd.random() < 0.5 else s
    return f"{rd.choice(LOI_GOI)} {s}{rd.choice(['', '??', ' ?'])}"


def bien_the(q, id_):
    v2 = ma_thuong(viet_tat(q, random.Random(f"qnoise-v1|{id_}|V2")))
    return {"V0": q,
            "V1": ma_thuong(bo_dau(q)),
            "V2": v2,
            "V3": ma_thuong(go_voi(q, random.Random(f"qnoise-v1|{id_}|V3"))),
            "V4": bo_dau(v2)}


def sinh(gt):
    out = []
    for c in sorted(gt, key=lambda c: c["id"]):
        if not la_goc(c):
            continue
        for v, q in bien_the(c["cau_hoi"], c["id"]).items():
            ca = {"id": f"QN-{c['id']}-{v}", "goc": c["id"], "bien_the": v, "he": "nl", "claim": "nl",
                  "claim_goc": c["claim"], "claim_ky_vong": y_dinh(c), "cau_hoi": q}
            ca.update({k: c.get(k) for k in KE_THUA})
            out.append(ca)
    return out


def main():
    gt = json.loads((HERE / "gtruth.json").read_text(encoding="utf-8"))["cases"]
    cs = sinh(gt)
    meta = {"ten": "Q-Noise v1", "loai": "tong_hop", "nguon": "G-Truth v1 (đóng băng 312b7ff)",
            "ghi_chu": "Câu G-Truth biến đổi tự động (bỏ dấu, viết tắt, gõ vội) — đo độ bền parser. TỔNG HỢP, "
                       "KHÔNG phải câu thật, KHÔNG tính vào Q-Real. Gold kế thừa từ ca gốc.",
            "bien_the": {"V0": "câu gốc", "V1": "bỏ dấu", "V2": "viết tắt", "V3": "gõ vội", "V4": "bỏ dấu + viết tắt"},
            "so_cau_goc": len({c["goc"] for c in cs}), "so_cau": len(cs)}
    (HERE / "qnoise.json").write_text(json.dumps({"meta": meta, "cases": cs}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"đã ghi qnoise.json: {meta['so_cau_goc']} câu gốc × {len(BIEN_THE)} biến thể = {len(cs)} câu")


if __name__ == "__main__":
    main()
