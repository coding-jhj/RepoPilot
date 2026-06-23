"""Compare keyword vs semantic retrieval on the lexical-gap benchmark.

    cd apps/api
    REPOPILOT_USE_EMBEDDINGS=true python -m eval.retrieval_run

Needs the [embeddings] extra (sentence-transformers). Without it, only the
keyword baseline runs and a hint is printed.
"""

from __future__ import annotations

from app.rag.embedder import build_embedder
from app.rag.retriever import InMemoryRetriever
from eval.retrieval_harness import RetrievalMetrics, evaluate_retrieval, load_corpus

_K = 3


def _line(label: str, metrics: RetrievalMetrics) -> str:
    return (
        f"{label:<16} recall@{metrics.k}={metrics.recall_at_k:.2f} "
        f"mrr={metrics.mrr:.2f}"
    )


def main() -> None:
    keyword = load_corpus(InMemoryRetriever())  # no embedder -> lexical path
    keyword_metrics = evaluate_retrieval(keyword, k=_K)
    print(_line("keyword-only", keyword_metrics))

    embedder = build_embedder()
    if embedder is None:
        print(
            "semantic         skipped (install the [embeddings] extra: "
            "pip install -e .[embeddings])"
        )
        return

    semantic = load_corpus(InMemoryRetriever(embedder=embedder))
    semantic_metrics = evaluate_retrieval(semantic, k=_K)
    print(_line("semantic", semantic_metrics))

    lift = semantic_metrics.recall_at_k - keyword_metrics.recall_at_k
    print(f"recall@{_K} lift: {lift:+.2f}")


if __name__ == "__main__":
    main()
