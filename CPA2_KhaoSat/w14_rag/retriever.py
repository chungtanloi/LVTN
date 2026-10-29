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

29/10/2026: search mặc định dùng mô hình kết hợp đặc trưng từ vựng đóng băng
trong retrieval_model_v3.json, chọn trên DEV và TRAIN loại cùng nhóm người trả lời,
áp dụng sửa nhãn nguồn TRAIN từ bản rà soát hiện có.
Retriever(ranked=False) giữ BM25 cũ và luôn dùng cho grounding chứng chỉ.
Không cần embedding/LLM hoặc thư viện ML trong runtime; điểm xếp hạng không phải xác suất.
"""
import hashlib, json, math, re, sys, unicodedata
from functools import lru_cache
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
CORPUS = HERE / "corpus.jsonl"
DEFAULT_MODEL = HERE / 'retrieval_model_v3.json'


@lru_cache(maxsize=1)
def source_documents():
    """Source display is separate from legacy lexical retrieval hints."""
    return {doc['id']: doc for doc in (json.loads(line) for line in
            (HERE / 'corpus_source_v1.jsonl').read_text(encoding='utf-8').splitlines() if line.strip())}


def resolve_source_passage(passage, question):
    """Resolve a verified OCR clause split without returning its old mixed text."""
    sources = source_documents()
    bindings = json.loads((HERE / 'source_bindings_v1.json').read_text(encoding='utf-8'))
    candidates = [sources[pid] for pid in bindings.get(passage['id'], [passage['id']])]
    if len(candidates) == 1:
        return candidates[0]
    scores = BM25([tach_tu(doc['text']) for doc in candidates]).scores(tach_tu(question))
    return candidates[max(range(len(candidates)), key=lambda i: scores[i])]

# Viết tắt dùng trong QĐ3266/QĐ5339 và cách sinh viên hay hỏi
VIET_TAT = {
    "tc": "tín chỉ", "hk": "học kỳ", "sv": "sinh viên", "hp": "học phần",
    "đtbctl": "điểm trung bình chung tích lũy", "đtbchk": "điểm trung bình chung học kỳ",
    "đtbcnh": "điểm trung bình chung năm học", "đrl": "điểm rèn luyện",
    "lvtn": "luận văn tốt nghiệp", "tltn": "tiểu luận tốt nghiệp",
    "ctđt": "chương trình đào tạo", "gdqp": "giáo dục quốc phòng", "gdtc": "giáo dục thể chất",
    "đhct": "đại học cần thơ", "cvht": "cố vấn học tập", "cntt": "công nghệ thông tin", "gpa": "điểm trung bình chung tích lũy",
    # Vocabulary observed in the synthetic survey training split; retrieval only.
    "cbhv": "cảnh báo học tập", "cbht": "cảnh báo học tập", "khht": "kế hoạch học tập",
    "đk": "đăng ký", "dk": "đăng ký",
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


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()


RETRIEVAL_ALIASES = [
    (r'\bcanh bao hoc vu\b', 'canh bao hoc tap'),
    (r'\b(?:rot|truot)\b', 'diem f'),
    (r'\bra truong\b', 'tot nghiep'),
    (r'\bduoi hoc\b', 'buoc thoi hoc'),
    (r'\bsong nganh\b', 'hoc cung luc hai chuong trinh'),
]


def retrieval_words(text):
    text = bo_dau(chuan_hoa(text))
    for pattern, replacement in RETRIEVAL_ALIASES:
        text = re.sub(pattern, replacement, text)
    return re.findall(r'\w+', text)


def retrieval_tokens(text):
    words = retrieval_words(text)
    return words + ['_'.join(words[i:i + 2]) for i in range(len(words) - 1)]


def passage_body(doc):
    text, title = doc['text'], doc.get('tieu_de', '')
    position = text.find(title)
    return text[position + len(title):] if title and position >= 0 else text


def unit_scores(values):
    denominator = max(values, default=0) or 1
    return [value / denominator for value in values]


def requested_decisions(question):
    """Keep the complete reference token; never truncate an unknown decision."""
    return set(re.findall(r'(?<!\w)(?:qd|quyet\s+dinh)\s*(\d\w*)', bo_dau(question.lower())))


def decision_number(document):
    match = re.fullmatch(r'qd(\d+)(?:_.*)?', document)
    return match.group(1) if match else None


def requested_articles(question):
    return set(re.findall(r'\bdieu\s+(\d\w*)', bo_dau(question.lower())))


def eligible_indices(docs, question):
    decisions, articles = requested_decisions(question), requested_articles(question)
    codes = set(re.findall(r'\b[A-Z]{2}\d{3}E?\b', question.upper()))
    curriculum = bool(codes) and bool(re.search(r'tien quyet|song hanh|hoc truoc|tin chi|thong tin (?:mon|hoc phan)', bo_dau(question.lower())))
    return [i for i, doc in enumerate(docs)
            if (not decisions or decision_number(doc['van_ban']) in decisions)
            and (not articles or str(doc.get('dieu')) in articles)
            and (not curriculum or doc.get('ma_hp') in codes)]


def source_excerpt(question, doc, limit=300):
    """Return a contiguous original-text window, never generated regulation text."""
    text = doc['text']
    if len(text) <= limit:
        return text, 0, len(text)
    query = set(retrieval_tokens(question))
    # Sentence starts and word boundaries keep the excerpt readable. Distinct
    # bigrams reward phrases without letting repeated boilerplate win.
    starts = [0] + [m.end() for m in re.finditer(r'\s+', text)]
    best = None
    for start in starts:
        end = min(start + limit, len(text))
        if end < len(text) and not text[end].isspace():
            boundary = text.rfind(' ', start, end)
            if boundary > start:
                end = boundary
        tokens = set(retrieval_tokens(text[start:end]))
        overlap = query & tokens
        score = sum(2 if '_' in token else 1 for token in overlap)
        candidate = (score, -start, start, end)
        if best is None or candidate[:2] > best[:2]:
            best = candidate
    return text[best[2]:best[3]], best[2], best[3]


class RetrievalRanker:
    """Small, frozen lexical model. Training examples only rank original sources.

    Runtime uses the standard library, not an embedding service or an LLM.
    No query IDs, evaluation gold or student profiles are read by this class.
    """
    FEATURE_NAMES = ('full', 'canonical', 'body', 'lead', 'title', 'window',
                     'example_max', 'example_top2', 'coverage', 'course_entity',
                     'document_entity', 'condition_lead', 'threshold_body')

    def __init__(self, docs, legacy, model_path=None):
        self.docs, self.legacy = docs, legacy
        config = json.loads(Path(model_path or DEFAULT_MODEL).read_text(encoding='utf-8'))
        examples_file = config.get('examples_file', 'rag_survey_train_sources_v1.json')
        if examples_file not in ('rag_survey_train_sources_v1.json', 'rag_survey_train_sources_v2.json'):
            raise ValueError('Unknown retrieval training artifact.')
        training = json.loads((HERE / examples_file).read_text(encoding='utf-8'))
        if config['examples_sha256'] != canonical_hash(training):
            raise ValueError('Retrieval training examples differ from the frozen model.')
        if config['corpus_sha256'] != canonical_hash(sorted(docs, key=lambda d: d['id'])):
            raise ValueError('Retrieval corpus differs from the frozen model.')
        self.weights = config['weights']
        if (config['features'] != list(self.FEATURE_NAMES) or len(self.weights) != len(self.FEATURE_NAMES)
                or any(not isinstance(w, (int, float)) or not math.isfinite(w) or w < 0 for w in self.weights)):
            raise ValueError('Invalid retrieval model configuration.')
        self.canonical = BM25([retrieval_tokens(d['text']) for d in docs])
        bodies = [passage_body(d) for d in docs]
        self.bodies = BM25([retrieval_tokens(text) for text in bodies], b=.2)
        self.leads = BM25([retrieval_tokens(' '.join(text.split()[:12])) for text in bodies], b=.2)
        self.titles = BM25([retrieval_tokens(d.get('tieu_de', '')) for d in docs])
        chunks, self.chunk_owners = [], []
        for i, text in enumerate(bodies):
            words = text.split()
            for start in range(0, max(len(words), 1), 32):
                chunks.append(retrieval_tokens(' '.join(words[start:start + 64])))
                self.chunk_owners.append(i)
        self.chunks = BM25(chunks, b=.2)
        self.body_tokens = [Counter(retrieval_tokens(text)) for text in bodies]
        self.lead_texts = [' '.join(retrieval_words(' '.join(text.split()[:20]))) for text in bodies]
        self.thresholds = [bool(re.search(r'(?:tu|duoi|tren|vuot qua).{0,35}(?:tro len|tro xuong|[0-9]|diem [a-f])', ' '.join(retrieval_words(text)))) for text in bodies]
        by_id = {doc['id']: i for i, doc in enumerate(docs)}
        self.examples = [q for q in training['queries'] if q['gold']]
        if not self.examples or any(q['split'] != 'train' or not set(q['gold']) <= set(by_id) for q in self.examples):
            raise ValueError('Retrieval examples must be train-only and point to existing sources.')
        self.example_index = BM25([retrieval_tokens(q['q']) for q in self.examples])
        self.example_owners = [[by_id[pid] for pid in q['gold']] for q in self.examples]

    def features(self, question, excluded_group=None):
        tokens = retrieval_tokens(question)
        scores = [unit_scores(self.legacy.scores(tach_tu(question))),
                  unit_scores(self.canonical.scores(tokens)), unit_scores(self.bodies.scores(tokens)),
                  unit_scores(self.leads.scores(tokens)), unit_scores(self.titles.scores(tokens))]
        windows = [0.0] * len(self.docs)
        for owner, score in zip(self.chunk_owners, self.chunks.scores(tokens)):
            windows[owner] = max(windows[owner], score)
        scores.append(unit_scores(windows))
        examples = [[] for _ in self.docs]
        for q, owners, score in zip(self.examples, self.example_owners, self.example_index.scores(tokens)):
            if excluded_group is not None and q['group'] == excluded_group:
                continue
            for owner in owners:
                examples[owner].append(score)
        scores.append(unit_scores([max(values, default=0) for values in examples]))
        scores.append(unit_scores([sum(sorted(values, reverse=True)[:2]) for values in examples]))
        codes = set(re.findall(r'\b[A-Z]{2}\d{3}E?\b', question.upper()))
        requested = requested_decisions(question)
        words = ' '.join(retrieval_words(question))
        condition = bool(re.search(r'\b(?:dieu kien|khi nao|truong hop)\b', words))
        bound = bool(re.search(r'bao nhieu|toi da|toi thieu|duoi|vuot', words))
        denominator = sum(self.canonical.idf.get(t, 0) for t in set(tokens)) or 1
        rows = []
        for i, doc in enumerate(self.docs):
            coverage = sum(self.canonical.idf.get(t, 0) for t in set(tokens) if t in self.body_tokens[i]) / denominator
            condition_lead = float(condition and bool(re.search(r'dieu kien|truong hop|chi duoc', self.lead_texts[i]))) * scores[3][i]
            rows.append([channel[i] for channel in scores] + [coverage,
                        float(bool(codes) and doc.get('ma_hp') in codes),
                        float(bool(requested) and decision_number(doc['van_ban']) in requested),
                        condition_lead, float(bound and self.thresholds[i]) * scores[2][i]])
        return rows

    def scores(self, question):
        return [float(sum(weight * value for weight, value in zip(self.weights, row))) for row in self.features(question)]


class Retriever:
    def __init__(self, corpus_path=None, *, ranked=True, model_path=None):
        config = json.loads(Path(model_path or DEFAULT_MODEL).read_text(encoding='utf-8')) if ranked else {}
        if corpus_path is None:
            corpus_file = config.get('corpus_file', 'corpus.jsonl')
            if corpus_file not in ('corpus.jsonl', 'corpus_source_v1.jsonl'):
                raise ValueError('Unknown retrieval corpus artifact.')
            corpus_path = HERE / corpus_file
        self.docs = [json.loads(l) for l in Path(corpus_path).read_text(encoding="utf-8").splitlines() if l.strip()]
        self.by_id = {d["id"]: d for d in self.docs}
        self.by_asp = {a: d for d in self.docs for a in d.get("asp", [])}
        self.by_rule = {r: d for d in self.docs for r in d.get("rules", [])}
        self.bm25 = BM25([tach_tu(d["text"]) for d in self.docs])
        hybrid = config.get('kind') == 'hybrid_feature_reranker'
        if hybrid and config.get('lexical_model') != 'retrieval_model_v4.json':
            raise ValueError('Unknown lexical model dependency.')
        lexical_path = HERE / config['lexical_model'] if hybrid else model_path
        self.ranker = RetrievalRanker(self.docs, self.bm25, lexical_path) if ranked else None
        if hybrid:
            if canonical_hash(json.loads(lexical_path.read_text(encoding='utf-8'))) != config['lexical_model_sha256']:
                raise ValueError('Hybrid lexical dependency changed.')
            from semantic_retrieval import HybridRanker
            self.ranker = HybridRanker(self.ranker, self.docs, config)

    def search(self, q, k=5, loai=None, van_ban=None):
        """Original source passages and ranking scores; scores are not confidence."""
        sc = self.ranker.scores(q) if self.ranker else self.bm25.scores(tach_tu(q))
        explicit_documents = requested_decisions(q)
        explicit_articles = requested_articles(q)
        codes = set(re.findall(r'\b[A-Z]{2}\d{3}E?\b', q.upper()))
        curriculum_query = bool(codes) and bool(re.search(
            r'tien quyet|song hanh|hoc truoc|tin chi|thong tin (?:mon|hoc phan)',
            bo_dau(q.lower())))
        idx = [i for i in sorted(range(len(self.docs)), key=lambda i: -sc[i])
               if sc[i] > 0 and (loai is None or self.docs[i]["loai"] == loai)
               and (van_ban is None or self.docs[i]["van_ban"] == van_ban)
               and (not self.ranker or not explicit_documents or decision_number(self.docs[i]['van_ban']) in explicit_documents)
               and (not self.ranker or not explicit_articles or str(self.docs[i].get('dieu')) in explicit_articles)
               and (not self.ranker or not curriculum_query or self.docs[i].get('ma_hp') in codes)]
        return [(self.docs[i], sc[i]) for i in idx[:k]]

    # ---------- grounding ----------
    def ground_rule(self, asp_id):
        return self.by_asp.get(asp_id)

    def ground_certificate(self, cert):
        """Gắn passage nguồn vào từng bước chứng minh. Bước nào có rule_id mà không có passage →
        ghi vào 'khong_nguon' (không được im lặng bỏ qua)."""
        nguon, khong_nguon = [], []
        for s in cert["proof"]["steps"]:
            # A certificate may be grounded again after the source index changes.
            for derived in ('passage_id', 'dia_chi', 'trang'):
                s.pop(derived, None)
            p = self.ground_rule(s["rule_id"])
            expected = s.get('source') or {}
            if (p is None or self.by_id.get(p['id']) != p or s['rule_id'] not in p.get('asp', [])
                    or any(expected.get(field) is not None and str(expected[field]) != str(p.get(field))
                           for field in ('van_ban', 'dieu', 'khoan'))):
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
            p = source_documents().get(pid, p)
            out.append({"passage_id": pid, "dia_chi": p["dia_chi"], "trang": p["trang"],
                        "trich": p["text"][:300]})
        return out


def kiem_trich_dan(cert, cited_ids):
    """Hậu kiểm grounding: trích một passage KHÔNG nằm trong nguồn của certificate → chặn.
    Trả về (ok, danh sách passage trích sai)."""
    hop_le = set(cert.get("grounding", {}).get("passages", []))
    sai = list(cert.get('grounding', {}).get('khong_nguon', []))
    for step in cert.get('proof', {}).get('steps', []):
        if not step.get('passage_id') or step['passage_id'] not in hop_le:
            sai.append(step.get('rule_id') or 'proof_step_without_source')
    sai.extend(c for c in cited_ids if c not in hop_le)
    sai = list(dict.fromkeys(sai))
    return (not sai), sai


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "sinh viên được đăng ký tối đa bao nhiêu tín chỉ"
    r = Retriever()
    for p, s in r.search(q, k=5):
        print(f"{s:7.2f}  {p['id']:<24} {p['text'][:110]}")
