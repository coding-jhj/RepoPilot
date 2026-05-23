from app.agents.state import AgentState
from app.core.llm import LLMProvider
from app.domain.models import AgentStep


class RepoReaderNode:
    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    def run(self, state: AgentState) -> AgentState:
        paths = sorted({chunk["path"] for chunk in state.retrieved_chunks})
        state.timeline.append(
            AgentStep(
                node="repo_reader",
                summary=f"Read {len(paths)} evidence files: {', '.join(paths[:4])}.",
            )
        )
        return state
