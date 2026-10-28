import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'CPA2_KhaoSat/w15_ocr'))
import ocr_transcript as ocr


def row(code, credits, score, confidence=.99):
    return {'ma': code, 'tc': credits, 'thi': score, 'thop': score, 'chu': 'A',
            'mien': False, 'ocr_raw': f'{code} {credits} {score} A',
            'conf': dict.fromkeys(('ma', 'tc', 'thi', 'thop', 'chu'), confidence)}


class OcrReviewTests(unittest.TestCase):
    def test_low_confidence_row_is_visible_but_not_a_student_fact(self):
        doc = {'hoc_ky': [{'ten': 'HK1', 'dong': [row('CT100', 2, 9.2), row('CT101', 4, 9.7, .2)],
                          'tong_dk': 6, 'dtbchk': 4.0, 'tc_tich_luy': 6}]}
        profile, _, report = ocr.sang_ho_so(doc)
        self.assertEqual(set(profile['grades']), {'CT100'})
        self.assertEqual(len(report['dong_can_ra_soat']), 1)
        review = report['dong_can_ra_soat'][0]
        self.assertEqual((review['ma'], review['thang10'], review['tc']), ('CT101', 97, 4))
        self.assertTrue(review['ly_do'])

    def test_retake_ambiguity_keeps_both_observed_attempts_for_review(self):
        doc = {'hoc_ky': [
            {'ten': 'HK1', 'dong': [row('CT101', 4, 9.7)], 'tong_dk': 4, 'dtbchk': 4.0},
            {'ten': 'HK2', 'dong': [row('CT101', 4, 9.7, .2)], 'tong_dk': 4, 'dtbchk': 4.0},
        ]}
        profile, _, report = ocr.sang_ho_so(doc)
        self.assertNotIn('CT101', profile['grades'])
        self.assertEqual([r['hoc_ky'] for r in report['dong_can_ra_soat']], ['HK1', 'HK2'])
        self.assertEqual(len({r['id'] for r in report['dong_can_ra_soat']}), 2)

    def test_unread_score_is_not_converted_to_zero(self):
        uncertain = row('CT101', 4, 9.7)
        uncertain.update(thi=None, thop=None, chu=None)
        doc = {'hoc_ky': [{'ten': 'HK1', 'dong': [uncertain], 'tong_dk': 4, 'dtbchk': 4.0}]}
        profile, _, report = ocr.sang_ho_so(doc)
        self.assertNotIn('CT101', profile['grades'])
        self.assertIsNone(report['dong_can_ra_soat'][0]['thang10'])

    def test_review_candidates_cannot_be_used_for_advice_by_checking_reviewed(self):
        from cpa2_api.worker import execute
        profile = json.loads((ROOT / 'CPA2_KhaoSat/w7_student_facts/students/sv_lvtn.json').read_text(encoding='utf8'))
        profile['meta'] = {'nguon': 'ocr', 'ocr_pending': False, 'reviewed_by_user': True,
                           'ocr_report': {'dong_can_ra_soat': [{'ma': 'CT101', 'thang10': 97}]}}
        result = execute('advice', {'profile': profile, 'question': 'Em đủ điều kiện tốt nghiệp chưa?'})
        self.assertEqual(result['verdict'], 'UNKNOWN')
        self.assertEqual(result['reason'], 'OCR_REVIEW_REQUIRED')
