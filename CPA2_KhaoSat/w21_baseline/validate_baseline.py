"""
validate_baseline.py — kiểm chứng đường ống baseline (CPA2, Tuần 21). KHÔNG gọi mạng, không cần API key.

  A. Đọc nhãn từ câu trả lời tự do (chỉ nhận dòng "NHAN: …"; thiếu/mơ hồ → UNKNOWN + đếm riêng)
  B. Prompt không lộ gold / id gốc / lý do; B2 chỉ đưa văn bản điều khoản (không rule id, không atom ASP)
  C. Công cụ B3: máy tính an toàn, tra CTĐT, vòng lặp có trần lượt
  D. Khoá API: thiếu khoá → dừng rõ ràng, không ghi kết quả; .env nằm trong .gitignore, .env.example không có giá trị
  E. Ngân sách: trần USD, bắt buộc có giá; ước lượng trước khi chạy thật
  F. Chấm điểm bằng đúng bộ chấm CPA² (client giả): id ánh xạ ngược đủ, Sound/Coverage khớp tính tay
  G. Bộ chặn: split test cần cờ riêng; prompt đóng băng (hash)
  H. Bộ chuyển đổi OpenAI / Gemini: dựng yêu cầu + đọc phản hồi mẫu (CHƯA kiểm với API thật)
  I. Sửa theo review lượt 1 (H1 câu hỏi rõ nghĩa, H2 lỗi API/checkpoint, M1 ngân sách, M2 hash, M3 errata, M5 lộ khoá, M6 chữ ký suy nghĩ…)
  J. Chạy thật ĐẦU-CUỐI qua CLI vào máy chủ giả cục bộ: kết quả, chi phí, checkpoint, trần, lỗi vĩnh viễn, không lộ khoá
  K. Sửa theo review lượt 2 (checkpoint cắt dở/ghi lỗi, ca LOI không vào số chính thức, trộn lần chạy, phân loại HTTP, 'công nhận', hash mã nguồn…)

Chạy: python validate_baseline.py
"""
import hashlib, json, os, re, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
REPO = ROOT.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "w20_benchmark"))
sys.path.insert(0, str(ROOT / "w17_adversarial"))

import llm
import baselines as B
import run_baseline as R

ok_all = True


def check(cond, msg):
    global ok_all
    print(f"  [{'OK' if cond else 'FAIL'}] {msg}")
    ok_all = ok_all and bool(cond)
    return cond


class Gia:
    """Client giả (CHỈ dùng trong test): trả lời theo kịch bản, ghi lại các lần gọi."""
    provider, model = "gia", "gia-1"

    def __init__(self, kich_ban):
        self.kb = kich_ban            # list[dict] hoặc hàm (messages, tools) → dict
        self.goi = []

    def chat(self, messages, tools=None):
        self.goi.append((json.loads(json.dumps(messages)), tools))
        r = self.kb(messages, tools) if callable(self.kb) else self.kb[min(len(self.goi) - 1, len(self.kb) - 1)]
        return {"text": r.get("text", ""), "tool_calls": r.get("tool_calls", []),
                "usage": r.get("usage", {"in": 100, "out": 10})}


def luon(nhan):
    return Gia(lambda m, t: {"text": f"Lập luận ngắn.\nNHAN: {nhan}"})


def phan_A():
    print("A. ĐỌC NHÃN")
    for s, mong, thieu in [("Lập luận.\nNHAN: TRUE", "TRUE", False), ("NHAN: false", "FALSE", False),
                           ("x\nNHÃN: UNKNOWN", "UNKNOWN", False), ("**NHAN: FALSE**", "FALSE", False),
                           ("NHAN: TRUE\n...sửa lại\nNHAN: FALSE", "FALSE", False),
                           ("Em đủ điều kiện, TRUE", "UNKNOWN", True), ("", "UNKNOWN", True),
                           ("NHAN: TRUE hoặc FALSE", "UNKNOWN", True), ("NHAN: CÓ", "UNKNOWN", True),
                           ("NHAN: TRUEISH", "UNKNOWN", True)]:
        r = B.doc_nhan(s)
        check(r == (mong, thieu), f"doc_nhan({s!r}) = {r}, mong {(mong, thieu)}")


def phan_B():
    print("B. PROMPT KHÔNG LỘ GOLD")
    import baseline as W
    goc = {}
    for split in ("dev", "test"):
        for c in R.tai_ca(split).values():
            goc[c["goc"]["id"]] = c
    ids = list(goc)
    ret = B.Retriever()
    lo = []
    for i, c in goc.items():
        for ten in ("b1", "b2"):
            p = B.dung_prompt(ten, c["vao"], ret)
            txt = json.dumps(p, ensure_ascii=False)
            for j in ids:
                if re.search(r"(?<![A-Za-z0-9])" + re.escape(j) + r"(?![A-Za-z0-9])", txt):
                    lo.append((i, ten, "id gốc " + j))
            for k in ("gold", "su_that", "student_id", "ly_do"):
                if k in txt.lower():
                    lo.append((i, ten, k))
            ly = (c["goc"].get("ly_do") or "")[:40]
            if len(ly) > 20 and ly in txt:
                lo.append((i, ten, "lý do gold"))
    check(not lo, f"{len(ids)} ca × B1/B2: không lộ id gốc / gold / lý do ({lo[:3]})")
    c = next(iter(goc.values()))
    p1 = json.dumps(B.dung_prompt("b1", c["vao"], ret), ensure_ascii=False)
    check(c["vao"]["cau_hoi"] in p1 and "NHAN:" in p1, "B1 chứa câu hỏi + định dạng nhãn")
    check("QĐ3266" not in p1 and "Điều " not in p1.replace("Điều kiện", ""), "B1 không kèm văn bản quy chế (LLM thuần)")
    c2 = next(x for x in goc.values() if "ho_so" in x["vao"])
    p2 = json.dumps(B.dung_prompt("b2", c2["vao"], ret), ensure_ascii=False)
    check("QĐ3266" in p2 or "QĐ5339" in p2 or "Chương trình" in p2, "B2 kèm điều khoản truy hồi")
    check(not re.search(r"\bR-[A-Z]\d{2}", p2) and "why(" not in p2 and "asp" not in p2.lower().replace("aspect", ""),
          "B2 chỉ đưa văn bản điều khoản (không rule id, không atom ASP)")


def phan_C():
    print("C. CÔNG CỤ B3")
    check(abs(B.may_tinh("(3*4.0+2*3.5)/5") - 3.8) < 1e-9, "may_tinh((3*4.0+2*3.5)/5) = 3.8")
    for xau in ("__import__('os').system('id')", "open('x')", "2**9999999", "1/0", "a+1", "[1,2]", "9"*60):
        r = B.chay_cong_cu("may_tinh", {"bieu_thuc": xau})
        check(isinstance(r, str) and r.startswith("LOI"), f"may_tinh({xau[:30]!r}) bị từ chối an toàn → {r[:40]!r}")
    r = json.loads(B.chay_cong_cu("tra_ctdt", {"ma_hp": "CT180"}))
    check(r.get("tin_chi") and "tien_quyet" in r and "ten" in r, f"tra_ctdt(CT180) có TC/tiên quyết ({sorted(r)})")
    check(B.chay_cong_cu("tra_ctdt", {"ma_hp": "ZZ999"}).startswith("KHÔNG CÓ"), "tra_ctdt mã lạ → KHÔNG CÓ")
    r = json.loads(B.chay_cong_cu("tra_cuu_quy_che", {"truy_van": "điều kiện tốt nghiệp"}))
    check(len(r) == 3 and all({"dia_chi", "noi_dung"} <= set(x) for x in r), "tra_cuu_quy_che trả 3 điều khoản (địa chỉ + nội dung)")
    check({t["name"] for t in B.TOOLS} == {"may_tinh", "tra_ctdt", "tra_cuu_quy_che"},
          "B3 chỉ có 3 công cụ tổng quát — KHÔNG có công cụ tính ĐTBCTL/tốt nghiệp (không phải solver)")
    ret = B.Retriever()
    vao = next(iter(R.tai_ca("dev").values()))["vao"]
    kb = [{"tool_calls": [{"id": "1", "name": "may_tinh", "args": {"bieu_thuc": "(3*4.0+2*3.5)/5"}}]},
          {"text": "ĐTB 3.8.\nNHAN: FALSE"}]
    g = Gia(kb)
    r = B.chay("b3", vao, g, ret)
    msgs2 = g.goi[1][0]
    check(r["tra_loi"] == "FALSE" and r["luot"] == 2 and not r["het_luot"], f"B3: gọi công cụ rồi trả lời ({r['tra_loi']}, {r['luot']} lượt)")
    check(any(m["role"] == "tool" and "3.8" in m["content"] for m in msgs2), "kết quả công cụ được đưa lại cho model")
    g = Gia(lambda m, t: {"tool_calls": [{"id": "x", "name": "may_tinh", "args": {"bieu_thuc": "1+1"}}]})
    r = B.chay("b3", vao, g, ret)
    check(r["tra_loi"] == "UNKNOWN" and r["het_luot"] and r["luot"] == B.MAX_LUOT, f"model gọi công cụ mãi → dừng ở {B.MAX_LUOT} lượt, UNKNOWN")
    g = Gia(lambda m, t: {"tool_calls": [{"id": "x", "name": "xoa_het", "args": {}}]} if len(m) < 4 else {"text": "NHAN: TRUE"})
    r = B.chay("b3", vao, g, ret)
    check(any(m["role"] == "tool" and "LOI" in m["content"] for m in g.goi[1][0]), "công cụ không tồn tại → báo lỗi cho model, không crash")


def phan_D():
    print("D. KHOÁ API")
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / ".env"
        f.write_text('# ghi chú\nOPENAI_API_KEY="abc 123"\nGEMINI_API_KEY=xyz\n\nRONG=\nDA_CO=moi\n', encoding="utf-8")
        e = llm.doc_env(f, {"DA_CO": "cu"})
        check(e.get("OPENAI_API_KEY") == "abc 123" and e.get("GEMINI_API_KEY") == "xyz" and e["DA_CO"] == "cu" and not e.get("RONG"),
              f"doc_env: bỏ ghi chú, bỏ nháy, không ghi đè biến môi trường có sẵn ({sorted(e)})")
    try:
        llm.tao_client("openai", {})
        kq = "không lỗi"
    except llm.ThieuKhoa as ex:
        kq = str(ex)
    check("OPENAI_API_KEY" in kq and ("không" in kq.lower() or "thiếu" in kq.lower()), f"thiếu khoá OpenAI → ThieuKhoa nêu tên biến ({kq})")
    try:
        llm.tao_client("openai", {"OPENAI_API_KEY": "k"})
        kq = "không lỗi"
    except llm.ThieuKhoa as ex:
        kq = str(ex)
    check("MODEL" in kq, f"có khoá mà chưa chọn model → ThieuKhoa nêu BASELINE_OPENAI_MODEL ({kq})")
    env = {k: v for k, v in os.environ.items() if not k.endswith("_API_KEY")}
    env["CPA2_ENV_FILE"] = os.devnull
    with tempfile.TemporaryDirectory() as d:
        env["CPA2_BASELINE_OUT"] = d
        p = subprocess.run([sys.executable, str(HERE / "run_baseline.py"), "--bl", "b1", "--nha", "openai", "--split", "dev",
                            "--chay-that"], capture_output=True, text=True, env=env, encoding="utf-8")
        check(p.returncode != 0 and "OPENAI_API_KEY" in (p.stdout + p.stderr) and not list(Path(d).iterdir()),
              f"chạy thật khi thiếu khoá: exit {p.returncode}, nêu tên biến, không ghi file kết quả")
        p = subprocess.run([sys.executable, str(HERE / "run_baseline.py"), "--bl", "b1", "--nha", "openai", "--split", "dev"],
                           capture_output=True, text=True, env=env, encoding="utf-8")
        check(p.returncode != 0 and not list(Path(d).iterdir()), "không có --chay-that thì không gọi API / không ghi kết quả")
    gi = (REPO / ".gitignore").read_text(encoding="utf-8").splitlines()
    check(".env" in [x.strip() for x in gi], ".env nằm trong .gitignore")
    ex = REPO / ".env.example"
    t = ex.read_text(encoding="utf-8") if ex.exists() else ""
    gt = [l.split("=", 1) for l in t.splitlines() if "=" in l and not l.lstrip().startswith("#")]
    check(ex.exists() and {"OPENAI_API_KEY", "GEMINI_API_KEY", "BASELINE_OPENAI_MODEL", "BASELINE_GEMINI_MODEL",
                           "BASELINE_TEMPERATURE", "BASELINE_MAX_OUT"} <= {k for k, _ in gt}
          and not any(re.search(r"(KEY|TOKEN|SECRET)", k) and v.strip() for k, v in gt) and "sk-" not in t,
          ".env.example có đủ tên biến, các biến khoá để TRỐNG")


def phan_E():
    print("E. NGÂN SÁCH")
    n = llm.NganSach(tran_usd=1.0, gia_vao=2.0, gia_ra=8.0)       # USD / 1 triệu token
    n.cong({"in": 100_000, "out": 10_000})
    check(abs(n.da_dung - (0.2 + 0.08)) < 1e-9, f"chi phí = 100k×2 + 10k×8 (/1M) = 0,28 USD ({n.da_dung})")
    n.kiem(uoc_vao=100_000, uoc_ra=10_000)
    try:
        n.kiem(uoc_vao=400_000, uoc_ra=0)
        kq = "không lỗi"
    except llm.VuotNganSach:
        kq = "VuotNganSach"
    check(kq == "VuotNganSach", "ước lượng làm tổng vượt trần → dừng TRƯỚC khi gọi")
    n.cong({"in": 1_000_000, "out": 0})
    try:
        n.kiem()
        kq = "không lỗi"
    except llm.VuotNganSach:
        kq = "VuotNganSach"
    check(kq == "VuotNganSach", "đã vượt trần → mọi lần gọi sau bị chặn")
    for loi in ({"OPENAI_API_KEY": "k", "BASELINE_OPENAI_MODEL": "m"},):
        try:
            llm.ngan_sach_tu_env("openai", loi)
            kq = "không lỗi"
        except llm.ThieuKhoa as ex:
            kq = str(ex)
        check("PRICE" in kq, f"chưa khai giá token → từ chối (không đoán giá) ({kq})")
    n2 = llm.ngan_sach_tu_env("openai", {"BASELINE_OPENAI_PRICE_IN": "1.5", "BASELINE_OPENAI_PRICE_OUT": "6", "BASELINE_MAX_USD": "7"})
    check((n2.tran_usd, n2.gia_vao, n2.gia_ra) == (7.0, 1.5, 6.0), "đọc giá + trần từ môi trường")
    n3 = llm.ngan_sach_tu_env("openai", {"BASELINE_OPENAI_PRICE_IN": "1.5", "BASELINE_OPENAI_PRICE_OUT": "6"})
    check(n3.tran_usd == 5.0, "trần mặc định 5 USD (Loi duyệt 'theo đề xuất')")
    g = llm.CoNganSach(luon("TRUE"), llm.NganSach(tran_usd=0.0001, gia_vao=100.0, gia_ra=100.0))
    g.chat([{"role": "user", "content": "x"}])
    try:
        g.chat([{"role": "user", "content": "x"}])
        kq = "không lỗi"
    except llm.VuotNganSach:
        kq = "VuotNganSach"
    check(kq == "VuotNganSach", "CoNganSach: lần gọi thứ hai bị chặn sau khi lần đầu tiêu hết trần")
    u = R.uoc_luong("b1", "dev", gia=None)
    check(u["so_ca"] == 78 and u["token_vao"] > 78 * 1000 and u["usd"] is None, f"ước lượng: 78 ca, ~{u['token_vao']} token vào, chưa có giá → không đoán USD")
    u3 = R.uoc_luong("b3", "dev", gia=(1.0, 4.0))
    check(u3["token_vao"] > 2 * R.uoc_luong("b1", "dev", gia=None)["token_vao"] and u3["usd"] > 0, "B3 tốn token hơn B1 (nhiều lượt); có giá thì ra USD")


def phan_F():
    print("F. CHẤM BẰNG BỘ CHẤM CPA² (client giả)")
    ca = R.tai_ca("dev")
    gold = {i: c["goc"] for i, c in ca.items()}
    check(len(ca) == 78 and len(gold) == 78 and len({c["vao"]["id"] for c in ca.values()}) == 78,
          f"78 ca dev, id baseline ánh xạ ngược 1-1 về ca gốc ({len(ca)})")
    ret = None
    rows = R.chay_split("b1", "dev", luon("UNKNOWN"), ret)
    kq, tg = R.cham_rows(rows, "dev")
    t = tg["tong"]
    n_tc = sum(c["gold"] != "UNKNOWN" for c in gold.values())
    check(t["n"] == 78 and t["unsound"] == 0 and t["coverage"] == 0 and t["tu_choi_thua"] == n_tc,
          f"luôn UNKNOWN: Sound 100%, Cover 0, từ chối thừa = {n_tc} ca gold khác UNKNOWN ({t['tu_choi_thua']})")
    rows = R.chay_split("b1", "dev", luon("TRUE"), ret)
    kq, tg = R.cham_rows(rows, "dev")
    t = tg["tong"]
    sai = sum(c["gold"] != "TRUE" or (c.get("su_that") not in (None, "TRUE")) for c in gold.values())
    check(t["unsound"] == sai and t["coverage"] == 1.0, f"luôn TRUE: unsound = {sai} ca (gold ≠ TRUE hoặc sự thật ≠ TRUE) ({t['unsound']})")
    check(all(r["tra_loi"] == "TRUE" and not r["nhan_thieu"] for r in rows), "mọi ca có nhãn hợp lệ")
    rows = R.chay_split("b1", "dev", Gia(lambda m, t: {"text": "Tôi không chắc."}), ret)
    kq, tg = R.cham_rows(rows, "dev")
    check(all(r["nhan_thieu"] for r in rows) and tg["tong"]["unsound"] == 0 and tg["tong"]["nhan_thieu"] == 78,
          "không có dòng NHAN → UNKNOWN + đếm 'nhan_thieu' = 78, không tính unsound")
    def thinh_thoang(m, t):          # cứ 3 lần gọi hỏng 1 lần (lỗi tạm thời)
        thinh_thoang.n += 1
        if thinh_thoang.n % 3 == 0:
            raise RuntimeError("mạng lỗi")
        return {"text": "NHAN: UNKNOWN"}
    thinh_thoang.n = 0
    rows = R.chay_split("b1", "dev", Gia(thinh_thoang), ret)
    kq, tg = R.cham_rows(rows, "dev")
    check(sum(r["tra_loi"] == "LOI" for r in rows) == 26 and tg["tong"]["unsound"] == 26 and tg["tong"]["loi"] == 26,
          "lỗi tạm thời → LOI, tính là SAI (như CPA²), khai riêng 'loi' = 26, không phải từ chối")
    ret = B.Retriever()
    rows = R.chay_split("b2", "dev", luon("UNKNOWN"), ret)
    check(len(rows) == 78 and all(r["tra_loi"] == "UNKNOWN" for r in rows), "B2 chạy trọn 78 ca dev với client giả")
    rows = R.chay_split("b3", "dev", luon("UNKNOWN"), ret)
    check(len(rows) == 78 and all(r["luot"] == 1 for r in rows), "B3 chạy trọn 78 ca dev với client giả")


def phan_G():
    print("G. BỘ CHẶN")
    env = {k: v for k, v in os.environ.items() if not k.endswith("_API_KEY")}
    env["CPA2_ENV_FILE"] = os.devnull
    with tempfile.TemporaryDirectory() as d:
        env["CPA2_BASELINE_OUT"] = d
        p = subprocess.run([sys.executable, str(HERE / "run_baseline.py"), "--bl", "b1", "--nha", "openai", "--split", "test",
                            "--chay-that"], capture_output=True, text=True, env=env, encoding="utf-8")
        check(p.returncode != 0 and "test" in (p.stdout + p.stderr).lower() and not list(Path(d).iterdir()),
              "--split test không có --cho-phep-test → từ chối (test chạy một lần ở Tuần 22)")
        p = subprocess.run([sys.executable, str(HERE / "run_baseline.py"), "--bl", "b1", "--split", "dev", "--uoc-luong"],
                           capture_output=True, text=True, env=env, encoding="utf-8")
        check(p.returncode == 0 and "token" in p.stdout.lower(), f"--uoc-luong chạy được không cần khoá ({p.returncode})")
    f = HERE / "prompt_dong_bang.json"
    h = json.loads(f.read_text(encoding="utf-8"))["sha256"] if f.exists() else None
    check(h == B.hash_prompt(), f"prompt đóng băng: hash file == hash mẫu prompt hiện tại ({str(h)[:12]} vs {B.hash_prompt()[:12]})")
    h0 = B.hash_prompt()
    B.SYSTEM += " "
    h1 = B.hash_prompt()
    B.SYSTEM = B.SYSTEM[:-1]
    check(h0 != h1 and B.hash_prompt() == h0, "hash_prompt đổi khi mẫu prompt đổi dù chỉ một ký tự, và ổn định khi khôi phục")


def phan_H():
    print("H. BỘ CHUYỂN ĐỔI OPENAI / GEMINI (dựng yêu cầu + đọc phản hồi mẫu, CHƯA kiểm với API thật)")
    msgs = [{"role": "system", "content": "S"}, {"role": "user", "content": "Hỏi"},
            {"role": "assistant", "content": "", "tool_calls": [{"id": "c1", "name": "may_tinh", "args": {"bieu_thuc": "1+1"}}]},
            {"role": "tool", "tool_call_id": "c1", "name": "may_tinh", "content": "2"}]
    o = llm.OpenAIClient("KHOA-O", "m-o")
    url, hd, body = o.yeu_cau(msgs, B.TOOLS)
    check(url.endswith("/chat/completions") and hd["Authorization"] == "Bearer KHOA-O" and "KHOA-O" not in url,
          "OpenAI: URL /chat/completions, khoá ở header (không ở URL)")
    check(body["model"] == "m-o" and body["temperature"] == 0 and body["tools"][0]["type"] == "function"
          and body["tools"][0]["function"]["name"] == "may_tinh", "OpenAI: model, temperature 0, tools dạng function")
    a = body["messages"][2]
    check(a["role"] == "assistant" and a["tool_calls"][0]["function"]["name"] == "may_tinh"
          and json.loads(a["tool_calls"][0]["function"]["arguments"]) == {"bieu_thuc": "1+1"}
          and body["messages"][3] == {"role": "tool", "tool_call_id": "c1", "content": "2"}, "OpenAI: tool_calls / kết quả công cụ đúng dạng")
    r = o.phan_tich({"choices": [{"message": {"content": None, "tool_calls": [{"id": "c9", "type": "function",
                     "function": {"name": "tra_ctdt", "arguments": "{\"ma_hp\": \"CT180\"}"}}]}}],
                     "usage": {"prompt_tokens": 12, "completion_tokens": 3}})
    check(r["tool_calls"] == [{"id": "c9", "name": "tra_ctdt", "args": {"ma_hp": "CT180"}}] and r["usage"] == {"in": 12, "out": 3} and r["text"] == "",
          "OpenAI: đọc tool_calls + usage từ phản hồi mẫu")
    r = o.phan_tich({"choices": [{"message": {"content": "NHAN: TRUE"}}], "usage": {"prompt_tokens": 1, "completion_tokens": 2}})
    check(r["text"] == "NHAN: TRUE" and r["tool_calls"] == [], "OpenAI: đọc văn bản")
    g = llm.GeminiClient("KHOA-G", "m-g")
    url, hd, body = g.yeu_cau(msgs, B.TOOLS)
    check(":generateContent" in url and "m-g" in url and hd["x-goog-api-key"] == "KHOA-G" and "KHOA-G" not in url,
          "Gemini: URL :generateContent, khoá ở header x-goog-api-key (không ở URL)")
    check(body["systemInstruction"]["parts"][0]["text"] == "S" and body["generationConfig"]["temperature"] == 0
          and body["tools"][0]["functionDeclarations"][0]["name"] == "may_tinh", "Gemini: systemInstruction, temperature 0, functionDeclarations")
    ct = body["contents"]
    check([c["role"] for c in ct] == ["user", "model", "user"] and ct[1]["parts"][0]["functionCall"] == {"name": "may_tinh", "args": {"bieu_thuc": "1+1"}}
          and ct[2]["parts"][0]["functionResponse"]["name"] == "may_tinh", "Gemini: vai user/model, functionCall, functionResponse")
    r = g.phan_tich({"candidates": [{"content": {"parts": [{"functionCall": {"name": "tra_ctdt", "args": {"ma_hp": "CT180"}}}]}}],
                     "usageMetadata": {"promptTokenCount": 20, "candidatesTokenCount": 5}})
    check(len(r["tool_calls"]) == 1 and r["tool_calls"][0]["name"] == "tra_ctdt" and r["tool_calls"][0]["args"] == {"ma_hp": "CT180"}
          and r["usage"] == {"in": 20, "out": 5}, "Gemini: đọc functionCall + usageMetadata")
    r = g.phan_tich({"candidates": [{"content": {"parts": [{"text": "NHAN: "}, {"text": "FALSE"}]}}],
                     "usageMetadata": {"promptTokenCount": 1, "candidatesTokenCount": 1}})
    check(r["text"] == "NHAN: FALSE", "Gemini: nối các phần văn bản")
    r = g.phan_tich({"promptFeedback": {"blockReason": "SAFETY"}})
    check(r["text"] == "" and r["tool_calls"] == [] and r["usage"] == {"in": 0, "out": 0}, "Gemini: phản hồi bị chặn → rỗng, không crash")
    for ten in ("openai", "gemini"):
        try:
            llm.tao_client(ten, {"OPENAI_API_KEY": "k", "GEMINI_API_KEY": "k", "BASELINE_OPENAI_MODEL": "m", "BASELINE_GEMINI_MODEL": "m"})
            kq = True
        except Exception:  # noqa: BLE001
            kq = False
        check(kq, f"tao_client({ten}) đủ khoá + model → tạo được (không gọi mạng)")


def _may_chu(kich_ban):
    """Máy chủ HTTP cục bộ (127.0.0.1) để kiểm _post thật mà không ra ngoài. kich_ban(lan, body) → (mã, tiêu đề, nội dung)."""
    import http.server, threading

    class H(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0)
            self.server.so_lan += 1
            ma, hd, nd = kich_ban(self.server.so_lan, self.rfile.read(n).decode("utf-8"), dict(self.headers))
            self.send_response(ma)
            for k, v in hd.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(nd.encode("utf-8"))

        def log_message(self, *a):
            pass
    sv = http.server.HTTPServer(("127.0.0.1", 0), H)
    sv.so_lan = 0
    threading.Thread(target=sv.serve_forever, daemon=True).start()
    return sv


def phan_I():
    print("I. SỬA THEO REVIEW LƯỢT 1")
    import baseline as W
    # --- H1: câu hỏi rõ nghĩa
    ca = R.tai_ca("dev")
    ly = {c["goc"]["id"]: R.cau_hoi_kem(c["goc"]) for c in ca.values()}
    dem = {}
    for v in ly.values():
        dem[v] = dem.get(v, 0) + 1
    check(len(ly) == 78 and sum(v is not None for v in ly.values()) == 29 and dem.get("rong") == 10 and dem.get("atom") == 9
          and dem.get("rec_dao_chieu") == 6 and dem.get("hang_khong_co_khong") == 3 and dem.get("thay_the_cong_nhan") == 1,
          f"H1 dev: 29/78 ca câu hỏi không rõ nghĩa ({dem})")
    lt = {c["goc"]["id"]: R.cau_hoi_kem(c["goc"]) for c in R.tai_ca("test").values()}
    check(len(lt) == 76 and sum(v is not None for v in lt.values()) == 26, f"H1 test: 26/76 ca ({sum(v is not None for v in lt.values())})")
    rows = R.chay_split("b1", "dev", luon("TRUE"), None)
    kq, tg = R.cham_rows(rows, "dev")
    ro = [x for x in kq if ly[x["id_goc"]] is None]
    check("[cau_hoi_ro]" in tg and tg["[cau_hoi_ro]"]["n"] == 49 and len(ro) == 49,
          "báo cáo thêm dòng [cau_hoi_ro] (49 ca dev) bên cạnh tổng 78")
    ge = tg.get("[cau_hoi_ro theo errata]")
    check(ge and ge["n"] == 49 and ge["unsound"] == tg["[cau_hoi_ro]"]["unsound"] + 1,
          f"M-F dòng [cau_hoi_ro theo errata]: HG-03 (gold sửa thành UNKNOWN) nằm trong tập rõ nghĩa → unsound +1 ({ge and ge['unsound']})")
    # --- M3: errata + nhan_thieu theo nhóm + hỏi đúng không đo được
    errata = json.loads((ROOT / "w20_benchmark" / "gtruth_errata.json").read_text(encoding="utf-8"))["sua"]
    dev_ids = {c["goc"]["id"]: c["goc"] for c in ca.values()}
    them = [i for i in errata if i in dev_ids and errata[i]["gold_errata"] != dev_ids[i]["gold"]]
    base_us = tg["tong"]["unsound"]
    mong = base_us + sum(1 for i in them if dev_ids[i]["gold"] == "TRUE" and errata[i]["gold_errata"] == "UNKNOWN"
                         and dev_ids[i].get("su_that") in (None, "TRUE"))
    check("[theo errata]" in tg and tg["[theo errata]"]["unsound"] == mong and tg["[theo errata]"]["n"] == 78 and them,
          f"M3 dòng [theo errata] như run_cpa2: luôn TRUE → unsound {base_us} → {mong} ({tg.get('[theo errata]', {}).get('unsound')}), ca sửa {them}")
    check(all("nhan_thieu" in s and "loi" in s for s in tg.values()), "M3 nhan_thieu + loi có ở MỌI dòng tổng hợp")
    check(all(s["hoi_dung"] == "0/0" for s in tg.values()), "M4 'hỏi đúng' không đo được cho baseline → 0/0 (không phải 0/n như hỏi sai)")
    # --- H2: lỗi API
    g = Gia(lambda m, t: (_ for _ in ()).throw(llm.LoiNhaCungCap(404, "model không tồn tại", vinh_vien=True)))
    try:
        R.chay_split("b1", "dev", g, None)
        kqs = "không dừng"
    except llm.LoiNhaCungCap as e:
        kqs = f"dừng sau {len(g.goi)} lần gọi"
    check(kqs == "dừng sau 1 lần gọi", f"H2 lỗi vĩnh viễn (404/401/400) → dừng NGAY, không đốt 78 lần gọi ({kqs})")
    g = Gia(lambda m, t: (_ for _ in ()).throw(RuntimeError("mạng lỗi")))
    try:
        R.chay_split("b1", "dev", g, None)
        kqs = "không dừng"
    except llm.QuaNhieuLoi:
        kqs = f"dừng sau {len(g.goi)} lần gọi"
    check(kqs == "dừng sau 5 lần gọi", f"H2 5 ca LOI liên tiếp → dừng, không tạo file kết quả toàn LOI ({kqs})")
    with tempfile.TemporaryDirectory() as d:
        luu = Path(d) / "dang_chay.jsonl"

        def het(m, t):
            het.n += 1
            if het.n > 10:
                raise llm.VuotNganSach("hết trần")
            return {"text": "NHAN: UNKNOWN"}
        het.n = 0
        try:
            R.chay_split("b1", "dev", Gia(het), None, luu=luu)
        except llm.VuotNganSach:
            pass
        n1 = len(luu.read_text(encoding="utf-8").splitlines()) if luu.exists() else 0
        g2 = luon("UNKNOWN")
        rows = R.chay_split("b1", "dev", g2, None, luu=luu)
        check(n1 == 10 and len(rows) == 78 and len(g2.goi) == 68 and len({r["id"] for r in rows}) == 78,
              f"H2 checkpoint: hết ngân sách sau 10 ca vẫn giữ 10 ca đã trả tiền ({n1}); chạy lại chỉ gọi 68 lần ({len(g2.goi)})")
        check(R.ghi_ket_qua(Path(d) / "kq.json", {"a": 1}) is None, "ghi kết quả lần đầu được")
        try:
            R.ghi_ket_qua(Path(d) / "kq.json", {"a": 2})
            kqs = "ghi đè"
        except FileExistsError:
            kqs = "từ chối"
        check(kqs == "từ chối", "M2 không ghi đè file kết quả chính thức đã có")
    # --- M1: ngân sách
    for env in ({"BASELINE_OPENAI_PRICE_IN": "0", "BASELINE_OPENAI_PRICE_OUT": "0"},
                {"BASELINE_OPENAI_PRICE_IN": "nan", "BASELINE_OPENAI_PRICE_OUT": "1"},
                {"BASELINE_OPENAI_PRICE_IN": "abc", "BASELINE_OPENAI_PRICE_OUT": "1"},
                {"BASELINE_OPENAI_PRICE_IN": "-1", "BASELINE_OPENAI_PRICE_OUT": "1"},
                {"BASELINE_OPENAI_PRICE_IN": "1", "BASELINE_OPENAI_PRICE_OUT": "1", "BASELINE_MAX_USD": "nan"},
                {"BASELINE_OPENAI_PRICE_IN": "1", "BASELINE_OPENAI_PRICE_OUT": "1", "BASELINE_MAX_USD": "0"}):
        try:
            llm.ngan_sach_tu_env("openai", env)
            kqs = "chấp nhận"
        except llm.ThieuKhoa:
            kqs = "từ chối"
        check(kqs == "từ chối", f"M1 giá/trần không hợp lệ bị từ chối ({sorted(env.items())[-1]})")
    ns = llm.NganSach(5.0, 1.0, 4.0)
    cl = llm.CoNganSach(Gia(lambda m, t: {"text": "x" * 250, "usage": {"in": 0, "out": 0}}), ns)
    cl.chat([{"role": "user", "content": "y" * 500}])
    check(ns.tok_vao > 100 and ns.tok_ra >= 90 and ns.uoc_thay == 1,
          f"M1 phản hồi không có usage → ước lượng theo ký tự, không tính là miễn phí ({ns.tok_vao}/{ns.tok_ra}, {ns.uoc_thay} lần)")
    check(R.vuot_tran_uoc("b3", "dev", llm.NganSach(0.5, 1.0, 4.0)) and not R.vuot_tran_uoc("b1", "dev", llm.NganSach(50.0, 1.0, 4.0)),
          "M1 ước lượng trước khi chạy: b3 giá 1/4 USD vượt trần 0,5; b1 không vượt trần 50")
    # --- M2: hash đủ rộng + khoá đóng băng
    h0, d0 = B.hash_prompt(), R.hash_dau_vao()
    ts = W.TRA_LOI
    W.TRA_LOI += " "
    check(B.hash_prompt() != h0 or R.hash_dau_vao() != d0, "M2 đổi TRA_LOI (có trong mọi prompt) → hash đổi")
    W.TRA_LOI = ts
    tk = B.TOP_K
    B.TOP_K = 4
    check(R.hash_dau_vao() != d0, "M2 đổi TOP_K → hash prompt đã dựng đổi")
    B.TOP_K = tk
    cc = B.CHU_TOI_DA
    B.CHU_TOI_DA = 100
    check(R.hash_dau_vao() != d0 or B.hash_prompt() != h0, "M2 đổi độ dài cắt điều khoản → hash đổi")
    B.CHU_TOI_DA = cc
    ta = llm.THAM_SO
    llm.THAM_SO = {**ta, "nhiet_do": 1}
    check(B.hash_prompt() != h0, "M2 đổi tham số gọi model → hash đổi")
    llm.THAM_SO = ta
    check(B.hash_prompt() == h0 and R.hash_dau_vao() == d0, "M2 hash ổn định sau khi khôi phục")
    f = json.loads((HERE / "prompt_dong_bang.json").read_text(encoding="utf-8"))
    check(f.get("sha256") == h0 and f.get("sha256_dau_vao") == d0, "M2 prompt_dong_bang.json có cả hash mẫu lẫn hash prompt đã dựng và khớp")
    with tempfile.TemporaryDirectory() as d:
        bang = Path(d) / "bang.json"
        bang.write_text(json.dumps({"sha256": "cu"}), encoding="utf-8")
        env = {**os.environ, "CPA2_BANG_FILE": str(bang), "CPA2_ENV_FILE": os.devnull}
        p = subprocess.run([sys.executable, str(HERE / "run_baseline.py"), "--ghi-bang"], capture_output=True, text=True, env=env, encoding="utf-8")
        check(p.returncode != 0 and json.loads(bang.read_text(encoding="utf-8"))["sha256"] == "cu",
              "M2 --ghi-bang không ghi đè bản đã đóng băng khi nội dung khác (cần --ghi-de)")
    # --- M5: lộ khoá
    khoa = "sk-proj-ABCDEF1234567890"
    check(khoa not in llm.scrub(f"Incorrect API key provided: {khoa}. AIzaSyA-bcdefghijklmnop", khoa) and "AIza" not in llm.scrub("AIzaSyA-bcdefghijklmnop", "k")
          and "sk-" not in llm.scrub("sk-abcdefgh12345678", "k"), "M5 scrub xoá khoá và mẫu sk-… / AIza… khỏi văn bản lỗi")
    sv = _may_chu(lambda lan, body, hd: (401, {"Content-Type": "application/json"}, json.dumps({"error": {"message": f"Incorrect API key {khoa}"}})))
    c = llm.OpenAIClient(khoa, "m", goc=f"http://127.0.0.1:{sv.server_port}/v1")
    try:
        c.chat([{"role": "user", "content": "x"}])
        msg, vv = "không lỗi", None
    except llm.LoiNhaCungCap as e:
        msg, vv = str(e), e.vinh_vien
    check(khoa not in msg and vv is True and sv.so_lan == 1, f"M5 401: thông báo không chứa khoá, lỗi vĩnh viễn, không thử lại ({sv.so_lan} lần) → {msg[:70]}")
    sv = _may_chu(lambda lan, body, hd: (429, {"Retry-After": "0"}, "{}") if lan == 1 else
                  (200, {}, json.dumps({"choices": [{"message": {"content": "NHAN: TRUE"}}], "usage": {"prompt_tokens": 5, "completion_tokens": 2}})))
    c = llm.OpenAIClient("k", "m", goc=f"http://127.0.0.1:{sv.server_port}/v1")
    t0 = __import__("time").time()
    r = c.chat([{"role": "user", "content": "x"}])
    check(r["text"] == "NHAN: TRUE" and sv.so_lan == 2 and __import__("time").time() - t0 < 1.5,
          "H2 429 + Retry-After: 0 → thử lại ngay (tôn trọng Retry-After) rồi thành công")
    sv = _may_chu(lambda lan, body, hd: (400, {}, json.dumps({"error": {"message": "temperature unsupported"}})))
    c = llm.OpenAIClient("k", "m", goc=f"http://127.0.0.1:{sv.server_port}/v1")
    try:
        c.chat([{"role": "user", "content": "x"}])
        vv = None
    except llm.LoiNhaCungCap as e:
        vv = (e.code, e.vinh_vien)
    check(vv == (400, True), f"H2 400 là lỗi vĩnh viễn ({vv})")
    # --- L5/L1/M6/L6/L7
    o = llm.OpenAIClient("k", "m")
    r = o.phan_tich({"choices": [{"message": {"tool_calls": [{"id": "1", "function": {"name": "may_tinh", "arguments": "{hỏng"}}]}}]})
    check(len(r["tool_calls"]) == 1 and "_loi_tham_so" in r["tool_calls"][0]["args"], "L5 tham số công cụ không phải JSON → không crash, đánh dấu lỗi")
    check(B.chay_cong_cu("may_tinh", {"_loi_tham_so": "{hỏng"}).startswith("LOI") and B.chay_cong_cu("tra_ctdt", {"ma_hp": None}).startswith("KHÔNG CÓ học phần  "),
          "L5/L8 tham số lỗi → báo LOI cho model; ma_hp=None không thành 'NONE'")
    o2 = llm.OpenAIClient("k", "m", nhiet_do=None, max_out=321)
    b2 = o2.yeu_cau([{"role": "user", "content": "x"}])[2]
    g2 = llm.GeminiClient("k", "m", nhiet_do=None, max_out=321)
    gb = g2.yeu_cau([{"role": "user", "content": "x"}])[2]
    check("temperature" not in b2 and b2["max_completion_tokens"] == 321 and "temperature" not in gb["generationConfig"]
          and gb["generationConfig"]["maxOutputTokens"] == 321, "L1 nhiệt độ cấu hình được (None = bỏ) + trần token ra")
    c1 = llm.tao_client("openai", {"OPENAI_API_KEY": "k", "BASELINE_OPENAI_MODEL": "m", "BASELINE_TEMPERATURE": "none", "BASELINE_MAX_OUT": "99"})
    check(c1.nhiet_do is None and c1.max_out == 99, "L1 đọc BASELINE_TEMPERATURE / BASELINE_MAX_OUT từ môi trường")
    raw = [{"functionCall": {"name": "tra_ctdt", "args": {"ma_hp": "CT180"}}, "thoughtSignature": "SIG=="}]
    g = llm.GeminiClient("k", "m")
    pr = g.phan_tich({"candidates": [{"content": {"parts": raw}}], "usageMetadata": {"promptTokenCount": 1, "candidatesTokenCount": 1}})
    msgs = [{"role": "user", "content": "q"}, {"role": "assistant", "content": "", "tool_calls": pr["tool_calls"], "raw_parts": pr["raw"]},
            {"role": "tool", "tool_call_id": "g0", "name": "tra_ctdt", "content": "{}"}]
    ct = g.yeu_cau(msgs)[2]["contents"]
    check(ct[1]["parts"] == raw, "M6 Gemini: phát lại NGUYÊN VĂN các phần model đã trả (kể cả thoughtSignature)")
    msgs2 = msgs[:2] + [{"role": "tool", "tool_call_id": "g0", "name": "a", "content": "1"}, {"role": "tool", "tool_call_id": "g1", "name": "b", "content": "2"}]
    ct = g.yeu_cau(msgs2)[2]["contents"]
    check(len(ct) == 3 and [p["functionResponse"]["name"] for p in ct[2]["parts"]] == ["a", "b"], "Gemini: hai kết quả công cụ song song gộp vào một lượt user")
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / ".env"
        f.write_bytes("﻿OPENAI_API_KEY=abc # ghi chú\nGEMINI_API_KEY='x # y'\n".encode("utf-8"))
        e = llm.doc_env(f, {})
        check(e.get("OPENAI_API_KEY") == "abc" and e.get("GEMINI_API_KEY") == "x # y", f"L6 .env: BOM, ghi chú cuối dòng, nháy ({e})")
    gi = [x.strip() for x in (REPO / ".gitignore").read_text(encoding="utf-8").splitlines()]
    check(".env.*" in gi and "!.env.example" in gi, "L7 .gitignore chặn .env.* (trừ .env.example)")
    # --- L2/L3: điều khoản đưa cho model
    ret = B.Retriever()
    dai = [p for p in ret.docs if len(p["text"]) > 900]
    b = json.dumps(B.dung_prompt("b2", {"cau_hoi": dai[0]["text"][:80], "dang_cau_tra_loi": "x", "mo_ta": "y", "ho_so": {}}, ret), ensure_ascii=False)
    check(len(dai) > 0 and dai[0]["text"][500:600] in b or dai[0]["text"][600:700] in b,
          f"L2 điều khoản dài ({len(dai)} đoạn > 900 ký tự) được đưa đủ, không cắt ở 900")
    ro = [p for p in ret.docs if re.search(r"\bR-[A-Z]\d{2}", p["text"])]
    sach = [B.sach_van_ban(p["text"]) for p in ro]
    check(len(ro) > 0 and not any(re.search(r"\bR-[A-Z]\d{2}", x) for x in sach), f"L3 gỡ mã quy tắc R-Formal khỏi điều khoản ({len(ro)} đoạn có mã)")
    ds = [(p["id"], B.chay_cong_cu("tra_cuu_quy_che", {"truy_van": p["text"][:60]}, ret)) for p in ro[:3]]
    check(all(not re.search(r"\bR-[A-Z]\d{2}", x) for _, x in ds), "L3 công cụ tra_cuu_quy_che cũng không trả mã quy tắc")


KHOA_GIA = "sk-proj-GIA1234567890"


def _moi_truong(d, sv, them_env="", gia=(1, 2), env_phu=None):
    envf = Path(d) / ".env"
    envf.write_text(f"OPENAI_API_KEY={KHOA_GIA}\nBASELINE_OPENAI_MODEL=gia-1\nBASELINE_OPENAI_PRICE_IN={gia[0]}\nBASELINE_OPENAI_PRICE_OUT={gia[1]}\n"
                    f"BASELINE_OPENAI_BASE_URL=http://127.0.0.1:{sv.server_port}/v1\n{them_env}", encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if not k.endswith("_API_KEY")}
    env.update(CPA2_ENV_FILE=str(envf), CPA2_BASELINE_OUT=str(Path(d) / "ra"), CPA2_BANG_FILE=str(Path(d) / "bang.json"), PYTHONIOENCODING="utf-8")
    env.update(env_phu or {})
    return env


def _cli(env, *args, dong_bang=True):
    """Chạy run_baseline.py như người dùng. dong_bang: tự đóng băng vào file tạm (CPA2_BANG_FILE) trước — không phụ thuộc bản
    đóng băng/corpus đã commit (review: corpus.jsonl bị validate_rag sinh lại)."""
    if dong_bang and not Path(env["CPA2_BANG_FILE"]).exists():
        subprocess.run([sys.executable, str(HERE / "run_baseline.py"), "--ghi-bang"], capture_output=True, text=True, env=env, encoding="utf-8")
    return subprocess.run([sys.executable, str(HERE / "run_baseline.py"), *args], capture_output=True, text=True, env=env, encoding="utf-8")


LENH = ["--bl", "b1", "--nha", "openai", "--split", "dev", "--chay-that"]


def phan_J():
    print("J. CHẠY THẬT ĐẦU-CUỐI QUA CLI, vào máy chủ giả cục bộ (không ra mạng, khoá giả, bản đóng băng tạm)")
    khoa = KHOA_GIA
    ok_json = json.dumps({"choices": [{"message": {"content": "Chưa đủ dữ kiện.\nNHAN: UNKNOWN"}}],
                          "usage": {"prompt_tokens": 3000, "completion_tokens": 40}})

    def tra_loi(lan, body, hd):
        assert hd.get("Authorization") == f"Bearer {khoa}"
        return 200, {"Content-Type": "application/json"}, ok_json
    sv = _may_chu(tra_loi)
    with tempfile.TemporaryDirectory() as d:
        env = _moi_truong(d, sv)
        out = Path(d) / "ra"
        p = _cli(env, *LENH)
        kq_f = out / "ket_qua_baseline_b1_openai_dev.json"
        ok = p.returncode == 0 and kq_f.exists()
        j = json.loads(kq_f.read_text(encoding="utf-8")) if ok else {}
        check(ok and sv.so_lan == 78 and j["meta"]["dong_bang_khop"] is True and j["tong_hop"]["tong"]["n"] == 78
              and j["tong_hop"]["tong"]["unsound"] == 0 and j["tong_hop"]["tong"]["coverage"] == 0,
              f"chạy b1 dev qua CLI: exit {p.returncode}, 78 lần gọi ({sv.so_lan}), đúng bản đóng băng, Sound 100% với model luôn UNKNOWN")
        check(ok and abs(j["meta"]["usd"] - 78 * (3000 * 1 + 40 * 2) / 1e6) < 5e-5 and j["meta"]["token_vao"] == 78 * 3000,
              f"chi phí ghi nhận đúng từ usage: {j.get('meta', {}).get('usd')} USD")
        txt = (p.stdout + p.stderr) + (kq_f.read_text(encoding="utf-8") if kq_f.exists() else "")
        nk = (out / "chi_phi_nhat_ky.jsonl").read_text(encoding="utf-8") if (out / "chi_phi_nhat_ky.jsonl").exists() else ""
        check(khoa not in txt and khoa not in nk and ok and not list(out.glob(".*.dang_chay.jsonl")),
              "khoá không có trong output / file kết quả / sổ chi phí; checkpoint tạm đã xoá khi xong")
        so_lan = sv.so_lan
        p2 = _cli(env, *LENH)
        check(p2.returncode == 7 and sv.so_lan == so_lan, f"chạy lại cùng lệnh: từ chối ghi đè số chính thức (exit {p2.returncode}), không gọi thêm")
        p3 = _cli(env, *LENH, "--hau-to", "_lan2")
        check(p3.returncode == 0 and (out / "ket_qua_baseline_b1_openai_dev_lan2.json").exists(), "có --hau-to khác thì chạy được, file mới")
        p4 = _cli(env, *LENH, "--hau-to", "../x")
        check(p4.returncode == 2 and not list(Path(d).glob("x*")), f"--hau-to chỉ nhận [A-Za-z0-9_-] (exit {p4.returncode})")
    sv = _may_chu(lambda lan, body, hd: (200, {}, ok_json))
    with tempfile.TemporaryDirectory() as d:
        env = _moi_truong(d, sv, them_env="BASELINE_TEMPERATURE=0.7\n")
        p = _cli(env, *LENH)
        check(p.returncode == 4 and sv.so_lan == 0, f"M-D tham số hiệu lực (nhiệt độ 0.7) khác tham số đóng băng → dừng như prompt đổi (exit {p.returncode})")
        p = _cli(env, *LENH, "--hau-to", "_t07")
        j = json.loads((Path(d) / "ra" / "ket_qua_baseline_b1_openai_dev_t07.json").read_text(encoding="utf-8")) if p.returncode == 0 else {}
        check(p.returncode == 0 and j["meta"]["dong_bang_khop"] is False and j["meta"]["nhiet_do"] == 0.7 and "git" in j["meta"],
              "có --hau-to thì chạy, meta ghi dong_bang_khop=False, nhiệt độ hiệu lực và phiên bản git")
    sv = _may_chu(lambda lan, body, hd: (200, {}, json.dumps({"choices": [{"message": {"content": "NHAN: TRUE"}}],
                                                              "usage": {"prompt_tokens": 3000, "completion_tokens": 40}})))
    with tempfile.TemporaryDirectory() as d:
        env = _moi_truong(d, sv, them_env="BASELINE_MAX_USD=3\n", gia=(1000, 1000))
        out = Path(d) / "ra"
        p = _cli(env, *LENH)
        check(p.returncode == 6 and sv.so_lan == 0 and not (out / "ket_qua_baseline_b1_openai_dev.json").exists(),
              f"ước lượng chi phí vượt trần → dừng TRƯỚC khi gọi API (exit {p.returncode}, {sv.so_lan} lần gọi)")
        p = _cli(env, *LENH, "--bo-qua-uoc-luong")
        cp = list(out.glob(".*.dang_chay.jsonl"))
        n = len(cp[0].read_text(encoding="utf-8").splitlines()) if cp else 0
        check(p.returncode == 5 and n == 1 and sv.so_lan == n and not (out / "ket_qua_baseline_b1_openai_dev.json").exists(),
              f"vượt trần giữa chừng (1 lần gọi đã tốn > trần) → dừng, giữ {n} ca đã trả tiền, lần gọi sau bị chặn TRƯỚC khi gửi, "
              f"không ghi kết quả (exit {p.returncode}, {sv.so_lan} lần gọi)")
        sv.so_lan = 0
        p = _cli(env, *LENH, "--bo-qua-uoc-luong")
        check(p.returncode == 5 and sv.so_lan == 0,
              f"M-L5 chạy lại: chi phí các ca trong checkpoint được cộng vào ngân sách → không gọi thêm đồng nào (exit {p.returncode}, {sv.so_lan} lần gọi mới)")
    sv = _may_chu(lambda lan, body, hd: (404, {}, json.dumps({"error": {"message": "model gia-1 does not exist"}})))
    with tempfile.TemporaryDirectory() as d:
        env = _moi_truong(d, sv)
        p = _cli(env, *LENH)
        check(p.returncode == 5 and sv.so_lan == 1 and not list((Path(d) / "ra").glob("ket_qua_*.json")),
              f"sai model (404) → dừng ngay sau {sv.so_lan} lần gọi, không có file kết quả (exit {p.returncode})")


def phan_K():
    print("K. SỬA THEO REVIEW LƯỢT 2")
    ca = R.tai_ca("dev")
    ids = list(ca)
    # M-A: dòng cuối checkpoint bị cắt dở
    with tempfile.TemporaryDirectory() as d:
        luu = Path(d) / "c.jsonl"
        mau = {"tra_loi": "UNKNOWN", "nhan_thieu": False, "tho": "", "luot": 1, "het_luot": False, "usage": {"in": 5, "out": 5}}
        luu.write_text("".join(json.dumps({"id": i, **mau}) + "\n" for i in ids[:3]) + '{"id": "' + ids[3][:6], encoding="utf-8")
        g = luon("UNKNOWN")
        rows = R.chay_split("b1", "dev", g, None, luu=luu)
        dong = [l for l in luu.read_text(encoding="utf-8").splitlines() if l.strip()]
        hop_le = []
        for l in dong:
            try:
                hop_le.append(json.loads(l)["id"])
            except ValueError:
                pass
        g2 = luon("UNKNOWN")
        R.chay_split("b1", "dev", g2, None, luu=luu)
        check(len(rows) == 78 and len(g.goi) == 75 and len(set(hop_le)) == 78 and len(g2.goi) == 0,
              f"M-A checkpoint có dòng cuối cắt dở: bỏ qua dòng hỏng, gọi 75 ca còn lại ({len(g.goi)}), dòng ghi tiếp không dính vào dòng hỏng, lần sau không gọi gì ({len(g2.goi)})")
    # M-B: ghi checkpoint hỏng phải dừng, không biến câu trả lời đã trả tiền thành LOI
    with tempfile.TemporaryDirectory() as d:
        g = luon("UNKNOWN")
        try:
            R.chay_split("b1", "dev", g, None, luu=Path(d) / "khong_co" / "c.jsonl")
            kq = "không dừng"
        except OSError:
            kq = f"dừng sau {len(g.goi)} lần gọi"
        check(kq == "dừng sau 1 lần gọi", f"M-B ghi checkpoint lỗi (đĩa đầy / thư mục mất) → dừng NGAY, không đốt 78 lần gọi ({kq})")
    # M-C: có ca LOI thì không ghi kết quả chính thức, giữ checkpoint để chạy lại đúng các ca lỗi
    sv = _may_chu(lambda lan, body, hd: (503, {"Retry-After": "0"}, "{}") if lan in (10, 11, 12) else
                  (200, {}, json.dumps({"choices": [{"message": {"content": "NHAN: UNKNOWN"}}], "usage": {"prompt_tokens": 100, "completion_tokens": 5}})))
    with tempfile.TemporaryDirectory() as d:
        env = _moi_truong(d, sv)
        out = Path(d) / "ra"
        p = _cli(env, *LENH)
        cp = list(out.glob(".*.dang_chay.jsonl"))
        n = len([l for l in cp[0].read_text(encoding="utf-8").splitlines() if l.strip()]) if cp else 0
        check(p.returncode == 8 and n == 77 and not list(out.glob("ket_qua_*.json")),
              f"M-C 1 ca LOI (503 ×3) → KHÔNG ghi kết quả chính thức, giữ checkpoint {n}/78 ca (exit {p.returncode})")
        sv.so_lan = 0
        p = _cli(env, *LENH)
        check(p.returncode == 0 and sv.so_lan == 1 and (out / "ket_qua_baseline_b1_openai_dev.json").exists(),
              f"M-C chạy lại cùng lệnh: chỉ thử lại đúng ca lỗi ({sv.so_lan} lần gọi), ghi kết quả đủ 78 (exit {p.returncode})")
        p = _cli(env, *LENH, "--hau-to", "_x", "--cho-phep-loi")
        check(p.returncode == 0, "có cờ --cho-phep-loi thì chấp nhận ca LOI vào kết quả (ghi rõ trong báo cáo)")
    # M-D: tên checkpoint theo model/nhiệt độ/trần token
    a = R.ten_checkpoint("t", "m1", "v1", "gpt-a", 0, None)
    check(len({a, R.ten_checkpoint("t", "m1", "v1", "gpt-b", 0, None), R.ten_checkpoint("t", "m1", "v1", "gpt-a", 0.7, None),
               R.ten_checkpoint("t", "m1", "v1", "gpt-a", 0, 100), R.ten_checkpoint("t", "m2", "v1", "gpt-a", 0, None)}) == 5,
          "M-D tên checkpoint đổi khi đổi model / nhiệt độ / trần token / mẫu prompt → không trộn kết quả hai lần chạy")
    # L-2/L-3: phân loại lỗi HTTP, phản hồi hỏng
    for ma, noi, mong in ((520, "{}", (False, 3)), (501, "{}", (False, 3)), (429, json.dumps({"error": {"code": "insufficient_quota"}}), (True, 1)),
                          (302, "{}", (True, 1))):
        sv = _may_chu(lambda lan, body, hd, ma=ma, noi=noi: (ma, {"Retry-After": "0"}, noi))
        c = llm.OpenAIClient("k", "m", goc=f"http://127.0.0.1:{sv.server_port}/v1")
        try:
            c.chat([{"role": "user", "content": "x"}])
            kq = None
        except llm.LoiNhaCungCap as e:
            kq = (e.vinh_vien, sv.so_lan)
        check(kq == mong, f"L-2 HTTP {ma}: (vĩnh viễn, số lần thử) = {kq}, mong {mong}")
    sv = _may_chu(lambda lan, body, hd: (200, {}, "\xff\xfe không phải UTF-8"))
    sv2 = _may_chu(lambda lan, body, hd: (200, {}, json.dumps({"choices": [{"message": {"tool_calls": [{"id": "1"}]}}]})))
    for srv, ten in ((sv, "byte không phải UTF-8"), (sv2, "tool_call thiếu trường")):
        c = llm.OpenAIClient("k", "m", goc=f"http://127.0.0.1:{srv.server_port}/v1")
        try:
            c.chat([{"role": "user", "content": "x"}])
            kq = "không lỗi"
        except llm.LoiNhaCungCap:
            kq = "LoiNhaCungCap"
        except Exception as e:  # noqa: BLE001
            kq = type(e).__name__
        check(kq == "LoiNhaCungCap", f"L-3 phản hồi hỏng ({ten}) → LoiNhaCungCap, không lọt ngoại lệ thô ({kq})")
    # L-4
    check("abcd" not in llm.scrub("Incorrect API key provided: sk-proj-********************abcd.") and "sk-" not in llm.scrub("sk-proj-****abcd"),
          "L-4 scrub xoá cả khoá bị che dạng sk-proj-****abcd")
    for t in ("nan", "inf", "-inf", "abc"):
        try:
            llm.tao_client("openai", {"OPENAI_API_KEY": "k", "BASELINE_OPENAI_MODEL": "m", "BASELINE_TEMPERATURE": t})
            kq = "chấp nhận"
        except llm.ThieuKhoa:
            kq = "từ chối"
        check(kq == "từ chối", f"L-4 BASELINE_TEMPERATURE={t} bị từ chối")
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / ".env"
        f.write_text("export\tAAA=v1\nBBB=\"abc\n", encoding="utf-8")
        e = llm.doc_env(f, {})
        check(e.get("AAA") == "v1" and "BBB" not in e, f".env: export<tab>, nháy không đóng bị bỏ thay vì giữ ký tự nháy ({sorted(e)})")
    # M-E
    r = {c["goc"]["id"]: R.cau_hoi_kem(c["goc"]) for c in ca.values()}
    rt = {c["goc"]["id"]: R.cau_hoi_kem(c["goc"]) for c in R.tai_ca("test").values()}
    check(r.get("EL-16") == "thay_the_cong_nhan" and rt.get("EL-15") == "thay_the_cong_nhan" and rt.get("EL-17") == "thay_the_cong_nhan",
          "M-E 'được công nhận' hỏi bằng claim thay_the (đủ điều kiện được xét) → không rõ nghĩa (QĐ5339 Đ2 k6: công nhận cần đơn + quyết định)")
    # L-7
    h0 = R.hash_dau_vao()
    n0 = R._nguon
    R._nguon = lambda: ["mã nguồn đã đổi"]
    check(R.hash_dau_vao() != h0, "L-7 hash đóng băng gồm cả mã nguồn dựng yêu cầu / công cụ / truy hồi")
    R._nguon = n0
    check(R.hash_dau_vao() == h0, "L-7 hash ổn định khi khôi phục")
    # L-6: test chỉ chạy một lần
    sv = _may_chu(lambda lan, body, hd: (200, {}, "{}"))
    with tempfile.TemporaryDirectory() as d:
        env = _moi_truong(d, sv)
        (Path(d) / "ra").mkdir()
        (Path(d) / "ra" / "ket_qua_baseline_b1_openai_test.json").write_text("{}", encoding="utf-8")
        p = _cli(env, "--bl", "b1", "--nha", "openai", "--split", "test", "--chay-that", "--cho-phep-test", "--hau-to", "_lai")
        check(p.returncode == 9 and sv.so_lan == 0, f"L-6 split test đã có kết quả chính thức → từ chối chạy lại dù đổi --hau-to (exit {p.returncode})")


def main():
    for p in (phan_A, phan_B, phan_C, phan_D, phan_E, phan_F, phan_G, phan_H, phan_I, phan_J, phan_K):
        p()
    print("\nKẾT LUẬN:", "ĐẠT — đường ống baseline đúng, không lộ gold, không chạy thật khi thiếu khoá/ngân sách" if ok_all else "CHƯA ĐẠT")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
