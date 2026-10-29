"""Apply the existing human source review to TRAIN only; leave old artifacts intact."""
import argparse
import copy
import json
from pathlib import Path

from retriever import HERE, canonical_hash


def build():
    base = json.loads((HERE / 'rag_survey_train_sources_v1.json').read_text(encoding='utf-8'))
    errata = json.loads((HERE / 'rag_soat_gold_errata_v1.json').read_text(encoding='utf-8'))
    revised = copy.deepcopy(base)
    changes = {row['id']: row for row in errata['changes'] if row['split'] == 'train'}
    count = 0
    for row in revised['queries']:
        if row['split'] != 'train':
            raise ValueError('Only TRAIN source examples may be updated.')
        if row['id'] in changes:
            change = changes[row['id']]
            if row['gold'] != change['original_gold']:
                raise ValueError('Review does not match the frozen original labels.')
            row['original_gold'] = row['gold']
            row['gold'] = change['corrected_gold'] or []
            row['source_review_status'] = change['loai']
            count += 1
    if count != len(changes):
        raise ValueError('Some reviewed TRAIN examples could not be matched.')
    revised['source_review'] = {
        'errata_file': 'rag_soat_gold_errata_v1.json', 'errata_sha256': canonical_hash(errata),
        'applied_train_rows': count,
        'policy': 'Apply existing TRAIN source corrections only. Unknown/unmapped sources excluded from positive examples. Original DEV and all TEST labels unchanged. Review is prediction-aware and partial, not independent evaluation.',
    }
    return revised


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build()
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(canonical_hash(result))
