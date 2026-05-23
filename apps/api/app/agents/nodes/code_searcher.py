from app.agents.state import AgentState
from app.core.llm import LLMProvider
from app.domain.models import AgentStep


class CodeSearcherNode:
    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    def run(self, state: AgentState) -> AgentState:
        state.timeline.append(
            AgentStep(
                node="code_searcher",
                summary=f"Retrieved {len(state.retrieved_chunks)} code chunks with line metadata.",
            )
        )
        return state
