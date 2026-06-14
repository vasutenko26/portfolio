"""
Абстракция над LLM-провайдером генерации ответа. Выбирается через LLM_PROVIDER:
  - gemini  (Google Generative Language API)
  - openai  (OpenAI или совместимый endpoint через OPENAI_BASE_URL)
  - ollama  (локальный Ollama — данные не покидают сервер вообще)

Эмбеддинги всегда self-hosted (см. embedder). LLM-провайдер — на выбор клиента:
для полностью on-prem/air-gap ставится ollama.
"""
import os
import logging

import httpx

log = logging.getLogger("rag.llm")

PROVIDER = os.environ.get("LLM_PROVIDER", "gemini").lower()
TIMEOUT = float(os.environ.get("LLM_TIMEOUT", "60"))
TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.2"))


class LLMError(RuntimeError):
    """Внятная ошибка генерации (провайдер недоступен/неверный ключ/таймаут)."""


def _require(name: str) -> str:
    val = os.environ.get(name, "").strip()
    if not val:
        raise LLMError(f"LLM provider '{PROVIDER}' requires {name} to be set")
    return val


def generate(system: str, user: str) -> str:
    try:
        if PROVIDER == "gemini":
            return _gemini(system, user)
        if PROVIDER == "openai":
            return _openai(system, user)
        if PROVIDER == "ollama":
            return _ollama(system, user)
        raise LLMError(f"unknown LLM_PROVIDER '{PROVIDER}'")
    except LLMError:
        raise
    except httpx.HTTPError as e:
        raise LLMError(f"LLM provider '{PROVIDER}' unreachable: {e}") from e
    except (KeyError, IndexError, ValueError) as e:
        raise LLMError(f"LLM provider '{PROVIDER}' returned an unexpected response: {e}") from e


def _gemini(system: str, user: str) -> str:
    key = _require("GEMINI_API_KEY")
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {"temperature": TEMPERATURE},
    }
    r = httpx.post(url, params={"key": key}, json=payload, timeout=TIMEOUT)
    if r.status_code != 200:
        raise LLMError(f"Gemini HTTP {r.status_code}: {r.text[:200]}")
    data = r.json()
    cand = data["candidates"][0]
    return "".join(p.get("text", "") for p in cand["content"]["parts"]).strip()


def _openai(system: str, user: str) -> str:
    key = _require("OPENAI_API_KEY")
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    r = httpx.post(
        f"{base}/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": TEMPERATURE,
        },
        timeout=TIMEOUT,
    )
    if r.status_code != 200:
        raise LLMError(f"OpenAI HTTP {r.status_code}: {r.text[:200]}")
    return r.json()["choices"][0]["message"]["content"].strip()


def _ollama(system: str, user: str) -> str:
    base = os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434").rstrip("/")
    model = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
    r = httpx.post(
        f"{base}/api/chat",
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {"temperature": TEMPERATURE},
        },
        timeout=TIMEOUT,
    )
    if r.status_code != 200:
        raise LLMError(f"Ollama HTTP {r.status_code}: {r.text[:200]}")
    return r.json()["message"]["content"].strip()


def provider_info() -> dict:
    model = {
        "gemini": os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        "openai": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        "ollama": os.environ.get("OLLAMA_MODEL", "llama3.1:8b"),
    }.get(PROVIDER, "?")
    return {"provider": PROVIDER, "model": model}
