"""Pinned E5 ONNX retrieval, CPU only, with no query-time network calls.

SentencePiece uses XLM-R's public vocabulary offset (+1, unknown=3,
start=0/end=2/padding=1). Prefixes and masked mean pooling follow the E5 card.
The offline index is bound to the entire clean corpus and model file hashes.
"""
import hashlib
import json
import os
from pathlib import Path

import numpy as np

from retriever import HERE, canonical_hash, unit_scores

REVISION = '614241f622f53c4eeff9890bdc4f31cfecc418b3'
MODEL_SHA = 'dd476dd0c2514e9b9be83aeb3853fac0763e0bdf4a71645407587d77c48a2d88'


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


class Encoder:
    def __init__(self, directory=None):
        import onnxruntime as ort
        import sentencepiece as spm
        directory = Path(directory or os.environ.get('CPA2_SEMANTIC_MODEL_DIR', HERE / 'semantic_assets'))
        manifest = json.loads((HERE / 'semantic_assets_v1.json').read_text(encoding='utf-8'))
        for asset in manifest['files']:
            if file_hash(directory / asset['name']) != asset['sha256']:
                raise ValueError('Semantic asset checksum differs from pinned manifest.')
        options = ort.SessionOptions()
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        options.enable_cpu_mem_arena = False
        options.enable_mem_pattern = False
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_BASIC
        self.session = ort.InferenceSession(str(directory / 'model.onnx'), sess_options=options, providers=['CPUExecutionProvider'])
        self.tokens = spm.SentencePieceProcessor(model_file=str(directory / 'sentencepiece.bpe.model'))

    def encode(self, texts, prefix, batch_size=4):
        results = []
        for start in range(0, len(texts), batch_size):
            rows = [[0] + [3 if token == 0 else token + 1 for token in self.tokens.encode(prefix + text)[:254]] + [2]
                    for text in texts[start:start + batch_size]]
            width = max(map(len, rows))
            ids = np.array([row + [1] * (width - len(row)) for row in rows], dtype=np.int64)
            mask = np.array([[1] * len(row) + [0] * (width - len(row)) for row in rows], dtype=np.int64)
            hidden = self.session.run(None, {'input_ids': ids, 'attention_mask': mask, 'token_type_ids': np.zeros_like(ids)})[0]
            vectors = (hidden * mask[:, :, None]).sum(axis=1) / mask.sum(axis=1)[:, None]
            vectors /= np.maximum(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-12)
            results.append(vectors.astype(np.float32))
        return np.concatenate(results)


def chunks(docs):
    texts, owners = [], []
    for i, doc in enumerate(docs):
        words = doc['text'].split()
        for start in range(0, len(words), 48):
            texts.append(' '.join(words[start:start + 72]))
            owners.append(i)
            if start + 72 >= len(words):
                break
    return texts, owners


class SemanticIndex:
    def __init__(self, docs, encoder=None):
        metadata = json.loads((HERE / 'semantic_index_v1.json').read_text(encoding='utf-8'))
        if metadata['corpus_sha256'] != canonical_hash(sorted(docs, key=lambda doc: doc['id'])):
            raise ValueError('Semantic index is stale for this source corpus.')
        path = HERE / 'semantic_index_v1.npz'
        if file_hash(path) != metadata['index_sha256']:
            raise ValueError('Semantic index checksum mismatch.')
        with np.load(path, allow_pickle=False) as data:
            self.vectors = data['vectors']
            self.owners = data['owners']
        self.docs = docs
        if self.vectors.ndim != 2 or self.vectors.shape[1] != 384 or len(self.owners) != len(self.vectors):
            raise ValueError('Invalid semantic index dimensions.')
        self.encoder = encoder or Encoder()

    def scores(self, question):
        vector = self.encoder.encode([question], 'query: ')[0]
        values = self.vectors @ vector
        scores = np.full(len(self.docs), -1.0)
        np.maximum.at(scores, self.owners, values)
        return scores.tolist()


class HybridRanker:
    def __init__(self, lexical, docs, config):
        import math
        self.lexical, self.docs, self.config = lexical, docs, config
        expected = list(lexical.FEATURE_NAMES) + ['dense_similarity', 'reciprocal_rank_fusion']
        if config['features'] != expected or len(config['weights']) != len(expected):
            raise ValueError('Invalid hybrid feature configuration.')
        if any(not isinstance(w, (float, int)) or not math.isfinite(w) or w < 0 for w in config['weights']):
            raise ValueError('Invalid hybrid weights.')
        for name, field in [('semantic_index_v1.json', 'semantic_index_sha256'), ('semantic_assets_v1.json', 'semantic_assets_sha256')]:
            if canonical_hash(json.loads((HERE / name).read_text(encoding='utf-8'))) != config[field]:
                raise ValueError('Hybrid model dependencies changed.')
        self.index = SemanticIndex(docs)

    def scores(self, question):
        from retriever import eligible_indices, tach_tu
        evidence = self.lexical.legacy.scores(tach_tu(question))
        eligible = [i for i in eligible_indices(self.docs, question) if evidence[i] > 0]
        if not eligible:
            return [0.0] * len(self.docs)
        features, candidates = hybrid_features(self.lexical.features(question), self.index.scores(question), self.lexical.weights, eligible)
        return [sum(w * f for w, f in zip(self.config['weights'], row)) if i in candidates else 0.0
                for i, row in enumerate(features)]


def hybrid_features(lexical_features, semantic_scores, lexical_weights, eligible):
    """Retrieve top 30 from each channel, then rerank 15 source features.

    The last two features are normalized dense similarity and reciprocal-rank
    fusion. The reranker is a small learned linear model, not a cross-encoder.
    """
    lexical_scores = [sum(w * f for w, f in zip(lexical_weights, row)) for row in lexical_features]
    ordered_lex = sorted(eligible, key=lambda i: (-lexical_scores[i], i))
    ordered_dense = sorted(eligible, key=lambda i: (-semantic_scores[i], i))
    candidates = set(ordered_lex[:30]) | set(ordered_dense[:30])
    rrf = [0.0] * len(lexical_scores)
    for ordered in (ordered_lex, ordered_dense):
        for rank, index in enumerate(ordered, 1):
            rrf[index] += 1 / (60 + rank)
    low = min((semantic_scores[i] for i in eligible), default=0)
    high = max((semantic_scores[i] for i in eligible), default=0)
    dense = [(value - low) / max(high - low, 1e-12) for value in semantic_scores]
    rrf = unit_scores(rrf)
    return [list(row) + [dense[i], rrf[i]] for i, row in enumerate(lexical_features)], candidates
