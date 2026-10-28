"""Rebuild OCR facts after explicit corrections, keeping aggregate checks intact."""
import copy
from datetime import datetime, timezone
import math
import uuid

from .profiles import COURSES, normalize


class OcrReviewError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def validate_row(values):
    from ocr_transcript import chu_tu_diem
    code = values.get('code')
    if not isinstance(code, str) or code not in COURSES:
        raise OcrReviewError('BAD_CODE')
    credits, score = values.get('credits'), values.get('thang10')
    if type(credits) is not int or credits != COURSES[code]['tin_chi']:
        raise OcrReviewError('CREDITS_MISMATCH')
    if type(score) is not int or not 0 <= score <= 100:
        raise OcrReviewError('BAD_SCORE')
    if values.get('letter') != chu_tu_diem(score / 10):
        raise OcrReviewError('LETTER_MISMATCH')
    return code, credits, score


def review(payload):
    from ocr_transcript import sang_ho_so
    base = normalize(payload['profile'])
    document = (base.get('meta', {}).get('ocr_report') or {}).get('tai_lieu_ocr')
    if not isinstance(document, dict) or not isinstance(document.get('hoc_ky'), list):
        raise OcrReviewError('OCR_REUPLOAD_REQUIRED')
    document = copy.deepcopy(document)
    semesters = document['hoc_ky']
    if not 1 <= len(semesters) <= 30:
        raise OcrReviewError('BAD_CONTEXT')
    rows = {}
    for hi, semester in enumerate(semesters):
        if not isinstance(semester, dict) or not isinstance(semester.get('dong'), list):
            raise OcrReviewError('BAD_CONTEXT')
        for ri, row in enumerate(semester['dong']):
            if not isinstance(row, dict):
                raise OcrReviewError('BAD_CONTEXT')
            rid = row.setdefault('row_id', f'{hi + 1}:{ri + 1}')
            if not isinstance(rid, str) or len(rid) > 80 or rid in rows:
                raise OcrReviewError('BAD_CONTEXT')
            # Revalidate every previous declaration; the supplied report is data.
            if row.get('user_review'):
                if row.get('mien'):
                    raise OcrReviewError('OFFICIAL_CONFIRMATION_REQUIRED')
                score = row.get('thop')
                if (type(score) not in (int, float) or not math.isfinite(score)
                        or not 0 <= score <= 10 or abs(score * 10 - round(score * 10)) > 1e-6):
                    raise OcrReviewError('BAD_SCORE')
                validate_row({'code': row.get('ma'), 'credits': row.get('tc'),
                              'thang10': round(score * 10), 'letter': row.get('chu')})
            rows[rid] = (semester, row)
    if len(rows) > 250:
        raise OcrReviewError('TOO_MANY_ROWS')
    action = payload['action']
    rid = payload.get('row_id')
    before = None
    if action == 'semester':
        index = payload.get('semester_index')
        if type(index) is not int or not 0 <= index < len(semesters):
            raise OcrReviewError('UNKNOWN_SEMESTER')
        changes = payload.get('totals') or {}
        limits = {'tong_dk': (0, 100, True), 'dtbchk': (0, 4, False),
                  'tc_tich_luy': (0, 1000, True), 'dtbctl': (0, 4, False)}
        if not changes or set(changes) - limits.keys():
            raise OcrReviewError('BAD_TOTALS')
        for key, value in changes.items():
            lo, hi, integer = limits[key]
            if (type(value) not in (int, float) or not math.isfinite(value)
                    or not lo <= value <= hi or (integer and type(value) is not int)
                    or (not integer and abs(value * 100 - round(value * 100)) > 1e-6)):
                raise OcrReviewError('BAD_TOTALS')
        before = {k: semesters[index].get(k) for k in changes}
        semesters[index].update(changes)
    elif action in ('approve', 'add', 'exclude'):
        if action == 'add':
            index = payload.get('semester_index')
            if type(index) is not int or not 0 <= index < len(semesters) or len(rows) >= 250:
                raise OcrReviewError('UNKNOWN_SEMESTER')
            semester, row = semesters[index], {}
            rid = 'manual:' + uuid.uuid4().hex
        else:
            if rid not in rows:
                raise OcrReviewError('UNKNOWN_ROW')
            semester, row = rows[rid]
            before = copy.deepcopy(row)
        if row.get('mien') or row.get('ma') == 'CC004':
            raise OcrReviewError('OFFICIAL_CONFIRMATION_REQUIRED')
        if action == 'exclude':
            semester['dong'].remove(row)
        else:
            code, credits, score = validate_row(payload)
            # Original OCR text/confidence are retained. This is a human
            # declaration, never a fabricated high-confidence OCR reading.
            row.update(row_id=rid, ma=code, tc=credits, thi=score / 10,
                       thop=score / 10, chu=payload['letter'], mien=False,
                       user_review=True)
            row.pop('ma_khac', None)
            if action == 'add':
                row['conf'] = {}
                semester['dong'].append(row)
    else:
        raise OcrReviewError('BAD_ACTION')
    history = document.setdefault('lich_su_ra_soat', [])
    if not isinstance(history, list) or len(history) >= 1000:
        raise OcrReviewError('BAD_CONTEXT')
    history.append({'action': action, 'row_id': rid, 'before': before,
                    'at': datetime.now(timezone.utc).isoformat()})
    declarations = {k: v for k, v in base.items() if k not in ('grades', 'exemptions', 'meta')}
    profile, _, report = sang_ho_so(document, khai_bao=declarations)
    for exemption in base.get('exemptions', []):
        if exemption not in profile['exemptions']:
            profile['exemptions'].append(exemption)
    unresolved = any(report.get(k) for k in ('khong_chac', 'dong_an', 'can_hoi', 'hoc_ky_lech',
                                             'can_xac_nhan', 'ngoai_ctdt', 'khai_bao_loi', 'dong_can_ra_soat'))
    profile['meta'].update({**base.get('meta', {}), 'nguon': 'ocr', 'ocr_report': report,
                            'ocr_pending': unresolved, 'reviewed_by_user': False})
    return {'profile': normalize(profile), 'report': report, 'needs_review': unresolved}
