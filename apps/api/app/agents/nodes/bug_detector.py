from app.agents.state import AgentState
from app.core.llm import LLMProvider
from app.domain.models import AgentStep, Evidence, Finding


class BugDetectorNode:
    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    def run(self, state: AgentState) -> AgentState:
        if "bug" not in state.task and "patch" not in state.task:
            state.timeline.append(
                AgentStep(node="bug_detector", summary="Skipped bug scan for this task.")
            )
            return state
        if not state.retrieved_chunks:
            return state
        chunk = state.retrieved_chunks[0]
        state.findings.append(
            Finding(
                title="Review candidate from selected code",
                summary=self.llm.complete("Find scoped code risks.", chunk["content"]),
                severity="medium",
                evidence=[
                    Evidence(
                        path=chunk["path"],
                        start_line=chunk["start_line"],
                        end_line=chunk["end_line"],
                    )
                ],
            )
        )
        state.timeline.append(
            AgentStep(node="bug_detector", summary="Added one evidence-backed review candidate.")
        )
        return state
