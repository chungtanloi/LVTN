"""One request per process: isolate legacy sys.path and bound solver execution."""
import json
from pathlib import Path
import sys
import tempfile

from .profiles import KB, normalize


def execute(operation, payload):
    sys.path.insert(0, str(KB / 'w14_rag'))
    from grounded_answer import tra_loi, tra_cuu
    if operation == 'lookup':
        return {'passages': tra_cuu(payload['question'])}
    if operation == 'review_ocr':
        sys.path.insert(0, str(KB / 'w15_ocr'))
        from .ocr_review import review
        return review(payload)
    if operation == 'ocr':
        sys.path.insert(0, str(KB / 'w15_ocr'))
        from ocr_transcript import doc_bang_diem, sang_ho_so
        from .ocr_input import read_pages
        images = read_pages(payload['paths'])
        try:
            document = doc_bang_diem(images)
            if not document['hoc_ky']:
                raise ValueError('Không nhận diện được bảng điểm theo học kỳ. Hãy dùng ảnh rõ của mẫu ĐHCT D5050A0.')
            profile, _, report = sang_ho_so(document)
            profile['meta'].update({'ocr_pending': True, 'ocr_report': report})
            return {'profile': profile, 'report': report, 'needs_review': True}
        finally:
            for image in images:
                image.close()
    profile = normalize(payload['profile'])
    metadata = profile.get('meta', {})
    report = metadata.get('ocr_report') or {}
    unresolved_ocr = any(report.get(key) for key in ('khong_chac', 'dong_an', 'can_hoi', 'hoc_ky_lech', 'can_xac_nhan', 'ngoai_ctdt', 'khai_bao_loi', 'dong_can_ra_soat'))
    if metadata.get('nguon') == 'ocr' and (metadata.get('ocr_pending', True) or not metadata.get('reviewed_by_user') or unresolved_ocr):
        return {'verdict': 'UNKNOWN', 'reason': 'OCR_REVIEW_REQUIRED', 'claim': 'input_incomplete',
                'explanation_vi': 'Bảng điểm OCR còn chờ kiểm tra. Hãy bổ sung các dòng và dữ kiện chưa chắc trước khi tư vấn.',
                'missing_facts': ['Rà soát và xác nhận bảng điểm OCR'], 'certificate': {'proof': {'steps': []}}, 'nguon': []}
    missing_scores = [code for code, grade in profile['grades'].items()
                      if grade.get('thang10') is None and grade.get('diem') not in ('M', 'W', 'I')]
    if missing_scores:
        return {'verdict': 'UNKNOWN', 'reason': 'NUMERIC_GRADES_REQUIRED', 'claim': 'input_incomplete',
                'explanation_vi': 'Hồ sơ nhập từ niên luận còn thiếu điểm số chính xác. Hãy bổ sung điểm thang 10 để CPA² không bỏ sót dữ kiện.',
                'missing_facts': [f'Điểm thang 10 của {code}' for code in missing_scores],
                'certificate': {'proof': {'steps': []}}, 'nguon': []}
    if operation == 'recommendations':
        sys.path.insert(0, str(KB / 'w19_recommendation'))
        from recommendation import de_xuat
        return de_xuat(profile, payload['semester'])
    # File adapter preserves the research CLI and shared loader unchanged.
    with tempfile.TemporaryDirectory(prefix='cpa2-') as directory:
        path = Path(directory) / 'profile.json'
        path.write_text(json.dumps(profile, ensure_ascii=False), encoding='utf-8')
        return tra_loi(payload['question'], path)


if __name__ == '__main__':
    try:
        request = json.load(sys.stdin)
        result = execute(request['operation'], request['payload'])
        print(json.dumps({'ok': True, 'result': result}, ensure_ascii=False))
    except Exception as error:
        # Never include student data in exception messages returned to logs.
        print(json.dumps({'ok': False, 'error_type': type(error).__name__,
                          'error_code': error.code if type(error).__name__ == 'OcrReviewError' else None}))
        sys.exit(1)
