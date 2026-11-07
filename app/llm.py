"""Praat met het taalmodel.

Mistral gebruikt hetzelfde API-formaat als OpenAI (/chat/completions en /embeddings).
Wisselen van aanbieder = LLM_BASE_URL, LLM_API_KEY en de modelnamen in .env aanpassen.
"""
import time

import requests

from app import config


class LLMError(RuntimeError):
    pass


def _post(base_url: str, api_key: str, path: str, payload: dict, retries: int = 4) -> dict:
    if not api_key or api_key.startswith("vul-hier"):
        raise LLMError("Geen API-sleutel gevonden. Controleer LLM_API_KEY (en EMBED_API_KEY) in je .env-bestand.")

    url = f"{base_url}{path}"
    headers = {"Authorization": f"Bearer {api_key}"}

    for attempt in range(retries):
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        # 429 = te veel verzoeken (komt vaak voor op het gratis plan): even wachten en opnieuw
        if resp.status_code in (429, 503) and attempt < retries - 1:
            time.sleep(2 ** attempt * 5)   # 5, 10, 20 seconden
            continue
        if not resp.ok:
            raise LLMError(f"{resp.status_code} van {url}: {resp.text[:300]}")
        return resp.json()
    raise LLMError("Te veel verzoeken achter elkaar; probeer het zo opnieuw.")


def embed(texts: list[str], batch_size: int = 32) -> list[list[float]]:
    """Zet teksten om in vectoren (embeddings) zodat we op betekenis kunnen zoeken."""
    vectors: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        data = _post(config.EMBED_BASE_URL, config.EMBED_API_KEY, "/embeddings",
                     {"model": config.EMBED_MODEL, "input": batch})
        # sorteer op index: de API garandeert de volgorde niet altijd
        for item in sorted(data["data"], key=lambda d: d["index"]):
            vectors.append(item["embedding"])
    return vectors


def chat(messages: list[dict], temperature: float = 0.1) -> str:
    """Vraag het taalmodel om een antwoord. Lage temperature = feitelijker, minder creatief."""
    payload = {"model": config.CHAT_MODEL, "messages": messages, "temperature": temperature}
    if config.REASONING_EFFORT:
        payload["reasoning_effort"] = config.REASONING_EFFORT
    data = _post(config.LLM_BASE_URL, config.LLM_API_KEY, "/chat/completions", payload)
    return (data["choices"][0]["message"].get("content") or "").strip()
