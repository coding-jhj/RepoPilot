"""Score the patch_writer path: are drafted scaffolds valid and in-scope?

    cd apps/api
    python -m eval.patch_run

Fully deterministic and offline: the static baseline drafts one scaffold per
static finding and every scaffold must apply cleanly and stay in scope. There is
no live-LLM arm here — fix correctness is out of scope for this eval (see
patch_harness.py).
"""

from __future__ import annotations

from eval.patch_harness import evaluate_patches


def main() -> None:
    m = evaluate_patches()
    print(
        f"static baseline    patches={m.patches} "
        f"appliable={m.appliable}/{m.patches} in_scope={m.in_scope}/{m.patches} "
        f"(n={m.n})"
    )


if __name__ == "__main__":
    main()
