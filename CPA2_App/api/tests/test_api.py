import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

from PIL import Image

os.environ['CPA2_SERVICE_KEY'] = 'test-only-service-key'
from fastapi.testclient import TestClient
from cpa2_api.main import app

ROOT = Path(__file__).resolve().parents[3]
SAMPLE = json.loads((ROOT / 'CPA2_KhaoSat/w7_student_facts/students/sv_lvtn.json').read_text(encoding='utf-8'))
HEADERS = {'Authorization': 'Bearer test-only-service-key'}


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_has_no_student_data(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['app'], 'CPA²')
        self.assertNotIn('profile', response.json())

    def test_protected_endpoints_require_key(self):
        self.assertEqual(self.client.post('/v1/advice', json={'question': 'tot nghiep', 'profile': SAMPLE}).status_code, 401)

    def test_rejects_other_cohort_and_injection(self):
        for patch in ({'cohort': 'K51'}, {'student_id': '../private'}, {'grades': {'CT1\"). evil.': {'code': 'CT1\"). evil.'}}}):
            profile = {**SAMPLE, **patch}
            response = self.client.post('/v1/profiles/validate', json={'profile': profile}, headers=HEADERS)
            self.assertEqual(response.status_code, 422, response.text)

    def test_legacy_adapter_does_not_guess_cohort(self):
        profile = {'student_id': 'B123', 'grades_by_code': {'CT101': 'A'}}
        response = self.client.post('/v1/profiles/validate', json={'profile': profile}, headers=HEADERS)
        self.assertEqual(response.status_code, 422)

    def test_legacy_adapter_preserves_letter_only_grade(self):
        profile = {'student_id': 'B123', 'major': 'cntt', 'cohort': 'K49', 'grades': {'CT101': {'code': 'CT101', 'letter_grade': 'B+', 'credits': 4}}}
        response = self.client.post('/v1/profiles/validate', json={'profile': profile}, headers=HEADERS)
        self.assertEqual(response.status_code, 200, response.text)
        grade = response.json()['profile']['grades']['CT101']
        self.assertEqual(grade['letter'], 'B+')
        self.assertIsNone(grade.get('thang10'))

    def test_unknown_question_never_defaults_to_graduation(self):
        response = self.client.post('/v1/advice', json={'question': 'Học phí bao nhiêu?', 'profile': SAMPLE}, headers=HEADERS)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['verdict'], 'UNKNOWN')
        self.assertEqual(response.json()['claim'], 'khong_ro')

    def test_result_matches_existing_pipeline(self):
        from cpa2_api.worker import execute
        expected = execute('advice', {'question': 'Em đủ điều kiện tốt nghiệp chưa?', 'profile': SAMPLE})
        response = self.client.post('/v1/advice', json={'question': 'Em đủ điều kiện tốt nghiệp chưa?', 'profile': SAMPLE}, headers=HEADERS)
        self.assertEqual(response.status_code, 200, response.text)
        for field in ('verdict', 'claim', 'certificate', 'nguon'):
            self.assertEqual(response.json()[field], expected[field])

    def test_ocr_uncertainty_blocks_conclusions(self):
        profile = {**SAMPLE, 'meta': {'nguon': 'ocr', 'ocr_pending': True}}
        response = self.client.post('/v1/advice', json={'question': 'Em đủ điều kiện tốt nghiệp chưa?', 'profile': profile}, headers=HEADERS)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['verdict'], 'UNKNOWN')
        self.assertEqual(response.json()['reason'], 'OCR_REVIEW_REQUIRED')

    def test_letter_only_import_never_silently_drops_grades(self):
        profile = {'student_id': 'sv_legacy', 'major': 'cntt', 'cohort': 'K49', 'grades': {'CT101': {'code': 'CT101', 'letter_grade': 'A', 'credits': 4}}}
        response = self.client.post('/v1/advice', json={'question': 'Em đủ điều kiện tốt nghiệp chưa?', 'profile': profile}, headers=HEADERS)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['verdict'], 'UNKNOWN')
        self.assertEqual(response.json()['reason'], 'NUMERIC_GRADES_REQUIRED')

    def test_invalid_file_is_rejected_before_ocr(self):
        response = self.client.post('/v1/ocr', files={'files': ('test.png', b'not an image', 'image/png')}, headers=HEADERS)
        self.assertEqual(response.status_code, 422)

    def test_review_checkbox_cannot_clear_ocr_mapping_uncertainty(self):
        profile = {**SAMPLE, 'meta': {'nguon': 'ocr', 'ocr_pending': False, 'reviewed_by_user': True, 'ocr_report': {'can_xac_nhan': ['CC004 chưa được Phòng Đào tạo xác nhận']}}}
        response = self.client.post('/v1/advice', json={'question': 'Em đủ điều kiện tốt nghiệp chưa?', 'profile': profile}, headers=HEADERS)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['verdict'], 'UNKNOWN')
        self.assertEqual(response.json()['reason'], 'OCR_REVIEW_REQUIRED')

    def test_semester_is_validated(self):
        response = self.client.post('/v1/recommendations', json={'profile': SAMPLE, 'semester': 4}, headers=HEADERS)
        self.assertEqual(response.status_code, 422)

    def test_missing_transferred_credits_do_not_mean_zero(self):
        for value, expected in ((None, 'UNKNOWN'), (0, 'TRUE'), (27, 'FALSE')):
            profile = {**SAMPLE, 'da_hoc_nam2': 17, 'tc_cong_nhan': value}
            response = self.client.post('/v1/advice', json={'question': 'Em đủ điều kiện tốt nghiệp chưa?', 'profile': profile}, headers=HEADERS)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()['verdict'], expected)

    def test_lookup_preserves_the_requested_course(self):
        response = self.client.post('/v1/lookup', json={'question': 'Môn CT177 có tiên quyết là gì?'}, headers=HEADERS)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['passages'][0]['passage_id'], 'ctdt_k49:CT177')

    def test_lookup_honors_the_explicit_regulation(self):
        response = self.client.post('/v1/lookup', json={'question': 'Theo QĐ5339, công nhận điểm học phần ở trường khác như thế nào?'}, headers=HEADERS)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()['passages'])
        self.assertTrue(all(p['passage_id'].startswith('qd5339:') for p in response.json()['passages']))

    def test_lookup_does_not_rename_unknown_regulations(self):
        for number in ('326', '53390'):
            response = self.client.post('/v1/lookup', json={'question': f'Theo QĐ{number}, công nhận điểm thế nào?'}, headers=HEADERS)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()['passages'], [])

    def test_lookup_without_evidence_returns_no_sources(self):
        response = self.client.post('/v1/lookup', json={'question': 'zzzxqv_kgjh'}, headers=HEADERS)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['passages'], [])

    def test_graduation_trace_keeps_the_claim(self):
        response = self.client.post('/v1/advice', json={'question': 'Em đủ điều kiện tốt nghiệp chưa?',
            'profile': {**SAMPLE, 'tc_cong_nhan': 0}}, headers=HEADERS)
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertEqual(result['verdict'], 'TRUE')
        proof = result['certificate']['proof']
        self.assertEqual(proof['steps'][0]['atom'], result['claim'])
        self.assertGreater(len(proof['steps']), 20)
        self.assertFalse(proof['truncated'])


def synthetic_pdf(pages, resolution=130.0):
    """PDF ảnh từ trang bảng điểm GIẢ LẬP (không dùng bảng điểm thật)."""
    buffer = io.BytesIO()
    pages[0].save(buffer, 'PDF', resolution=resolution, save_all=True, append_images=pages[1:], quality=95)
    return buffer.getvalue()


def synthetic_pages():
    sys.path.insert(0, str(ROOT / 'CPA2_KhaoSat/w15_ocr'))
    from render_transcript import render
    return render(SAMPLE)


def has_tesseract():
    sys.path.insert(0, str(ROOT / 'CPA2_KhaoSat/w15_ocr'))
    try:
        import ocr_transcript  # noqa: F401  (cấu hình đường dẫn Tesseract)
        import pytesseract
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


class PdfTranscriptTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def post(self, *files):
        return self.client.post('/v1/ocr', files=[('files', f) for f in files], headers=HEADERS)

    def test_pdf_pages_render_at_bounded_transcript_resolution(self):
        from cpa2_api.ocr_input import read_pages
        pages = synthetic_pages()
        buffer = io.BytesIO()   # chế độ P: Pillow lưu không nén mất dữ liệu (L thì thành JPEG)
        pages[0].convert('P').save(buffer, 'PDF', resolution=130.0, save_all=True,
                                   append_images=[page.convert('P') for page in pages[1:]])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'transcript.pdf'
            path.write_bytes(buffer.getvalue())
            images = read_pages([path])
        self.assertEqual(len(images), len(pages))
        for page, image in zip(pages, images):
            self.assertEqual(image.width, 2448)
            self.assertAlmostEqual(image.height / image.width, page.height / page.width, places=3)
            image.close()

    def test_pdf_with_more_than_four_pages_is_rejected(self):
        page = Image.new('L', (1105, 1430), 255)
        response = self.post(('bang_diem.pdf', synthetic_pdf([page] * 5), 'application/pdf'))
        self.assertEqual(response.status_code, 422, response.text)

    def test_fake_pdf_is_rejected(self):
        response = self.post(('bang_diem.pdf', b'%PDF-1.7\nkhong phai pdf', 'application/pdf'))
        self.assertEqual(response.status_code, 422, response.text)

    def test_oversized_pdf_page_is_rejected_before_rendering(self):
        # trang 200 × 200 inch → 26 000 × 26 000 điểm ảnh ở 130 DPI
        page = Image.new('L', (20, 20), 255)
        response = self.post(('bang_diem.pdf', synthetic_pdf([page], resolution=0.1), 'application/pdf'))
        self.assertEqual(response.status_code, 422, response.text)

    def test_pdf_and_images_cannot_exceed_four_pages(self):
        page = Image.new('L', (1105, 1430), 255)
        png = io.BytesIO()
        page.save(png, 'PNG')
        response = self.post(('bang_diem.pdf', synthetic_pdf([page] * 4), 'application/pdf'),
                             ('page.png', png.getvalue(), 'image/png'))
        self.assertEqual(response.status_code, 422, response.text)

    def test_encrypted_pdf_is_rejected(self):
        try:
            from pypdf import PdfReader, PdfWriter
        except ImportError:
            self.skipTest('cần pypdf để dựng PDF có mật khẩu')
        writer = PdfWriter(clone_from=PdfReader(io.BytesIO(synthetic_pdf([Image.new('L', (1105, 1430), 255)]))))
        writer.encrypt('mat-khau')
        buffer = io.BytesIO()
        writer.write(buffer)
        response = self.post(('bang_diem.pdf', buffer.getvalue(), 'application/pdf'))
        self.assertEqual(response.status_code, 422, response.text)

    @unittest.skipUnless(has_tesseract(), 'cần Tesseract (vie) để chạy OCR')
    def test_pdf_upload_reaches_ocr_and_requires_review(self):
        # Độ chính xác OCR với ảnh nén JPEG trong PDF là việc của w15 (Viec_ton_dong C19), không kiểm ở đây
        response = self.post(('bang_diem.pdf', synthetic_pdf(synthetic_pages()), 'application/pdf'))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()['needs_review'])
        self.assertTrue(response.json()['profile']['meta']['ocr_pending'])
        self.assertGreater(response.json()['report']['tong_dong'], 0)


if __name__ == '__main__':
    unittest.main()
