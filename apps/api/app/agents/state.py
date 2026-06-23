from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.models import AgentStep, Finding, Patch


@dataclass
class AgentState:
    repo_id: str
    task: str
    retrieved_chunks: list[dict]
    findings: list[Finding] = field(default_factory=list)
    timeline: list[AgentStep] = field(default_factory=list)
    summary: str = ""
    deep: bool = False
    patches: list[Patch] = field(default_factory=list)
