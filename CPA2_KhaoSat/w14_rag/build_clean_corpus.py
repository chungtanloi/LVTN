"""Build a source-only retrieval corpus; keep legacy evidence and notes separate."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

import build_corpus as original

HERE = Path(__file__).parent


def build():
    old = [json.loads(line) for line in (HERE / 'corpus.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    raw = {}
    for document, path in original.OCR.items():
        raw.update(original.parse_ocr(document, path))
    for path in original.CHEP_TAY:
        raw.update(original.parse_chep_tay(path))
    corrections = json.loads((HERE / 'source_corrections_v1.json').read_text(encoding='utf-8'))['passages']
    docs, notes = [], []
    for source in old:
        doc = copy.deepcopy(source)
        if doc['loai'] == 'quy_che':
            pid = doc['id']
            if pid in corrections:
                body, quality = corrections[pid]['text'], 'visual_transcription'
                doc['trang'] = corrections[pid]['page']
            elif pid in raw and raw[pid]['ocr']:
                body = raw[pid]['ocr']
                quality = 'existing_transcription' if raw[pid].get('chep_tay') else 'ocr_unreviewed'
            else:
                raise ValueError(f'No original source body for {pid}; do not substitute analyst notes.')
            if doc['van_ban'] == 'qd3266' and doc['dieu'] == 24:
                doc['tieu_de'] = 'Điểm trung bình chung học kỳ, điểm trung bình chung năm học và điểm trung bình chung tích lũy'
            doc['text'] = f"{doc['dia_chi']}. {doc['tieu_de']}. {body}"
            doc['source_quality'] = quality
            doc['source_page'] = doc['trang']
            notes.append({'passage_id': pid, 'previous_text': source['text'],
                          'previous_sha256': hashlib.sha256(source['text'].encode()).hexdigest(),
                          'reason': 'Use source body only; previous concatenated OCR and R-Formal notes retained for audit.'})
        docs.append(doc)
    # OCR read the number 4 as '+,' and merged this unmodelled clause into K3.
    template = copy.deepcopy(next(d for d in docs if d['id'] == 'qd3266:D22:K3'))
    template.update(id='qd3266:D22:K4', khoan=4, dia_chi='QĐ3266 Điều 22 khoản 4',
                    rules=[], asp=[], text='QĐ3266 Điều 22 khoản 4. Điểm học phần. ' + corrections['qd3266:D22:K4']['text'])
    docs.insert(next(i for i, d in enumerate(docs) if d['id'] == 'qd3266:D22:K5'), template)
    assert len({d['id'] for d in docs}) == len(docs)
    return docs, notes


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--notes', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.notes.exists():
        raise ValueError('Refusing to overwrite an existing corpus artifact.')
    docs, notes = build()
    for path, records in ((args.output, docs), (args.notes, notes)):
        with path.open('x', encoding='utf-8') as stream:
            for record in records:
                stream.write(json.dumps(record, ensure_ascii=False) + '\n')
    print(f'{len(docs)} source passages; {len(notes)} legacy text records retained outside retrieval.')
