"""Tests for the test writer and its eval.

The skeletons are deliberately failing placeholders (a deterministic generator
can't know the right assertion), so the bar is structural: it must parse, expose
a collectable test_* function, and name its evidence — never "the test passes".
"""

import ast

from app.agents.nodes.bug_detector import BugDetectorNode
from app.agents.nodes.test_writer import TestWriterNode
from app.agents.state import AgentState
from app.core.llm import FakeLLMProvider
from app.domain.models import Evidence, Finding
from eval.bug_dataset import CASES
from eval.test_scaffold_harness import evaluate_test_scaffolds


def _draft(chunk: dict):
    state = AgentState(repo_id="t", task="test_generation", retrieved_chunks=[chunk])
    BugDetectorNode(FakeLLMProvider()).run(state)
    TestWriterNode(FakeLLMProvider()).run(state)
    return state.test_skeletons


def test_test_writer_drafts_valid_skeleton():
    pattern_case = next(c for c in CASES if c.group == "pattern")
    skeletons = _draft(pattern_case.chunk)

    assert len(skeletons) == 1
    skeleton = skeletons[0]
    tree = ast.parse(skeleton.code)  # raises if not valid Python
    assert any(
        isinstance(n, ast.FunctionDef) and n.name.startswith("test_")
        for n in ast.walk(tree)
    )
    assert skeleton.path in skeleton.code


def test_static_baseline_skeletons_are_deterministic():
    m = evaluate_test_scaffolds()
    assert (m.skeletons, m.parseable, m.has_test_fn, m.refs_evidence) == (3, 3, 3, 3)


def test_no_skeleton_for_semantic_or_clean_chunks():
    for case in CASES:
        if case.group in ("semantic", "clean"):
            assert _draft(case.chunk) == []


def test_test_writer_skipped_without_test_task():
    state = AgentState(
        repo_id="t",
        task="bug_scan",
        retrieved_chunks=[CASES[0].chunk],
    )
    BugDetectorNode(FakeLLMProvider()).run(state)
    TestWriterNode(FakeLLMProvider()).run(state)
    assert state.test_skeletons == []


def test_duplicate_evidence_paths_get_distinct_test_names():
    # Two findings on the same file must not collide into one test name.
    ev = [Evidence(path="dup.py", start_line=1, end_line=1)]
    state = AgentState(repo_id="t", task="test_generation", retrieved_chunks=[])
    state.findings = [
        Finding(title="A", summary="x", severity="low", evidence=ev),
        Finding(title="B", summary="y", severity="low", evidence=ev),
    ]
    TestWriterNode(FakeLLMProvider()).run(state)

    names = []
    for skeleton in state.test_skeletons:
        tree = ast.parse(skeleton.code)
        names += [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    assert len(names) == len(set(names)) == 2
