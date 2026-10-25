"""Prepare explicitly synthetic survey data; train an offline intent baseline.

No student profiles, no solver labels, no external API. Holdout questions are
never used by training/tuning. This model is an experiment, not an academic
decision-maker and is not automatically installed in the production parser.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from nhap_qreal import an_danh, chuan, khoa_trung


def prepare(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    accepted = [r for r in rows if chuan(r.get('dong_y')).casefold() in ('tôi đồng ý', 'đồng ý')]
    if any('synthetic' not in r.get('nguon', '').casefold() for r in accepted):
        raise ValueError('This importer accepts explicitly SYNTHETIC data only; use the consent/anonymization Q-Real pipeline for real responses.')
    parent = list(range(len(accepted)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    records, seen = [], {}
    for i, row in enumerate(accepted):
        for n in range(1, 5):
            question = an_danh(chuan(row.get(f'cau_hoi_{n}')))
            if not question:
                continue
            label = chuan(row.get(f'cau_hoi_{n}_intent'))
            if not label:
                raise ValueError('Question has no preassigned intent label.')
            key = khoa_trung(question)
            if key in seen:
                previous = seen[key]
                if records[previous]['intent'] != label:
                    raise ValueError('Duplicate question has conflicting labels; manual review required.')
                parent[find(i)] = find(records[previous]['row'])
            else:
                seen[key] = len(records)
            records.append({'question': question, 'intent': label,
                            'style': chuan(row.get(f'cau_hoi_{n}_kieu')), 'row': i, 'key': key})
    groups = defaultdict(list)
    for i, row in enumerate(accepted):
        groups[find(i)].append(chuan(row.get('id')) or str(i))
    group_ids = {i: hashlib.sha256('|'.join(sorted(ids)).encode()).hexdigest()[:16] for i, ids in groups.items()}
    output, emitted = [], set()
    for r in records:
        if r['key'] in emitted:
            continue
        emitted.add(r['key'])
        group = group_ids[find(r['row'])]
        bucket = int(group, 16) % 10
        split = 'train' if bucket < 6 else ('dev' if bucket < 8 else 'test')
        output.append({'id': 'QS-' + hashlib.sha256(r['key'].encode()).hexdigest()[:12],
                       'question': r['question'], 'intent': r['intent'], 'style': r['style'],
                       'group': group, 'split': split, 'source': 'synthetic_survey'})
    return output, {'raw_rows': len(rows), 'consenting_rows': len(accepted),
                    'raw_questions': len(records), 'unique_questions': len(output),
                    'counts': dict(Counter(r['split'] for r in output)),
                    'source_sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                    'real_question_count': 0}


def tokens(text):
    import unicodedata
    text = unicodedata.normalize('NFD', text.casefold().replace('đ', 'd'))
    words = re.findall(r'\w+', ''.join(c for c in text if unicodedata.category(c) != 'Mn'))
    return words + ['_'.join(pair) for pair in zip(words, words[1:])]


def fit(records, alpha=1.0):
    docs, counts = Counter(), defaultdict(Counter)
    for r in records:
        docs[r['intent']] += 1
        counts[r['intent']].update(tokens(r['question']))
    return {'alpha': alpha, 'documents': dict(docs), 'counts': {k: dict(v) for k, v in counts.items()},
            'vocabulary': sorted({t for v in counts.values() for t in v})}


def predict(model, question):
    query = Counter(tokens(question))
    vocab = set(model['vocabulary'])
    alpha = model['alpha']
    scores = {}
    for label, count in model['documents'].items():
        frequencies = model['counts'][label]
        denominator = sum(frequencies.values()) + alpha * len(vocab)
        scores[label] = math.log(count / sum(model['documents'].values())) + sum(
            n * math.log((frequencies.get(t, 0) + alpha) / denominator) for t, n in query.items() if t in vocab)
    return max(scores, key=scores.get)


def train(records):
    training = [r for r in records if r['split'] == 'train']
    dev = [r for r in records if r['split'] == 'dev']
    if not training or not dev:
        raise ValueError('Need nonempty train and dev groups.')
    candidates = []
    for alpha in (0.1, 0.5, 1.0, 2.0):
        model = fit(training, alpha)
        correct = sum(predict(model, r['question']) == r['intent'] for r in dev)
        candidates.append((correct, alpha, model))
    correct, alpha, model = max(candidates, key=lambda c: (c[0], -c[1]))
    model['meta'] = {'kind': 'offline_synthetic_intent_baseline', 'production_enabled': False,
                     'train_n': len(training), 'dev_n': len(dev), 'dev_correct': correct,
                     'dev_accuracy': correct / len(dev), 'alpha_selected_on': 'dev',
                     'test_evaluated': False, 'training_ids': sorted(r['id'] for r in training),
                     'tuning_ids': sorted(r['id'] for r in dev)}
    return model


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=HERE / 'qreal/synthetic_survey')
    args = parser.parse_args()
    records, meta = prepare(args.input)
    model = train(records)
    model['meta']['source_sha256'] = meta['source_sha256']
    args.output.mkdir(parents=True, exist_ok=True)
    for split in ('train', 'dev', 'test'):
        (args.output / (split + '.jsonl')).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in records if r['split'] == split), encoding='utf-8')
    (args.output / 'manifest.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (args.output / 'intent_model.json').write_text(json.dumps(model, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'dataset': meta, 'training': {k: v for k, v in model['meta'].items() if not k.endswith('_ids')}}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
