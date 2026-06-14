# Case — Self-hosted RAG assistant ("chat with your documents")

> Subheading proof: **answers cite the exact document + page · out-of-corpus → "not found", no hallucination · embeddings 100% local · Ollama option = zero data egress**

## 01 — Brief

Businesses and factories sit on piles of internal documents — equipment manuals, HS&E
policies, contracts — that nobody wants to paste into a public chatbot. The brief: a
self-hosted "chat with your documents" assistant. Upload PDFs/Markdown, ask in plain
language, get an answer that **links back to the source**, and keep the data on the
client's own server.

## 02 — What I did

- Built the full **RAG pipeline**: ingest → chunk with overlap → embed → store in
  **Qdrant** with per-chunk metadata (filename, page) → retrieve top-k → grounded LLM
  answer with **mandatory `[n]` citations** mapped to the exact source snippet.
- **Local embeddings** (sentence-transformers `all-MiniLM-L6-v2`, baked into the
  embedder image) — no paid embedding API, indexing text never leaves the box.
- **Pluggable LLM** via env (`gemini` / `openai` / `ollama`). Ollama makes the whole
  thing air-gapped; cloud providers are there for a quick start.
- **Honest retrieval**: the model is instructed to answer only from the supplied
  excerpts and to return a sentinel when the answer isn't there — the API converts that
  to a clean "not found", so it never invents facts.
- A clean **vanilla-JS chat UI**: file upload with per-file chunk counts, answers with
  clickable `[n]` citations that expand to show the exact source fragment.
- **Robust errors**: embedder/Qdrant down → `503` with a clear message, LLM error →
  `502`; nothing fails silently. Least-privilege containers, internal-only vector DB and
  embedder, TLS-only via Caddy.

## 03 — Outcome

End-to-end test with two 2-page PDFs (a boiler manual and a remote-work policy):

| Question | Answer | Citation |
|---|---|---|
| Max operating pressure of the X200 boiler? | "…6 bar [1]" | `x200_boiler_manual.pdf — p.2` |
| How many remote days per week at ACME? | "…up to 3 days [1]" | `acme_remote_policy.pdf — p.2` |
| What does error code E04 mean? | "…low water pressure; refill to 1.5 bar [1]" | `x200_boiler_manual.pdf — p.2` |
| **What is the capital of France?** | **"Не нашёл ответа в загруженных материалах."** | — (correctly refuses) |

- Citations resolve to the **correct file and page**; the out-of-corpus question is
  refused instead of answered from world knowledge.
- Embeddings computed locally; with `LLM_PROVIDER=ollama` the deployment makes **no
  external calls** at all.
- One-command bring-up; embedder/Qdrant never exposed; clear failure modes verified
  (embedder down → `503`).

> Public exposure pending one external step: a DNS record for `rag.davidvasutenko.fun`
> → the server (Caddy block already staged). The stack is fully functional internally.

---

## Screenshots to capture (live service, for the gallery)

1. **Answer with a citation** — a question answered with an inline `[1]` and the source
   chip `manual.pdf — p.2` (the hero shot).
2. **Expanded citation** — the `[1]` source opened, showing the exact source fragment
   the answer used.
3. **"Not found"** — an out-of-corpus question returning the honest "не нашёл" message.
4. **Upload state** — a couple of PDFs uploaded with their per-file chunk counts.
5. **Provider line / config** — the header showing "LLM: ollama · embeddings: self-hosted"
   (the data-residency selling point).
6. **(Optional) architecture** — the compose/services diagram for the "runs on your box" story.

## Metrics / proofs for the subheading

- **`answers cite document + page`** — every grounded answer links to its source.
- **`out-of-corpus → "not found"`** — verified; no hallucination.
- **`embeddings 100% local`** — sentence-transformers in-container, no embedding API.
- **`zero data egress (Ollama)`** — fully on-prem option for sensitive documents.
