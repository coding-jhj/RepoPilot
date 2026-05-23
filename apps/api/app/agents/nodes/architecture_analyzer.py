from app.agents.state import AgentState
from app.core.llm import LLMProvider
from app.domain.models import AgentStep, Evidence, Finding


class ArchitectureAnalyzerNode:
    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    def run(self, state: AgentState) -> AgentState:
        if not state.retrieved_chunks:
            state.summary = "No indexed evidence is available for this repository yet."
            return state
        first = state.retrieved_chunks[0]
        state.summary = self.llm.complete(
            "You are RepoPilot, a repo-aware software engineering agent.",
            f"Summarize {state.task} using evidence from {first['path']}.",
        )
        state.findings.append(
            Finding(
                title="Repository behavior is grounded in retrieved code",
                summary=state.summary,
                severity="info",
                evidence=[
                    Evidence(
                        path=first["path"],
                        start_line=first["start_line"],
                        end_line=first["end_line"],
                    )
                ],
            )
        )
        state.timeline.append(
            AgentStep(node="architecture_analyzer", summary="Produced evidence-backed summary.")
        )
        return state
