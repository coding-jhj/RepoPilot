"""Retriever ranking tests.

The semantic path is pinned with a hand-built fake embedder (controlled vectors,
no model, no torch) so the default suite stays offline. The real MiniLM model is
exercised only by the optional retrieval eval (`eval/retrieval_run.py`).
"""

from __future__ import annotations

import math

from app.domain.models import CodeChunk
from app.rag.retriever import InMemoryRetriever


def _norm(vec: list[float]) -> list[float]:
    length = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / length for x in vec]


class _FakeEmbedder:
    """Maps any text containing a marker to that marker's vector.

    Lets a test assert the cosine ranking on a lexical-gap query: the query and
    the target share a *concept* (vector) but no tokens.
    """

    def __init__(self, markers: dict[str, list[float]]) -> None:
        self._markers = markers

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for text in texts:
            vec = next(
                (v for marker, v in self._markers.items() if marker in text),
                [0.0, 0.0, 1.0],
            )
            out.append(_norm(vec))
        return out


_AUTH = [1.0, 0.0, 0.0]
_MATH = [0.0, 1.0, 0.0]
_AUTH_CHUNK = CodeChunk(
    path="auth.py",
    start_line=1,
    end_line=1,
    content="def login(user): return verify_password(user)",
)
_MATH_CHUNK = CodeChunk(
    path="math.py", start_line=1, end_line=1, content="def add(a, b): return a + b"
)


def test_semantic_search_beats_lexical_gap():
    # Query shares NO tokens with the auth chunk ("authenticate" vs
    # "verify_password"), so keyword matching would tie. The embedder maps both
    # to the auth concept, so the auth chunk must rank first.
    embedder = _FakeEmbedder({"authenticate": _AUTH, "verify_password": _AUTH, "add": _MATH})
    retriever = InMemoryRetriever(embedder=embedder)
    retriever.add_chunks("r", [_MATH_CHUNK, _AUTH_CHUNK])

    top = retriever.search("how do I authenticate a user", repo_id="r", limit=1)

    assert len(top) == 1
    assert top[0].path == "auth.py"


def test_keyword_fallback_when_no_embedder():
    retriever = InMemoryRetriever()  # no embedder -> lexical path
    retriever.add_chunks("r", [_MATH_CHUNK, _AUTH_CHUNK])

    top = retriever.search("login", repo_id="r", limit=1)

    assert top[0].path == "auth.py"


def test_empty_repo_returns_nothing():
    assert InMemoryRetriever().search("anything", repo_id="missing") == []
