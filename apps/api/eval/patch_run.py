"""Score the patch_writer path: static scaffold baseline vs deep (Gemini) fix arm.

    cd apps/api
    python -m eval.patch_run                                # static baseline (offline)
    REPOPILOT_GEMINI_API_KEY=... python -m eval.patch_run   # + deep fix arm

The static baseline drafts one review scaffold per static finding; every scaffold
must apply cleanly and stay in scope, so its numbers are deterministic and
committable. The deep arm asks a live model for an actual fix per finding: the
diff is appliable by construction, and ``verified`` reports how many of those
fixes removed the flagged static defect (a closed-loop, necessary-not-sufficient
correctness check). The live numbers are still an illustrative sample run, not a
pinned result.
"""

from __future__ import annotations

import os

from app.core.llm import build_llm_provider
from eval.patch_harness import PatchMetrics, evaluate_patches


def _line(label: str, m: PatchMetrics) -> str:
    return (
        f"{label:<18} patches={m.patches} appliable={m.appliable}/{m.patches} "
        f"in_scope={m.in_scope}/{m.patches} fixes={m.fixes}/{m.patches} "
        f"verified={m.verified}/{m.fixes} (n={m.n})"
    )


def main() -> None:
    print(_line("static baseline", evaluate_patches()))

    api_key = os.environ.get("REPOPILOT_GEMINI_API_KEY") or os.environ.get(
        "GEMINI_API_KEY"
    )
    if not api_key:
        print(
            "deep (gemini)      skipped (set REPOPILOT_GEMINI_API_KEY to run the "
            "opt-in deep fix arm; verified= reports fixes that removed the flagged "
            "defect, but the run is a sample, not pinned)"
        )
        return

    gemini = build_llm_provider("gemini", api_key=api_key)
    deep = evaluate_patches(gemini, deep=True)
    print(_line("deep (gemini)*", deep))
    print(
        "* sample run, not reproducible; verified = flagged static defect removed "
        "(necessary, not sufficient — semantic-fix correctness still unchecked)"
    )


if __name__ == "__main__":
    main()
