from __future__ import annotations

import re
from pathlib import Path

from app.agents.nodes.bug_detector import MANUAL_REVIEW_TITLE
from app.agents.state import AgentState
from app.core.llm import LLMProvider
from app.domain.models import AgentStep, TestSkeleton


def _test_name(path: str, taken: set[str]) -> str:
    stem = re.sub(r"\W+", "_", Path(path).stem).strip("_") or "code"
    base = f"test_{stem}"
    name = base
    i = 2
    while name in taken:
        name = f"{base}_{i}"
        i += 1
    taken.add(name)
    return name


class TestWriterNode:
    """Draft a regression-test skeleton for each substantive finding.

    This is a skeleton, not a passing test: a deterministic generator cannot know
    the correct assertion without the fix. It emits valid Python with a failing
    ``test_*`` placeholder that names the flagged evidence, so a developer has a
    scoped starting point. The test eval pins structural validity (parses, has a
    test function, references the evidence), not test correctness.
    """

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    def run(self, state: AgentState) -> AgentState:
        if "test" not in state.task:
            state.timeline.append(
                AgentStep(node="test_writer", summary="Skipped test generation.")
            )
            return state

        taken: set[str] = set()
        for finding in state.findings:
            if finding.title == MANUAL_REVIEW_TITLE or not finding.evidence:
                continue
            path = finding.evidence[0].path
            code = self._skeleton(_test_name(path, taken), path, finding.title)
            state.test_skeletons.append(
                TestSkeleton(path=path, code=code, finding_title=finding.title)
            )

        state.timeline.append(
            AgentStep(
                node="test_writer",
                summary=f"Drafted {len(state.test_skeletons)} regression-test skeleton(s).",
            )
        )
        return state

    def _skeleton(self, name: str, path: str, title: str) -> str:
        return (
            f"# RepoPilot regression-test skeleton - {title}\n"
            f"# Evidence: {path}\n"
            f"def {name}():\n"
            f'    """Cover the issue flagged in {path}; fill in arrange/act/assert."""\n'
            f'    raise AssertionError("test skeleton not implemented")\n'
        )
