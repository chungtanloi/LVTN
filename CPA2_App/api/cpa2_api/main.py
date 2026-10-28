import asyncio
import hmac
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import warnings
from typing import Annotated

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import JSONResponse
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field

from .profiles import KB, CURRICULUM, kb_version, normalize

security = HTTPBearer(auto_error=False)
VERSION = kb_version()
CAPACITY = asyncio.Semaphore(2)
Image.MAX_IMAGE_PIXELS = 20_000_000


async def authorized(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)]):
    key = os.environ.get('CPA2_SERVICE_KEY', '')
    if not key:
        raise HTTPException(503, 'Dịch vụ chưa cấu hình khóa truy cập.')
    if not credentials or not hmac.compare_digest(credentials.credentials, key):
        raise HTTPException(401, 'Không được phép truy cập.')


app = FastAPI(title='CPA² Academic Advising API', version='0.1.0')


@app.middleware('http')
async def limit_body(request, call_next):
    limit = 21 * 1024 * 1024 if request.url.path == '/v1/ocr' else 1024 * 1024
    if request.method in ('POST', 'PUT', 'PATCH'):
        chunks, size = [], 0
        async for chunk in request.stream():
            size += len(chunk)
            if size > limit:
                return JSONResponse({'detail': 'Dữ liệu gửi lên vượt kích thước cho phép.'}, status_code=413)
            chunks.append(chunk)
        request._body = b''.join(chunks)
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


class ProfileRequest(BaseModel):
    profile: dict


class AdviceRequest(ProfileRequest):
    question: str = Field(min_length=1, max_length=2000)


class LookupRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class RecommendationRequest(ProfileRequest):
    semester: int = Field(ge=1, le=3)


def validate(profile):
    try:
        return normalize(profile)
    except (ValueError, TypeError, KeyError) as error:
        raise HTTPException(422, str(error)) from None


async def run(operation, payload, timeout=30):
    async with CAPACITY:
        env = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
        process = await asyncio.create_subprocess_exec(
            sys.executable, '-m', 'cpa2_api.worker',
            cwd=Path(__file__).resolve().parents[1], env=env,
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        try:
            out, _ = await asyncio.wait_for(process.communicate(json.dumps({'operation': operation, 'payload': payload}).encode()), timeout)
        except (asyncio.TimeoutError, asyncio.CancelledError) as error:
            if process.returncode is None:
                process.kill()
            await process.communicate()
            if isinstance(error, asyncio.CancelledError):
                raise
            raise HTTPException(504, 'Tác vụ quá thời gian xử lý. Hãy giảm số dữ kiện chưa chắc và thử lại.') from None
        try:
            message = json.loads(out)
        except (ValueError, UnicodeError):
            raise HTTPException(502, 'Dịch vụ suy luận trả dữ liệu không hợp lệ.') from None
        if not message.get('ok'):
            if message.get('error_type') == 'OcrInputError':
                raise HTTPException(422, 'PDF không hợp lệ, bị khóa hoặc vượt giới hạn tổng 4 trang / 20 triệu điểm ảnh mỗi trang.')
            raise HTTPException(502, 'Không thể hoàn tất xử lý. Hãy kiểm tra đầu vào hoặc môi trường OCR.')
        return {**message['result'], 'kb_version': VERSION}


@app.get('/health')
def health():
    return {'app': 'CPA²', 'status': 'ok', 'kb_version': VERSION}


@app.get('/v1/catalog', dependencies=[Depends(authorized)])
def catalog():
    return {'meta': CURRICULUM['meta'], 'courses': CURRICULUM['hoc_phan'], 'kb_version': VERSION}


@app.get('/v1/demo-profiles', dependencies=[Depends(authorized)])
def demos():
    names = {'sv_lvtn': 'Hồ sơ xét luận văn', 'sv_tltn': 'Hồ sơ tiểu luận', 'sv_mien_ielts': 'Hồ sơ có IELTS', 'sv_du_hp': 'Hồ sơ đủ học phần', 'sv_5hp': 'Hồ sơ đầu khóa'}
    # These are synthetic demo scenarios, explicitly declaring no transferred credits.
    # Raw imported profiles do not receive this default.
    return [{'id': sid, 'name': name, 'profile': {**json.loads((KB / f'w7_student_facts/students/{sid}.json').read_text(encoding='utf-8')), 'tc_cong_nhan': 0}} for sid, name in names.items()]


@app.post('/v1/profiles/validate', dependencies=[Depends(authorized)])
def validate_profile(request: ProfileRequest):
    return {'profile': validate(request.profile), 'kb_version': VERSION}


@app.post('/v1/advice', dependencies=[Depends(authorized)])
async def advice(request: AdviceRequest):
    return await run('advice', {'question': request.question, 'profile': validate(request.profile)})


@app.post('/v1/lookup', dependencies=[Depends(authorized)])
async def lookup(request: LookupRequest):
    return await run('lookup', request.model_dump())


@app.post('/v1/recommendations', dependencies=[Depends(authorized)])
async def recommend(request: RecommendationRequest):
    return await run('recommendations', {'profile': validate(request.profile), 'semester': request.semester})


@app.post('/v1/ocr', dependencies=[Depends(authorized)])
async def ocr(files: Annotated[list[UploadFile], File()]):
    if not 1 <= len(files) <= 4:
        raise HTTPException(422, 'Chọn PDF hoặc ảnh PNG/JPEG, tổng tối đa 4 trang theo thứ tự.')
    with tempfile.TemporaryDirectory(prefix='cpa2-ocr-') as directory:
        paths, total = [], 0
        for index, upload in enumerate(files):
            data = await upload.read(10 * 1024 * 1024 + 1)
            total += len(data)
            if len(data) > 10 * 1024 * 1024 or total > 20 * 1024 * 1024:
                raise HTTPException(413, 'Mỗi tệp tối đa 10 MB, tổng tối đa 20 MB.')
            if data.startswith(b'%PDF-'):
                path = Path(directory) / f'input-{index}.pdf'
                path.write_bytes(data)
                paths.append(str(path))
                continue
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter('error', Image.DecompressionBombWarning)
                    with Image.open(io.BytesIO(data)) as image:
                        if image.format not in ('PNG', 'JPEG'):
                            raise ValueError('Unsupported image')
                        image.verify()
            except (UnidentifiedImageError, ValueError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
                raise HTTPException(422, 'Ảnh không hợp lệ hoặc vượt quá 20 triệu điểm ảnh.') from None
            path = Path(directory) / f'page-{index}.png'
            path.write_bytes(data)
            paths.append(str(path))
        return await run('ocr', {'paths': paths}, timeout=120)
