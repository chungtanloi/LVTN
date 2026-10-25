"""Run research validations in a disposable copy, preserving existing reports/gold."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

root = Path(__file__).resolve().parents[2]
directory = Path(tempfile.mkdtemp(prefix='cpa2-research-check-'))
copy = directory / 'CPA2_KhaoSat'
shutil.copytree(root / 'CPA2_KhaoSat', copy, ignore=shutil.ignore_patterns('__pycache__', '_rieng', '_tho', '_anh', 'runs', '*.csv'))
failures = []
scripts = sorted(copy.glob('w*/validate_*.py'), key=lambda path: int(path.parent.name.split('_')[0][1:]))
for script in scripts:
    started = time.monotonic()
    try:
        result = subprocess.run([sys.executable, script.name], cwd=script.parent, env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}, capture_output=True, timeout=600)
        (directory / (script.parent.name + '.log')).write_bytes(result.stdout + result.stderr)
        print(f'{script.parent.name}: {"PASS" if result.returncode == 0 else "FAIL"} ({time.monotonic() - started:.1f}s)', flush=True)
        if result.returncode: failures.append(script.parent.name)
    except subprocess.TimeoutExpired as error:
        (directory / (script.parent.name + '.log')).write_bytes((error.stdout or b'') + (error.stderr or b''))
        print(f'{script.parent.name}: TIMEOUT', flush=True)
        failures.append(script.parent.name)
print(f'Logs: {directory}', flush=True)
print(f'Result: {len(scripts) - len(failures)}/{len(scripts)} pass', flush=True)
if failures: print('Failures: ' + ', '.join(failures), flush=True)
sys.exit(bool(failures))
