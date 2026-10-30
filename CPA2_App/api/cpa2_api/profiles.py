"""Validated adapter for CPA² and exported AcademiQ profiles. No legacy DB imports."""
import copy
import hashlib
import json
import math
import re
from pathlib import Path

from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[3]
KB = ROOT / 'CPA2_KhaoSat'
SCHEMA = json.loads((KB / 'w7_student_facts/student_fact_schema.json').read_text(encoding='utf-8'))
CURRICULUM = json.loads((KB / 'w6_curriculum/curriculum_cntt_k49.json').read_text(encoding='utf-8'))
COURSES = {c['ma']: c for c in CURRICULUM['hoc_phan']}
CODE = re.compile(r'[A-Z]{1,4}[0-9]{2,4}[A-Z]?\Z')
SAFE_TEXT = re.compile(r'[a-zA-Z0-9_+.-]+\Z')


def normalize(raw: dict) -> dict:
    profile = copy.deepcopy(raw)
    if profile.get('major') != 'cntt' or profile.get('cohort') != 'K49':
        raise ValueError('CPA² hiện chỉ hỗ trợ ngành CNTT, khóa K49. Không tự đổi ngành hoặc khóa.')
    if profile.get('ctdt', 'cntt_k49') != 'cntt_k49':
        raise ValueError('Chương trình đào tạo chưa được hỗ trợ.')
    sid = profile.get('student_id', '')
    if not isinstance(sid, str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', sid):
        raise ValueError('Mã hồ sơ chỉ gồm chữ, số, dấu gạch ngang và gạch dưới.')
    if not re.fullmatch(r'sv_[a-z0-9_]+', sid):
        profile['student_id'] = 'sv_' + hashlib.sha256(sid.encode()).hexdigest()[:16]
    profile['ctdt'] = 'cntt_k49'
    grades = profile.get('grades')
    if grades is None and isinstance(profile.get('grades_by_code'), dict):
        grades = {code: {'code': code, 'letter_grade': letter,
                         'credits': profile.get('course_credits', {}).get(code)}
                  for code, letter in profile['grades_by_code'].items()}
    if not isinstance(grades, dict) or len(grades) > 250:
        raise ValueError('Bảng điểm phải là danh sách theo mã học phần, tối đa 250 học phần.')
    profile['grades'] = grades
    for code, grade in grades.items():
        if not CODE.fullmatch(code) or code not in COURSES:
            raise ValueError(f'Mã học phần không thuộc CTĐT CNTT K49: {code[:40]}')
        if not isinstance(grade, dict) or grade.get('code', code) != code:
            raise ValueError(f'Bản ghi {code} không hợp lệ hoặc không khớp mã học phần.')
        grade['code'] = code
        if 'letter_grade' in grade:
            grade['letter'] = grade.pop('letter_grade')
            grade.pop('gpa_points', None)
            # Do not invent exact numerical grades from a letter interval.
        if grade.get('credits') is None:
            grade['credits'] = COURSES[code]['tin_chi']
        if grade.get('letter') in ('M', 'W', 'I'):
            grade['diem'] = grade['letter']
    errors = sorted(Draft7Validator(SCHEMA).iter_errors(profile), key=lambda e: str(e.path))
    if errors:
        error = errors[0]
        raise ValueError(f"{'.'.join(map(str, error.path))}: {error.message}")
    # All strings interpolated into ASP must be constrained at this boundary.
    for field in ('khong_tinh_tich_luy',):
        for code in profile.get(field, []):
            if code not in COURSES:
                raise ValueError(f'{field}: mã học phần không hợp lệ.')
    for exemption in profile.get('exemptions', []):
        if exemption['ma_hp'] not in COURSES:
            raise ValueError('Quyết định miễn có mã học phần chưa hỗ trợ.')
    for cert in profile.get('certificates', []):
        if not math.isfinite(cert['diem']) or not 0 <= cert['diem'] <= 10000:
            raise ValueError('Điểm chứng chỉ phải là số hữu hạn trong miền được hỗ trợ.')
        for key in ('loai', 'ngon_ngu'):
            value = cert.get(key)
            if isinstance(value, str) and not SAFE_TEXT.fullmatch(value):
                raise ValueError('Chứng chỉ có giá trị không hợp lệ.')
    for key, maximum in (('da_hoc_nam2', 60), ('tc_cong_nhan', 500), ('tc_diem_f', 500)):
        if profile.get(key) is not None and not 0 <= profile[key] <= maximum:
            raise ValueError(f'{key}: giá trị phải từ 0 đến {maximum}.')
    return profile


def kb_version() -> str:
    digest = hashlib.sha256()
    # Hash the actual runtime inputs, not unrelated probe/test LP files.
    runtime = (
        'w5_rformal/qd3266_r_formal_v1.lp', 'w5_rformal/qd5339_r_formal_v1.lp', 'w5_rformal/r_formal_v1.json',
        'w6_curriculum/curriculum_schema.lp', 'w6_curriculum/curriculum_cntt_k49.lp', 'w6_curriculum/curriculum_cntt_k49.json',
        'w7_student_facts/loader.py', 'w7_student_facts/student_fact_schema.json',
        'w8_elective/elective_solver.lp', 'w9_exemption/exemption_substitution_solver.lp', 'w10_graduation/graduation_solver.lp',
        'w12_integration/prototype.py', 'w14_rag/retriever.py', 'w14_rag/corpus.jsonl', 'w14_rag/grounded_answer.py',
        'w14_rag/retrieval_model_v3.json', 'w14_rag/rag_survey_train_sources_v2.json',
        'w14_rag/corpus_source_v1.jsonl',
        'w14_rag/source_bindings_v1.json',
        'w14_rag/cross_encoder.py', 'w14_rag/prepare_cross_encoder.py',
        'w14_rag/cross_encoder_assets_v1.json', 'w14_rag/retrieval_release_v6.json',
        'w15_ocr/ocr_transcript.py', 'w16_abstention/abstention.py',
        'w18_eligibility/eligibility.py', 'w18_eligibility/eligibility.lp',
        'w19_recommendation/recommendation.py', 'w19_recommendation/recommendation.lp',
    )
    for relative in sorted(runtime):
        path = KB / relative
        digest.update(path.relative_to(KB).as_posix().encode())
        digest.update(path.read_text(encoding='utf-8').encode('utf-8'))
    for name in ('ocr_review.py', 'ocr_input.py', 'worker.py'):
        digest.update(('api/' + name).encode())
        digest.update(Path(__file__).with_name(name).read_text(encoding='utf-8').encode('utf-8'))
    return digest.hexdigest()[:16]
