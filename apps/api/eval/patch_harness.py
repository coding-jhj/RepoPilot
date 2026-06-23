"""Score the patch_writer path: are drafted patches valid and in-scope?

Runs the real ``BugDetectorNode -> PatchWriterNode`` pipeline on the labelled bug
dataset, then checks every drafted patch on two deterministic bars:

- **appliable** — the hunk's context/removed lines match the source exactly
  (``patch_applies``); a well-formed ``diff --git`` header is not enough.
- **in-scope** — the diff only touches the evidence path it was drafted for
  (``PatchService.validate``).

The static baseline produces one scaffold per static finding (the 3 pattern
bugs), so it is fully deterministic and offline — committable as fact (the
baseline drafts no fixes, so ``fixes`` and ``verified`` are both 0).

The deep arm adds a third bar, ``verified``: of the LLM fixes, how many actually
removed the flagged defect. That is checked in a closed loop (re-run the static
analyzer on the corrected chunk; see ``PatchWriterNode._verify_fix``) and is a
necessary, not sufficient, correctness signal — it catches a "fix" that does not
remove the flagged pattern. It only applies to statically-detectable findings;
semantic-fix correctness is still out of scope.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.agents.nodes.bug_detector import BugDetectorNode
from app.agents.nodes.patch_writer import PatchWriterNode
from app.agents.state import AgentState
from app.code.diff import patch_applies
from app.core.llm import FakeLLMProvider, LLMProvider
from app.services.patch_service import PatchService
from eval.bug_dataset import CASES, BugCase

_REPO_ID = "patch-eval"


@dataclass(frozen=True)
class PatchMetrics:
    patches: int      # total patches drafted across all cases
    appliable: int    # of those, how many apply cleanly to their source
    in_scope: int     # of those, how many touch only their evidence path
    fixes: int        # of those, how many are deep LLM fix drafts (vs scaffolds)
    verified: int     # of the fixes, how many removed the flagged static defect
    n: int            # cases evaluated


def _patches_for(case: BugCase, llm: LLMProvider, deep: bool):
    state = AgentState(
        repo_id=_REPO_ID,
        task="patch_generation",
        retrieved_chunks=[case.chunk],
        deep=deep,
    )
    BugDetectorNode(llm).run(state)
    PatchWriterNode(llm).run(state)
    return state.patches


def evaluate_patches(
    llm: LLMProvider | None = None,
    *,
    deep: bool = False,
    cases: list[BugCase] | None = None,
) -> PatchMetrics:
    """Score the patch writer. With no llm, uses the offline static baseline."""
    llm = llm or FakeLLMProvider()
    cases = cases or CASES
    validator = PatchService()
    patches = appliable = in_scope = fixes = verified = 0
    for case in cases:
        source = {case.chunk["path"]: case.chunk["content"]}
        for patch in _patches_for(case, llm, deep):
            patches += 1
            if patch.kind == "fix":
                fixes += 1
                if patch.verified:
                    verified += 1
            if patch_applies(patch.diff, source):
                appliable += 1
            if validator.validate(patch.diff, [patch.path]).valid:
                in_scope += 1
    return PatchMetrics(
        patches=patches, appliable=appliable, in_scope=in_scope, fixes=fixes,
        verified=verified, n=len(cases),
    )
