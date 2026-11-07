"""Stap 2 van RAG: zoeken. Een simpele vectoropslag met numpy.

Voor een paar honderd stukken tekst is dit snel genoeg en je ziet precies wat er gebeurt.
Bij veel meer documenten kun je deze module vervangen door Chroma of pgvector;
de rest van de code merkt daar niets van.
"""
import json

import numpy as np

from app import config

_CHUNKS = config.INDEX_DIR / "chunks.json"
_VECTORS = config.INDEX_DIR / "vectors.npy"

_cache: tuple[list[dict], np.ndarray] | None = None


def _normalize(m: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(m, axis=-1, keepdims=True)
    return m / np.clip(norms, 1e-12, None)


def save(chunks: list[dict], vectors: list[list[float]]) -> None:
    global _cache
    config.INDEX_DIR.mkdir(parents=True, exist_ok=True)
    matrix = _normalize(np.asarray(vectors, dtype=np.float32))
    _CHUNKS.write_text(json.dumps(chunks, ensure_ascii=False, indent=1), encoding="utf-8")
    np.save(_VECTORS, matrix)
    _cache = (chunks, matrix)


def load() -> tuple[list[dict], np.ndarray]:
    global _cache
    if _cache is None:
        if not _CHUNKS.exists():
            raise FileNotFoundError("Nog geen index. Draai eerst: python -m app.ingest")
        _cache = (json.loads(_CHUNKS.read_text(encoding="utf-8")), np.load(_VECTORS))
    return _cache


def search(query_vector: list[float], k: int = config.TOP_K) -> list[dict]:
    """Geeft de k stukken terug die qua betekenis het meest op de vraag lijken (cosinus-gelijkenis)."""
    chunks, matrix = load()
    q = _normalize(np.asarray(query_vector, dtype=np.float32))
    scores = matrix @ q
    top = np.argsort(-scores)[:k]
    return [{**chunks[i], "score": float(scores[i])} for i in top]
