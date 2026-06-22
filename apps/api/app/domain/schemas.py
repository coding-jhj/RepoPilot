from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class RepoImportRequest(BaseModel):
    url: HttpUrl
    branch: str = Field(default="main", min_length=1, max_length=128)


class RepoImportResponse(BaseModel):
    repo_id: str
    owner: str
    name: str
    clone_url: str
    status: str


class AnalysisRequest(BaseModel):
    repo_id: str
    task: Literal[
        "overview",
        "architecture",
        "bug_scan",
        "refactor_plan",
        "test_generation",
        "patch_generation",
    ]
    deep: bool = False
    api_key: str | None = None
    model: str | None = None


class EvidenceResponse(BaseModel):
    path: str
    start_line: int
    end_line: int


class FindingResponse(BaseModel):
    title: str
    summary: str
    severity: str
    evidence: list[EvidenceResponse]


class AgentStepResponse(BaseModel):
    node: str
    summary: str


class AnalysisResponse(BaseModel):
    status: str
    summary: str
    findings: list[FindingResponse]
    timeline: list[AgentStepResponse]


class ChatRequest(BaseModel):
    repo_id: str
    question: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    answer: str
    evidence: list[EvidenceResponse]


class PatchRequest(BaseModel):
    repo_id: str
    instruction: str
    approved_paths: list[str]


class PatchResponse(BaseModel):
    diff: str
    valid: bool
    touched_paths: list[str]
    messages: list[str]


class PullRequestFile(BaseModel):
    path: str = Field(min_length=1)
    content: str


class PullRequestRequest(BaseModel):
    repo_id: str
    title: str
    body: str
    diff: str
    confirmed: bool = False
    # Optional real-PR fields. When a token is present the service opens a real
    # pull request; otherwise it stays a mocked demo response.
    token: str | None = None
    owner: str | None = None
    repo: str | None = None
    base: str = "main"
    head: str | None = None
    files: list[PullRequestFile] | None = None


class PullRequestResponse(BaseModel):
    status: str
    url: str | None = None
    message: str
