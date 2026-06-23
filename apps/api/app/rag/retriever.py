from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import asdict

from app.domain.models import CodeChunk
from app.rag.embedder import Embedder


class InMemoryRetriever:
    """Repo-scoped chunk store with two retrieval modes.

    With an embedder it ranks by cosine similarity (semantic). Without one it
    falls back to lexical term-overlap. The semantic path is what lets a query
    like "how does login work" find `verify_password` even with no shared tokens.
    """

    def __init__(self, embedder: Embedder | None = None) -> None:
        self._chunks: dict[str, list[CodeChunk]] = defaultdict(list)
        # Parallel to self._chunks[repo_id]; only populated when an embedder is set.
        self._vectors: dict[str, list[list[float]]] = defaultdict(list)
        self._embedder = embedder

    def add_chunks(self, repo_id: str, chunks: list[CodeChunk | dict]) -> None:
        normalized = [
            chunk if isinstance(chunk, CodeChunk) else CodeChunk(**chunk)
            for chunk in chunks
        ]
        self._chunks[repo_id].extend(normalized)
        if self._embedder is not None and normalized:
            texts = [f"{chunk.path}\n{chunk.content}" for chunk in normalized]
            self._vectors[repo_id].extend(self._embedder.embed_batch(texts))

    def search(self, query: str, repo_id: str, limit: int = 5) -> list[CodeChunk]:
        chunks = self._chunks[repo_id]
        if not chunks:
            return []
        vectors = self._vectors[repo_id]
        if self._embedder is not None and len(vectors) == len(chunks):
            return self._semantic_search(query, chunks, vectors, limit)
        return self._keyword_search(query, chunks, limit)

    def _semantic_search(
        self,
        query: str,
        chunks: list[CodeChunk],
        vectors: list[list[float]],
        limit: int,
    ) -> list[CodeChunk]:
        query_vec = self._embedder.embed_batch([query])[0]
        scored = sorted(
            zip(chunks, vectors),
            key=lambda pair: _dot(query_vec, pair[1]),
            reverse=True,
        )
        return [chunk for chunk, _ in scored[:limit]]

    @staticmethod
    def _keyword_search(
        query: str, chunks: list[CodeChunk], limit: int
    ) -> list[CodeChunk]:
        query_terms = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", query.lower()))

        def score(chunk: CodeChunk) -> tuple[int, int]:
            haystack = f"{chunk.path}\n{chunk.content}".lower()
            matches = sum(1 for term in query_terms if term in haystack)
            return matches, -len(chunk.content)

        ranked = sorted(chunks, key=score, reverse=True)
        return ranked[:limit]

    def dump(self, repo_id: str) -> list[dict]:
        return [asdict(chunk) for chunk in self._chunks[repo_id]]


def _dot(a: list[float], b: list[float]) -> float:
    # Vectors are L2-normalized by the embedder, so dot product == cosine.
    return sum(x * y for x, y in zip(a, b))
