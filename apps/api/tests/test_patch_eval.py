"""Tests for the patch writer and its eval.

The load-bearing test is the appliability check: ``patch_applies`` must reject a
hunk whose context no longer matches the source. Without that, the eval's "valid
diff" bar would pass any well-formed ``diff --git`` header, including garbage —
the eval would measure nothing.
"""

from app.agents.nodes.bug_detector import BugDetectorNode
from app.agents.nodes.patch_writer import PatchWriterNode
from app.agents.state import AgentState
from app.code.diff import build_git_diff, patch_applies
from app.core.llm import FakeLLMProvider
from app.services.patch_service import PatchService
from eval.bug_dataset import CASES
from eval.patch_harness import evaluate_patches


def _draft(chunk: dict):
    state = AgentState(
        repo_id="t", task="patch_generation", retrieved_chunks=[chunk]
    )
    BugDetectorNode(FakeLLMProvider()).run(state)
    PatchWriterNode(FakeLLMProvider()).run(state)
    return state.patches


def test_patch_writer_drafts_appliable_scoped_scaffold():
    pattern_case = next(c for c in CASES if c.group == "pattern")
    patches = _draft(pattern_case.chunk)

    assert len(patches) == 1
    patch = patches[0]
    assert "RepoPilot: review" in patch.diff
    assert patch_applies(patch.diff, {patch.path: pattern_case.chunk["content"]})
    assert PatchService().validate(patch.diff, [patch.path]).valid


def test_patch_applies_rejects_corrupted_hunk():
    src = "def run(expr):\n    return eval(expr)"
    diff = build_git_diff("calc.py", src, "# marker\n" + src)
    assert patch_applies(diff, {"calc.py": src})

    tampered = diff.replace("return eval(expr)", "return eval(expr)  # drift")
    assert not patch_applies(tampered, {"calc.py": src})
    assert not patch_applies(diff, {"other.py": src})  # path not in sources


def test_static_baseline_patches_are_deterministic():
    # 3 pattern bugs -> 3 scaffolds; every one applies cleanly and stays in scope.
    m = evaluate_patches()
    assert (m.patches, m.appliable, m.in_scope) == (3, 3, 3)


def test_no_patch_for_semantic_or_clean_chunks():
    # Static finds nothing here, so the writer has nothing to scaffold.
    for case in CASES:
        if case.group in ("semantic", "clean"):
            assert _draft(case.chunk) == []


def test_draft_patch_output_is_valid_scoped_diff():
    # The shared builder must keep PatchService.draft_patch producing a diff that
    # its own validator accepts.
    service = PatchService()
    diff = service.draft_patch("tidy imports", ["app/main.py"])
    assert service.validate(diff, ["app/main.py"]).valid
