"""Score the bug_scan path on the labelled benchmark: precision / recall / F1.

Detection runs the real ``BugDetectorNode`` so the eval measures the production
path, not a reimplementation. A chunk counts as *flagged* when the node emits at
least one substantive finding citing it — the always-on fallback finding
(``MANUAL_REVIEW_TITLE``) is excluded so an empty result reads as "no bug found".

Detection is per-chunk binary (any substantive finding => flagged), mirroring the
retrieval eval's "target in top-k". This gives credit even if the model flags a
different issue than the planted one; it slightly inflates the deep arm's recall.
That is an accepted simplification at this scope, called out so the numbers are
read honestly.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.agents.nodes.bug_detector import MANUAL_REVIEW_TITLE, BugDetectorNode
from app.agents.state import AgentState
from app.core.llm import FakeLLMProvider, LLMProvider
from app.domain.models import Finding
from eval.bug_dataset import CASES, BugCase

_REPO_ID = "bug-eval"


@dataclass(frozen=True)
class BugMetrics:
    precision: float  # of chunks flagged, fraction that truly had a bug
    recall: float     # of buggy chunks, fraction that were flagged
    f1: float
    tp: int
    fp: int
    fn: int
    n: int


def substantive_findings(chunk: dict, llm: LLMProvider, deep: bool) -> list[Finding]:
    """Run the real bug detector on one chunk; drop the always-on fallback."""
    state = AgentState(
        repo_id=_REPO_ID,
        task="bug_scan",
        retrieved_chunks=[chunk],
        deep=deep,
    )
    BugDetectorNode(llm).run(state)
    return [f for f in state.findings if f.title != MANUAL_REVIEW_TITLE]


def _flagged(case: BugCase, llm: LLMProvider, deep: bool) -> bool:
    findings = substantive_findings(case.chunk, llm, deep)
    path = case.chunk["path"]
    return any(ev.path == path for f in findings for ev in f.evidence)


def evaluate_bugs(
    llm: LLMProvider | None = None,
    *,
    deep: bool = False,
    cases: list[BugCase] | None = None,
) -> BugMetrics:
    """Score a detector. With no llm, uses the offline static-only baseline."""
    llm = llm or FakeLLMProvider()
    cases = cases or CASES
    tp = fp = fn = 0
    for case in cases:
        flagged = _flagged(case, llm, deep)
        if case.has_bug and flagged:
            tp += 1
        elif not case.has_bug and flagged:
            fp += 1
        elif case.has_bug and not flagged:
            fn += 1
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )
    return BugMetrics(
        precision=precision, recall=recall, f1=f1, tp=tp, fp=fp, fn=fn, n=len(cases)
    )
