"""Evaluate the actual lookup response, including clean source binding and clarification."""
import argparse
import datetime
import json
from pathlib import Path

from grounded_answer import lookup_response
from retriever import HERE, DEFAULT_MODEL, canonical_hash


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError('Refusing to overwrite an evaluation report.')
    dataset = json.loads((HERE / 'rag_source_checks_v1.json').read_text(encoding='utf-8'))
    rows = []
    for q in dataset['queries']:
        response = lookup_response(q['q'])
        ids = [p['passage_id'] for p in response['passages']]
        rank = next((i + 1 for i, pid in enumerate(ids) if pid in q.get('gold', [])), None)
        passed = bool(response.get('clarification')) if q.get('expected') == 'clarification' else (
            not ids and not response.get('clarification') if q.get('expected') == 'empty' else rank is not None)
        rows.append({'id': q['id'], 'returned': ids, 'first_relevant_rank': rank, 'passed': passed})
    result = {'meta': {'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                       'dataset_sha256': canonical_hash(dataset), 'model_sha256': canonical_hash(json.loads(DEFAULT_MODEL.read_text(encoding='utf-8'))),
                       'scope': dataset['meta'], 'not_acceptance_benchmark': True},
              'passed': sum(row['passed'] for row in rows), 'n': len(rows),
              'positive_n': sum(bool(q.get('gold')) for q in dataset['queries']),
              'positive_hits_at_1': sum(row['first_relevant_rank'] == 1 for row in rows), 'rows': rows}
    with args.report.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, ensure_ascii=False, indent=2))
