"""
baselines.py — ba baseline KHÔNG có solver cho Tuần 21 (CPA2): so sánh với CPA² trên cùng đầu vào và cùng bộ chấm.

  b1  LLM thuần      hồ sơ/bảng điểm + câu hỏi. Không kèm văn bản quy chế.
  b2  RAG thuần      như b1 + TOP_K điều khoản BM25 (w14 Retriever) tìm theo câu hỏi. Chỉ đưa văn bản điều khoản + địa chỉ,
                     KHÔNG rule id / atom ASP / chứng chỉ.
  b3  Tool-calling   như b1 + 3 công cụ TỔNG QUÁT: may_tinh (số học), tra_ctdt (một học phần), tra_cuu_quy_che (BM25).
                     Không có công cụ tính ĐTBCTL / xét tốt nghiệp — nếu có thì thành solver.

Nhãn: chỉ nhận dòng "NHAN: TRUE|FALSE|UNKNOWN". Thiếu / mơ hồ → UNKNOWN và đếm riêng (nhan_thieu): dạng trả lời được
nêu trong prompt, nên thiếu nhãn không bị tính là kết luận sai; số 'nhan_thieu' báo cáo để người đọc tự đánh giá.
Hỏi đúng (hoi_dung) không đo được cho baseline: câu trả lời tự do không có danh sách biến cần hỏi.

Đóng băng (prompt_dong_bang.json) TRƯỚC lần chạy thật đầu tiên, hai hash:
  sha256            hash_prompt(): mọi mẫu + dạng trả lời của w20 (TRA_LOI) + công cụ + trần lượt + TOP_K + độ dài cắt điều khoản
                    + bộ lọc mã quy tắc + tham số gọi model (llm.THAM_SO)
  sha256_dau_vao    run_baseline.hash_dau_vao(): prompt ĐÃ DỰNG cho mọi ca dev+test (b1/b2/b3) + nội dung corpus + CTĐT
Sửa gì làm đổi một trong hai → số chính thức giữ nguyên, số mới ghi ra file riêng (--hau-to). Ghi lại bản đóng băng:
python run_baseline.py --ghi-bang (từ chối ghi đè bản khác trừ khi --ghi-de).
"""
import ast, hashlib, json, operator, re, sys, unicodedata
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
for d in (HERE, ROOT / "w14_rag", ROOT / "w20_benchmark", ROOT / "w17_adversarial"):
    sys.path.insert(0, str(d))
from retriever import Retriever  # noqa: E402
import baseline as W  # noqa: E402  (w20: dạng trả lời TRA_LOI nằm trong mọi prompt → vào hash)
import llm  # noqa: E402

CURRICULUM = ROOT / "w6_curriculum" / "curriculum_cntt_k49.json"
MAX_LUOT = 6          # trần số lượt gọi model cho một ca (b3)
TOP_K = 5             # số điều khoản đưa vào b2
TOOL_K = 3            # số điều khoản tra_cuu_quy_che trả về
LAM_TRON = 6          # số chữ số thập phân của may_tinh
CHU_TOI_DA = 4000     # ký tự tối đa mỗi điều khoản đưa cho model (đoạn dài nhất trong corpus ~3500: không cắt cụt mệnh đề cần thiết)
_MA_QUY_TAC = r"\(?\bxem\s+R-[A-Z]\d{2}[a-z]?\b\)?|\bR-[A-Z]\d{2}[a-z]?\b"      # mã quy tắc R-Formal lẫn trong văn bản điều khoản
NHAN_MAU = "NHAN: TRUE | NHAN: FALSE | NHAN: UNKNOWN"

SYSTEM = ("Bạn là trợ lý tư vấn học vụ của Trường Đại học Cần Thơ (chương trình đào tạo CNTT K49). Chỉ dựa trên dữ kiện được cung "
          "cấp trong cuộc trò chuyện. Nếu dữ kiện chưa đủ để kết luận chắc chắn thì trả lời UNKNOWN, không đoán.")
SYSTEM_B3 = (" Bạn có thể gọi công cụ khi cần: may_tinh (số học), tra_ctdt (thông tin một học phần trong CTĐT), "
             "tra_cuu_quy_che (tìm điều khoản quy chế). Công cụ không biết hồ sơ của sinh viên; hồ sơ nằm trong câu hỏi.")
HUONG_DAN = ("Hãy lập luận ngắn gọn (tối đa 10 dòng), rồi viết dòng cuối cùng ĐÚNG MỘT trong các dạng sau: "
             + NHAN_MAU + ". Không viết gì sau dòng này.")
MAU_NGUOI_DUNG = ("{dang}\n\nCÂU HỎI: {cau_hoi}\n\nGHI CHÚ: {mo_ta}\n\nDỮ KIỆN (JSON):\n{du_kien}\n{them}\n{huong_dan}")
MAU_DIEU_KHOAN = "\nĐIỀU KHOẢN LIÊN QUAN (trích từ quy chế / CTĐT):\n{ds}\n"

TOOLS = [
    {"name": "may_tinh", "description": "Tính một biểu thức số học (+ - * / // % ** và ngoặc). Ví dụ: (3*4.0+2*3.5)/5.",
     "parameters": {"type": "object", "properties": {"bieu_thuc": {"type": "string"}}, "required": ["bieu_thuc"]}},
    {"name": "tra_ctdt", "description": "Tra thông tin một học phần trong CTĐT CNTT K49 theo mã (tên, tín chỉ, tiên quyết, song hành, loại).",
     "parameters": {"type": "object", "properties": {"ma_hp": {"type": "string"}}, "required": ["ma_hp"]}},
    {"name": "tra_cuu_quy_che", "description": "Tìm 3 điều khoản quy chế (QĐ3266, QĐ5339) / CTĐT liên quan nhất tới truy vấn.",
     "parameters": {"type": "object", "properties": {"truy_van": {"type": "string"}}, "required": ["truy_van"]}},
]


def sach_van_ban(text):
    """Gỡ mã quy tắc R-Formal (vd. 'xem R-M16') khỏi văn bản điều khoản: baseline không được thấy tên quy tắc của hệ thống."""
    return re.sub(r"[ \t]{2,}", " ", re.sub(_MA_QUY_TAC, "", text))


def hash_prompt():
    return hashlib.sha256(json.dumps({"system": SYSTEM, "system_b3": SYSTEM_B3, "huong_dan": HUONG_DAN, "mau": MAU_NGUOI_DUNG,
                                      "dieu_khoan": MAU_DIEU_KHOAN, "tools": TOOLS, "max_luot": MAX_LUOT, "top_k": TOP_K,
                                      "chu_toi_da": CHU_TOI_DA, "ma_quy_tac": _MA_QUY_TAC, "tra_loi": W.TRA_LOI,
                                      "tham_so": llm.THAM_SO, "tool_k": TOOL_K, "lam_tron": LAM_TRON},
                                     sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- đọc nhãn
_NHAN = re.compile(r"NH[AÃ]N\s*:\s*([^\n]*)", re.I)


def doc_nhan(s):
    """(nhãn, nhan_thieu). Chỉ dòng 'NHAN: X' cuối cùng, X phải đúng một trong TRUE/FALSE/UNKNOWN."""
    ms = _NHAN.findall(unicodedata.normalize("NFC", s or ""))
    if ms:
        v = ms[-1].strip().strip("*_`'\" .,;:!").upper()
        if v in ("TRUE", "FALSE", "UNKNOWN"):
            return v, False
    return "UNKNOWN", True


# ---------------------------------------------------------------- công cụ
_OP = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
       ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod, ast.Pow: operator.pow}


def may_tinh(bieu_thuc):
    """Số học an toàn: chỉ số + toán tử + ngoặc; hằng ≤ 1e12; luỹ thừa mũ ≤ 10. Không gọi hàm, không tên biến."""
    if len(bieu_thuc) > 200:
        raise ValueError("biểu thức quá dài")

    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and type(n.value) in (int, float) and abs(n.value) <= 1e12:
            return n.value
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
            v = ev(n.operand)
            return v if isinstance(n.op, ast.UAdd) else -v
        if isinstance(n, ast.BinOp) and type(n.op) in _OP:
            a, b = ev(n.left), ev(n.right)
            if isinstance(n.op, ast.Pow) and abs(b) > 10:
                raise ValueError("số mũ quá lớn")
            v = _OP[type(n.op)](a, b)
            if abs(v) > 1e15:
                raise ValueError("kết quả quá lớn")
            return v
        raise ValueError("biểu thức không hợp lệ")
    return ev(ast.parse(bieu_thuc.strip(), mode="eval"))


_CT = None
_RET = None


def _ctdt():
    global _CT
    if _CT is None:
        _CT = {h["ma"]: h for h in json.loads(CURRICULUM.read_text(encoding="utf-8"))["hoc_phan"]}
    return _CT


def _ret(ret=None):
    global _RET
    if ret is not None:
        return ret
    if _RET is None:
        _RET = Retriever()
    return _RET


def chay_cong_cu(ten, args, ret=None):
    try:
        if ten == "may_tinh":
            if "_loi_tham_so" in args:
                return "LOI: tham số công cụ không phải JSON hợp lệ"
            return repr(round(may_tinh(str(args.get("bieu_thuc", ""))), LAM_TRON))
        if ten == "tra_ctdt":
            ma = str(args.get("ma_hp") or "").strip().upper()
            h = _ctdt().get(ma)
            if h is None:
                return f"KHÔNG CÓ học phần {ma} trong CTĐT CNTT K49"
            return json.dumps({k: h.get(k) for k in ("ma", "ten", "tin_chi", "tien_quyet", "tien_quyet_tc", "song_hanh", "hk",
                                                    "dieu_kien", "khoi", "cot")}, ensure_ascii=False)
        if ten == "tra_cuu_quy_che":
            return json.dumps([{"dia_chi": p.get("dia_chi") or p["tieu_de"], "noi_dung": sach_van_ban(p["text"])[:CHU_TOI_DA]}
                               for p, _ in _ret(ret).search(str(args.get("truy_van") or ""), k=TOOL_K)], ensure_ascii=False)
        return f"LOI: không có công cụ {ten}"
    except Exception as e:  # noqa: BLE001 — lỗi công cụ báo lại cho model, không làm hỏng ca
        return f"LOI: {type(e).__name__}: {e}"


# ---------------------------------------------------------------- prompt + vòng lặp
def dung_prompt(ten, vao, ret=None):
    du_kien = {k: vao[k] for k in ("ho_so", "bang_diem_ocr", "khai_bao") if k in vao}
    them = ""
    if ten == "b2":
        ds = "\n".join(f"[{i}] {p.get('dia_chi') or p['tieu_de']}: {sach_van_ban(p['text'])[:CHU_TOI_DA]}"
                       for i, (p, _) in enumerate(_ret(ret).search(vao["cau_hoi"], k=TOP_K), 1))
        them = MAU_DIEU_KHOAN.format(ds=ds)
    nd = MAU_NGUOI_DUNG.format(dang=vao["dang_cau_tra_loi"], cau_hoi=vao["cau_hoi"], mo_ta=vao["mo_ta"],
                               du_kien=json.dumps(du_kien, ensure_ascii=False), them=them, huong_dan=HUONG_DAN)
    return [{"role": "system", "content": SYSTEM + (SYSTEM_B3 if ten == "b3" else "")}, {"role": "user", "content": nd}]


def chay(ten, vao, client, ret=None):
    """Một ca → {tra_loi, nhan_thieu, tho, luot, het_luot, usage}. Ngoại lệ của client (mạng, hết ngân sách) do nơi gọi xử lý."""
    msgs = dung_prompt(ten, vao, ret)
    tools = TOOLS if ten == "b3" else None
    u = {"in": 0, "out": 0}
    luot = 0
    tho = []
    while luot < MAX_LUOT:
        r = client.chat(msgs, tools)
        luot += 1
        u["in"] += r["usage"]["in"]
        u["out"] += r["usage"]["out"]
        tho.append(r["text"])
        if tools and r["tool_calls"]:
            msgs.append({"role": "assistant", "content": r["text"], "tool_calls": r["tool_calls"], "raw_parts": r.get("raw")})
            for t in r["tool_calls"]:
                msgs.append({"role": "tool", "tool_call_id": t["id"], "name": t["name"],
                             "content": chay_cong_cu(t["name"], t["args"], ret)})
            continue
        nhan, thieu = doc_nhan(r["text"])
        return {"tra_loi": nhan, "nhan_thieu": thieu, "tho": "\n---\n".join(tho), "luot": luot, "het_luot": False, "usage": u}
    return {"tra_loi": "UNKNOWN", "nhan_thieu": True, "tho": "\n---\n".join(tho), "luot": luot, "het_luot": True, "usage": u}

