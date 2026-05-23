from __future__ import annotations

from app.agents.graph import RepoPilotAgent
from app.domain.models import AgentResult
from app.rag.retriever import InMemoryRetriever


class AnalysisService:
    def __init__(self, agent: RepoPilotAgent, retriever: InMemoryRetriever) -> None:
        self.agent = agent
        self.retriever = retriever

    def analyze(self, repo_id: str, task: str, deep: bool = False) -> AgentResult:
        limit = 12 if deep else 5
        chunks = self.retriever.search(task.replace("_", " "), repo_id=repo_id, limit=limit)
        return self.agent.run(
            repo_id=repo_id,
            task=task,
            retrieved_chunks=[
                {
                    "path": chunk.path,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "content": chunk.content,
                }
                for chunk in chunks
            ],
        )
