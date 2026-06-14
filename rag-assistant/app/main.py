"""
RAG-ассистент «чат с документами». FastAPI: загрузка документов, вопрос → ответ
СО ССЫЛКАМИ на источник. Если ответа в документах нет — честно «не нашёл».
"""
import os
import re
import logging

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import rag
import llm

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("rag.api")

MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "25"))

SYSTEM_PROMPT = (
    "Ты — ассистент, который отвечает СТРОГО по предоставленным фрагментам документов. "
    "Используй только информацию из фрагментов ниже — никаких внешних знаний и догадок. "
    "Каждый фрагмент помечен номером вида [1], [2]. В ответе обязательно ссылайся на "
    "использованные фрагменты этими метками. Отвечай на языке вопроса. "
    "Если ответа во фрагментах НЕТ — верни ровно одну строку: NO_ANSWER"
)

app = FastAPI(title="RAG assistant — chat with your documents")


class QueryRequest(BaseModel):
    question: str
    top_k: int | None = None


def _cite(src: dict) -> str:
    loc = f"p.{src['page']}" if src.get("page") else (src.get("section") or "")
    return f"{src['filename']}" + (f" — {loc}" if loc else "")


@app.get("/healthz")
def healthz():
    return {"status": "ok", **llm.provider_info()}


@app.get("/api/stats")
def stats():
    try:
        return rag.stats()
    except rag.StoreError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/ingest")
async def ingest(file: UploadFile = File(...)):
    data = await file.read()
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"file too large (> {MAX_UPLOAD_MB} MB)")
    try:
        n = rag.ingest(file.filename, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except rag.EmbedderError as e:
        raise HTTPException(status_code=503, detail=f"embedder error: {e}")
    except rag.StoreError as e:
        raise HTTPException(status_code=503, detail=f"vector store error: {e}")
    if n == 0:
        raise HTTPException(status_code=422, detail="no extractable text in document")
    return {"filename": file.filename, "chunks": n}


@app.post("/api/query")
def query(req: QueryRequest):
    question = (req.question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="empty question")

    try:
        hits = rag.search(question, req.top_k)
    except rag.EmbedderError as e:
        raise HTTPException(status_code=503, detail=f"embedder error: {e}")
    except rag.StoreError as e:
        raise HTTPException(status_code=503, detail=f"vector store error: {e}")

    if not hits:
        return {"found": False, "answer": "Не нашёл ответа в загруженных материалах.", "sources": []}

    context = "\n\n".join(
        f"[{i}] (источник: {_cite(h)})\n{h['text']}" for i, h in enumerate(hits, start=1)
    )
    user = f"Фрагменты:\n{context}\n\nВопрос: {question}"

    try:
        answer = llm.generate(SYSTEM_PROMPT, user)
    except llm.LLMError as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")

    if answer.strip().upper().startswith("NO_ANSWER") or not answer.strip():
        return {"found": False, "answer": "Не нашёл ответа в загруженных материалах.", "sources": []}

    # цитаты: какие метки [n] реально использованы в ответе
    used = {int(m) for m in re.findall(r"\[(\d+)\]", answer) if 1 <= int(m) <= len(hits)}
    if used:
        sources = [
            {"n": i, "label": _cite(hits[i - 1]), "snippet": hits[i - 1]["text"],
             "filename": hits[i - 1]["filename"], "page": hits[i - 1]["page"],
             "section": hits[i - 1]["section"], "score": hits[i - 1]["score"]}
            for i in sorted(used)
        ]
    else:
        # модель не проставила метки — показываем топ-результаты как источники
        sources = [
            {"n": i, "label": _cite(h), "snippet": h["text"], "filename": h["filename"],
             "page": h["page"], "section": h["section"], "score": h["score"]}
            for i, h in enumerate(hits, start=1)
        ]
    return {"found": True, "answer": answer, "sources": sources}


@app.exception_handler(Exception)
async def unhandled(_request, exc: Exception):
    log.exception("unhandled error")
    return JSONResponse(status_code=500, content={"detail": f"internal error: {exc}"})


# Статический веб-чат (отдаётся этим же сервисом).
app.mount("/", StaticFiles(directory="static", html=True), name="static")
