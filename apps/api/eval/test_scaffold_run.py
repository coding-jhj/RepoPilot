"""Score the test_writer path: are drafted test skeletons structurally sound?

    cd apps/api
    python -m eval.test_scaffold_run

Fully deterministic and offline: the static baseline drafts one regression-test
skeleton per static finding, and each must parse, expose a test_* function, and
name its evidence path. Test correctness is out of scope (see
test_scaffold_harness.py).
"""

from __future__ import annotations

from eval.test_scaffold_harness import evaluate_test_scaffolds


def main() -> None:
    m = evaluate_test_scaffolds()
    print(
        f"static baseline    skeletons={m.skeletons} "
        f"parseable={m.parseable}/{m.skeletons} "
        f"has_test_fn={m.has_test_fn}/{m.skeletons} "
        f"refs_evidence={m.refs_evidence}/{m.skeletons} (n={m.n})"
    )


if __name__ == "__main__":
    main()
