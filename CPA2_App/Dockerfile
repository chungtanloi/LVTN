FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONIOENCODING=utf-8 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-vie tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY CPA2_App/api/requirements.lock /app/requirements.txt
RUN pip install -r requirements.txt
COPY CPA2_App/api/cpa2_api /app/CPA2_App/api/cpa2_api
# Copy only runtime KB and code, never the legacy DB, transcripts or .env.
COPY CPA2_KhaoSat/w5_rformal/*.lp CPA2_KhaoSat/w5_rformal/r_formal_v1.json /app/CPA2_KhaoSat/w5_rformal/
COPY CPA2_KhaoSat/w6_curriculum/*.lp CPA2_KhaoSat/w6_curriculum/*.json /app/CPA2_KhaoSat/w6_curriculum/
COPY CPA2_KhaoSat/w7_student_facts/loader.py CPA2_KhaoSat/w7_student_facts/student_fact_schema.json /app/CPA2_KhaoSat/w7_student_facts/
COPY CPA2_KhaoSat/w7_student_facts/students/*.json /app/CPA2_KhaoSat/w7_student_facts/students/
COPY CPA2_KhaoSat/w8_elective/*.lp /app/CPA2_KhaoSat/w8_elective/
COPY CPA2_KhaoSat/w9_exemption/*.lp /app/CPA2_KhaoSat/w9_exemption/
COPY CPA2_KhaoSat/w10_graduation/*.lp /app/CPA2_KhaoSat/w10_graduation/
COPY CPA2_KhaoSat/w11_proof/*.py CPA2_KhaoSat/w11_proof/*.json /app/CPA2_KhaoSat/w11_proof/
COPY CPA2_KhaoSat/w12_integration/prototype.py /app/CPA2_KhaoSat/w12_integration/
COPY CPA2_KhaoSat/w14_rag/grounded_answer.py CPA2_KhaoSat/w14_rag/retriever.py CPA2_KhaoSat/w14_rag/corpus.jsonl /app/CPA2_KhaoSat/w14_rag/
COPY CPA2_KhaoSat/w15_ocr/ocr_transcript.py /app/CPA2_KhaoSat/w15_ocr/
COPY CPA2_KhaoSat/w16_abstention/abstention.py /app/CPA2_KhaoSat/w16_abstention/
COPY CPA2_KhaoSat/w18_eligibility/eligibility.py CPA2_KhaoSat/w18_eligibility/*.lp /app/CPA2_KhaoSat/w18_eligibility/
COPY CPA2_KhaoSat/w19_recommendation/recommendation.py CPA2_KhaoSat/w19_recommendation/*.lp /app/CPA2_KhaoSat/w19_recommendation/
RUN useradd --create-home cpa2
USER cpa2
WORKDIR /app/CPA2_App/api
EXPOSE 8000
CMD ["sh", "-c", "uvicorn cpa2_api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
