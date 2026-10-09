"""
retriever.py — truy hồi + grounding cho CPA2 (Tuần 14)

Hai việc tách bạch:
  1. TRUY HỒI (search): câu hỏi tiếng Việt → top-k passage quy chế/CTĐT. Dùng cho câu tra cứu
     ("quy chế nói gì về ...") và làm baseline RAG ở Tuần 21.
  2. GROUNDING (ground_certificate): bước chứng minh why(atom, rule) → passage nguồn. Đây là tra
     cứu TẤT ĐỊNH qua bảng asp → passage, KHÔNG qua truy hồi: nguồn của một kết luận do chứng
     minh quyết định, không do độ giống văn bản quyết định.
  Hậu kiểm (kiem_trich_dan): mọi passage được trích trong câu trả lời phải là nguồn của certificate.

Truy hồi không cần mạng: BM25 trên âm tiết + bigram âm tiết (tiếng Việt: "tốt nghiệp", "cảnh báo"
là hai âm tiết), có dấu + không dấu, mở rộng viết tắt học vụ (TC ↔ tín chỉ, ĐTBCTL ↔ ...).
Cấu hình chốt trên tập DEV (rag_queries.json), không nhìn tập TEST:
  unigram, b=0.75, + TF-IDF ký tự (RRF)  → R@1 11/24, R@5 17/24
  unigram, b=0.75, BM25 thuần            → R@1 15/24, R@5 20/24
  bigram,  b=0.4,  BM25 thuần (chọn)     → R@1 18/24, R@5 21/24
TF-IDF n-gram ký tự làm GIẢM kết quả ở mọi cấu hình nên đã bỏ.

Chạy: python retriever.py "sinh viên được đăng ký tối đa bao nhiêu tín chỉ"
"""
import json, math, re, sys, unicodedata
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
CORPUS = HERE / "corpus.jsonl"

# Viết tắt dùng trong QĐ3266/QĐ5339 và cách sinh viên hay hỏi
VIET_TAT = {
    "tc": "tín chỉ", "hk": "học kỳ", "sv": "sinh viên", "hp": "học phần",
    "đtbctl": "điểm trung bình chung tích lũy", "đtbchk": "điểm trung bình chung học kỳ",
    "đtbcnh": "điểm trung bình chung năm học", "đrl": "điểm rèn luyện",
    "lvtn": "luận văn tốt nghiệp", "tltn": "tiểu luận tốt nghiệp",
    "ctđt": "chương trình đào tạo", "gdqp": "giáo dục quốc phòng", "gdtc": "giáo dục thể chất",
    "đhct": "đại học cần thơ", "cvht": "cố vấn học tập", "cntt": "công nghệ thông tin", "gpa": "điểm trung bình chung tích lũy",
}


def bo_dau(s):
    s = s.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def chuan_hoa(s):
    s = unicodedata.normalize("NFC", s).lower()
    for vt, day_du in VIET_TAT.items():
        if re.search(rf"\b{vt}\b", s):
            s += " " + day_du
        if day_du in s:
            s += " " + vt
    return s


def tach_tu(s):
    tu = re.findall(r"\w+", chuan_hoa(s))
    x = tu + [a + "_" + b for a, b in zip(tu, tu[1:])]
    return x + [bo_dau(t) for t in x if bo_dau(t) != t]


class BM25:
    def __init__(self, docs, k1=1.5, b=0.4):
        self.k1, self.b = k1, b
        self.tf = [Counter(d) for d in docs]
        self.len = [len(d) for d in docs]
        self.avg = sum(self.len) / len(docs)
        df = Counter(t for d in docs for t in set(d))
        n = len(docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def scores(self, q):
        out = []
        for tf, L in zip(self.tf, self.len):
            s = 0.0
            for t in q:
                if t in tf:
                    f = tf[t]
                    s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * L / self.avg))
            out.append(s)
        return out


class Retriever:
    def __init__(self, corpus_path=CORPUS):
        self.docs = [json.loads(l) for l in Path(corpus_path).read_text(encoding="utf-8").splitlines() if l.strip()]
        self.by_id = {d["id"]: d for d in self.docs}
        self.by_asp = {a: d for d in self.docs for a in d.get("asp", [])}
        self.by_rule = {r: d for d in self.docs for r in d.get("rules", [])}
        self.bm25 = BM25([tach_tu(d["text"]) for d in self.docs])

    def search(self, q, k=5, loai=None, van_ban=None):
        """Trả về [(passage, điểm BM25)] — điểm chỉ dùng để xếp hạng, không phải độ tin cậy."""
        sc = self.bm25.scores(tach_tu(q))
        idx = [i for i in sorted(range(len(self.docs)), key=lambda i: -sc[i])
               if (loai is None or self.docs[i]["loai"] == loai)
               and (van_ban is None or self.docs[i]["van_ban"] == van_ban)]
        return [(self.docs[i], sc[i]) for i in idx[:k]]

    # ---------- grounding ----------
    def ground_rule(self, asp_id):
        return self.by_asp.get(asp_id)

    def ground_certificate(self, cert):
        """Gắn passage nguồn vào từng bước chứng minh. Bước nào có rule_id mà không có passage →
        ghi vào 'khong_nguon' (không được im lặng bỏ qua)."""
        nguon, khong_nguon = [], []
        for s in cert["proof"]["steps"]:
            p = self.ground_rule(s["rule_id"])
            if p is None:
                khong_nguon.append(s["rule_id"])
                continue
            s["passage_id"] = p["id"]
            s["dia_chi"] = p["dia_chi"]
            s["trang"] = p["trang"]
            if p["id"] not in nguon:
                nguon.append(p["id"])
        cert["grounding"] = {"passages": nguon, "khong_nguon": khong_nguon}
        return cert

    def trich_dan(self, cert, toi_da=3):
        """Đoạn trích dẫn cho câu trả lời — chỉ lấy từ nguồn của certificate."""
        out = []
        for pid in cert.get("grounding", {}).get("passages", [])[:toi_da]:
            p = self.by_id[pid]
            out.append({"passage_id": pid, "dia_chi": p["dia_chi"], "trang": p["trang"],
                        "trich": p["text"][:300]})
        return out


def kiem_trich_dan(cert, cited_ids):
    """Hậu kiểm grounding: trích một passage KHÔNG nằm trong nguồn của certificate → chặn.
    Trả về (ok, danh sách passage trích sai)."""
    hop_le = set(cert.get("grounding", {}).get("passages", []))
    sai = [c for c in cited_ids if c not in hop_le]
    return (not sai), sai


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "sinh viên được đăng ký tối đa bao nhiêu tín chỉ"
    r = Retriever()
    for p, s in r.search(q, k=5):
        print(f"{s:7.2f}  {p['id']:<24} {p['text'][:110]}")
