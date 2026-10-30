"""Check Docker COPY selection without Docker or access to the source checkout at runtime."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / 'CPA2_App/api'))
from cpa2_api.profiles import kb_version
expected_version = kb_version()
with tempfile.TemporaryDirectory(prefix='cpa2-runtime-') as directory:
    target = Path(directory)
    for line in (root / 'CPA2_App/Dockerfile').read_text(encoding='utf-8').splitlines():
        if not line.startswith('COPY '):
            continue
        *sources, destination = line.split()[1:]
        dest = target / destination.removeprefix('/app/').rstrip('/')
        dest.mkdir(parents=True, exist_ok=True)
        for source in sources:
            matches = list(root.glob(source))
            if not matches:
                raise RuntimeError(f'COPY matches no source: {source}')
            for path in matches:
                if path.is_dir():
                    shutil.copytree(path, dest / path.name, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__'))
                else:
                    shutil.copy2(path, dest / path.name)
    # Docker COPY directory semantics copy contents, not the directory name.
    copied = target / 'CPA2_App/api/cpa2_api/cpa2_api'
    if copied.exists():
        for path in copied.iterdir():
            shutil.move(str(path), copied.parent / path.name)
        copied.rmdir()
    sample = json.loads((target / 'CPA2_KhaoSat/w7_student_facts/students/sv_lvtn.json').read_text(encoding='utf-8'))
    # Simulate the model-data layer created by Docker RUN, without depending on
    # the source checkout while the packaged worker executes.
    assets = Path(os.environ.get('CPA2_CROSS_ENCODER_DIR', root / 'CPA2_KhaoSat/w14_rag/cross_encoder_assets'))
    shutil.copytree(assets, target / 'CPA2_KhaoSat/w14_rag/cross_encoder_assets')
    runtime_env = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
    runtime_env.pop('CPA2_CROSS_ENCODER_DIR', None)
    runtime_env['CPA2_CROSS_ENCODER_CACHE'] = str(target / 'cross-cache')
    prepared = subprocess.run([sys.executable, str(target / 'CPA2_KhaoSat/w14_rag/prepare_cross_encoder.py'),
                               '--optimize', str(target / 'cross-cache')], env=runtime_env, capture_output=True, timeout=90)
    if prepared.returncode:
        raise RuntimeError('Packaged cross-encoder startup preparation failed.')
    version = subprocess.check_output([sys.executable, '-c', 'from cpa2_api.profiles import kb_version; print(kb_version())'], cwd=target / 'CPA2_App/api', text=True).strip()
    if version != expected_version:
        raise RuntimeError('KB version differs between checkout and packaged runtime.')
    print(f'PASS packaged KB version: {version}', flush=True)
    for operation, payload in [
        ('advice', {'profile': sample, 'question': 'Em đủ điều kiện tốt nghiệp chưa?'}),
        ('advice', {'profile': sample, 'question': 'Em đủ điều kiện làm luận văn tốt nghiệp không?'}),
        ('advice', {'profile': sample, 'question': 'Em có được đăng ký CT180 không?'}),
        ('recommendations', {'profile': sample, 'semester': 1}),
        ('lookup', {'question': 'điểm W'}),
    ]:
        result = subprocess.run([sys.executable, '-m', 'cpa2_api.worker'], input=json.dumps({'operation': operation, 'payload': payload}), text=True, encoding='utf-8', capture_output=True, cwd=target / 'CPA2_App/api', env=runtime_env, timeout=125 if operation == 'lookup' else 35)
        if result.returncode:
            raise RuntimeError(f'{operation}: {result.stdout} {result.stderr}')
        if not json.loads(result.stdout)['ok']:
            raise RuntimeError(f'{operation}: invalid output')
        print(f'PASS packaged runtime: {operation} {payload.get("question", "")}', flush=True)
