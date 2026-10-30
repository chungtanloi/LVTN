"""Development-only probe. This command never reads any TEST/holdout labels."""
import argparse
import json
import time
from pathlib import Path

from retriever import HERE, Retriever
from cross_encoder import CrossEncoder, CrossRetriever


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError('Refusing to overwrite a probe.')
    engine = CrossRetriever(Retriever(), CrossEncoder(args.assets))
    queries = [q for q in json.loads((HERE / 'rag_queries.json').read_text(encoding='utf-8'))['queries'] if q['split'] == 'dev']
    rows, start = [], time.monotonic()
    for query in queries:
        ranked = engine.scored(query['q'])
        rank = next((i+1 for i, (d, _) in enumerate(ranked) if d['id'] in query['gold']), None)
        rows.append({'id': query['id'], 'q': query['q'], 'gold': query['gold'], 'rank': rank,
                     'ranked': [[d['id'], s] for d, s in ranked]})
        print(query['id'], 'rank', rank, 'top', ranked[0][0]['id'] if ranked else '-', flush=True)
    report = {'scope': 'DEV only', 'n': len(rows), 'hits_at_1': sum(r['rank'] == 1 for r in rows),
              'hits_at_5': sum(r['rank'] is not None and r['rank'] <= 5 for r in rows),
              'elapsed_sec': time.monotonic()-start, 'rows': rows}
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print({k:v for k,v in report.items() if k != 'rows'}, flush=True)
