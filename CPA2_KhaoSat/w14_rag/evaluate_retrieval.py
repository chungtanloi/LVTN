"""Report frozen retrieval models. No training or parameter selection occurs here."""
import argparse
import datetime
import json
from pathlib import Path

from retriever import Retriever, canonical_hash

HERE = Path(__file__).parent


def evaluate(retriever, queries, corrections=None):
    rows = []
    for query in queries:
        gold = (corrections or {}).get(query['id'], query['gold'])
        ids = [doc['id'] for doc, _ in retriever.search(query['q'], k=10)]
        rank = next((i + 1 for i, pid in enumerate(ids) if pid in gold), None)
        rows.append({'id': query['id'], 'gold': gold, 'returned': ids,
                     'first_relevant_rank': rank, 'hit_at_1': rank == 1,
                     'hit_at_5': rank is not None and rank <= 5})
    n = len(rows)
    if not n:
        raise ValueError('The requested evaluation split is empty.')
    return {'n': n, 'hits_at_1': sum(row['hit_at_1'] for row in rows),
            'hits_at_5': sum(row['hit_at_5'] for row in rows),
            'recall_at_1': sum(row['hit_at_1'] for row in rows) / n,
            'recall_at_5': sum(row['hit_at_5'] for row in rows) / n,
            'mrr': sum(1 / row['first_relevant_rank'] if row['first_relevant_rank'] else 0 for row in rows) / n,
            'rows': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', choices=['original', 'survey-holdout'], default='original')
    parser.add_argument('--split', choices=['dev', 'test'], default='dev')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError('Refusing to overwrite an evaluation report.')
    path = HERE / ('rag_queries.json' if args.dataset == 'original' else 'rag_survey_holdout_v1.json')
    dataset = json.loads(path.read_text(encoding='utf-8'))
    queries = [q for q in dataset['queries'] if q['split'] == args.split]
    corrections = {}
    errata = None
    if args.dataset == 'survey-holdout':
        errata = json.loads((HERE / 'rag_survey_holdout_errata_v1.json').read_text(encoding='utf-8'))
        corrections = {q['id']: q['corrected_gold'] for q in errata['changes']}
    config = json.loads((HERE / 'retrieval_model_v1.json').read_text(encoding='utf-8'))
    result = {'meta': {'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                       'dataset': args.dataset, 'split': args.split,
                       'dataset_sha256': canonical_hash(dataset), 'model_sha256': canonical_hash(config),
                       'errata_sha256': canonical_hash(errata) if errata else None,
                       'previously_seen_diagnostic': args.dataset == 'original' and args.split == 'test',
                       'synthetic': True,
                       'data_origin': 'synthetic_survey' if args.dataset == 'survey-holdout' else 'handcrafted_rag_queries',
                       'gold_annotators': 1,
                       'measurement': 'Relevant source retrieval, not answer accuracy or academic soundness.'}}
    for name, enabled in (('legacy_bm25', False), ('ranked', True)):
        retriever = Retriever(ranked=enabled)
        result[name] = evaluate(retriever, queries, corrections)
        if corrections:
            result[name + '_original_gold'] = evaluate(retriever, queries)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open('x', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps({'meta': result['meta'], **{k: {name: value for name, value in v.items() if name != 'rows'} for k, v in result.items() if k != 'meta'}}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
