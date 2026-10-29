"""Select lexical weights on DEV and leave-group-out TRAIN, never test labels.

All examples from the query's survey respondent group are removed from its
example features. This prevents paraphrases from the same respondent acting as
their own retrieval labels. Every respondent contributes equally to selection.
Runtime needs no NumPy. An existing model output is never overwritten.
"""
import argparse
import json
import tempfile
from pathlib import Path

import numpy as np

from retriever import HERE, Retriever, canonical_hash


def train(output, reviewed=False):
    if output.exists():
        raise ValueError('Refusing to overwrite a model artifact.')
    examples_file = 'rag_survey_train_sources_v2.json' if reviewed else 'rag_survey_train_sources_v1.json'
    training = json.loads((HERE / examples_file).read_text(encoding='utf-8'))
    config = json.loads((HERE / 'retrieval_model_v1.json').read_text(encoding='utf-8'))
    if reviewed:
        config.update(examples_file=examples_file, examples_sha256=canonical_hash(training))
    with tempfile.TemporaryDirectory(prefix='cpa2-retrieval-seed-') as directory:
        seed = Path(directory) / 'seed.json'
        seed.write_text(json.dumps(config), encoding='utf-8')
        engine = Retriever(model_path=seed)
    dev = [q for q in json.loads((HERE / 'rag_queries.json').read_text(encoding='utf-8'))['queries'] if q['split'] == 'dev']
    queries = [q for q in training['queries'] if q['gold']]
    features = np.asarray([engine.ranker.features(q['q'], excluded_group=q['group']) for q in queries]
                              + [engine.ranker.features(q['q']) for q in dev])
    labels = np.asarray([[d['id'] in q['gold'] for d in engine.docs] for q in queries + dev])
    groups = sorted({q['group'] for q in queries})
    query_weights = np.array([1 / len(groups) / sum(r['group'] == q['group'] for r in queries) for q in queries])
    rng = np.random.default_rng(29)
    best = None
    # Predeclared selection: satisfy original DEV gates, then maximize group-
    # macro reciprocal rank and recall@5; DEV MRR is only a final tie breaker.
    for batch in range(20):
        weights = rng.dirichlet(np.full(features.shape[-1], .5), size=500)
        if batch == 0:
            weights[0] = engine.ranker.weights
        scores = np.einsum('qdf,wf->wqd', features, weights)
        relevant = np.where(labels[None, :, :], scores, -np.inf).max(axis=2)
        ranks = 1 + (scores > relevant[:, :, None]).sum(axis=2)
        # Stable corpus ordering also resolves a tie with a relevant passage.
        first_gold = np.where(labels[None, :, :] & (scores == relevant[:, :, None]), np.arange(len(engine.docs)), len(engine.docs)).min(axis=2)
        ranks += ((scores == relevant[:, :, None]) & (np.arange(len(engine.docs)) < first_gold[:, :, None])).sum(axis=2)
        group_mrr = (1 / ranks[:, :len(queries)] * query_weights).sum(axis=1)
        group_r5 = ((ranks[:, :len(queries)] <= 5) * query_weights).sum(axis=1)
        dev_ranks = ranks[:, len(queries):]
        for i in range(len(weights)):
            d1, d5 = int((dev_ranks[i] == 1).sum()), int((dev_ranks[i] <= 5).sum())
            key = (d1 / len(dev) >= .8 and d5 / len(dev) >= .95,
                   float(group_mrr[i]), float(group_r5[i]), float((1 / dev_ranks[i]).mean()))
            if best is None or key > best[0]:
                best = (key, weights[i].tolist(), d1, d5)
    config.update(version=3 if reviewed else 2, weights=best[1], selection_split='dev_and_train_leave_group_out',
                  holdout_used_for_selection=False, seed=29, selection_trials=10000,
                  dev_n=len(dev), dev_hits_at_1=best[2], dev_hits_at_5=best[3],
                  train_queries=len(queries), train_groups=len(groups),
                  group_macro_mrr=best[0][1], group_macro_recall_at_5=best[0][2],
                  selection_objective='DEV gates, group-macro TRAIN MRR, group-macro TRAIN R@5, DEV MRR',
                  self_group_examples_excluded=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        json.dump(config, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({**config, 'model_sha256': canonical_hash(config)}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reviewed', action='store_true', help='Use source corrections from the existing human review.')
    args = parser.parse_args()
    train(args.output, args.reviewed)
