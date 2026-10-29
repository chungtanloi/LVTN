"""Train the lightweight hybrid reranker on DEV + group-excluded TRAIN only."""
import argparse
import json
from pathlib import Path

import numpy as np

from retriever import HERE, Retriever, canonical_hash
from semantic_retrieval import Encoder, SemanticIndex, hybrid_features


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Refusing to overwrite a trained model.')
    engine = Retriever(model_path=HERE / 'retrieval_model_v4.json')
    training = json.loads((HERE / 'rag_survey_train_sources_v2.json').read_text(encoding='utf-8'))
    train = [q for q in training['queries'] if q['gold']]
    dev = [q for q in json.loads((HERE / 'rag_queries.json').read_text(encoding='utf-8'))['queries'] if q['split'] == 'dev']
    index = SemanticIndex(engine.docs, Encoder(args.assets))
    weights = engine.ranker.weights
    matrices, masks = [], []
    id_to_index = {d['id']: i for i, d in enumerate(engine.docs)}
    for q in train + dev:
        features = engine.ranker.features(q['q'], excluded_group=q.get('group'))
        eligible = [id_to_index[d['id']] for d, _ in engine.search(q['q'], k=len(engine.docs))]
        rows, candidates = hybrid_features(features, index.scores(q['q']), weights, eligible)
        matrices.append(rows)
        masks.append([i in candidates for i in range(len(engine.docs))])
    features = np.asarray(matrices)
    candidates = np.asarray(masks)
    gold = np.asarray([[d['id'] in q['gold'] for d in engine.docs] for q in train + dev])
    groups = sorted({q['group'] for q in train})
    macro = np.array([1 / len(groups) / sum(r['group'] == q['group'] for r in train) for q in train])
    rng, best = np.random.default_rng(30), None
    for batch in range(20):
        choices = rng.dirichlet(np.full(features.shape[-1], .5), size=500)
        if batch == 0:
            choices[0] = weights + [0, 0]
        scores = np.einsum('qdf,wf->wqd', features, choices)
        scores = np.where(candidates[None, :, :], scores, -np.inf)
        relevant = np.where(gold[None, :, :], scores, -np.inf).max(axis=2)
        ranks = 1 + (scores > relevant[:, :, None]).sum(axis=2)
        first = np.where(gold[None, :, :] & (scores == relevant[:, :, None]), np.arange(len(engine.docs)), len(engine.docs)).min(axis=2)
        ranks += ((scores == relevant[:, :, None]) & (np.arange(len(engine.docs)) < first[:, :, None])).sum(axis=2)
        ranks = np.where(np.isfinite(relevant), ranks, np.inf)
        mrr = (1 / ranks[:, :len(train)] * macro).sum(axis=1)
        recall5 = ((ranks[:, :len(train)] <= 5) * macro).sum(axis=1)
        for i in range(len(choices)):
            d1 = int((ranks[i, len(train):] == 1).sum())
            d5 = int((ranks[i, len(train):] <= 5).sum())
            key = (d1 / len(dev) >= .8 and d5 / len(dev) >= .95, float(mrr[i]), float(recall5[i]), float((1 / ranks[i, len(train):]).mean()))
            if best is None or key > best[0]:
                best = (key, choices[i].tolist(), d1, d5)
    config = {
        'version': 5, 'kind': 'hybrid_feature_reranker', 'corpus_file': 'corpus_source_v1.jsonl',
        'lexical_model': 'retrieval_model_v4.json',
        'lexical_model_sha256': canonical_hash(json.loads((HERE / 'retrieval_model_v4.json').read_text(encoding='utf-8'))),
        'corpus_sha256': canonical_hash(sorted(engine.docs, key=lambda d: d['id'])),
        'features': list(engine.ranker.FEATURE_NAMES) + ['dense_similarity', 'reciprocal_rank_fusion'],
        'weights': best[1], 'candidate_count_per_channel': 30,
        'selection_split': 'dev_and_train_leave_group_out', 'self_group_examples_excluded': True,
        'holdout_used_for_selection': False, 'seed': 30, 'selection_trials': 10000,
        'dev_n': len(dev), 'dev_hits_at_1': best[2], 'dev_hits_at_5': best[3],
        'dev_gates_met': bool(best[0][0]), 'group_macro_mrr': best[0][1], 'group_macro_recall_at_5': best[0][2],
        'train_queries': len(train), 'train_groups': len(groups),
        'semantic_index_sha256': canonical_hash(json.loads((HERE / 'semantic_index_v1.json').read_text(encoding='utf-8'))),
        'semantic_assets_sha256': canonical_hash(json.loads((HERE / 'semantic_assets_v1.json').read_text(encoding='utf-8'))),
    }
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(config, stream, indent=2)
        stream.write('\n')
    print(json.dumps(config, indent=2))
