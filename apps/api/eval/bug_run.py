"""Score the bug_scan path: static baseline vs Gemini deep analysis.

    cd apps/api
    python -m eval.bug_run                       # static baseline only (offline)
    REPOPILOT_GEMINI_API_KEY=... python -m eval.bug_run   # + deep arm

The static baseline is deterministic and offline — its numbers are reproducible
and committable. The deep arm calls a live model; even at low temperature it is
not reproducible, so treat any deep number as an illustrative sample run, not a
pinned result.
"""

from __future__ import annotations

import os

from app.core.llm import build_llm_provider
from eval.bug_harness import BugMetrics, evaluate_bugs


def _line(label: str, m: BugMetrics) -> str:
    return (
        f"{label:<18} precision={m.precision:.2f} recall={m.recall:.2f} "
        f"f1={m.f1:.2f}  (tp={m.tp} fp={m.fp} fn={m.fn}, n={m.n})"
    )


def main() -> None:
    baseline = evaluate_bugs()  # FakeLLMProvider -> static rules only, offline
    print(_line("static baseline", baseline))

    api_key = os.environ.get("REPOPILOT_GEMINI_API_KEY") or os.environ.get(
        "GEMINI_API_KEY"
    )
    if not api_key:
        print(
            "deep (gemini)      skipped (set REPOPILOT_GEMINI_API_KEY to run the "
            "opt-in deep arm; its numbers are an illustrative sample, not pinned)"
        )
        return

    gemini = build_llm_provider("gemini", api_key=api_key)
    deep = evaluate_bugs(gemini, deep=True)
    print(_line("deep (gemini)*", deep))
    print(f"recall lift: {deep.recall - baseline.recall:+.2f}  (* sample run, not reproducible)")


if __name__ == "__main__":
    main()
