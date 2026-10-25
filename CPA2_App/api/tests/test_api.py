import json
import os
from pathlib import Path
import unittest

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


if __name__ == '__main__':
    unittest.main()
