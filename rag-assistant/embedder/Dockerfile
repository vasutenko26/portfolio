FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/models \
    EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2

# CPU-only torch (без CUDA — меньше образ, не нужен GPU)
RUN pip install torch==2.3.1 --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install -r requirements.txt

# Модель вшивается в образ → офлайн-репродьюсибилити, текст не уходит наружу.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('${EMBED_MODEL}')"

COPY server.py .

RUN useradd -u 10001 -m bot && chown -R bot /models
USER bot

EXPOSE 8000
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
