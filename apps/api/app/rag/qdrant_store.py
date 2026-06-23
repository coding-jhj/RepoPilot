from app.domain.models import CodeChunk
from app.rag.embedder import Embedder
from app.rag.retriever import InMemoryRetriever


class LocalQdrantLikeStore(InMemoryRetriever):
    """Small local stand-in with the same repo/chunk boundary as Qdrant."""

    def __init__(self, embedder: Embedder | None = None) -> None:
        super().__init__(embedder=embedder)

    def upsert_chunks(self, repo_id: str, chunks: list[CodeChunk]) -> None:
        self.add_chunks(repo_id, chunks)
