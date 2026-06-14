# RAG assistant — chat with your documents (self-hosted)

Upload PDF / Markdown / text → ask a question → get an answer **with citations to the
source document and page**. If the answer isn't in your documents, it says so instead
of making something up. Embeddings run **locally** (no paid embedding API); the LLM
provider is configurable, and with Ollama the data never leaves the server at all.

`docker compose up -d` brings up the vector DB, the local embedder and the API+UI.

## What this demonstrates

> **Automation + AI, on the client's own hardware.** Sells: "I'll put a private
> 'chat with your documents' assistant on your server — manuals, policies, contracts —
> answers cite the exact source, and your data stays in-house." Aimed at businesses /
> factories that can't send internal documents to a cloud API.

- A complete **RAG pipeline as code**: ingest → chunk (with overlap) → local embed →
  Qdrant → retrieve top-k → grounded answer with **mandatory source citations**.
- **Data residency**: embeddings are self-hosted (sentence-transformers); choose a
  local LLM (Ollama) for a fully on-prem, no-egress deployment.
- **Honest answers**: out-of-corpus questions return "not found", not a hallucination.
- Production hygiene: clear error surfaces when a dependency is down, least-privilege
  containers, no internal ports exposed, TLS-only via Caddy.

## Architecture

```
 browser ──TLS──► Caddy ──► rag-app (FastAPI + web UI)
                              ├─► embedder  (sentence-transformers, local)
                              ├─► qdrant    (vector DB)
                              └─► LLM        (gemini | openai | ollama, via env)
```

| Service | Role | Exposed |
|---|---|---|
| `app` | FastAPI: `/api/ingest`, `/api/query`, serves the chat UI | via Caddy only |
| `embedder` | local sentence-transformers embeddings (`all-MiniLM-L6-v2`, 384-d) | internal |
| `qdrant` | vector store with per-chunk metadata (filename, page/section) | internal |

The LLM is **not** a container by default — it's whatever `LLM_PROVIDER` points at.
Embeddings are always local, so indexing never sends your text anywhere.

## Data residency / LLM choice

| `LLM_PROVIDER` | Where the question + retrieved context go |
|---|---|
| `ollama` | **nowhere external** — fully on-prem (recommended for sensitive docs) |
| `gemini` / `openai` | retrieved snippets are sent to that API for generation only |

Embeddings and the documents themselves are **always** processed locally. For an
air-gapped install, run Ollama (`OLLAMA_BASE_URL`, `OLLAMA_MODEL`) and nothing leaves
the box.

## Endpoints

- `POST /api/ingest` — multipart file (`.pdf`, `.md`, `.txt`); chunks + indexes it.
- `POST /api/query` — `{"question": "..."}` → `{found, answer, sources[]}`; the answer
  carries inline `[n]` markers that map to `sources[n]` (filename + page/section + snippet).
- `GET /api/stats` — indexed documents / chunk count.
- `GET /healthz` — liveness + active LLM provider/model.

## Run

Prereqs: the main `portfolio` stack is up (owns `portfolio_internal` + Caddy); for
public access, a DNS record for `rag.davidvasutenko.fun` points here.

```bash
cp .env.example .env          # set LLM_PROVIDER + the matching key (e.g. GEMINI_API_KEY)
docker compose up -d          # qdrant + local embedder + app/UI (embedder warms up ~1 min)

# publish via Caddy (block already in the repo-root Caddyfile):
docker compose -p portfolio restart caddy
```

Open `https://rag.davidvasutenko.fun`, drop in a couple of PDFs, ask away.

## Caddy

```caddy
rag.davidvasutenko.fun {
	encode zstd gzip
	header { -Server; Strict-Transport-Security "max-age=31536000;"; X-Content-Type-Options "nosniff" }
	request_body { max_size 30MB }
	reverse_proxy rag-app:8000
}
```

## Configuration (`.env`)

| Var | Default | Notes |
|---|---|---|
| `LLM_PROVIDER` | `gemini` | `gemini` \| `openai` \| `ollama` |
| `EMBED_MODEL` | `all-MiniLM-L6-v2` | local embedding model (baked into the embedder image) |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `900` / `150` | characters |
| `TOP_K` | `5` | retrieved chunks per question |
| `MAX_UPLOAD_MB` | `25` | upload cap |

## Security model

- Only `app` is reachable from outside, and only through Caddy/TLS. `qdrant` and
  `embedder` publish **no host ports** (internal `rag` network).
- Containers run as a non-root user; secrets (LLM keys) come from the gitignored `.env`.
- Errors are explicit (`503` embedder/vector-store down, `502` LLM error, `400/413/422`
  bad input) — the service never fails silently.
