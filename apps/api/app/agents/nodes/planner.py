from app.agents.state import AgentState
from app.core.llm import LLMProvider
from app.domain.models import AgentStep


class PlannerNode:
    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    def run(self, state: AgentState) -> AgentState:
        state.timeline.append(
            AgentStep(
                node="planner",
                summary=f"Planned scoped analysis for {state.task}.",
            )
        )
        return state
