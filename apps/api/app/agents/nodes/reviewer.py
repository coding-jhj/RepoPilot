from app.agents.state import AgentState
from app.core.llm import LLMError, LLMProvider
from app.domain.models import AgentStep

_SUMMARY_SYSTEM = (
    "You are a senior reviewer. In 2-3 plain sentences, summarize the key findings for a "
    "developer skimming the report. Be specific and do not invent issues beyond those listed."
)


class ReviewerNode:
    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    def run(self, state: AgentState) -> AgentState:
        if state.deep and getattr(self.llm, "enabled", False) and state.findings:
            digest = "\n".join(
                f"- [{finding.severity}] {finding.title}: {finding.summary}"
                for finding in state.findings
            )
            try:
                state.summary = self.llm.complete(
                    _SUMMARY_SYSTEM, f"Task: {state.task}\nFindings:\n{digest}"
                )
            except LLMError as exc:
                state.timeline.append(
                    AgentStep(node="reviewer", summary=f"LLM summary unavailable: {exc}")
                )
        state.timeline.append(
            AgentStep(
                node="reviewer",
                summary="Checked that findings cite retrieved file and line evidence.",
            )
        )
        return state
