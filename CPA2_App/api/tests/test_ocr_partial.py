"""A missing final row must not invalidate all earlier cumulative checks."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'CPA2_KhaoSat/w15_ocr'))
import ocr_transcript as ocr


def row(code, credits, score=9.0, letter='A'):
    return {'ma': code, 'tc': credits, 'thi': score, 'thop': score,
            'chu': letter, 'mien': False,
            'conf': dict.fromkeys(('ma', 'tc', 'thi', 'thop', 'chu'), .99)}


class PartialTranscriptTests(unittest.TestCase):
    def test_incomplete_final_semester_does_not_blame_complete_earlier_semesters(self):
        semesters = [
            {'ten': 'HK1', 'dong': [row('CT100', 2)], 'tong_dk': 2,
             'dtbchk': 4.0, 'tc_tich_luy': 2, 'dtbctl': 0.0},
            {'ten': 'HK2', 'dong': [row('CT101', 4),
                {'ma': 'CC004', 'tc': 10, 'mien': True, 'conf': {'ma': .99, 'tc': .99}}],
             'tong_dk': 4, 'dtbchk': 4.0, 'tc_tich_luy': 16, 'dtbctl': 4.0},
            # The printed totals include a lost CT173 row worth 3 credits.
            {'ten': 'HK3', 'dong': [row('CT172', 4, 8.8, 'B+')], 'tong_dk': 7,
             'dtbchk': 3.07, 'tc_tich_luy': 23, 'dtbctl': 3.77},
        ]
        for printed_total in (7, None):
            with self.subTest(printed_total=printed_total):
                doc = {'hoc_ky': copy.deepcopy(semesters)}
                doc['hoc_ky'][-1]['tong_dk'] = printed_total
                profile, extra, report = ocr.sang_ho_so(doc)
                self.assertIn('CT101', profile['grades'])
                self.assertNotIn('HK2 (TC tích lũy)', report['hoc_ky_lech'])
                self.assertIn('HK3', report['hoc_ky_lech'])
                self.assertGreater(report['dong_an'], 0)
                self.assertEqual(ocr.ket_luan(profile, extra, report), 'UNKNOWN')
                detail = report['doi_chieu_hoc_ky'][-1]
                self.assertEqual(detail['tong_tc_cac_dong'], 4)
                self.assertFalse(detail['du_dong_theo_tong_tc'])
                self.assertIsNone(detail['tc_tich_luy_tinh_lai'])
