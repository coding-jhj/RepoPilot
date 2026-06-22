from __future__ import annotations

from app.agents.nodes.architecture_analyzer import ArchitectureAnalyzerNode
from app.agents.nodes.bug_detector import BugDetectorNode
from app.agents.nodes.code_searcher import CodeSearcherNode
from app.agents.nodes.patch_writer import PatchWriterNode
from app.agents.nodes.planner import PlannerNode
from app.agents.nodes.repo_reader import RepoReaderNode
from app.agents.nodes.reviewer import ReviewerNode
from app.agents.nodes.test_writer import TestWriterNode
from app.agents.state import AgentState
from app.core.llm import LLMProvider
from app.domain.models import AgentResult


class RepoPilotAgent:
    def __init__(self, llm: LLMProvider) -> None:
        self.nodes = [
            PlannerNode(llm),
            RepoReaderNode(llm),
            CodeSearcherNode(llm),
            ArchitectureAnalyzerNode(llm),
            BugDetectorNode(llm),
            TestWriterNode(llm),
            PatchWriterNode(llm),
            ReviewerNode(llm),
        ]

    def run(
        self, repo_id: str, task: str, retrieved_chunks: list[dict], deep: bool = False
    ) -> AgentResult:
        state = AgentState(
            repo_id=repo_id, task=task, retrieved_chunks=retrieved_chunks, deep=deep
        )
        for node in self.nodes:
            state = node.run(state)
        return AgentResult(
            status="completed",
            summary=state.summary,
            findings=state.findings,
            timeline=state.timeline,
        )
