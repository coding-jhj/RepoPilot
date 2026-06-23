from __future__ import annotations

from pathlib import Path

from app.agents.nodes.bug_detector import MANUAL_REVIEW_TITLE
from app.agents.state import AgentState
from app.code.diff import build_git_diff
from app.core.llm import LLMProvider
from app.domain.models import AgentStep, Patch

# Hash-comment languages; everything else gets a C-style line comment.
_HASH_SUFFIXES = {".py", ".rb", ".sh", ".yml", ".yaml", ".toml"}


def _comment_prefix(path: str) -> str:
    return "#" if Path(path).suffix in _HASH_SUFFIXES else "//"


class PatchWriterNode:
    """Turn substantive findings into scoped, appliable patch scaffolds.

    This is a review scaffold, not a fix: for each finding it emits a real
    unified diff that inserts a review marker at the top of the flagged chunk,
    anchored on the actual code so the diff applies cleanly. Generating a true
    fix is left to deep analysis; the deterministic scaffold is what the patch
    eval pins (valid + in-scope).
    """

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    def run(self, state: AgentState) -> AgentState:
        if "patch" not in state.task:
            state.timeline.append(
                AgentStep(node="patch_writer", summary="Skipped patch generation.")
            )
            return state

        chunks_by_path = {c["path"]: c for c in state.retrieved_chunks}
        for finding in state.findings:
            if finding.title == MANUAL_REVIEW_TITLE or not finding.evidence:
                continue
            path = finding.evidence[0].path
            chunk = chunks_by_path.get(path)
            if chunk is None:
                continue
            diff = self._scaffold(path, chunk["content"], finding.title)
            if diff:
                state.patches.append(
                    Patch(path=path, diff=diff, finding_title=finding.title)
                )

        state.timeline.append(
            AgentStep(
                node="patch_writer",
                summary=f"Drafted {len(state.patches)} scoped patch scaffold(s) for review.",
            )
        )
        return state

    def _scaffold(self, path: str, content: str, title: str) -> str:
        marker = f"{_comment_prefix(path)} RepoPilot: review - {title}\n"
        return build_git_diff(path, content, marker + content)
