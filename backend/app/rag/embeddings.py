"""Pluggable dense embedding providers. BM25 works without any of them."""
from __future__ import annotations

import logging
from typing import Protocol

import httpx
import numpy as np

from ..config import Settings

log = logging.getLogger(__name__)


class Embedder(Protocol):
    name: str

    def embed(self, texts: list[str], kind: str = "document") -> np.ndarray: ...


class VoyageEmbedder:
    """Voyage AI (Anthropic's recommended embedding partner). Uses the REST API directly."""

    name = "voyage"

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    def embed(self, texts: list[str], kind: str = "document") -> np.ndarray:
        vectors: list[list[float]] = []
        with httpx.Client(timeout=120) as client:
            for i in range(0, len(texts), 128):
                batch = texts[i:i + 128]
                resp = client.post(
                    "https://api.voyageai.com/v1/embeddings",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"input": batch, "model": self.model, "input_type": "document" if kind == "document" else "query"},
                )
                resp.raise_for_status()
                vectors.extend(item["embedding"] for item in resp.json()["data"])
        arr = np.asarray(vectors, dtype=np.float32)
        return arr / (np.linalg.norm(arr, axis=1, keepdims=True) + 1e-9)


class LocalEmbedder:
    """sentence-transformers model, if installed (pip install sentence-transformers)."""

    name = "local"

    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer  # type: ignore

        self.model = SentenceTransformer(model_name)

    def embed(self, texts: list[str], kind: str = "document") -> np.ndarray:
        return np.asarray(self.model.encode(texts, normalize_embeddings=True, batch_size=64), dtype=np.float32)


def build_embedder(settings: Settings) -> Embedder | None:
    provider = settings.embeddings_provider.lower()
    if provider == "voyage" and settings.voyage_api_key:
        return VoyageEmbedder(settings.voyage_api_key, settings.voyage_model)
    if provider == "local":
        try:
            return LocalEmbedder(settings.local_embedding_model)
        except Exception as exc:  # pragma: no cover - optional dependency
            log.warning("local embeddings unavailable (%s); falling back to BM25 only", exc)
    return None
