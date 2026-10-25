"""
run_baseline.py — chạy baseline (LLM thuần, RAG thuần, tool-calling) trên G-Truth v1 + OCR-Noise v1 và chấm bằng ĐÚNG bộ chấm
của CPA² (run_adversarial.cham / tong_hop). CPA2, Tuần 21.

Mã thoát: 0 xong · 2 dùng sai / bị chặn (test, thiếu cờ) · 3 thiếu khoá/model/giá · 4 prompt hoặc tham số khác bản đóng băng · 5 dừng giữa
chừng (vượt trần, lỗi vĩnh viễn, 5 ca lỗi liên tiếp) · 6 ước lượng vượt trần · 7 file kết quả đã có · 8 còn ca LOI (chưa ghi kết quả
chính thức; chạy lại để thử đúng các ca đó, hoặc --cho-phep-loi) · 9 split test đã có kết quả chính thức.

Bộ chặn (các mục đầu dừng TRƯỚC khi gọi API / ghi kết quả; mục "dừng giữa chừng" thì giữ checkpoint):
  - không có --chay-that  → không gọi gì (dùng --uoc-luong để xem số token / USD)
  - --split test          → cần thêm --cho-phep-test (test chạy MỘT lần ở Tuần 22, cùng CPA²)
  - thiếu khoá / model / giá token → dừng, nêu tên biến cần đặt (không có kết quả giả)
  - prompt, dữ liệu, mã nguồn dựng yêu cầu hoặc tham số hiệu lực (nhiệt độ, trần token ra) khác prompt_dong_bang.json → chỉ chạy khi có
    --hau-to (số chính thức giữ nguyên). Muốn đổi tham số mặc định thì đổi llm.THAM_SO RỒI --ghi-bang --ghi-de TRƯỚC lần chạy đầu
  - file kết quả đã có → từ chối ghi đè (chạy lại phải có --hau-to khác)
  - ước lượng chi phí vượt trần → dừng (muốn chạy tiếp: nâng BASELINE_MAX_USD có chủ đích hoặc --bo-qua-uoc-luong)
  - vượt trần USD (mặc định 5; BASELINE_MAX_USD) giữa chừng, lỗi vĩnh viễn của nhà cung cấp (sai model/khoá…), hoặc 5 ca lỗi liên
    tiếp → dừng; các ca đã trả tiền được giữ ở file .dang_chay (chạy lại thì bỏ qua các ca đó), không chấm, không có file kết quả

Chấm: CÙNG bộ chấm CPA², thêm các dòng
  [cau_hoi_ro]    chỉ các ca câu hỏi rõ nghĩa (loại ca câu hỏi rỗng / hỏi bằng ký hiệu ASP / đề xuất đảo chiều / "xếp hạng gì?").
                  Lý do: CPA² nhận thẳng `claim` còn baseline phải hiểu câu hỏi (w20 chưa viết câu hỏi tự nhiên cho mọi claim) →
                  28/78 ca dev không phải câu hỏi đúng/sai rõ nghĩa; xem cau_hoi_kem()
  [theo errata]   như run_cpa2 (gold phát hiện sai sau đóng băng)
  nhan_thieu      số ca không có dòng "NHAN: …" hợp lệ (tính UNKNOWN); loi: số ca lỗi gọi API (tính SAI như CPA²)
  "hỏi đúng" không đo được cho baseline → 0/0

Chạy:  python run_baseline.py --bl b1 --split dev --uoc-luong
       python run_baseline.py --bl b1 --nha openai --split dev --chay-that
Kết quả: ket_qua_baseline_<bl>_<nha>_<split><hau-to>.json (thư mục CPA2_BASELINE_OUT nếu đặt). Khoá API không bao giờ vào file.
Dữ liệu gửi đi là hồ sơ GIẢ LẬP của benchmark — không gửi câu trả lời thật của biểu mẫu Q-Real.
"""
import argparse, hashlib, json, os, re, subprocess, sys, time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
REPO = ROOT.parent
for d in (HERE, ROOT / "w20_benchmark", ROOT / "w17_adversarial"):
    sys.path.insert(0, str(d))
import baseline as W                   # w20_benchmark/baseline.py: đầu vào trung lập + id mờ
import baselines as B
import llm
from run_adversarial import cham, tong_hop, pct

MO_HINH = {"b1": "LLM thuần", "b2": "RAG thuần", "b3": "Tool-calling"}
TOKEN_MOI_KY_TU = llm.TOKEN_MOI_KY_TU      # ước lượng thô (chỉ để ước lượng chi phí)
LOI_LIEN_TIEP_TOI_DA = 5
TOKEN_RA_MOI_LUOT = 400
LUOT_B3_UOC = 3                # giả định ước lượng: b3 trung bình 3 lượt, mỗi lượt thêm ~1500 token ngữ cảnh


def tai_ca(split):
    """{id baseline: {'goc': ca gốc, 'vao': đầu vào trung lập}} — chỉ ca được chấm điểm."""
    out = {}
    for ten in ("gtruth.json", "ocr_noise.json"):
        for c in json.loads((ROOT / "w20_benchmark" / ten).read_text(encoding="utf-8"))["cases"]:
            if c["cham_diem"] and c["split"] == split:
                vao = W.dau_vao_baseline(c)
                out[vao["id"]] = {"goc": c, "vao": vao, "bo": ten.split(".")[0]}
    return out


def cau_hoi_kem(c):
    """Lý do câu hỏi baseline KHÔNG phải câu hỏi đúng/sai rõ nghĩa, hoặc None nếu rõ nghĩa (review Tuần 21, H1).
    Quy tắc theo hình thức câu hỏi + loại ca, KHÔNG theo kết quả chạy."""
    q = (c.get("cau_hoi") or "").strip()
    if not q:
        return "rong"                       # câu hỏi rỗng: claim chỉ có ở trường claim (CPA² đọc claim, baseline không có)
    if re.search(r"[A-Za-z_]\w*\(", q):
        return "atom"                       # hỏi bằng ký hiệu ASP (passed("X")?), không phải ngôn ngữ tự nhiên
    if c["he"] == "rec":
        return "rec_dao_chieu"              # claim là phủ định của câu hỏi (khong_de_xuat / tong_tc_le_20) → trả lời đúng bị chấm sai
    if str(c.get("claim", "")).startswith("thay_the:") and "công nhận" in q.lower():
        return "thay_the_cong_nhan"         # hỏi 'được công nhận' nhưng claim chỉ là 'đủ điều kiện được xét' (QĐ5339 Đ2 k6: cần đơn + quyết định)
    if c["nhom"] == "hang" and not q.rstrip("? ").endswith("không"):
        return "hang_khong_co_khong"        # 'xếp hạng gì?' không trả lời được bằng TRUE/FALSE
    return None


def _errata():
    out = {}
    f = ROOT / "w20_benchmark" / "gtruth_errata.json"
    if f.exists():
        out = {i: v["gold_errata"] for i, v in json.loads(f.read_text(encoding="utf-8"))["sua"].items()}
    return out


def doc_luu(luu, ca):
    """Đọc checkpoint: bỏ qua dòng hỏng (cắt dở khi tiến trình chết), dòng thiếu id/nhãn hợp lệ, id không thuộc split."""
    xong = {}
    if luu and Path(luu).exists():
        for dong in Path(luu).read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                r = json.loads(dong)
            except ValueError:
                continue
            if isinstance(r, dict) and r.get("id") in ca and r.get("tra_loi") in ("TRUE", "FALSE", "UNKNOWN"):
                xong[r["id"]] = r
    return xong


def _ghi_dong(luu, r):
    """Thêm một dòng vào checkpoint, xuống dòng trước nếu dòng cuối cũ bị cắt dở; fsync để không mất ca đã trả tiền. Lỗi ghi → OSError."""
    luu = Path(luu)
    can_xuong = False
    if luu.exists() and luu.stat().st_size > 0:
        with open(luu, "rb") as f:
            f.seek(-1, 2)
            can_xuong = f.read(1) != b"\n"
    with open(luu, "ab") as f:
        f.write((("\n" if can_xuong else "") + json.dumps(r, ensure_ascii=False) + "\n").encode("utf-8"))
        f.flush()
        os.fsync(f.fileno())


def chay_split(ten, split, client, ret, luu=None):
    """Chạy mọi ca của split. luu: file JSONL checkpoint — mỗi ca xong ghi ngay (ca đã trả tiền không mất khi bị dừng giữa chừng);
    chạy lại thì bỏ qua ca đã có. Dừng bằng ngoại lệ: VuotNganSach, LoiNhaCungCap vĩnh viễn, QuaNhieuLoi (5 ca LOI liên tiếp),
    OSError (không ghi được checkpoint — KHÔNG biến câu trả lời đã trả tiền thành LOI)."""
    ca = tai_ca(split)
    xong = doc_luu(luu, ca)
    rows, lien_tiep = [], 0
    for id_, c in ca.items():
        if id_ in xong:
            rows.append(xong[id_])
            continue
        try:
            r = {"id": id_, **B.chay(ten, c["vao"], client, ret)}
        except llm.VuotNganSach:
            raise
        except llm.LoiNhaCungCap as e:
            if e.vinh_vien:
                raise
            r, lien_tiep = _loi(id_, e), lien_tiep + 1
        except Exception as e:  # noqa: BLE001 — một ca lỗi (mạng, ngoại lệ lạ) → LOI, tính là SAI như CPA²; không lưu để chạy lại được
            r, lien_tiep = _loi(id_, e), lien_tiep + 1
        else:
            lien_tiep = 0
            if luu:
                _ghi_dong(luu, r)
        if lien_tiep >= LOI_LIEN_TIEP_TOI_DA:
            raise llm.QuaNhieuLoi(f"{lien_tiep} ca lỗi liên tiếp (ca cuối {id_}: {r.get('loi')})")
        rows.append(r)
    return rows


def ten_checkpoint(ten_file, h_mau, h_vao, model, nhiet_do, max_out):
    """Tên checkpoint gồm mọi thứ làm câu trả lời khác đi → chạy lại với model/nhiệt độ/prompt khác không trộn kết quả."""
    h = hashlib.sha256(json.dumps([h_mau, h_vao, model, nhiet_do, max_out]).encode("utf-8")).hexdigest()[:12]
    return f".{ten_file}.{h}.dang_chay.jsonl"


def _loi(id_, e):
    return {"id": id_, "tra_loi": "LOI", "nhan_thieu": False, "tho": "", "luot": 0, "het_luot": False,
            "usage": {"in": 0, "out": 0}, "loi": llm.scrub(f"{type(e).__name__}: {e}")[:200]}


def ghi_ket_qua(duong_dan, obj):
    """Ghi file kết quả; KHÔNG ghi đè file đã có (số chính thức)."""
    p = Path(duong_dan)
    if p.exists():
        raise FileExistsError(str(p))
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def _tong(xs, rows_by_id):
    t = tong_hop(xs)
    t["nhan_thieu"] = sum(rows_by_id[x["id"]]["nhan_thieu"] for x in xs)
    t["loi"] = sum(x["tra_loi"] == "LOI" for x in xs)
    return t


def cham_rows(rows, split):
    ca = tai_ca(split)
    errata = _errata()
    by_id = {r["id"]: r for r in rows}
    kq, kq_e = [], []
    for r in rows:
        c = ca[r["id"]]["goc"]
        x = {"id": r["id"], "id_goc": c["id"], "nhom": c["nhom"], "he": c["he"], "gold": c["gold"], "su_that": c.get("su_that"),
             "loai_gold": c["loai_gold"], "tra_loi": r["tra_loi"], "luot": r["luot"], "cau_hoi_kem": cau_hoi_kem(c)}
        x.update(cham(c, r["tra_loi"], []))
        x["hoi_dung"] = None            # câu trả lời tự do không có danh sách biến cần hỏi → không đo được
        kq.append(x)
        ce = {**c, "gold": errata[c["id"]]} if ca[r["id"]]["bo"] == "gtruth" and c["id"] in errata else c
        kq_e.append({**x, **cham(ce, r["tra_loi"], []), "hoi_dung": None})
    tg = {"tong": _tong(kq, by_id)}
    tg["[cau_hoi_ro]"] = _tong([x for x in kq if x["cau_hoi_kem"] is None], by_id)
    for lg in ("quy_che", "thiet_ke"):
        con = [x for x in kq if x["loai_gold"] == lg]
        if con:
            tg[f"[{lg}]"] = _tong(con, by_id)
    if errata:
        tg["[theo errata]"] = _tong(kq_e, by_id)
        tg["[cau_hoi_ro theo errata]"] = _tong([x for x in kq_e if x["cau_hoi_kem"] is None], by_id)
    theo = defaultdict(list)
    for x in kq:
        theo[x["nhom"]].append(x)
    for k, v in sorted(theo.items()):
        tg[k] = _tong(v, by_id)
    return kq, tg


def uoc_luong(ten, split, gia):
    """Ước lượng token (thô) và USD nếu có giá (vào, ra — USD / 1 triệu token). Không gọi mạng."""
    ret = B.Retriever() if ten in ("b2", "b3") else None
    tv = 0.0
    ds = tai_ca(split)
    for c in ds.values():
        base = len(json.dumps(B.dung_prompt(ten, c["vao"], ret), ensure_ascii=False)) / TOKEN_MOI_KY_TU
        if ten == "b3":
            base += len(json.dumps(B.TOOLS, ensure_ascii=False)) / TOKEN_MOI_KY_TU
            tv += base * LUOT_B3_UOC + 1500 * sum(range(LUOT_B3_UOC))      # ngữ cảnh tăng dần qua các lượt
        else:
            tv += base
    tr = len(ds) * TOKEN_RA_MOI_LUOT * (LUOT_B3_UOC if ten == "b3" else 1)
    return {"so_ca": len(ds), "token_vao": int(tv), "token_ra": int(tr),
            "usd": None if gia is None else (tv * gia[0] + tr * gia[1]) / 1e6}


def vuot_tran_uoc(ten, split, ngan):
    """Ước lượng chi phí (giá của ngân sách) có vượt trần không — kiểm TRƯỚC khi gọi API."""
    u = uoc_luong(ten, split, gia=(ngan.gia_vao, ngan.gia_ra))
    return u["usd"] > ngan.tran_usd


def _nguon():
    """Mã nguồn dựng yêu cầu / công cụ / truy hồi (chuẩn hoá xuống dòng) — đổi một ký tự là bản đóng băng cũ không còn khớp."""
    return [(f).read_text(encoding="utf-8").replace("\r\n", "\n") for f in
            (HERE / "baselines.py", HERE / "llm.py", ROOT / "w14_rag" / "retriever.py", ROOT / "w20_benchmark" / "baseline.py")]


def hash_dau_vao():
    """sha256 của prompt ĐÃ DỰNG cho mọi ca dev+test (b1/b2/b3) + nội dung corpus điều khoản + CTĐT + mã nguồn dựng yêu cầu. Bắt thay đổi
    mà hash mẫu bỏ sót (câu hỏi, mô tả, hồ sơ, điều khoản truy hồi, dữ liệu nguồn, định dạng kết quả công cụ). Hash theo nội dung đã
    đọc nên không phụ thuộc kiểu xuống dòng. ⚠ corpus.jsonl do w14/build_corpus.py sinh: nếu bản đã commit lỗi thời so với bộ sinh thì
    validate_rag sẽ làm hash đổi (đã gặp sau C15) — sinh lại và commit corpus TRƯỚC khi đóng băng."""
    ret = B.Retriever()
    h = hashlib.sha256()
    for split in ("dev", "test"):
        for id_, c in tai_ca(split).items():
            for ten in ("b1", "b2", "b3"):
                h.update(json.dumps(B.dung_prompt(ten, c["vao"], ret), ensure_ascii=False, sort_keys=True).encode("utf-8"))
    h.update(json.dumps([[d["id"], d["text"], d.get("dia_chi"), d.get("tieu_de")] for d in sorted(ret.docs, key=lambda d: d["id"])],
                        ensure_ascii=False).encode("utf-8"))
    h.update(json.dumps(sorted(B._ctdt().items()), ensure_ascii=False, default=str).encode("utf-8"))
    for t in _nguon():
        h.update(hashlib.sha256(t.encode("utf-8")).digest())
    return h.hexdigest()


def duong_dan_bang():
    return Path(os.environ.get("CPA2_BANG_FILE") or HERE / "prompt_dong_bang.json")


def _in_bang(tg):
    print(f"\n{'nhóm':15} {'n':>3} {'Sound':>7} {'Cover':>7} {'SelAcc':>7} {'đúng':>5} {'unsound':>8} {'từ chối thừa':>13} {'thiếu nhãn':>11} {'lỗi':>4}")
    for k, s in tg.items():
        print(f"{k:15} {s['n']:>3} {pct(s['soundness']):>7} {pct(s['coverage']):>7} {pct(s['selective_acc']):>7} "
              f"{s['dung_gold']:>5} {s['unsound']:>8} {s['tu_choi_thua']:>13} {s['nhan_thieu']:>11} {s['loi']:>4}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bl", choices=sorted(MO_HINH))
    ap.add_argument("--nha", choices=sorted(llm.NHA))
    ap.add_argument("--split", choices=["dev", "test"])
    ap.add_argument("--hau-to", default="", type=lambda x: x if re.fullmatch(r"[A-Za-z0-9_-]*", x) else
                    (_ for _ in ()).throw(argparse.ArgumentTypeError("--hau-to chỉ nhận chữ, số, _ và -")))
    ap.add_argument("--uoc-luong", action="store_true")
    ap.add_argument("--chay-that", action="store_true", help="gọi API thật (tốn tiền)")
    ap.add_argument("--cho-phep-test", action="store_true", help="chỉ dùng ở Tuần 22, một lần")
    ap.add_argument("--bo-qua-uoc-luong", action="store_true", help="chạy dù ước lượng chi phí vượt trần")
    ap.add_argument("--cho-phep-loi", action="store_true", help="ghi kết quả dù còn ca LOI (tính SAI; phải nêu trong báo cáo)")
    ap.add_argument("--ghi-bang", action="store_true", help="ghi prompt_dong_bang.json (trước lần chạy thật đầu tiên)")
    ap.add_argument("--ghi-de", action="store_true", help="cho phép --ghi-bang ghi đè bản đóng băng khác")
    a = ap.parse_args()
    bang = duong_dan_bang()
    if a.ghi_bang:
        moi = {"sha256": B.hash_prompt(), "sha256_dau_vao": hash_dau_vao(),
               "ghi_chu": "sha256 = mẫu prompt + công cụ + tham số (baselines.hash_prompt); sha256_dau_vao = prompt đã dựng cho mọi ca dev+test "
                          "+ nội dung corpus/CTĐT (run_baseline.hash_dau_vao). Đóng băng + commit TRƯỚC lần chạy thật đầu tiên; sửa sau đó thì "
                          "chạy với --hau-to và giữ số chính thức."}
        if bang.exists() and not a.ghi_de:
            cu = json.loads(bang.read_text(encoding="utf-8"))
            if (cu.get("sha256"), cu.get("sha256_dau_vao")) != (moi["sha256"], moi["sha256_dau_vao"]):
                print(f"Từ chối: {bang.name} đã đóng băng với nội dung khác. Muốn thay thì thêm --ghi-de (có chủ đích, ghi vào báo cáo).")
                return 2
        bang.write_text(json.dumps(moi, ensure_ascii=False, indent=1), encoding="utf-8")
        print("đã ghi", bang.name, moi["sha256"][:12], moi["sha256_dau_vao"][:12])
        return 0
    if not a.bl or not a.split:
        print("Thiếu --bl và --split.")
        return 2
    if a.split == "test" and not a.cho_phep_test:
        print("Từ chối: split test chỉ chạy MỘT lần ở Tuần 22 (cùng CPA²). Cần --cho-phep-test.")
        return 2
    env = llm.doc_env(os.environ.get("CPA2_ENV_FILE") or REPO / ".env")
    if a.uoc_luong:
        gia = None
        if a.nha and env.get(f"BASELINE_{a.nha.upper()}_PRICE_IN") and env.get(f"BASELINE_{a.nha.upper()}_PRICE_OUT"):
            try:
                ns = llm.ngan_sach_tu_env(a.nha, env)
                gia = (ns.gia_vao, ns.gia_ra)
            except llm.ThieuKhoa as e:
                print(f"Bỏ qua giá không hợp lệ: {e}")
        u = uoc_luong(a.bl, a.split, gia)
        print(f"{MO_HINH[a.bl]} · {a.split}: {u['so_ca']} ca, ~{u['token_vao']:,} token vào, ~{u['token_ra']:,} token ra "
              f"(ước lượng thô, 1 token ≈ {TOKEN_MOI_KY_TU} ký tự" + (f"; ~{u['usd']:.2f} USD" if u["usd"] is not None else
              "; chưa khai giá nên không ra USD") + ")")
        return 0
    if not a.chay_that:
        print("Không làm gì: thêm --chay-that để gọi API thật, hoặc --uoc-luong để xem chi phí ước lượng.")
        return 2
    if not a.nha:
        print("Thiếu --nha (openai | gemini).")
        return 2
    try:
        client = llm.tao_client(a.nha, env)
        ngan = llm.ngan_sach_tu_env(a.nha, env)
    except llm.ThieuKhoa as e:
        print(f"Dừng: {e}")
        return 3
    ra = Path(os.environ.get("CPA2_BASELINE_OUT") or HERE)
    ten_file = f"ket_qua_baseline_{a.bl}_{a.nha}_{a.split}{a.hau_to}"
    if a.split == "test" and list(ra.glob(f"ket_qua_baseline_{a.bl}_{a.nha}_test*.json")):
        print("Dừng: split test đã có kết quả chính thức cho baseline/nhà cung cấp này — chỉ chạy MỘT lần (Tuần 22); đổi --hau-to không mở lại.")
        return 9
    if (ra / (ten_file + ".json")).exists():
        print(f"Dừng: {ten_file}.json đã có — không ghi đè số chính thức. Chạy lại phải có --hau-to khác.")
        return 7
    h_mau, h_vao = B.hash_prompt(), hash_dau_vao()
    cu = json.loads(bang.read_text(encoding="utf-8")) if bang.exists() else {}
    tham_so_khop = client.nhiet_do == llm.THAM_SO["nhiet_do"] and client.max_out == llm.THAM_SO["max_out"]
    khop = (cu.get("sha256"), cu.get("sha256_dau_vao")) == (h_mau, h_vao) and tham_so_khop
    if not khop and not a.hau_to:
        print("Dừng: prompt/dữ liệu/mã nguồn hoặc tham số hiệu lực (nhiệt độ, trần token ra) khác bản đóng băng "
              + ("(tham số: BASELINE_TEMPERATURE / BASELINE_MAX_OUT khác llm.THAM_SO) " if not tham_so_khop else "")
              + "(hoặc chưa đóng băng: python run_baseline.py --ghi-bang). Số chính thức phải theo bản đóng băng; muốn chạy bản mới thì "
                "thêm --hau-to và ghi rõ trong báo cáo.")
        return 4
    if not a.bo_qua_uoc_luong and vuot_tran_uoc(a.bl, a.split, ngan):
        u = uoc_luong(a.bl, a.split, (ngan.gia_vao, ngan.gia_ra))
        print(f"Dừng: ước lượng ~{u['usd']:.2f} USD vượt trần {ngan.tran_usd:.2f} USD. Nâng BASELINE_MAX_USD có chủ đích, hoặc --bo-qua-uoc-luong.")
        return 6
    ret = B.Retriever() if a.bl in ("b2", "b3") else None
    cl = llm.CoNganSach(client, ngan)
    git = _git()
    meta = {"bl": a.bl, "nha": a.nha, "model": client.model, "split": a.split, "prompt_sha256": h_mau, "dau_vao_sha256": h_vao,
            "dong_bang_khop": khop, "hau_to": a.hau_to, "nhiet_do": client.nhiet_do, "max_out": client.max_out,
            "ngay": time.strftime("%Y-%m-%d"), "tran_usd": ngan.tran_usd, "git": git}
    luu = ra / ten_checkpoint(ten_file, h_mau, h_vao, client.model, client.nhiet_do, client.max_out)
    ra.mkdir(parents=True, exist_ok=True)
    truoc = doc_luu(luu, tai_ca(a.split))
    for r in truoc.values():                    # chi phí các ca đã trả tiền ở lần chạy trước cũng tính vào trần
        ngan.cong(r.get("usage") or {})
    print(f"{MO_HINH[a.bl]} · {a.nha}/{client.model} · {a.split} (trần {ngan.tran_usd:.2f} USD"
          + (f"; tiếp tục từ checkpoint {len(truoc)} ca, đã tính {ngan.da_dung:.4f} USD" if truoc else "") + ")\n")
    trang_thai = {"v": "gian_doan"}

    def nhat_ky():
        with open(ra / "chi_phi_nhat_ky.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({**meta, "ket_thuc": trang_thai["v"], "usd": round(ngan.da_dung, 4), "token_vao": ngan.tok_vao,
                                "token_ra": ngan.tok_ra, "uoc_thay": ngan.uoc_thay}, ensure_ascii=False) + "\n")
    try:
        try:
            rows = chay_split(a.bl, a.split, cl, ret, luu=luu)
        except (llm.VuotNganSach, llm.LoiNhaCungCap, llm.QuaNhieuLoi, OSError) as e:
            trang_thai["v"] = type(e).__name__
            print(f"Dừng: {llm.scrub(e)}\nCác ca đã xong được giữ ở {luu.name}; chạy lại cùng lệnh để tiếp tục. Chưa có kết quả chính thức.")
            return 5
        n_loi = sum(r["tra_loi"] == "LOI" for r in rows)
        if n_loi and not a.cho_phep_loi:
            trang_thai["v"] = "con_loi"
            print(f"Dừng: còn {n_loi} ca LOI (lỗi gọi API tạm thời, tính SAI). KHÔNG ghi kết quả chính thức; checkpoint giữ nguyên — chạy lại cùng lệnh "
                  "để thử đúng các ca đó, hoặc --cho-phep-loi để chấp nhận (phải nêu trong báo cáo).")
            return 8
        kq, tg = cham_rows(rows, a.split)
        for r, x in zip(rows, kq):
            dau = "✗ UNSOUND" if x["unsound"] else ("✓" if x["dung_gold"] else "· từ chối thừa" if x["tu_choi_thua"] else "·")
            print(f"  {x['id_goc']:8} {x['nhom']:14} gold={x['gold']:7} → {r['tra_loi']:9} {dau}")
        _in_bang(tg)
        print(f"\nchi phí ~{ngan.da_dung:.4f} USD ({ngan.tok_vao:,} vào / {ngan.tok_ra:,} ra; {ngan.uoc_thay} lần phải ước lượng vì thiếu usage)")
        meta.update(usd=round(ngan.da_dung, 4), token_vao=ngan.tok_vao, token_ra=ngan.tok_ra, uoc_thay=ngan.uoc_thay)
        ghi_ket_qua(ra / (ten_file + ".json"), {"meta": meta, "tong_hop": tg, "ca": kq, "tra_loi_tho": rows})
        trang_thai["v"] = "xong"
        luu.unlink(missing_ok=True)
        return 0
    finally:
        nhat_ky()


def _git():
    """Phiên bản mã nguồn của lần chạy: commit + cây làm việc có sửa chưa commit không (None nếu không có git)."""
    try:
        gc = lambda *x: subprocess.run(["git", "-C", str(REPO), *x], capture_output=True, text=True, timeout=20)  # noqa: E731
        return {"commit": gc("rev-parse", "HEAD").stdout.strip() or None, "chua_commit": bool(gc("status", "--porcelain").stdout.strip())}
    except Exception:  # noqa: BLE001
        return None


if __name__ == "__main__":
    sys.exit(main())
