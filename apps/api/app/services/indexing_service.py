from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.code.parser import CodeParser
from app.domain.models import CodeChunk, CodeDocument
from app.rag.chunker import CodeChunker
from app.rag.qdrant_store import LocalQdrantLikeStore


IGNORED_DIRS = {
    ".git",
    "node_modules",
    ".next",
    "dist",
    "build",
    "__pycache__",
    ".venv",
    "venv",
}


@dataclass(frozen=True)
class IndexResult:
    repo_id: str
    files_indexed: int
    chunks_indexed: int
    documents: list[CodeDocument]


class IndexingService:
    def __init__(
        self,
        store: LocalQdrantLikeStore,
        parser: CodeParser | None = None,
        chunker: CodeChunker | None = None,
        max_files: int = 500,
        max_file_bytes: int = 200_000,
    ) -> None:
        self.store = store
        self.parser = parser or CodeParser()
        self.chunker = chunker or CodeChunker()
        self.max_files = max_files
        self.max_file_bytes = max_file_bytes

    def index_repo(self, repo_id: str, repo_root: Path) -> IndexResult:
        documents: list[CodeDocument] = []
        chunks: list[CodeChunk] = []

        for path in self._iter_indexable_files(repo_root):
            if len(documents) >= self.max_files:
                break
            document = self.parser.parse_file(path, repo_root)
            documents.append(document)
            chunks.extend(self.chunker.chunk(document))

        self.store.upsert_chunks(repo_id, chunks)
        return IndexResult(
            repo_id=repo_id,
            files_indexed=len(documents),
            chunks_indexed=len(chunks),
            documents=documents,
        )

    def _iter_indexable_files(self, repo_root: Path):
        for path in repo_root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in IGNORED_DIRS for part in path.parts):
                continue
            if path.suffix.lower() not in {".py", ".ts", ".tsx", ".js", ".jsx", ".md"}:
                continue
            if path.stat().st_size > self.max_file_bytes:
                continue
            yield path
