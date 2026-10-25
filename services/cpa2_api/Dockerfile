# Dịch vụ cpa2_api (FastAPI + clingo + Tesseract tiếng Việt). Build từ GỐC repo:
#   docker build -f services/cpa2_api/Dockerfile -t cpa2-api .
# Chạy:  docker run -p 8000:8000 -e CPA2_API_KEY=... cpa2-api      (KHÔNG đặt khoá vào image)
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 \
    CPA2_ROOT=/app/CPA2_KhaoSat CPA2_WORKERS=2 CPA2_WORKERS_OCR=1 CPA2_RAM_MB=4096 OMP_THREAD_LIMIT=1

# Tesseract + gói ngôn ngữ Việt (OCR bảng điểm). Số liệu OCR đổi theo phiên bản Tesseract (Bài học Tuần 15): chỉ so sánh trước/sau
# trên CÙNG môi trường. Chưa build được image trong môi trường phát triển (không có Docker daemon) — xem README.
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-vie tini \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY services/cpa2_api/requirements.lock /app/requirements.lock
RUN pip install --no-cache-dir -r /app/requirements.lock

# Tri thức: chỉ các thư mục cần cho suy diễn / truy hồi / OCR (không kèm báo cáo, dữ liệu thu thập, kết quả benchmark)
COPY CPA2_KhaoSat/w5_rformal /app/CPA2_KhaoSat/w5_rformal
COPY CPA2_KhaoSat/w6_curriculum /app/CPA2_KhaoSat/w6_curriculum
COPY CPA2_KhaoSat/w7_student_facts /app/CPA2_KhaoSat/w7_student_facts
COPY CPA2_KhaoSat/w8_elective /app/CPA2_KhaoSat/w8_elective
COPY CPA2_KhaoSat/w9_exemption /app/CPA2_KhaoSat/w9_exemption
COPY CPA2_KhaoSat/w10_graduation /app/CPA2_KhaoSat/w10_graduation
COPY CPA2_KhaoSat/w11_proof /app/CPA2_KhaoSat/w11_proof
COPY CPA2_KhaoSat/w12_integration /app/CPA2_KhaoSat/w12_integration
COPY CPA2_KhaoSat/w14_rag /app/CPA2_KhaoSat/w14_rag
COPY CPA2_KhaoSat/w15_ocr /app/CPA2_KhaoSat/w15_ocr
COPY CPA2_KhaoSat/w16_abstention /app/CPA2_KhaoSat/w16_abstention
COPY CPA2_KhaoSat/w18_eligibility /app/CPA2_KhaoSat/w18_eligibility
COPY CPA2_KhaoSat/w19_recommendation /app/CPA2_KhaoSat/w19_recommendation
COPY services/cpa2_api/cpa2_api /app/cpa2_api

# Chạy bằng người dùng không đặc quyền
RUN useradd --create-home --uid 10001 cpa2
USER cpa2

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4).status==200 else 1)"
# Một tiến trình uvicorn; việc nặng (clingo, OCR) chạy trong CPA2_WORKERS tiến trình con có giới hạn thời gian cứng (tien_trinh.py).
# KHÔNG dùng --limit-concurrency: nó tính cả kết nối nhàn rỗi/treo và từ chối 503 cả /health lẫn yêu cầu hợp lệ. Quá tải được xử lý ở bể
# tiến trình (qua_tai sau 5s). Chống kết nối treo: --timeout-keep-alive ở đây, thời gian chờ đọc header/body đặt ở reverse proxy của nền tảng.
# Giới hạn bộ nhớ: mỗi tiến trình con tự giới hạn RLIMIT_AS (CPA2_RAM_MB, mặc định 4096); đặt giới hạn RAM của container
# ≥ (CPA2_WORKERS + CPA2_WORKERS_OCR) × ~1,5 GB + 0,5 GB (xem README).
# tini làm PID 1: dọn zombie (tesseract cháu bị giết cả nhóm khi hết giờ sẽ được nhận làm con của PID 1 — uvicorn không gặt chúng).
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["uvicorn", "cpa2_api.main:tao_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "5"]
