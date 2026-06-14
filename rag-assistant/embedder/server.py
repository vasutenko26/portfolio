#!/usr/bin/env python3
"""
Self-hosted эмбеддер на sentence-transformers. Без платных API: модель крутится
локально, текст не покидает сервер. Отдаёт нормализованные векторы (cosine = dot).
"""
import os
import logging

from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("embedder")

MODEL_NAME = os.environ.get("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
log.info("loading model %s", MODEL_NAME)
model = SentenceTransformer(MODEL_NAME)
DIM = model.get_sentence_embedding_dimension()
log.info("model ready, dim=%s", DIM)

app = FastAPI(title="RAG embedder")


class EmbedRequest(BaseModel):
    texts: list[str]


@app.get("/healthz")
def healthz():
    return {"status": "ok", "model": MODEL_NAME, "dim": DIM}


@app.post("/embed")
def embed(req: EmbedRequest):
    vectors = model.encode(
        req.texts,
        normalize_embeddings=True,
        batch_size=32,
        show_progress_bar=False,
    ).tolist()
    return {"embeddings": vectors, "dim": DIM}
