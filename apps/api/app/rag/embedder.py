"""Embedders turn text into vectors for semantic retrieval.

The real provider wraps a small sentence-transformer (all-MiniLM-L6-v2, 384-dim,
CPU). It is an optional dependency: the deterministic keyword path and the test
suite never import it. See `pyproject.toml` `[embeddings]` extra.
"""

from __future__ import annotations

import os
from typing import Protocol, runtime_checkable


def _configure_backend_env() -> None:
    """Pin the torch backend before transformers is first imported.

    transformers auto-detects a backend at import time; if TensorFlow is present
    but tf_keras is not, the import raises. Forcing USE_TF/USE_FLAX=0 keeps it on
    torch. KMP_DUPLICATE_LIB_OK works around a Windows OpenMP clash between torch
    and MKL (harmless on Linux/CI). Must run before the SDK import to take effect.
    """
    os.environ.setdefault("USE_TF", "0")
    os.environ.setdefault("USE_FLAX", "0")
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
    os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")


@runtime_checkable
class Embedder(Protocol):
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Return one L2-normalized vector per input text (dot product = cosine)."""


class SentenceTransformerEmbedder:
    """all-MiniLM-L6-v2 wrapper. Loads the model lazily and once.

    Lazy + cached so importing this module costs nothing and the ~90MB weights
    load a single time per process (the first call pays the cost). Vectors are
    L2-normalized so a plain dot product is cosine similarity.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self._model = None  # loaded on first embed_batch

    def _load(self):
        if self._model is None:
            _configure_backend_env()
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self._load().encode(texts, normalize_embeddings=True)
        return [vector.tolist() for vector in vectors]


def build_embedder() -> Embedder | None:
    """Construct the real embedder, or None if the optional dep is missing.

    Callers fall back to keyword retrieval when this returns None, so a missing
    `sentence-transformers` install degrades gracefully instead of crashing.
    """
    _configure_backend_env()
    try:
        import sentence_transformers  # noqa: F401
    except Exception:
        return None
    return SentenceTransformerEmbedder()
