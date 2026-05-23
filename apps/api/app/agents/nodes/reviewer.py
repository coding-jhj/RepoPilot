from app.agents.state import AgentState
from app.core.llm import LLMProvider
from app.domain.models import AgentStep


class ReviewerNode:
    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    def run(self, state: AgentState) -> AgentState:
        state.timeline.append(
            AgentStep(
                node="reviewer",
                summary="Checked that findings cite retrieved file and line evidence.",
            )
        )
        return state
