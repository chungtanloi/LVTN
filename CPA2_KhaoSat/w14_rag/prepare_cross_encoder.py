"""Download only immutable checksum-pinned model data; never execute remote code."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request
import os

HERE = Path(__file__).parent


def file_hash(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def prepare(directory):
    directory.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((HERE / 'cross_encoder_assets_v1.json').read_text(encoding='utf-8'))
    for asset in manifest['files']:
        path = directory / asset['name']
        if not path.exists() or file_hash(path) != asset['sha256']:
            temp = path.with_suffix('.download')
            with urllib.request.urlopen(asset['url'], timeout=90) as response, temp.open('wb') as output:
                size = 0
                while block := response.read(1024 * 1024):
                    size += len(block)
                    if size > asset['size']:
                        raise ValueError('Download exceeds pinned size.')
                    output.write(block)
            if size != asset['size'] or file_hash(temp) != asset['sha256']:
                raise ValueError('Cross-encoder download checksum mismatch.')
            temp.replace(path)
        print('Verified:', asset['name'], flush=True)


def optimize(directory, target):
    """Run on the serving machine: optimized CPU graphs can be hardware-specific."""
    import onnxruntime as ort
    target.mkdir(parents=True, exist_ok=True)
    output = target / 'model.onnx'
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    options.enable_cpu_mem_arena = False
    options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    options.optimized_model_filepath = str(output)
    session = ort.InferenceSession(str(directory / 'model.onnx'), sess_options=options, providers=['CPUExecutionProvider'])
    metadata = {'original_sha256': file_hash(directory / 'model.onnx'),
                'optimized_sha256': file_hash(output), 'onnxruntime': ort.__version__,
                'scope': 'Generated on the serving machine; regenerate on every container start.'}
    (target / 'metadata.json').write_text(json.dumps(metadata), encoding='utf-8')
    print('Prepared optimized graph on this machine.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=HERE / 'cross_encoder_assets')
    parser.add_argument('--optimize', type=Path)
    args = parser.parse_args()
    prepare(args.directory)
    if args.optimize:
        optimize(args.directory, args.optimize)
