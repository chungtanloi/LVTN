"""Evaluate a frozen cross-encoder candidate; never select or change parameters."""
import argparse
import datetime
import json
from pathlib import Path
import time

from retriever import HERE, Retriever, canonical_hash
from grounded_answer import lookup_response, tra_cuu
from cross_encoder import CrossEncoder, CrossRetriever


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', type=Path, required=True)
    parser.add_argument('--dataset', choices=['dev', 'final', 'diagnostic'], required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--retrieval-only', action='store_true', help='Bypass clarification for positive source-ranking measurement, not for controls.')
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError('Refusing to overwrite an evaluation.')
    config = json.loads((HERE / 'retrieval_release_v6.json').read_text(encoding='utf-8'))
    if args.dataset == 'final':
        dataset = json.loads((HERE / 'rag_acceptance_holdout_v2_20261030.json').read_text(encoding='utf-8'))
        queries = dataset['queries']
    else:
        original = json.loads((HERE / 'rag_queries.json').read_text(encoding='utf-8'))
        queries = [q for q in original['queries'] if q['split'] == ('dev' if args.dataset == 'dev' else 'test')]
        if args.dataset == 'diagnostic':
            survey = json.loads((HERE / 'rag_survey_holdout_v1.json').read_text(encoding='utf-8'))
            errata = json.loads((HERE / 'rag_survey_holdout_errata_v1.json').read_text(encoding='utf-8'))
            corrections = {q['id']: q['corrected_gold'] for q in errata['changes']}
            queries += [{**q, 'gold': corrections.get(q['id'], q['gold'])} for q in survey['queries'] if q['split'] == 'test']
        dataset = {'queries': queries, 'scope': args.dataset}
    start = time.perf_counter()
    engine = CrossRetriever(Retriever(), CrossEncoder(args.assets), config)
    load_sec = time.perf_counter() - start
    rows = []
    for query in queries:
        start = time.perf_counter()
        response = ({'passages': tra_cuu(query['q'], k=5, r=engine)}
                    if args.retrieval_only and query.get('gold') else lookup_response(query['q'], r=engine))
        ids = [p['passage_id'] for p in response['passages']]
        rank = next((i+1 for i, pid in enumerate(ids) if pid in query.get('gold', [])), None)
        expected = query.get('expected')
        control_ok = (bool(response.get('clarification')) if expected == 'clarification' else not ids and not response.get('clarification')) if expected else None
        rows.append({'id': query['id'], 'gold': query.get('gold'), 'expected': expected,
                     'returned': ids, 'first_relevant_rank': rank, 'control_ok': control_ok,
                     'elapsed_sec': time.perf_counter()-start})
        print(query['id'], 'rank', rank, 'control', control_ok, 'sec', round(rows[-1]['elapsed_sec'],2), flush=True)
    n = sum(bool(q.get('gold')) for q in queries)
    h1 = sum(r['first_relevant_rank'] == 1 for r in rows)
    h5 = sum(r['first_relevant_rank'] is not None for r in rows)
    report = {'meta': {'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                       'dataset': args.dataset, 'dataset_sha256': canonical_hash(dataset),
                       'measurement': 'source_retrieval' if args.retrieval_only else 'lookup_pipeline',
                       'configuration_sha256': canonical_hash(config), 'model_load_sec': load_sec,
                       'limitations': 'Synthetic/handcrafted source retrieval; one source annotator, no real student logs or independent human review.'},
              'n': n, 'hits_at_1': h1, 'hits_at_5': h5, 'recall_at_1': h1/n, 'recall_at_5': h5/n,
              'meets_numeric_targets': h1/n >= .8 and h5/n >= .95,
              'controls_n': sum(q.get('expected') is not None for q in queries),
              'controls_passed': sum(r['control_ok'] is True for r in rows), 'rows': rows}
    with args.report.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({k:v for k,v in report.items() if k!='rows'}, ensure_ascii=False, indent=2), flush=True)
