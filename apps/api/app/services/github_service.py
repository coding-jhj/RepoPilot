from __future__ import annotations

import uuid

import httpx

from app.services.github_pr_service import FileChange, GitHubError, GitHubPRService


class GitHubService:
    """Entry point for PR creation.

    Opt-in by design: a real pull request is opened only when a ``token`` is
    supplied. Without one the public demo gets a mocked response and never needs
    credentials. ``confirmed`` is always required as a safety gate.
    """

    def create_pull_request(
        self,
        repo_id: str,
        title: str,
        body: str,
        diff: str,
        confirmed: bool,
        *,
        token: str | None = None,
        owner: str | None = None,
        repo: str | None = None,
        base: str = "main",
        head: str | None = None,
        files: list[dict] | None = None,
        client: httpx.Client | None = None,
    ) -> dict:
        if not confirmed:
            return {
                "status": "blocked",
                "url": None,
                "message": "PR creation requires explicit confirmation.",
            }

        if not token:
            # Free public demo path — unchanged mocked behaviour.
            return {
                "status": "mocked",
                "url": f"https://github.com/repopilot/demo/pull/{repo_id[-4:]}",
                "message": f"Mock PR created for: {title}",
            }

        if not (owner and repo and files):
            return {
                "status": "error",
                "url": None,
                "message": "A real PR needs owner, repo and at least one file change.",
            }

        branch = head or f"repopilot/patch-{uuid.uuid4().hex[:8]}"
        changes = [FileChange(path=f["path"], content=f["content"]) for f in files]

        try:
            with GitHubPRService(token=token, client=client) as service:
                return service.create_pull_request(
                    owner=owner,
                    repo=repo,
                    base=base,
                    head=branch,
                    title=title,
                    body=body,
                    files=changes,
                )
        except GitHubError as error:
            return {"status": "failed", "url": None, "message": str(error)}
