"""Tests for the bug-finding eval.

The first test is the load-bearing one: it asserts the dataset's static-rule
split actually holds (pattern bugs trip a rule, semantic bugs and clean chunks
trip none). If a "semantic" chunk accidentally contained `eval(` or a bare
`except:`, static would catch it and the whole "deep adds recall" story would
collapse silently — so this is verified, not assumed.
"""

from dataclasses import dataclass

from app.code.rules import StaticRuleAnalyzer
from eval.bug_dataset import CASES
from eval.bug_harness import evaluate_bugs


def test_dataset_static_split_holds():
    analyzer = StaticRuleAnalyzer()
    for case in CASES:
        hits = analyzer.analyze_chunk(case.chunk)
        if case.group == "pattern":
            assert hits, f"pattern bug {case.bug_kind} should trip a static rule"
        else:
            assert not hits, (
                f"{case.group} chunk {case.chunk['path']} unexpectedly tripped a "
                f"static rule: {[f.title for f in hits]}"
            )


def test_static_baseline_metrics_are_deterministic():
    # 3 pattern bugs caught, 5 semantic missed, 4 clean silent.
    m = evaluate_bugs()  # FakeLLMProvider -> static only, offline
    assert (m.tp, m.fp, m.fn) == (3, 0, 5)
    assert m.precision == 1.0
    assert round(m.recall, 3) == 0.375


@dataclass
class _FlagAllLLM:
    """Stub that flags every chunk, to exercise the deep path and FP counting."""

    enabled: bool = True

    def complete(self, system: str, prompt: str) -> str:
        return '{"title": "Possible issue", "severity": "medium", "summary": "Flagged for review."}'


def test_deep_arm_scoring_with_stub():
    # Flags all 12 chunks: every buggy one becomes a TP (recall 1.0), every clean
    # one a FP (precision = 8/12). Verifies the deep path runs and the math holds.
    m = evaluate_bugs(_FlagAllLLM(), deep=True)
    assert m.tp == 8 and m.fn == 0
    assert m.fp == 4
    assert m.recall == 1.0
    assert round(m.precision, 3) == 0.667


def test_fake_provider_stays_static_even_in_deep_mode():
    # FakeLLMProvider.enabled is False -> deep scan skipped, same as the baseline.
    from app.core.llm import FakeLLMProvider

    assert evaluate_bugs(FakeLLMProvider(), deep=True).tp == 3
