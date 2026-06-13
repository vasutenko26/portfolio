FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY assistant.py .

# дроп до непривилегированного пользователя; /data монтируется томом
RUN useradd -u 10001 -m bot && mkdir -p /data && chown bot:bot /data
USER bot

CMD ["python", "assistant.py"]
