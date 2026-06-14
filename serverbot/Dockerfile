FROM python:3.12-slim

# util-linux → nsenter (вход в namespace хоста для сбора серверного отчёта от root)
# tzdata    → ZoneInfo('Europe/Kyiv'); ca-certificates → httpx по HTTPS
RUN apt-get update && apt-get install -y --no-install-recommends \
        util-linux tzdata ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY serverbot.py .

# Контейнер работает от root намеренно: nsenter -t 1 требует CAP_SYS_ADMIN (privileged)
CMD ["python", "serverbot.py"]
