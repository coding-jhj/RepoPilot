from app.agents.state import AgentState
from app.core.llm import LLMProvider
from app.domain.models import AgentStep


class TestWriterNode:
    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    def run(self, state: AgentState) -> AgentState:
        summary = "Prepared test strategy for selected evidence." if "test" in state.task else "Skipped test generation."
        state.timeline.append(AgentStep(node="test_writer", summary=summary))
        return state
