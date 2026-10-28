import copy
import sys
from pathlib import Path
import unittest
import os
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'CPA2_KhaoSat/w15_ocr'))
import ocr_transcript as ocr
from cpa2_api.ocr_review import review, OcrReviewError


def profile(rows=None, total=4, average=4.0):
    rows = rows or [{'ma': 'CT101', 'tc': 4, 'thi': 9.7, 'thop': 9.7, 'chu': 'A',
                     'mien': False, 'ocr_raw': 'CT101 4 9.7 A',
                     'conf': dict.fromkeys(('ma', 'tc', 'thi', 'thop', 'chu'), .2)}]
    p, _, report = ocr.sang_ho_so({'hoc_ky': [{'ten': 'HK1', 'dong': rows, 'tong_dk': total, 'dtbchk': average}]})
    p['meta'].update(ocr_report=report, ocr_pending=True)
    return p


def approve(p, **patch):
    return review({'profile': p, 'action': 'approve', 'row_id': '1:1', 'code': 'CT101',
                   'credits': 4, 'thang10': 97, 'letter': 'A', **patch})


class OcrApprovalTests(unittest.TestCase):
    def test_http_review_validates_and_keeps_final_approval_explicit(self):
        from fastapi.testclient import TestClient
        from cpa2_api.main import app
        with patch.dict(os.environ, {'CPA2_SERVICE_KEY': 'review-test-key'}):
            client = TestClient(app)
            payload = {'profile': profile(), 'action': 'approve', 'row_id': '1:1', 'code': 'CT101',
                       'credits': 4, 'thang10': 97, 'letter': 'A'}
            self.assertEqual(client.post('/v1/ocr/review', json=payload).status_code, 401)
            headers = {'Authorization': 'Bearer review-test-key'}
            bad = client.post('/v1/ocr/review', json={**payload, 'credits': 3}, headers=headers)
            self.assertEqual(bad.status_code, 422, bad.text)
            result = client.post('/v1/ocr/review', json=payload, headers=headers)
            self.assertEqual(result.status_code, 200, result.text)
            reviewed = result.json()['profile']
            response = client.post('/v1/advice', json={'profile': reviewed, 'question': 'Em đủ điều kiện tốt nghiệp chưa?'}, headers=headers)
            self.assertEqual(response.json()['reason'], 'OCR_REVIEW_REQUIRED')
            reviewed['meta']['reviewed_by_user'] = True
            response = client.post('/v1/advice', json={'profile': reviewed, 'question': 'Em đủ điều kiện tốt nghiệp chưa?'}, headers=headers)
            self.assertNotEqual(response.json().get('reason'), 'OCR_REVIEW_REQUIRED')
    def test_corrected_and_approved_row_becomes_a_fact_with_manual_provenance(self):
        p = profile(); before = copy.deepcopy(p)
        result = approve(p)
        self.assertEqual(p, before)
        grade = result['profile']['grades']['CT101']
        self.assertEqual((grade['thang10'], grade['source']), (97, 'manual_review'))
        self.assertEqual(grade['confidence'], .2)  # not fabricated OCR confidence
        self.assertFalse(result['needs_review'])
        self.assertFalse(result['profile']['meta']['reviewed_by_user'])
        self.assertEqual(len(result['report']['tai_lieu_ocr']['lich_su_ra_soat']), 1)

    def test_invalid_field_changes_are_rejected(self):
        for patch in ({'code': 'BAD'}, {'credits': 3}, {'thang10': 110}, {'letter': 'B'}, {'thang10': True}):
            with self.subTest(patch=patch), self.assertRaises(OcrReviewError):
                approve(profile(), **patch)

    def test_approving_a_row_does_not_clear_a_semester_average_conflict(self):
        result = approve(profile(average=3.0))
        self.assertTrue(result['needs_review'])
        self.assertIn('HK1 (ĐTBCHK)', result['report']['hoc_ky_lech'])
        self.assertTrue(result['report']['dong_can_ra_soat'][0]['da_duyet'])
        result = review({'profile': result['profile'], 'action': 'semester',
                         'semester_index': 0, 'totals': {'dtbchk': 4.0}})
        self.assertFalse(result['needs_review'])

    def test_a_missing_course_can_be_added_to_the_correct_semester(self):
        result = approve(profile(total=6))
        self.assertTrue(result['report']['dong_an'])
        result = review({'profile': result['profile'], 'action': 'add', 'semester_index': 0,
                         'code': 'CT100', 'credits': 2, 'thang10': 92, 'letter': 'A'})
        self.assertFalse(result['needs_review'])
        self.assertEqual(set(result['profile']['grades']), {'CT100', 'CT101'})

    def test_a_false_ocr_row_can_be_excluded_without_erasing_audit_data(self):
        p = profile(total=0)
        result = review({'profile': p, 'action': 'exclude', 'row_id': '1:1'})
        self.assertFalse(result['report']['dong_can_ra_soat'])
        self.assertEqual(result['report']['tai_lieu_ocr']['lich_su_ra_soat'][0]['before']['ma'], 'CT101')

    def test_old_reports_require_reocr_and_exemptions_cannot_be_self_approved(self):
        p = profile(); del p['meta']['ocr_report']['tai_lieu_ocr']
        with self.assertRaises(OcrReviewError) as error: approve(p)
        self.assertEqual(error.exception.code, 'OCR_REUPLOAD_REQUIRED')
        p = profile([{'ma': 'CC004', 'tc': 10, 'mien': True, 'conf': {'ma': .99, 'tc': .99}}], 10)
        for action in ('approve', 'exclude'):
            with self.assertRaises(OcrReviewError) as error: approve(p, action=action)
            self.assertEqual(error.exception.code, 'OFFICIAL_CONFIRMATION_REQUIRED')

    def test_forged_prior_approval_flags_are_still_validated(self):
        p = profile()
        row = p['meta']['ocr_report']['tai_lieu_ocr']['hoc_ky'][0]['dong'][0]
        row.update(user_review=True, tc=3)
        with self.assertRaises(OcrReviewError): approve(p)

    def test_reviewed_row_ids_remain_stable_when_an_earlier_row_is_removed(self):
        p = profile([{'ma': 'CT100', 'tc': 2, 'thi': 9.2, 'thop': 9.2, 'chu': 'A', 'conf': {'ma': .1}},
                     {'ma': 'CT101', 'tc': 4, 'thi': 9.7, 'thop': 9.7, 'chu': 'A', 'conf': {'ma': .1}}], 4)
        result = review({'profile': p, 'action': 'exclude', 'row_id': '1:1'})
        result = approve(result['profile'], row_id='1:2')
        self.assertFalse(result['needs_review'])
