from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


RepoStatus = Literal["cloning", "indexed", "failed"]
AnalysisStatus = Literal["queued", "running", "completed", "failed"]
AnalysisType = Literal[
    "overview",
    "architecture",
    "bug_scan",
    "refactor_plan",
    "test_generation",
    "patch_generation",
]


@dataclass(frozen=True)
class ParsedRepoUrl:
    owner: str
    name: str
    clone_url: str


@dataclass(frozen=True)
class CodeSymbol:
    name: str
    kind: str
    line: int


@dataclass(frozen=True)
class CodeDocument:
    path: str
    language: str
    content: str
    imports: list[str] = field(default_factory=list)
    symbols: list[CodeSymbol] = field(default_factory=list)


@dataclass(frozen=True)
class CodeChunk:
    path: str
    start_line: int
    end_line: int
    content: str


@dataclass(frozen=True)
class Evidence:
    path: str
    start_line: int
    end_line: int


@dataclass(frozen=True)
class Finding:
    title: str
    summary: str
    severity: Literal["info", "low", "medium", "high"]
    evidence: list[Evidence]


@dataclass(frozen=True)
class AgentStep:
    node: str
    summary: str


@dataclass(frozen=True)
class AgentResult:
    status: AnalysisStatus
    summary: str
    findings: list[Finding]
    timeline: list[AgentStep]


@dataclass(frozen=True)
class Patch:
    path: str
    diff: str
    finding_title: str


@dataclass(frozen=True)
class PatchValidationReport:
    valid: bool
    touched_paths: list[str]
    messages: list[str]
