from app.agents.state import AgentState
from app.core.llm import LLMProvider
from app.domain.models import AgentStep


class PatchWriterNode:
    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    def run(self, state: AgentState) -> AgentState:
        summary = "Patch generation requires explicit user approval." if "patch" in state.task else "Skipped patch generation."
        state.timeline.append(AgentStep(node="patch_writer", summary=summary))
        return state
