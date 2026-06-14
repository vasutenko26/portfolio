"""
RAG-ядро: чанкинг документов, клиент эмбеддера, запись/поиск в Qdrant.
Метаданные чанка (filename, page/section) сохраняются для цитат.
"""
import os
import io
import re
import uuid
import logging

import httpx
from pypdf import PdfReader
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

log = logging.getLogger("rag.core")

QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")
EMBEDDER_URL = os.environ.get("EMBEDDER_URL", "http://embedder:8000").rstrip("/")
COLLECTION = os.environ.get("COLLECTION", "documents")
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "900"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "150"))
TOP_K = int(os.environ.get("TOP_K", "5"))
EMBED_TIMEOUT = float(os.environ.get("EMBED_TIMEOUT", "60"))


class EmbedderError(RuntimeError):
    """Эмбеддер недоступен/ошибся."""


class StoreError(RuntimeError):
    """Qdrant недоступен/ошибся."""


_qdrant: QdrantClient | None = None


def qdrant() -> QdrantClient:
    global _qdrant
    if _qdrant is None:
        _qdrant = QdrantClient(url=QDRANT_URL, timeout=30)
    return _qdrant


# ---------- эмбеддинги ----------

def embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    try:
        r = httpx.post(f"{EMBEDDER_URL}/embed", json={"texts": texts}, timeout=EMBED_TIMEOUT)
        r.raise_for_status()
        return r.json()["embeddings"]
    except httpx.HTTPError as e:
        raise EmbedderError(f"embedder unreachable: {e}") from e
    except (KeyError, ValueError) as e:
        raise EmbedderError(f"embedder returned unexpected response: {e}") from e


def embed_dim() -> int:
    try:
        r = httpx.get(f"{EMBEDDER_URL}/healthz", timeout=15)
        r.raise_for_status()
        return int(r.json()["dim"])
    except (httpx.HTTPError, KeyError, ValueError) as e:
        raise EmbedderError(f"embedder healthz failed: {e}") from e


# ---------- коллекция ----------

def ensure_collection(dim: int) -> None:
    try:
        client = qdrant()
        if not client.collection_exists(COLLECTION):
            client.create_collection(
                collection_name=COLLECTION,
                vectors_config=qm.VectorParams(size=dim, distance=qm.Distance.COSINE),
            )
            log.info("created collection %s (dim=%s)", COLLECTION, dim)
    except Exception as e:  # noqa: BLE001 — qdrant client raises various
        raise StoreError(f"qdrant unavailable: {e}") from e


# ---------- чанкинг ----------

def _split(text: str) -> list[str]:
    """Чанки ~CHUNK_SIZE символов с overlap, по возможности по границе пробела."""
    text = re.sub(r"[ \t]+", " ", text).strip()
    if not text:
        return []
    chunks, start, n = [], 0, len(text)
    while start < n:
        end = min(start + CHUNK_SIZE, n)
        if end < n:
            sp = text.rfind(" ", start + CHUNK_SIZE // 2, end)
            if sp != -1:
                end = sp
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= n:
            break
        start = max(end - CHUNK_OVERLAP, start + 1)
    return chunks


def parse_document(filename: str, data: bytes) -> list[dict]:
    """→ список {text, page, section} для файла (PDF / MD / TXT)."""
    name = filename.lower()
    out: list[dict] = []
    if name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        for i, page in enumerate(reader.pages, start=1):
            for chunk in _split(page.extract_text() or ""):
                out.append({"text": chunk, "page": i, "section": None})
    elif name.endswith((".md", ".markdown", ".txt")):
        text = data.decode("utf-8", errors="replace")
        # разбить по заголовкам markdown, секция = текущий заголовок
        section = None
        buf: list[str] = []

        def flush():
            if buf:
                for chunk in _split("\n".join(buf)):
                    out.append({"text": chunk, "page": None, "section": section})

        for line in text.splitlines():
            m = re.match(r"^#{1,6}\s+(.*)", line)
            if m:
                flush()
                buf = []
                section = m.group(1).strip()
            else:
                buf.append(line)
        flush()
    else:
        raise ValueError(f"unsupported file type: {filename} (allowed: pdf, md, txt)")
    return out


# ---------- ingest / поиск ----------

def ingest(filename: str, data: bytes) -> int:
    pieces = parse_document(filename, data)
    if not pieces:
        return 0
    vectors = embed([p["text"] for p in pieces])
    ensure_collection(len(vectors[0]))
    points = [
        qm.PointStruct(
            id=str(uuid.uuid4()),
            vector=vec,
            payload={
                "filename": filename,
                "page": p["page"],
                "section": p["section"],
                "text": p["text"],
            },
        )
        for p, vec in zip(pieces, vectors)
    ]
    try:
        qdrant().upsert(collection_name=COLLECTION, points=points, wait=True)
    except Exception as e:  # noqa: BLE001
        raise StoreError(f"qdrant upsert failed: {e}") from e
    return len(points)


def search(question: str, top_k: int | None = None) -> list[dict]:
    top_k = top_k or TOP_K
    try:
        if not qdrant().collection_exists(COLLECTION):
            return []
    except Exception as e:  # noqa: BLE001
        raise StoreError(f"qdrant unavailable: {e}") from e
    qvec = embed([question])[0]
    try:
        hits = qdrant().search(collection_name=COLLECTION, query_vector=qvec, limit=top_k)
    except Exception as e:  # noqa: BLE001
        raise StoreError(f"qdrant search failed: {e}") from e
    return [
        {
            "text": h.payload.get("text", ""),
            "filename": h.payload.get("filename", "?"),
            "page": h.payload.get("page"),
            "section": h.payload.get("section"),
            "score": round(float(h.score), 4),
        }
        for h in hits
    ]


def stats() -> dict:
    try:
        client = qdrant()
        if not client.collection_exists(COLLECTION):
            return {"documents": 0, "chunks": 0}
        info = client.count(collection_name=COLLECTION, exact=True)
        files = set()
        # собрать уникальные имена файлов (по скроллу payload)
        points, _ = client.scroll(collection_name=COLLECTION, limit=10000, with_payload=["filename"])
        for p in points:
            files.add(p.payload.get("filename"))
        return {"documents": len(files), "chunks": info.count, "files": sorted(f for f in files if f)}
    except Exception as e:  # noqa: BLE001
        raise StoreError(f"qdrant unavailable: {e}") from e
