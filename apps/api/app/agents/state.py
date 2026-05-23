from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.models import AgentStep, Finding


@dataclass
class AgentState:
    repo_id: str
    task: str
    retrieved_chunks: list[dict]
    findings: list[Finding] = field(default_factory=list)
    timeline: list[AgentStep] = field(default_factory=list)
    summary: str = ""
