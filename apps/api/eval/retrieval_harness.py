"""Score a retriever on the lexical-gap benchmark: recall@k and MRR@k."""

from __future__ import annotations

from dataclasses import dataclass

from app.rag.retriever import InMemoryRetriever
from eval.retrieval_dataset import CASES, CORPUS, RetrievalCase

_REPO_ID = "retrieval-eval"


@dataclass(frozen=True)
class RetrievalMetrics:
    recall_at_k: float  # fraction of queries whose target is in the top k
    mrr: float          # mean reciprocal rank of the target (0 if beyond k)
    k: int


def load_corpus(retriever: InMemoryRetriever) -> InMemoryRetriever:
    retriever.add_chunks(_REPO_ID, list(CORPUS))
    return retriever


def evaluate_retrieval(
    retriever: InMemoryRetriever,
    cases: list[RetrievalCase] | None = None,
    k: int = 3,
) -> RetrievalMetrics:
    """Assumes the corpus is already loaded into `retriever`."""
    cases = cases or CASES
    hits = 0
    reciprocal = 0.0
    for case in cases:
        results = retriever.search(case.query, repo_id=_REPO_ID, limit=k)
        paths = [chunk.path for chunk in results]
        if case.target_path in paths:
            hits += 1
            reciprocal += 1.0 / (paths.index(case.target_path) + 1)
    n = len(cases) or 1
    return RetrievalMetrics(recall_at_k=hits / n, mrr=reciprocal / n, k=k)
