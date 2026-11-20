"""Verify Clerk -> Convex -> Render with disposable, synthetic test accounts.

Run from CPA2_App/web after pulling Clerk env vars. Credentials never leave the
ignored environment files or request headers. --cleanup removes only accounts
whose exact test email matches the private state created by this script.
"""
import argparse
import io
import json
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parent
WEB = APP / 'web'
STATE = WEB / '.vercel/cloud-qa.json'
CONVEX = 'https://exciting-cheetah-606.convex.cloud'


def env_values(path):
    values = {}
    for line in Path(path).read_text(encoding='utf-8-sig').splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            key, value = line.split('=', 1)
            values[key] = value.strip().strip('"')
    return values


def http(url, data=None, token=None, method=None):
    headers = {'Content-Type': 'application/json', 'User-Agent': 'CPA2-Cloud-QA/0.1', 'Accept': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    request = urllib.request.Request(url, data=None if data is None else json.dumps(data).encode(), headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=50) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        # Do not print full request headers, JWTs, or service keys.
        detail = error.read().decode()
        try:
            errors = json.loads(detail).get('errors', [])
            detail = '; '.join(str(item.get('code', '')) + ': ' + str(item.get('message', '')) for item in errors)
        except ValueError:
            detail = 'HTTP request failed'
        raise RuntimeError(f'HTTP {error.code}: {detail[:400]}') from None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cleanup', action='store_true')
    parser.add_argument('--ocr', action='store_true')
    parser.add_argument('--pdf', action='store_true', help='Verify a full synthetic PDF through cloud OCR.')
    parser.add_argument('--env-file', default=str(WEB / '.env.clerk.production'))
    args = parser.parse_args()
    key = env_values(args.env_file)['CLERK_SECRET_KEY']
    if not key.startswith('sk_test_'):
        raise RuntimeError('This QA script is restricted to a Clerk test instance.')

    def clerk(path, data=None, method=None):
        return http('https://api.clerk.com/v1' + path, data, key, method)

    def call(kind, function, payload, user=None):
        jwt = clerk(f"/sessions/{user['session']}/tokens/convex", {})['jwt'] if user else None
        return http(CONVEX + '/api/' + kind, {'path': 'cpa2:' + function, 'args': payload, 'format': 'json'}, jwt)

    def success(kind, function, payload, user):
        result = call(kind, function, payload, user)
        if result.get('status') != 'success':
            raise RuntimeError(f'{function} failed: {result.get("errorMessage", "unknown error")[:500]}')
        return result.get('value')

    if args.ocr or args.pdf:
        state = json.loads(STATE.read_text())
        alice = state['users'][0]
        sys.path.insert(0, str(ROOT / 'CPA2_KhaoSat/w15_ocr'))
        from render_transcript import render
        sample = json.loads((ROOT / 'CPA2_KhaoSat/w7_student_facts/students/sv_lvtn.json').read_text(encoding='utf-8'))
        pages = render(sample)
        buffer = io.BytesIO()
        if args.pdf:
            pages[0].save(buffer, format='PDF', save_all=True, append_images=pages[1:], resolution=144)
            (WEB / '.vercel/qa-transcript.pdf').write_bytes(buffer.getvalue())
        else:
            pages[0].save(buffer, format='PNG')
        content_type = 'application/pdf' if args.pdf else 'image/png'
        upload_url = success('mutation', 'uploadUrl', {'consent': True}, alice)
        request = urllib.request.Request(upload_url, data=buffer.getvalue(), headers={'Content-Type': content_type}, method='POST')
        with urllib.request.urlopen(request, timeout=30) as response:
            storage_id = json.load(response)['storageId']
        job_id = success('mutation', 'startOcr', {'storageIds': [storage_id]}, alice)
        previous = None
        for attempt in range(60):
            own = success('query', 'state', {}, alice)
            job = next((job for job in own['uploads'] if job['_id'] == job_id), None)
            status = job['status'] if job else 'missing'
            if status != previous:
                print('Cloud OCR status:', status, flush=True)
                previous = status
            if status == 'error':
                raise RuntimeError('Cloud OCR failed: ' + job.get('error', 'unknown error'))
            if status == 'done':
                result = job['result']
                if not result['needs_review'] or not result['profile']['meta']['ocr_pending'] or not result['report']['tong_dong']:
                    raise RuntimeError('Cloud OCR did not preserve a nonempty draft for review.')
                from ocr_transcript import so_khop
                correct, accepted, wrong = so_khop(result['profile'], sample)
                if not accepted or correct / accepted < .99:
                    raise RuntimeError(f'Cloud OCR accepted facts below 99% correctness: {wrong}')
                print(f'PASS: {content_type}, {len(pages) if args.pdf else 1} page(s), Convex Storage -> scheduled OCR -> Render -> review draft; rows: {result["report"]["tong_dong"]}, correct facts: {correct}/{accepted}, KB: {result.get("kb_version")}')
                return
            time.sleep(5)
        raise RuntimeError('Cloud OCR did not complete in the verification window.')

    if args.cleanup:
        if not STATE.exists():
            print('No cloud QA accounts to clean up.')
            return
        state = json.loads(STATE.read_text())
        for user in state['users']:
            account = clerk('/users/' + user['id'])
            expected = user['email']
            if not expected.startswith('cpa2_qa_') or '+clerk_test@' not in expected or not any(email['email_address'] == expected for email in account.get('email_addresses', [])):
                raise RuntimeError('Refusing to delete an account not created for CPA2 QA.')
            success('mutation', 'eraseData', {}, user)
            remaining = success('query', 'state', {}, user)
            if remaining['profile'] is not None or remaining['messages'] or remaining['uploads']:
                raise RuntimeError('Owner data remained after eraseData.')
            clerk('/users/' + user['id'], method='DELETE')
        STATE.unlink()
        print('PASS: synthetic Clerk accounts and their Convex data removed.')
        return

    if STATE.exists():
        raise RuntimeError('Clean up the previous QA state before creating more test accounts.')
    state = {'users': [], 'convex': CONVEX}
    STATE.parent.mkdir(exist_ok=True)
    for name in ('alice', 'bob'):
        email = f'cpa2_qa_{name}_{int(time.time())}+clerk_test@example.com'
        account = clerk('/users', {'email_address': [email], 'skip_password_requirement': True})
        user = {'id': account['id'], 'email': email}
        state['users'].append(user)
        STATE.write_text(json.dumps(state), encoding='utf-8')
        session = clerk('/sessions', {'user_id': account['id']})
        user['session'] = session['id']
        STATE.write_text(json.dumps(state), encoding='utf-8')
    alice, bob = state['users']

    anonymous = call('query', 'state', {})
    if anonymous.get('status') == 'success':
        raise RuntimeError('Anonymous access unexpectedly succeeded.')
    print('PASS: anonymous profile access rejected.')
    profile = {**json.loads((ROOT / 'CPA2_KhaoSat/w7_student_facts/students/sv_lvtn.json').read_text(encoding='utf-8')), 'tc_cong_nhan': 0}
    refused = call('action', 'saveProfile', {'profile': profile, 'consent': False}, alice)
    if refused.get('status') == 'success':
        raise RuntimeError('Profile was saved without consent.')
    print('PASS: explicit consent required.')
    saved = success('action', 'saveProfile', {'profile': profile, 'consent': True}, alice)
    if saved['revision'] != 1:
        raise RuntimeError('Expected first profile revision.')
    answer = success('action', 'advise', {'question': 'Em đủ điều kiện tốt nghiệp chưa?'}, alice)
    if answer['result']['verdict'] != 'TRUE' or not answer['result']['certificate']['proof']['steps']:
        raise RuntimeError('Expected a proved graduation answer.')
    certificate = answer['result']['certificate']
    proof = certificate['proof']
    if (len(proof['steps']) <= 20 or proof['steps'][0]['atom'] != certificate['claim']
            or proof.get('truncated') is not False or certificate['grounding']['khong_nguon']
            or any(not step.get('passage_id') for step in proof['steps'])):
        raise RuntimeError('Expected the full claim-first source trace with every step grounded.')
    print('PASS: Clerk JWT -> Convex action -> Render solver -> proof -> stored answer.')
    other = success('query', 'state', {}, bob)
    if other['profile'] is not None or other['messages']:
        raise RuntimeError('Cross-account data leak.')
    success('mutation', 'eraseData', {}, bob)
    own = success('query', 'state', {}, alice)
    if own['profile'] is None or len(own['messages']) != 1:
        raise RuntimeError('Another account erased the owner data.')
    print('PASS: separate accounts cannot read or erase each other data.')
    updated = success('action', 'saveProfile', {'profile': {**profile, 'tc_diem_f': 0}, 'consent': True}, alice)
    own = success('query', 'state', {}, alice)
    if updated['revision'] != 2 or own['messages'][0]['revision'] != 1:
        raise RuntimeError('Profile update changed historical provenance.')
    print('PASS: immutable historical profile revision.')
    unknown = success('action', 'advise', {'question': 'Học phí bao nhiêu?'}, alice)
    if unknown['result']['verdict'] != 'UNKNOWN' or unknown['result']['claim'] != 'khong_ro':
        raise RuntimeError('Out-of-scope question incorrectly answered.')
    print('PASS: unsupported question stays UNKNOWN.')
    # C26/C20: HP LLCT chương trình cũ (QĐ5339 Đ3 k9) chỉ để xét công nhận; cần quyết định (Đ2 k6)
    old = json.loads(json.dumps(profile))
    for code in ('ML016', 'ML018', 'ML019'):
        old['grades'].pop(code, None)
    old['grades']['ML010'] = {'code': 'ML010', 'credits': 3, 'thang10': 80, 'letter': 'B+', 'status': 'passed'}
    success('action', 'saveProfile', {'profile': old, 'consent': True}, alice)
    question = 'Kỳ này em đăng ký ML019 được không?'
    answer = success('action', 'advise', {'question': question}, alice)
    if answer['result']['verdict'] != 'FALSE':
        raise RuntimeError(f'C20: recognition without a decision gave {answer["result"]["verdict"]}.')
    decided = {**old, 'exemptions': [{'ma_hp': 'ML016', 'quyet_dinh': True}, {'ma_hp': 'ML018', 'quyet_dinh': True}]}
    success('action', 'saveProfile', {'profile': decided, 'consent': True}, alice)
    answer = success('action', 'advise', {'question': question}, alice)
    if answer['result']['verdict'] != 'TRUE':
        raise RuntimeError(f'C20: recognition with a decision gave {answer["result"]["verdict"]}.')
    print('PASS: C26 old LLCT course saved; C20 recognition needs a decision (FALSE -> TRUE).')
    for code in ('TC025', 'CT999'):
        bad = {**profile, 'grades': {**profile['grades'], code: {'code': code, 'credits': 1, 'thang10': 90, 'letter': 'A', 'status': 'passed'}}}
        if call('action', 'saveProfile', {'profile': bad, 'consent': True}, alice).get('status') == 'success':
            raise RuntimeError(f'Out-of-curriculum code {code} was accepted.')
    print('PASS: other out-of-curriculum codes (TC025, CT999) still rejected.')
    # Tuần 24 (34aa001): mục tiêu hạng + so sánh hình thức cuối khoá + bản sửa gắn nguồn bước w18. Hồ sơ giả lập sv_lvtn bỏ
    # CT550E, khai báo không F / không kỷ luật cấp Trường. Mục tiêu giỏi với 18 TC: N = 3940, D = 125 →
    # S = ⌈(320·143 − 39400)/10⌉ = 636 → trung bình tối thiểu 3,54.
    time.sleep(65)   # giới hạn tần suất của ứng dụng: 10 yêu cầu/phút/tài khoản (convex takeQuota) — các ca trên đã dùng hết
    w24 = {**profile, 'tc_diem_f': 0, 'ky_luat_canh_cao_cap_truong': False,
           'grades': {k: v for k, v in profile['grades'].items() if k != 'CT550E'}}
    success('action', 'saveProfile', {'profile': w24, 'consent': True}, alice)
    for question, verdict, text in (
            ('Kỳ tới em học 18 tín chỉ thì cần trung bình bao nhiêu để tốt nghiệp loại giỏi?', 'TRUE', '3,54'),
            ('Em nên làm luận văn hay tiểu luận?', 'TRUE', 'lựa chọn là của bạn'),
            ('Em đủ điều kiện làm luận văn chưa?', 'TRUE', None)):
        result = success('action', 'advise', {'question': question}, alice)['result']
        steps = result.get('certificate', {}).get('proof', {}).get('steps', [])
        if (result['verdict'] != verdict or (text and text not in result.get('explanation_vi', ''))
                or not result.get('nguon') or any(not s.get('passage_id') for s in steps)):
            raise RuntimeError(f'W24 {question!r}: {result.get("verdict")} {result.get("grounding_errors")} '
                               f'{result.get("explanation_vi", "")[:120]!r}')
    print('PASS: W24 target rank (3,54 over 18 TC), thesis/essay comparison and thesis eligibility are grounded on cloud.')
    print('QA state retained privately for browser checks. Run --cleanup afterwards.')


if __name__ == '__main__':
    main()
