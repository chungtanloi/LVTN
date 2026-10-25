"""Run research validations in a disposable copy, preserving existing reports/gold."""
import os
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--work-dir', type=Path, help='New isolated output directory; must not already exist.')
args = parser.parse_args()
directory = args.work_dir.resolve() if args.work_dir else Path(tempfile.mkdtemp(prefix='cpa2-research-check-'))
if args.work_dir:
    directory.mkdir(parents=True, exist_ok=False)
copy = directory / 'CPA2_KhaoSat'
shutil.copytree(root / 'CPA2_KhaoSat', copy, ignore=shutil.ignore_patterns('__pycache__', '_rieng', '_tho', '_anh', 'runs', '*.csv'))
failures = []
scripts = sorted(copy.glob('w*/validate_*.py'), key=lambda path: int(path.parent.name.split('_')[0][1:]))
for script in scripts:
    started = time.monotonic()
    try:
        with (directory / (script.parent.name + '-' + script.stem + '.log')).open('wb') as log:
            result = subprocess.run([sys.executable, script.name], cwd=script.parent, env={**os.environ, 'PYTHONIOENCODING': 'utf-8', 'PYTHONUNBUFFERED': '1'}, stdout=log, stderr=subprocess.STDOUT, timeout=600)
        print(f'{script.parent.name}: {"PASS" if result.returncode == 0 else "FAIL"} ({time.monotonic() - started:.1f}s)', flush=True)
        if result.returncode: failures.append(script.parent.name)
    except subprocess.TimeoutExpired as error:
        print(f'{script.parent.name}: TIMEOUT', flush=True)
        failures.append(script.parent.name)
print(f'Logs: {directory}', flush=True)
print(f'Result: {len(scripts) - len(failures)}/{len(scripts)} pass', flush=True)
if failures: print('Failures: ' + ', '.join(failures), flush=True)
sys.exit(bool(failures))
