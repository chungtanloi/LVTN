"""Fetch checksum-pinned public weights at build time, or create the offline index."""
import argparse
import json
from pathlib import Path
import urllib.request

from retriever import HERE, canonical_hash
from semantic_retrieval import Encoder, REVISION, chunks, file_hash


def fetch(directory):
    directory.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((HERE / 'semantic_assets_v1.json').read_text(encoding='utf-8'))
    for asset in manifest['files']:
        path = directory / asset['name']
        if not path.exists() or file_hash(path) != asset['sha256']:
            temporary = path.with_suffix('.download')
            with urllib.request.urlopen(asset['url'], timeout=60) as response, temporary.open('wb') as output:
                size = 0
                while block := response.read(1024 * 1024):
                    size += len(block)
                    if size > asset['size']:
                        raise ValueError('Semantic download exceeds pinned size.')
                    output.write(block)
            if file_hash(temporary) != asset['sha256'] or size != asset['size']:
                raise ValueError('Semantic download does not match pinned asset.')
            temporary.replace(path)
        print('Verified:', asset['name'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--index', action='store_true')
    args = parser.parse_args()
    fetch(args.directory)
    if args.index:
        import numpy as np
        output = HERE / 'semantic_index_v1.npz'
        if output.exists() or (HERE / 'semantic_index_v1.json').exists():
            raise ValueError('Refusing to overwrite an existing semantic index.')
        docs = [json.loads(line) for line in (HERE / 'corpus_source_v1.jsonl').read_text(encoding='utf-8').splitlines()]
        texts, owners = chunks(docs)
        vectors = Encoder(args.directory).encode(texts, 'passage: ')
        np.savez_compressed(output, vectors=vectors, owners=np.asarray(owners, dtype=np.int32))
        metadata = {'model': 'intfloat/multilingual-e5-small', 'revision': REVISION,
                    'corpus_sha256': canonical_hash(sorted(docs, key=lambda d: d['id'])),
                    'index_sha256': file_hash(output), 'passages': len(docs), 'chunks': len(texts),
                    'pooling': 'masked_mean_l2', 'max_tokens': 256, 'window_words': 72, 'stride_words': 48}
        (HERE / 'semantic_index_v1.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(metadata, indent=2))
