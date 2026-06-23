"""Tests for the patch writer and its eval.

The load-bearing test is the appliability check: ``patch_applies`` must reject a
hunk whose context no longer matches the source. Without that, the eval's "valid
diff" bar would pass any well-formed ``diff --git`` header, including garbage —
the eval would measure nothing.
"""

from app.agents.nodes.bug_detector import BugDetectorNode
from app.agents.nodes.patch_writer import PatchWriterNode
from app.agents.state import AgentState
from app.code.diff import (
    apply_patch_to_text,
    apply_unified_diff,
    build_git_diff,
    patch_applies,
)
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


def test_apply_unified_diff_round_trips_build_git_diff():
    a = "def run(expr):\n    return eval(expr)"
    b = "def run(expr):\n    return ast.literal_eval(expr)"
    diff = build_git_diff("calc.py", a, b)
    assert apply_unified_diff(diff, {"calc.py": a}) == {"calc.py": b + "\n"}


def test_apply_patch_to_text_splices_chunk_diff_into_full_file():
    # The diff is built against a chunk; applying it to the whole file must land
    # on the right block by content match, not chunk-relative line numbers.
    chunk = "    except:\n        return None"
    fixed = "    except Exception as err:\n        log(err)\n        return None"
    diff = build_git_diff("loader.py", chunk, fixed)

    full = (
        "import logging\n\n"
        "def load(path):\n"
        "    try:\n"
        "        return read(path)\n"
        "    except:\n"
        "        return None\n"
    )
    out = apply_patch_to_text(full, diff, "loader.py")
    assert "except Exception as err:" in out
    assert "    except:\n" not in out
    assert out.startswith("import logging\n\ndef load(path):")  # untouched lines kept


def test_apply_patch_to_text_rejects_drifted_file():
    chunk = "    return eval(expr)"
    diff = build_git_diff("calc.py", chunk, "    return safe(expr)")
    drifted = "def run(expr):\n    return compute(expr)\n"  # chunk no longer present
    try:
        apply_patch_to_text(drifted, diff, "calc.py")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError on drifted file")


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


class _StubFixLLM:
    """Enabled fake LLM returning a canned corrected chunk.

    Lets the deep patch path be tested deterministically, without a live model:
    the mechanism (LLM text -> appliable, in-scope fix diff) is what we pin, not
    Gemini's output.
    """

    enabled = True

    def __init__(self, fixed: str) -> None:
        self.fixed = fixed

    def complete(self, system: str, prompt: str) -> str:
        return self.fixed


def _deep_draft(chunk: dict, fixed: str):
    llm = _StubFixLLM(fixed)
    state = AgentState(
        repo_id="t", task="patch_generation", retrieved_chunks=[chunk], deep=True
    )
    BugDetectorNode(llm).run(state)
    PatchWriterNode(llm).run(state)
    return state.patches


def test_deep_fix_produces_appliable_in_scope_fix_patch():
    pattern_case = next(c for c in CASES if c.group == "pattern")
    content = pattern_case.chunk["content"]
    patches = _deep_draft(pattern_case.chunk, "# fixed by deep analysis\n" + content)

    assert len(patches) == 1
    patch = patches[0]
    assert patch.kind == "fix"
    assert "RepoPilot: review" not in patch.diff  # a real fix, not the scaffold
    assert patch_applies(patch.diff, {patch.path: content})
    assert PatchService().validate(patch.diff, [patch.path]).valid


def test_deep_fix_falls_back_to_scaffold_on_noop():
    # Model echoes the chunk unchanged -> empty diff -> scaffold fallback, so the
    # finding still yields a reviewable patch.
    pattern_case = next(c for c in CASES if c.group == "pattern")
    patches = _deep_draft(pattern_case.chunk, pattern_case.chunk["content"])

    assert len(patches) == 1
    assert patches[0].kind == "scaffold"


def test_static_baseline_drafts_no_fixes():
    # Offline baseline is scaffold-only; it must never fabricate a "fix".
    assert evaluate_patches().fixes == 0


def test_static_baseline_verifies_nothing():
    # No fixes -> nothing to verify; the closed-loop count must stay 0.
    assert evaluate_patches().verified == 0


def _bare_except_case():
    return next(c for c in CASES if c.bug_kind == "bare_except")


def test_deep_fix_is_verified_when_static_defect_removed():
    # A real fix (bare `except:` -> `except Exception:`) makes the static rule stop
    # firing, so the closed-loop check confirms the flagged defect is gone.
    case = _bare_except_case()
    real_fix = case.chunk["content"].replace("except:", "except Exception:")
    patches = _deep_draft(case.chunk, real_fix)

    assert len(patches) == 1
    patch = patches[0]
    assert patch.kind == "fix"
    assert patch.verified is True


def test_deep_fix_is_unverified_when_defect_remains():
    # A "fix" that changes something but leaves the bare except in place must NOT be
    # marked verified — this is the case the closed-loop check exists to catch.
    case = _bare_except_case()
    fake_fix = "# attempted fix\n" + case.chunk["content"]  # bare except still there
    patches = _deep_draft(case.chunk, fake_fix)

    assert len(patches) == 1
    patch = patches[0]
    assert patch.kind == "fix"  # diff is non-empty, so it is a fix draft...
    assert patch.verified is False  # ...but unverified: the defect survived
