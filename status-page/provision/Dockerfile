FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY provision.py monitors.yml ./

# дроп до непривилегированного пользователя
RUN useradd -u 10001 -m bot
USER bot

CMD ["python", "provision.py"]
