"""
llm.py — client LLM tối thiểu cho baseline Tuần 21 (CPA2). Chỉ dùng thư viện chuẩn (urllib): CLAUDE.md cấm cài thêm thư viện.

  doc_env        đọc .env (KEY=VALUE; BOM, chú thích cuối dòng, nháy) — không ghi đè biến môi trường có sẵn, không sửa os.environ
  tao_client     OpenAI / Gemini từ biến môi trường; thiếu khoá hoặc chưa chọn model → ThieuKhoa (nêu tên biến)
  NganSach       trần USD + giá token (USD / 1 triệu token) lấy từ môi trường — KHÔNG đoán giá, giá/trần phải hữu hạn và > 0
  CoNganSach     bọc client: chặn lần gọi sau khi đã vượt trần (vượt tối đa một lần gọi); phản hồi không có usage → ước lượng
                 theo số ký tự (không tính là miễn phí)
  scrub          xoá khoá API và mẫu khoá (sk-…, AIza…) khỏi mọi văn bản lỗi trước khi lưu/in

Lỗi gọi API: LoiNhaCungCap(code, thông báo, vinh_vien). 4xx (trừ 408/429) = vĩnh viễn (sai model, sai khoá, tham số bị từ chối):
nơi gọi dừng ngay, không đốt tiền cho 78 lần gọi hỏng. 429/5xx/lỗi mạng được thử lại (tôn trọng Retry-After); hết lượt thử
vẫn là lỗi tạm thời.

Giao diện chung: client.chat(messages, tools=None) → {"text", "tool_calls": [{"id","name","args"}], "usage": {"in","out"}, ["raw"]}
  messages: {"role": system|user|assistant|tool, "content", ["tool_calls"], ["raw_parts"], ["tool_call_id", "name"]}
  raw_parts (Gemini): phần model đã trả, phát lại NGUYÊN VĂN (kể cả thoughtSignature mà họ Gemini 3 yêu cầu khi gọi công cụ).

⚠ Dạng yêu cầu/phản hồi OpenAI Chat Completions và Gemini generateContent dưới đây viết theo tài liệu công khai nhưng
CHƯA kiểm với API thật (cloud không có khoá; validate_baseline H/I chỉ kiểm với phản hồi mẫu và một máy chủ cục bộ). Tên model
và giá token do người chạy khai trong môi trường (BASELINE_<NHA>_MODEL, BASELINE_<NHA>_PRICE_IN/OUT) — tên trong CLAUDE.md
(Terra/Sol/Flash) là tên thương mại, cần đối chiếu ID API lúc chạy. Nhiệt độ mặc định 0 (BASELINE_TEMPERATURE; "none" = bỏ tham
số, cần với model từ chối nhiệt độ ≠ mặc định); BASELINE_MAX_OUT đặt trần token ra (model suy luận tính cả token nghĩ).
BASELINE_<NHA>_BASE_URL (tuỳ chọn) đổi địa chỉ gốc API — dùng để kiểm thử với máy chủ giả cục bộ; khoá sẽ được gửi tới địa chỉ đó,
nên chỉ đặt khi tự kiểm soát địa chỉ.
"""
import http.client, json, math, os, re, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

TOKEN_MOI_KY_TU = 2.5            # ước lượng thô: 1 token ≈ 2,5 ký tự (JSON + tiếng Việt)
THAM_SO = {"nhiet_do": 0, "max_out": None, "thu_lai": 3, "cho_giay": 120}      # có trong hash đóng băng (baselines.hash_prompt)
_MAC_DINH = object()


class ThieuKhoa(Exception):
    """Thiếu khoá API / model / giá token — dừng trước khi gọi bất cứ thứ gì."""


class VuotNganSach(Exception):
    pass


class LoiNhaCungCap(Exception):
    def __init__(self, code, thong_bao, vinh_vien=False):
        super().__init__(f"{'HTTP ' + str(code) if code else 'mạng'}: {thong_bao}")
        self.code, self.vinh_vien = code, vinh_vien


class QuaNhieuLoi(Exception):
    pass


def scrub(s, khoa=None):
    s = str(s)
    if khoa:
        s = s.replace(khoa, "[đã xoá khoá]")
    s = re.sub(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_\-*]{4,}", "[đã xoá khoá]", s)      # gồm dạng bị che sk-proj-****abcd
    s = re.sub(r"AIza[0-9A-Za-z_\-]{10,}", "[đã xoá khoá]", s)
    return re.sub(r"(?i)bearer\s+[A-Za-z0-9._\-]{8,}", "Bearer [đã xoá khoá]", s)


def doc_env(duong_dan=None, env=None):
    """Đọc file .env rồi phủ biến môi trường (khác rỗng) lên trên. Trả dict mới; không sửa os.environ."""
    env = os.environ if env is None else env
    out = {}
    p = Path(duong_dan) if duong_dan else None
    if p and p.is_file():
        for dong in p.read_text(encoding="utf-8-sig").splitlines():
            dong = re.sub(r"^export\s+", "", dong.strip())
            if not dong or dong.startswith("#") or "=" not in dong:
                continue
            k, v = dong.split("=", 1)
            v = v.strip()
            if v[:1] in ("\"", "'"):
                if v.find(v[0], 1) < 0:
                    continue                      # nháy không đóng → bỏ dòng, không giữ ký tự nháy làm giá trị
                v = v[1:v.find(v[0], 1)]
            else:
                v = re.split(r"\s+#", v, maxsplit=1)[0].strip()
            if k.strip() and v:
                out[k.strip()] = v
    out.update({k: v for k, v in dict(env).items() if v != ""})
    return out


NHA = {"openai": ("OPENAI_API_KEY", "BASELINE_OPENAI_MODEL"), "gemini": ("GEMINI_API_KEY", "BASELINE_GEMINI_MODEL")}


def tao_client(ten, env):
    if ten not in NHA:
        raise ThieuKhoa(f"nhà cung cấp lạ: {ten} (openai | gemini)")
    bien_khoa, bien_model = NHA[ten]
    if not env.get(bien_khoa):
        raise ThieuKhoa(f"thiếu {bien_khoa}: đặt trong biến môi trường của phiên cloud hoặc file .env (xem .env.example)")
    if not env.get(bien_model):
        raise ThieuKhoa(f"chưa chọn model: đặt {bien_model} (ID model theo tài liệu của nhà cung cấp, không đoán)")
    t = env.get("BASELINE_TEMPERATURE")
    try:
        nhiet = THAM_SO["nhiet_do"] if not t else (None if t.strip().lower() == "none" else float(t))
        if nhiet is not None and not math.isfinite(nhiet):
            raise ValueError
        mo = int(env["BASELINE_MAX_OUT"]) if env.get("BASELINE_MAX_OUT") else THAM_SO["max_out"]
    except ValueError:
        raise ThieuKhoa("BASELINE_TEMPERATURE phải là số hoặc 'none'; BASELINE_MAX_OUT phải là số nguyên") from None
    kw = {"goc": env[f"BASELINE_{ten.upper()}_BASE_URL"].rstrip("/")} if env.get(f"BASELINE_{ten.upper()}_BASE_URL") else {}
    return (OpenAIClient if ten == "openai" else GeminiClient)(env[bien_khoa], env[bien_model], nhiet_do=nhiet, max_out=mo, **kw)


class NganSach:
    def __init__(self, tran_usd, gia_vao, gia_ra):
        self.tran_usd, self.gia_vao, self.gia_ra = float(tran_usd), float(gia_vao), float(gia_ra)
        self.tok_vao = self.tok_ra = 0
        self.uoc_thay = 0          # số lần phải ước lượng vì phản hồi không có usage

    @property
    def da_dung(self):
        return (self.tok_vao * self.gia_vao + self.tok_ra * self.gia_ra) / 1e6

    def cong(self, usage):
        self.tok_vao += int(usage.get("in", 0))
        self.tok_ra += int(usage.get("out", 0))

    def kiem(self, uoc_vao=0, uoc_ra=0):
        du = self.da_dung + (uoc_vao * self.gia_vao + uoc_ra * self.gia_ra) / 1e6
        if du > self.tran_usd:
            raise VuotNganSach(f"đã dùng {self.da_dung:.4f} USD, thêm ước lượng sẽ thành {du:.4f} > trần {self.tran_usd:.2f} USD")


def _so_duong(env, bien, mac_dinh=None):
    v = env.get(bien)
    if not v:
        if mac_dinh is None:
            raise ThieuKhoa(f"chưa khai {bien}")
        return mac_dinh
    try:
        x = float(v)
    except ValueError:
        raise ThieuKhoa(f"{bien} = {v!r} không phải số") from None
    if not math.isfinite(x) or x <= 0:
        raise ThieuKhoa(f"{bien} = {v!r}: phải là số hữu hạn > 0 (giá 0 hoặc NaN làm trần ngân sách không bao giờ chạy)")
    return x


def ngan_sach_tu_env(ten, env):
    k = ten.upper()
    if not (env.get(f"BASELINE_{k}_PRICE_IN") and env.get(f"BASELINE_{k}_PRICE_OUT")):
        raise ThieuKhoa(f"chưa khai giá token: đặt BASELINE_{k}_PRICE_IN và BASELINE_{k}_PRICE_OUT (USD / 1 triệu token, lấy từ "
                        "bảng giá hiện hành của nhà cung cấp) — hệ thống không đoán giá")
    return NganSach(_so_duong(env, "BASELINE_MAX_USD", 5.0), _so_duong(env, f"BASELINE_{k}_PRICE_IN"),
                    _so_duong(env, f"BASELINE_{k}_PRICE_OUT"))


class CoNganSach:
    def __init__(self, client, ngan_sach):
        self.client, self.ngan_sach = client, ngan_sach
        self.provider, self.model = client.provider, client.model

    def chat(self, messages, tools=None):
        self.ngan_sach.kiem()
        r = self.client.chat(messages, tools)
        u = r["usage"]
        if not u.get("in"):         # một lần gọi thật luôn có token vào > 0: không có usage → vẫn bị tính tiền
            u = {"in": int(len(json.dumps(messages, ensure_ascii=False)) / TOKEN_MOI_KY_TU),
                 "out": int((len(r["text"]) + len(json.dumps(r["tool_calls"], ensure_ascii=False))) / TOKEN_MOI_KY_TU)}
            self.ngan_sach.uoc_thay += 1
        self.ngan_sach.cong(u)
        return r


def _post(url, headers, body, khoa=None):
    """POST JSON. Thử lại 408/425/429/5xx/lỗi mạng (Retry-After tôn trọng, tối đa 60 giây); 429 hết hạn mức (insufficient_quota) và
    mọi 4xx khác là LỖI VĨNH VIỄN. Phản hồi không phải JSON/UTF-8 không thử lại. Thông báo lỗi đã scrub khoá."""
    thu, cho = THAM_SO["thu_lai"], THAM_SO["cho_giay"]
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    for lan in range(thu):
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", **headers}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=cho) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            noi = scrub(e.read().decode("utf-8", "replace"), khoa)[:300]
            tam = (e.code >= 500 or e.code in (408, 425, 429)) and "insufficient_quota" not in noi
            if tam and lan < thu - 1:
                ra = e.headers.get("Retry-After") if e.headers else None
                time.sleep(min(float(ra), 60) if ra and re.fullmatch(r"\d+(\.\d+)?", ra) else 2 ** (lan + 1))
                continue
            raise LoiNhaCungCap(e.code, noi, vinh_vien=not tam) from None
        except ValueError:                        # JSONDecodeError / UnicodeDecodeError: nhà cung cấp trả rác, thử lại không đổi được gì
            raise LoiNhaCungCap(None, "phản hồi không phải JSON/UTF-8 hợp lệ") from None
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError, http.client.HTTPException) as e:
            if lan < thu - 1:
                time.sleep(2 ** (lan + 1))
                continue
            raise LoiNhaCungCap(None, scrub(f"{type(e).__name__}: {getattr(e, 'reason', e)}", khoa)[:200]) from None


class _Chung:
    def __init__(self, khoa, model, goc, nhiet_do=_MAC_DINH, max_out=_MAC_DINH):
        self.khoa, self.model, self.goc = khoa, model, goc
        self.nhiet_do = THAM_SO["nhiet_do"] if nhiet_do is _MAC_DINH else nhiet_do
        self.max_out = THAM_SO["max_out"] if max_out is _MAC_DINH else max_out

    def chat(self, messages, tools=None):
        url, hd, body = self.yeu_cau(messages, tools)
        p = _post(url, hd, body, self.khoa)
        try:
            return self.phan_tich(p)
        except (KeyError, TypeError, ValueError, AttributeError, IndexError):
            raise LoiNhaCungCap(None, "phản hồi sai định dạng (thiếu trường)") from None


class OpenAIClient(_Chung):
    provider = "openai"

    def __init__(self, khoa, model, goc="https://api.openai.com/v1", **kw):
        super().__init__(khoa, model, goc, **kw)

    def yeu_cau(self, messages, tools=None):
        ms = []
        for m in messages:
            if m["role"] == "assistant" and m.get("tool_calls"):
                ms.append({"role": "assistant", "content": m.get("content") or None,
                           "tool_calls": [{"id": t["id"], "type": "function",
                                           "function": {"name": t["name"], "arguments": json.dumps(t["args"], ensure_ascii=False)}}
                                          for t in m["tool_calls"]]})
            elif m["role"] == "tool":
                ms.append({"role": "tool", "tool_call_id": m["tool_call_id"], "content": m["content"]})
            else:
                ms.append({"role": m["role"], "content": m["content"]})
        body = {"model": self.model, "messages": ms}
        if self.nhiet_do is not None:
            body["temperature"] = self.nhiet_do
        if self.max_out:
            body["max_completion_tokens"] = self.max_out
        if tools:
            body["tools"] = [{"type": "function", "function": {"name": t["name"], "description": t["description"],
                                                               "parameters": t["parameters"]}} for t in tools]
        return f"{self.goc}/chat/completions", {"Authorization": f"Bearer {self.khoa}"}, body

    def phan_tich(self, p):
        m = (p.get("choices") or [{}])[0].get("message") or {}
        tc = []
        for t in m.get("tool_calls") or []:
            try:
                args = json.loads(t["function"].get("arguments") or "{}")
                if not isinstance(args, dict):
                    raise ValueError
            except ValueError:
                args = {"_loi_tham_so": str(t["function"].get("arguments"))[:200]}
            tc.append({"id": t["id"], "name": t["function"]["name"], "args": args})
        u = p.get("usage") or {}
        return {"text": m.get("content") or "", "tool_calls": tc,
                "usage": {"in": u.get("prompt_tokens", 0), "out": u.get("completion_tokens", 0)}}


class GeminiClient(_Chung):
    provider = "gemini"

    def __init__(self, khoa, model, goc="https://generativelanguage.googleapis.com/v1beta", **kw):
        super().__init__(khoa, model, goc, **kw)

    def yeu_cau(self, messages, tools=None):
        he_thong = "\n".join(m["content"] for m in messages if m["role"] == "system")
        ct = []
        for m in messages:
            if m["role"] == "system":
                continue
            if m["role"] == "tool":
                p = {"functionResponse": {"name": m["name"], "response": {"result": m["content"]}}}
                if ct and ct[-1]["role"] == "user" and "functionResponse" in ct[-1]["parts"][-1]:
                    ct[-1]["parts"].append(p)
                else:
                    ct.append({"role": "user", "parts": [p]})
            elif m["role"] == "assistant":
                parts = m.get("raw_parts") or (([{"text": m["content"]}] if m.get("content") else []) +
                                               [{"functionCall": {"name": t["name"], "args": t["args"]}} for t in m.get("tool_calls") or []])
                ct.append({"role": "model", "parts": parts})
            else:
                ct.append({"role": "user", "parts": [{"text": m["content"]}]})
        cfg = {}
        if self.nhiet_do is not None:
            cfg["temperature"] = self.nhiet_do
        if self.max_out:
            cfg["maxOutputTokens"] = self.max_out
        body = {"contents": ct, "generationConfig": cfg}
        if he_thong:
            body["systemInstruction"] = {"parts": [{"text": he_thong}]}
        if tools:
            body["tools"] = [{"functionDeclarations": [{"name": t["name"], "description": t["description"],
                                                         "parameters": t["parameters"]} for t in tools]}]
        return (f"{self.goc}/models/{urllib.parse.quote(self.model, safe='')}:generateContent",
                {"x-goog-api-key": self.khoa}, body)

    def phan_tich(self, p):
        c = (p.get("candidates") or [{}])[0].get("content") or {}
        text, tc = "", []
        for i, ph in enumerate(c.get("parts") or []):
            if "text" in ph:
                text += ph["text"]
            elif "functionCall" in ph:
                tc.append({"id": f"g{i}", "name": ph["functionCall"]["name"], "args": ph["functionCall"].get("args") or {}})
        u = p.get("usageMetadata") or {}
        return {"text": text, "tool_calls": tc, "raw": c.get("parts") or None,
                "usage": {"in": u.get("promptTokenCount", 0), "out": u.get("candidatesTokenCount", 0) + u.get("thoughtsTokenCount", 0)}}
