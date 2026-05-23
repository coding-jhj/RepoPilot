from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import asdict

from app.domain.models import CodeChunk


class InMemoryRetriever:
    def __init__(self) -> None:
        self._chunks: dict[str, list[CodeChunk]] = defaultdict(list)

    def add_chunks(self, repo_id: str, chunks: list[CodeChunk | dict]) -> None:
        for chunk in chunks:
            if isinstance(chunk, CodeChunk):
                self._chunks[repo_id].append(chunk)
            else:
                self._chunks[repo_id].append(CodeChunk(**chunk))

    def search(self, query: str, repo_id: str, limit: int = 5) -> list[CodeChunk]:
        query_terms = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", query.lower()))

        def score(chunk: CodeChunk) -> tuple[int, int]:
            haystack = f"{chunk.path}\n{chunk.content}".lower()
            matches = sum(1 for term in query_terms if term in haystack)
            return matches, -len(chunk.content)

        ranked = sorted(self._chunks[repo_id], key=score, reverse=True)
        return ranked[:limit]

    def dump(self, repo_id: str) -> list[dict]:
        return [asdict(chunk) for chunk in self._chunks[repo_id]]
