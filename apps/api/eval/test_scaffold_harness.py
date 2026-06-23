"""Score the test_writer path: are drafted test skeletons structurally sound?

Runs the real ``BugDetectorNode -> TestWriterNode`` pipeline on the labelled bug
dataset and checks every drafted skeleton on deterministic, offline bars that
mirror the patch eval's appliability check:

- **parseable** — ``ast.parse`` succeeds (it is valid Python, not a broken stub).
- **has_test_fn** — a ``test_``-prefixed function exists (pytest can collect it).
- **refs_evidence** — the skeleton names the evidence path it was drafted for.

Test *correctness* is deliberately not measured: a deterministic generator can
only emit a failing placeholder, so the bar is structural soundness + scope, the
same honesty line the patch eval holds.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass

from app.agents.nodes.bug_detector import BugDetectorNode
from app.agents.nodes.test_writer import TestWriterNode
from app.agents.state import AgentState
from app.core.llm import FakeLLMProvider, LLMProvider
from eval.bug_dataset import CASES, BugCase

_REPO_ID = "test-eval"


@dataclass(frozen=True)
class TestScaffoldMetrics:
    skeletons: int     # total skeletons drafted across all cases
    parseable: int     # of those, how many are valid Python
    has_test_fn: int   # of those, how many expose a test_* function
    refs_evidence: int # of those, how many name their evidence path
    n: int             # cases evaluated


def _has_test_fn(tree: ast.Module) -> bool:
    return any(
        isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
        for node in ast.walk(tree)
    )


def _skeletons_for(case: BugCase, llm: LLMProvider):
    state = AgentState(
        repo_id=_REPO_ID,
        task="test_generation",
        retrieved_chunks=[case.chunk],
    )
    BugDetectorNode(llm).run(state)
    TestWriterNode(llm).run(state)
    return state.test_skeletons


def evaluate_test_scaffolds(
    llm: LLMProvider | None = None,
    *,
    cases: list[BugCase] | None = None,
) -> TestScaffoldMetrics:
    """Score the test writer. With no llm, uses the offline static baseline."""
    llm = llm or FakeLLMProvider()
    cases = cases or CASES
    skeletons = parseable = has_fn = refs = 0
    for case in cases:
        for skeleton in _skeletons_for(case, llm):
            skeletons += 1
            try:
                tree = ast.parse(skeleton.code)
            except SyntaxError:
                continue
            parseable += 1
            if _has_test_fn(tree):
                has_fn += 1
            if skeleton.path in skeleton.code:
                refs += 1
    return TestScaffoldMetrics(
        skeletons=skeletons,
        parseable=parseable,
        has_test_fn=has_fn,
        refs_evidence=refs,
        n=len(cases),
    )
