from __future__ import annotations

from app.agents.graph import RepoPilotAgent
from app.core.llm import build_llm_provider
from app.domain.models import AgentResult
from app.rag.retriever import InMemoryRetriever


class AnalysisService:
    def __init__(self, agent: RepoPilotAgent, retriever: InMemoryRetriever) -> None:
        self.agent = agent
        self.retriever = retriever

    def analyze(
        self,
        repo_id: str,
        task: str,
        deep: bool = False,
        api_key: str | None = None,
        model: str | None = None,
    ) -> AgentResult:
        agent = self.agent
        if deep and api_key:
            llm = build_llm_provider("gemini", api_key=api_key, model=model)
            agent = RepoPilotAgent(llm=llm)
        limit = 12 if deep else 5
        chunks = self.retriever.search(task.replace("_", " "), repo_id=repo_id, limit=limit)
        return agent.run(
            repo_id=repo_id,
            task=task,
            deep=deep,
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
