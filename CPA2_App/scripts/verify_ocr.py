"""Exercise the real HTTP OCR boundary with a synthetic transcript, no real data."""
import io
import json
import os
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / 'CPA2_KhaoSat/w15_ocr'))
sys.path.insert(0, str(root / 'CPA2_App/api'))
os.environ['CPA2_SERVICE_KEY'] = 'test-only-service-key'
from render_transcript import render
from fastapi.testclient import TestClient
from cpa2_api.main import app

profile = json.loads((root / 'CPA2_KhaoSat/w7_student_facts/students/sv_5hp.json').read_text(encoding='utf-8'))
images = render(profile)
files = []
for index, image in enumerate(images):
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    files.append(('files', (f'page-{index}.png', buffer.getvalue(), 'image/png')))
pdf = io.BytesIO()
images[0].save(pdf, format='PDF', save_all=True, append_images=images[1:], resolution=144)
from ocr_transcript import so_khop
for label, inputs in [('PNG', files), ('PDF', [('files', ('transcript.pdf', pdf.getvalue(), 'application/pdf'))])]:
    response = TestClient(app).post('/v1/ocr', files=inputs, headers={'Authorization': 'Bearer test-only-service-key'})
    if response.status_code != 200:
        raise RuntimeError(f'{label} OCR HTTP status: {response.status_code}: {response.text}')
    result = response.json()
    if not result['needs_review'] or not result['profile']['meta']['ocr_pending'] or not result['report'].get('tong_dong'):
        raise RuntimeError('OCR must produce a nonempty draft requiring review.')
    correct, accepted, wrong = so_khop(result['profile'], profile)
    if not accepted or correct / accepted < .99:
        raise RuntimeError(f'{label}: accepted facts below the 99% correctness gate: {wrong}')
    print(f"PASS: {label} OCR HTTP, {len(images)} synthetic page(s), {result['report']['tong_dong']} rows, {correct}/{accepted} accepted facts correct; pending review preserved.")
