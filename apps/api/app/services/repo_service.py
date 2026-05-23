from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path

from app.domain.models import ParsedRepoUrl


class RepoService:
    _github_url_pattern = re.compile(
        r"^https://github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<name>[A-Za-z0-9_.-]+?)(?:\.git)?/?$"
    )

    def __init__(self, workspace_root: Path, clone_timeout_seconds: int = 45) -> None:
        self.workspace_root = workspace_root
        self.clone_timeout_seconds = clone_timeout_seconds
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate_github_url(cls, url: str) -> ParsedRepoUrl:
        match = cls._github_url_pattern.match(url)
        if not match:
            raise ValueError("Only public HTTPS GitHub repository URLs are supported.")
        owner = match.group("owner")
        name = match.group("name")
        if ".." in owner or ".." in name:
            raise ValueError("Repository URL contains unsafe path segments.")
        return ParsedRepoUrl(
            owner=owner,
            name=name,
            clone_url=f"https://github.com/{owner}/{name}.git",
        )

    def repo_id_for(self, clone_url: str, branch: str) -> str:
        digest = hashlib.sha1(f"{clone_url}:{branch}".encode("utf-8")).hexdigest()[:12]
        return f"repo_{digest}"

    def workspace_for(self, repo_id: str) -> Path:
        if not re.match(r"^repo_[a-fA-F0-9A-Za-z_-]+$", repo_id):
            raise ValueError("Invalid repo id.")
        workspace = (self.workspace_root / repo_id).resolve()
        if not workspace.is_relative_to(self.workspace_root.resolve()):
            raise ValueError("Workspace path escaped root.")
        return workspace

    def clone_public_repo(self, url: str, branch: str = "main") -> tuple[str, ParsedRepoUrl]:
        parsed = self.validate_github_url(url)
        repo_id = self.repo_id_for(parsed.clone_url, branch)
        workspace = self.workspace_for(repo_id)
        if workspace.exists() and (workspace / ".git").exists():
            return repo_id, parsed
        workspace.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                branch,
                parsed.clone_url,
                str(workspace),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=self.clone_timeout_seconds,
        )
        return repo_id, parsed
