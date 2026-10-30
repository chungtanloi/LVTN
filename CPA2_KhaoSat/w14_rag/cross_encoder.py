"""CPU ONNX cross-encoder; pinned weights, no runtime HTTP or remote Python."""
import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path

import numpy as np

from retriever import HERE, BM25, tach_tu, eligible_indices, source_documents, source_excerpt, resolve_source_passage, canonical_hash


class CrossEncoder:
    def __init__(self, directory=None):
        import onnxruntime as ort
        import sentencepiece as spm
        directory = Path(directory or os.environ.get('CPA2_CROSS_ENCODER_DIR', HERE / 'cross_encoder_assets'))
        manifest = json.loads((HERE / 'cross_encoder_assets_v1.json').read_text(encoding='utf-8'))
        for asset in manifest['files']:
            digest = hashlib.sha256()
            with (directory / asset['name']).open('rb') as stream:
                while block := stream.read(1024 * 1024):
                    digest.update(block)
            if digest.hexdigest() != asset['sha256']:
                raise ValueError('Cross-encoder asset checksum mismatch.')
        optimized = Path(os.environ.get('CPA2_CROSS_ENCODER_CACHE', '/tmp/cpa2-cross-encoder'))
        model = directory / 'model.onnx'
        if (optimized / 'metadata.json').exists():
            metadata = json.loads((optimized / 'metadata.json').read_text(encoding='utf-8'))
            candidate = optimized / 'model.onnx'
            if (metadata['original_sha256'] != manifest['files'][0]['sha256']
                    or metadata['onnxruntime'] != ort.__version__
                    or hashlib.sha256(candidate.read_bytes()).hexdigest() != metadata['optimized_sha256']):
                raise ValueError('Optimized cross-encoder cache differs from pinned model.')
            model = candidate
        options = ort.SessionOptions()
        options.intra_op_num_threads = 2
        options.inter_op_num_threads = 1
        options.enable_cpu_mem_arena = False
        options.enable_mem_pattern = False
        options.graph_optimization_level = (ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            if os.environ.get('CPA2_CE_OPTIMIZE', 'all') == 'all' else ort.GraphOptimizationLevel.ORT_ENABLE_BASIC)
        if model.parent == optimized:
            options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_DISABLE_ALL
        self.session = ort.InferenceSession(str(model), sess_options=options, providers=['CPUExecutionProvider'])
        self.tokens = spm.SentencePieceProcessor(model_file=str(directory / 'sentencepiece.bpe.model'))

    def score(self, question, texts, batch_size=2):
        # XLM-R paired format: <s> question </s></s> passage </s>.
        query = [3 if i == 0 else i + 1 for i in self.tokens.encode(question)[:96]]
        rows = [[0] + query + [2, 2] + [3 if i == 0 else i + 1 for i in self.tokens.encode(text)[:508-len(query)]] + [2]
                for text in texts]
        scores = []
        for start in range(0, len(rows), batch_size):
            part = rows[start:start + batch_size]
            width = max(map(len, part))
            ids = np.asarray([row + [1] * (width - len(row)) for row in part], dtype=np.int64)
            mask = np.asarray([[1] * len(row) + [0] * (width - len(row)) for row in part], dtype=np.int64)
            inputs = {'input_ids': ids, 'attention_mask': mask}
            if any(i.name == 'token_type_ids' for i in self.session.get_inputs()):
                inputs['token_type_ids'] = np.zeros_like(ids)
            logits = self.session.run(None, inputs)[0]
            if not np.isfinite(logits).all():
                raise ValueError('Cross-encoder produced invalid ranking values.')
            scores.extend(float(value) for value in logits.reshape(-1))
        return scores


class CrossRetriever:
    def __init__(self, base, encoder=None, config=None):
        self.base = base
        self.encoder = encoder
        self.docs = list(source_documents().values())
        self.by_id = {d['id']: d for d in self.docs}
        self.clean = BM25([tach_tu(d['text']) for d in self.docs])
        self.config = config or {'candidate_limit': 20, 'cross_weight': .5}
        if not 1 <= self.config['candidate_limit'] <= 40 or not 0 <= self.config['cross_weight'] <= 1:
            raise ValueError('Invalid cross-encoder search configuration.')
        if 'assets_sha256' in self.config:
            manifest = json.loads((HERE / 'cross_encoder_assets_v1.json').read_text(encoding='utf-8'))
            if canonical_hash(manifest) != self.config['assets_sha256']:
                raise ValueError('Cross-encoder manifest differs from frozen release.')
            if canonical_hash(self.docs) != self.config['source_corpus_sha256']:
                raise ValueError('Cross-encoder source corpus differs from frozen release.')
            bindings = json.loads((HERE / 'source_bindings_v1.json').read_text(encoding='utf-8'))
            if canonical_hash(bindings) != self.config['source_bindings_sha256']:
                raise ValueError('Cross-encoder source bindings differ from frozen release.')

    def lexical_scores(self, question):
        values = {}
        for doc, score in self.base.search(question, k=len(self.base.docs)):
            pid = resolve_source_passage(doc, question)['id']
            values[pid] = max(values.get(pid, 0), score)
        return values

    def candidates(self, question, limit=None):
        limit = limit or self.config['candidate_limit']
        values = self.lexical_scores(question)
        legacy = set(sorted(values, key=lambda pid: -values[pid])[:limit])
        clean = self.clean.scores(tach_tu(question))
        eligible = eligible_indices(self.docs, question)
        clean_top = sorted((i for i in eligible if clean[i] > 0), key=lambda i: (-clean[i], i))[:limit]
        chosen = legacy | {self.docs[i]['id'] for i in clean_top}
        return [self.docs[i] for i in eligible if self.docs[i]['id'] in chosen]

    def scored(self, question):
        docs = self.candidates(question)
        if not docs:
            return []
        if len(docs) == 1:
            return [(docs[0], 1.0)]
        if self.encoder is None:
            self.encoder = CrossEncoder()
        # A query-aware original-text window preserves clauses at the end of a
        # long passage, without generating or modifying the source wording.
        texts = [source_excerpt(question, d, limit=1500)[0] for d in docs]
        scores = self.encoder.score(question, texts)
        low, high = min(scores), max(scores)
        lexical = self.lexical_scores(question)
        maximum = max(lexical.values(), default=1) or 1
        alpha = self.config['cross_weight']
        fused = [alpha * ((s-low)/(high-low) if high > low else 0)
                 + (1-alpha) * lexical.get(d['id'], 0)/maximum for d, s in zip(docs, scores)]
        return sorted(zip(docs, fused), key=lambda row: (-row[1], row[0]['id']))

    def search(self, question, k=5, **filters):
        return [(d, s) for d, s in self.scored(question)
                if (filters.get('loai') is None or d['loai'] == filters['loai'])
                and (filters.get('van_ban') is None or d['van_ban'] == filters['van_ban'])][:k]


@lru_cache(maxsize=1)
def production_search():
    from retriever import Retriever
    config = json.loads((HERE / 'retrieval_release_v6.json').read_text(encoding='utf-8'))
    return CrossRetriever(Retriever(model_path=HERE / 'retrieval_model_v3.json'), config=config)
