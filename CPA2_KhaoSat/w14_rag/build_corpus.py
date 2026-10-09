"""
build_corpus.py — sinh corpus truy hồi cho RAG grounding (CPA2, Tuần 14)

Đơn vị truy hồi = (văn bản, điều, khoản) — trùng mức trích dẫn của rule_src/why ở Tuần 11,
nên một passage có thể đối chiếu thẳng với bước chứng minh trong certificate.

Ba nguồn, theo thứ tự tin cậy:
  1. trích R-Formal (r_formal_v1.json, đối chiếu tay với ảnh PDF)   — gắn vào passage tương ứng
  2. OCR toàn văn (w5_rformal/source/*_ocr_raw.txt)                — thân passage
  3. Curriculum KB (curriculum_cntt_k49.json)                       — passage CTĐT (học phần, nhóm)

Trang OCR trắng (QĐ3266 trang 20 → Điều 33–35) KHÔNG làm mất passage: điều/khoản nào có quy tắc
R-Formal mà OCR không có thì passage được dựng từ trích R-Formal, gắn nguon="trich_r_formal".

Chạy: python build_corpus.py   → corpus.jsonl + corpus_report.txt
"""
import json, re, sys
from pathlib import Path

HERE = Path(__file__).parent
W5 = HERE.parent / "w5_rformal"
W6 = HERE.parent / "w6_curriculum"
CATALOG = W5 / "r_formal_v1.json"
CURRICULUM = W6 / "curriculum_cntt_k49.json"
OCR = {
    "qd3266": W5 / "source" / "QD3266_ocr_raw.txt",
    "qd5339": W5 / "source" / "QD5339_ocr_raw.txt",
}
TEN_VB = {"qd3266": "QĐ3266", "qd5339": "QĐ5339"}
# Trang bắt đầu phần quy định (bỏ quyết định ban hành ở trang 1–2) và trang kết thúc
# (QĐ5339: sau Phụ lục 1 là các mẫu đơn, trang 13–19 — không phải quy định)
TRANG_DAU = {"qd3266": 3, "qd5339": 3}
TRANG_CUOI = {"qd3266": 99, "qd5339": 12}

RE_TRANG = re.compile(r"^===== TRANG (\d+) =====")
RE_DIEU = re.compile(r"^[\W_]{0,3}Điều (\d+)\.\s*(.*)")
# OCR làm hỏng dấu sau số khoản: "2 Điểm", "5, Các", "10.SV" → chấp nhận . hoặc , tuỳ chọn,
# miễn là ký tự kế tiếp là chữ HOA (loại "3,60 - 4,00", "2.50") và số khoản đúng thứ tự.
RE_KHOAN = re.compile(r"^[\W_]{0,3}(\d{1,2})(?:[.,]\s*|\s+)(?=[A-ZĐÀ-Ỹ])")
RE_PHU_LUC = re.compile(r"^Phụ lục (\d+)\s+(.*)")


def pid(vb, dieu, khoan):
    return f"{vb}:D{dieu}:K{khoan or 0}"


def clean(lines):
    s = " ".join(l.strip() for l in lines if l.strip())
    s = re.sub(r"\s+", " ", s)
    return s.strip(" _")


def parse_ocr(vb, path):
    """Tách OCR thành passage theo điều/khoản. Số điều và số khoản phải tăng đơn điệu —
    tham chiếu chéo kiểu 'xem Điều 24' hay danh sách đánh số trong khoản không mở passage mới."""
    passages = {}
    trang = 0
    dieu, tieu_de, khoan = None, "", 0
    buf, trang_buf = [], None

    def flush():
        if dieu is not None and buf:
            text = clean(buf)
            if len(text) >= 15:
                passages[pid(vb, dieu, khoan)] = {
                    "van_ban": vb, "dieu": dieu, "khoan": khoan or None,
                    "tieu_de": tieu_de, "trang": trang_buf, "ocr": text,
                }

    for raw in path.read_text(encoding="utf-8").splitlines():
        m = RE_TRANG.match(raw)
        if m:
            trang = int(m.group(1))
            continue
        if trang < TRANG_DAU[vb] or trang > TRANG_CUOI[vb]:
            continue
        line = raw.strip()
        m = RE_PHU_LUC.match(line)
        if m:
            flush()
            dieu, tieu_de, khoan = f"PL{m.group(1)}", m.group(2), 0
            buf, trang_buf = [], trang
            continue
        m = RE_DIEU.match(line)
        if m and (dieu is None or (isinstance(dieu, int) and int(m.group(1)) > dieu)):
            flush()
            dieu, tieu_de, khoan = int(m.group(1)), m.group(2).strip(" :"), 0
            buf, trang_buf = [], trang
            continue
        m = RE_KHOAN.match(line)
        # cho nhảy cóc 1 khoản: khoản k+1 bị OCR làm nát hẳn ("+," thay "4.") thì k+2 vẫn mở
        # passage mới; nội dung khoản bị nát nằm lại trong passage trước, quy tắc của nó dùng trích
        if m and dieu is not None and int(m.group(1)) in (khoan + 1, khoan + 2):
            flush()
            khoan = int(m.group(1))
            buf, trang_buf = [line], trang
            continue
        if buf == [] and trang_buf is None:
            trang_buf = trang
        buf.append(line)
    flush()
    return passages


def gan_r_formal(passages, rules):
    """Gắn trích R-Formal vào passage. Quy tắc không có khoản → passage K0 của điều đó.
    Không có passage OCR tương ứng → dựng passage từ trích (nguon=trich_r_formal)."""
    thieu_ocr = []
    for r in rules:
        vb = r["van_ban"]
        dieu = r["dieu"] if r["dieu"] is not None else "PL1"   # R-M07: Phụ lục 1
        k = r["khoan"]
        key = pid(vb, dieu, k)
        if key not in passages and k is None:
            # quy tắc cấp điều: gắn vào khoản đầu tiên có thật của điều đó
            cung_dieu = sorted(p for p in passages if p.startswith(f"{vb}:D{dieu}:K"))
            if cung_dieu:
                key = cung_dieu[0]
        if key not in passages:
            thieu_ocr.append(r["id"])
            passages[key] = {"van_ban": vb, "dieu": dieu, "khoan": k, "tieu_de": "",
                             "trang": r["trang"], "ocr": ""}
        p = passages[key]
        p.setdefault("rules", []).append(r["id"])
        if r.get("asp"):
            p.setdefault("asp", []).append(r["asp"])
        p.setdefault("trich", []).append(r["trich"])
        if r["trich"].startswith("[Điều") or r["trich"].startswith("[QĐ5339 Điều"):
            # bản ghi X: trích là tiêu đề điều do người chép — dùng khi OCR không có tiêu đề
            p["tieu_de"] = p["tieu_de"] or r["trich"].split("]", 1)[1].strip()
    # passage dựng từ trích chưa có tiêu đề điều → mượn của passage cùng điều
    tieu_de = {}
    for p in passages.values():
        if p["tieu_de"]:
            tieu_de.setdefault((p["van_ban"], p["dieu"]), p["tieu_de"])
    for p in passages.values():
        p["tieu_de"] = p["tieu_de"] or tieu_de.get((p["van_ban"], p["dieu"]), "")
    return thieu_ocr


# Tên nhóm tự chọn bằng tiếng Việt — passage phải đọc được như văn bản, không chỉ chứa mã g_*
TEN_NHOM = {"g_gdtc": "Giáo dục thể chất", "g_ngoai_ngu": "Ngoại ngữ (Anh văn hoặc Pháp văn)",
            "g_xa_hoi": "Khoa học xã hội", "g_chuyen_nganh": "Chuyên ngành (CN1, CN2 hoặc CN3)",
            "g_tot_nghiep": "Tốt nghiệp (luận văn, tiểu luận hoặc học phần thay thế)"}


def passage_ctdt(cur):
    out = []
    # cách sinh viên gọi CTĐT: "CTĐT CNTT K49" — tên chính thức không chứa các chữ này
    ten_ctdt = f'{cur["meta"]["ten"]} (CTĐT ngành CNTT khoá K49)'
    vb = cur["meta"]["van_ban"]
    nhom_cua = {}
    for g, s in cur["nhom"].items():
        for lst in (s.get("nhanh") or {}).values():
            for c in lst:
                nhom_cua[c] = g
    for hp in cur["hoc_phan"]:
        tq = ", ".join(hp["tien_quyet"]) or "không"
        if hp.get("tien_quyet_tc"):
            tq += f"; tích lũy tối thiểu {hp['tien_quyet_tc']} TC"
        sh = ", ".join(hp["song_hanh"]) or "không"
        loai = "bắt buộc" if hp["cot"] == "BB" else f"tự chọn ({hp['cot']})"
        if hp["ma"] in nhom_cua:
            loai = f"tự chọn, nhóm {nhom_cua[hp['ma']]}"
        text = (f"Học phần {hp['ma']} {hp['ten']}: {hp['tin_chi']} tín chỉ, {loai}, khối {hp['khoi']}. "
                f"Tiên quyết: {tq}. Song hành: {sh}.")
        if hp.get("dieu_kien"):
            text += f" Là học phần điều kiện ({hp['dieu_kien']}), không tính vào điểm trung bình."
        if hp.get("hk"):
            text += f" Mở ở học kỳ {hp['hk']}."
        out.append({"id": f"ctdt_k49:{hp['ma']}", "loai": "ctdt", "van_ban": vb, "ma_hp": hp["ma"],
                    "trang": hp["trang"], "tieu_de": f"{ten_ctdt} — {hp['ma']}",
                    "text": text, "nguon": "curriculum_kb"})
    for g, s in cur["nhom"].items():
        if s["kieu"] == "mot_nhanh":
            nh = "; ".join(f"nhánh {b}: {', '.join(l)}" for b, l in s["nhanh"].items())
            text = (f"Nhóm tự chọn {TEN_NHOM.get(g, g)} ({g}, khối {s['khoi']}) của {ten_ctdt}: chọn MỘT nhánh và tích lũy tối thiểu "
                    f"{s['min']} tín chỉ trong nhánh đó, không cộng dồn tín chỉ giữa các nhánh. {nh}.")
        else:
            text = f"Nhóm tự chọn {TEN_NHOM.get(g, g)} ({g}, khối {s['khoi']}) của {ten_ctdt}: tích lũy tối thiểu {s['min']} tín chỉ trong nhóm."
        out.append({"id": f"ctdt_k49:nhom:{g}", "loai": "ctdt", "van_ban": vb, "trang": None,
                    "tieu_de": f"{ten_ctdt} — nhóm {g}", "text": text + f" Nguồn: {s['o_nguon']}.",
                    "nguon": "curriculum_kb"})
    return out


def build():
    cat = json.loads(CATALOG.read_text(encoding="utf-8"))
    passages = {}
    for vb, path in OCR.items():
        passages.update(parse_ocr(vb, path))
    so_ocr = len(passages)
    thieu_ocr = gan_r_formal(passages, cat["rules"])

    corpus = []
    for key, p in passages.items():
        vb, dieu, k = p["van_ban"], p["dieu"], p["khoan"]
        dia_chi = f"{TEN_VB[vb]} " + (f"Phụ lục {str(dieu)[2:]}" if str(dieu).startswith("PL") else f"Điều {dieu}")
        if k:
            dia_chi += f" khoản {k}"
        trich = " ".join(p.get("trich", []))
        tieu_de = f" {p['tieu_de']}." if p["tieu_de"] else ""   # Đ33–34: trang OCR trắng, không có tiêu đề
        text = f"{dia_chi}.{tieu_de} {p['ocr']} {trich}".strip()
        corpus.append({
            "id": key, "loai": "quy_che", "van_ban": vb, "dieu": dieu, "khoan": k,
            "trang": p["trang"], "tieu_de": p["tieu_de"], "dia_chi": dia_chi,
            "text": re.sub(r"\s+", " ", text),
            "rules": p.get("rules", []), "asp": p.get("asp", []),
            "nguon": "ocr" if p["ocr"] else "trich_r_formal",
        })
    corpus.sort(key=lambda d: (d["van_ban"], str(d["dieu"]).zfill(4), d["khoan"] or 0))
    cur = json.loads(CURRICULUM.read_text(encoding="utf-8"))
    corpus += passage_ctdt(cur)

    ids = [d["id"] for d in corpus]
    assert len(ids) == len(set(ids)), "trùng id passage"
    with open(HERE / "corpus.jsonl", "w", encoding="utf-8") as f:
        for d in corpus:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    qc = [d for d in corpus if d["loai"] == "quy_che"]
    rep = [
        "CORPUS TUẦN 14",
        f"  passage quy chế: {len(qc)} (OCR {so_ocr}, dựng từ trích R-Formal {len(qc) - so_ocr})",
        f"  passage CTĐT   : {len(corpus) - len(qc)}",
        f"  quy tắc R-Formal không có passage OCR (dùng trích): {thieu_ocr}",
        f"  điều theo văn bản: " + ", ".join(
            f"{TEN_VB[vb]} {sorted({d['dieu'] for d in qc if d['van_ban'] == vb}, key=str)}" for vb in OCR),
    ]
    (HERE / "corpus_report.txt").write_text("\n".join(rep) + "\n", encoding="utf-8")
    print("\n".join(rep))
    return corpus


if __name__ == "__main__":
    build()
    sys.exit(0)
