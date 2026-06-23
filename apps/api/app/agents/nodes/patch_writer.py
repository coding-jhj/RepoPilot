from __future__ import annotations

from pathlib import Path

from app.agents.nodes.bug_detector import MANUAL_REVIEW_TITLE
from app.agents.state import AgentState
from app.code.diff import build_git_diff
from app.core.llm import LLMError, LLMProvider
from app.domain.models import AgentStep, Finding, Patch

# Hash-comment languages; everything else gets a C-style line comment.
_HASH_SUFFIXES = {".py", ".rb", ".sh", ".yml", ".yaml", ".toml"}

_FIX_SYSTEM = (
    "You are a senior software engineer. You are given one code chunk and a known "
    "issue in it. Return ONLY the full corrected version of that exact chunk: keep "
    "all surrounding code, make the smallest change that fixes the issue, and output "
    "the code verbatim with no explanation and no markdown fences."
)


def _comment_prefix(path: str) -> str:
    return "#" if Path(path).suffix in _HASH_SUFFIXES else "//"


def _strip_fences(text: str) -> str:
    """Drop a leading ```lang fence and trailing ``` the model may wrap code in."""
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()[1:]  # drop opening fence (``` or ```python)
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines)


class PatchWriterNode:
    """Turn substantive findings into scoped, appliable patches.

    Two arms, sharing one appliability+scope contract:

    - **scaffold (default, deterministic)** — emits a real unified diff that inserts
      a review marker at the top of the flagged chunk, anchored on the actual code
      so it applies cleanly. This is what the patch eval pins (valid + in-scope).
    - **deep fix (opt-in)** — when ``state.deep`` and the LLM is enabled, asks the
      model for a corrected version of the chunk and diffs original -> fix. The diff
      is appliable by construction (difflib); *correctness* is not verified here, so
      it is a draft for review, not a trusted fix. Falls back to the scaffold on any
      LLM error or no-op result, so every finding still yields a patch.
    """

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    def run(self, state: AgentState) -> AgentState:
        if "patch" not in state.task:
            state.timeline.append(
                AgentStep(node="patch_writer", summary="Skipped patch generation.")
            )
            return state

        deep = bool(state.deep and getattr(self.llm, "enabled", False))
        chunks_by_path = {c["path"]: c for c in state.retrieved_chunks}
        fixes = 0
        for finding in state.findings:
            if finding.title == MANUAL_REVIEW_TITLE or not finding.evidence:
                continue
            path = finding.evidence[0].path
            chunk = chunks_by_path.get(path)
            if chunk is None:
                continue
            patch = None
            if deep:
                patch = self._deep_fix(state, path, chunk["content"], finding)
            if patch is None:
                patch = self._scaffold(path, chunk["content"], finding.title)
            if patch is not None:
                state.patches.append(patch)
                if patch.kind == "fix":
                    fixes += 1

        total = len(state.patches)
        if deep:
            summary = (
                f"Drafted {total} patch(es): {fixes} deep fix draft(s) + "
                f"{total - fixes} scaffold(s) for review."
            )
        else:
            summary = f"Drafted {total} scoped patch scaffold(s) for review."
        state.timeline.append(AgentStep(node="patch_writer", summary=summary))
        return state

    def _scaffold(self, path: str, content: str, title: str) -> Patch | None:
        marker = f"{_comment_prefix(path)} RepoPilot: review - {title}\n"
        diff = build_git_diff(path, content, marker + content)
        if not diff:
            return None
        return Patch(path=path, diff=diff, finding_title=title, kind="scaffold")

    def _deep_fix(
        self, state: AgentState, path: str, content: str, finding: Finding
    ) -> Patch | None:
        prompt = (
            f"Issue: {finding.title}\n{finding.summary}\n\n"
            f"File: {path}\n```\n{content}\n```\n\n"
            "Return the full corrected chunk only."
        )
        try:
            raw = self.llm.complete(_FIX_SYSTEM, prompt)
        except LLMError as exc:
            state.timeline.append(
                AgentStep(node="patch_writer", summary=f"Deep patch unavailable: {exc}")
            )
            return None
        diff = build_git_diff(path, content, _strip_fences(raw))
        if not diff:  # model returned the chunk unchanged -> nothing to apply
            return None
        return Patch(path=path, diff=diff, finding_title=finding.title, kind="fix")
