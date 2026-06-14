FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY exporter.py .

# непривилегированный пользователь; доступ к docker.sock — через supplementary
# группу docker (group_add в compose), сокет монтируется read-only.
RUN useradd -u 10001 -m bot
USER bot

EXPOSE 9101
CMD ["python", "exporter.py"]
