"""Reproduce the frozen small retrieval model using DEV only.

Source-linked examples must be train-only. NumPy is used offline; production
ranking uses Python's standard library. This command never reads holdout labels
and cannot overwrite an existing output file.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from retriever import Retriever, canonical_hash

HERE = Path(__file__).parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Refusing to overwrite a model artifact.')
    retriever = Retriever(ranked=True)
    queries = [q for q in json.loads((HERE / 'rag_queries.json').read_text(encoding='utf-8'))['queries'] if q['split'] == 'dev']
    features = np.asarray([retriever.ranker.features(q['q']) for q in queries])
    gold = np.asarray([[d['id'] in q['gold'] for d in retriever.docs] for q in queries])
    rng = np.random.default_rng(21)
    best = None
    for _ in range(10):
        weights = rng.dirichlet(np.full(features.shape[-1], .25), size=1000)
        scores = np.einsum('qdf,wf->wqd', features, weights)
        labels = np.broadcast_to(gold, (len(weights), *gold.shape))
        first = np.argmax(scores, axis=2)
        hits1 = np.take_along_axis(labels, first[:, :, None], axis=2).sum(axis=(1, 2))
        top5 = np.argpartition(-scores, 4, axis=2)[:, :, :5]
        hits5 = np.take_along_axis(labels, top5, axis=2).any(axis=2).sum(axis=1)
        i = int(np.argmax(hits1 * 100 + hits5))
        key = (int(hits1[i]), int(hits5[i]))
        if best is None or key > best[0]:
            best = (key, weights[i])
    config = json.loads((HERE / 'retrieval_model_v1.json').read_text(encoding='utf-8'))
    config.update(weights=best[1].tolist(), dev_n=len(queries),
                  dev_hits_at_1=best[0][0], dev_hits_at_5=best[0][1])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps({'dev_hits_at_1': best[0][0], 'dev_hits_at_5': best[0][1],
                      'dev_n': len(queries), 'model_sha256': canonical_hash(config)}, indent=2))


if __name__ == '__main__':
    main()
