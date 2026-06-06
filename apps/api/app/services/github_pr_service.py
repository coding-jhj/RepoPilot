"""Real GitHub pull-request creation over the REST API.

This replaces the previous mock. It is intentionally opt-in: a PR is only created
when the caller supplies a token. Without one, :class:`GitHubService` keeps
returning a mocked response so the free public demo never needs credentials.

The flow is the standard "branch + commit + open PR" dance:

1. resolve the base branch head SHA
2. create a new branch ref from it
3. upsert each changed file with the Contents API on that branch
4. open the pull request

An ``httpx.Client`` is injected so tests can drive it with ``httpx.MockTransport``
and assert the call sequence without touching the network.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass

import httpx

GITHUB_API = "https://api.github.com"


@dataclass(frozen=True)
class FileChange:
    path: str
    content: str


class GitHubError(RuntimeError):
    """Raised when the GitHub API rejects a request in the PR flow."""


class GitHubPRService:
    def __init__(self, token: str, client: httpx.Client | None = None) -> None:
        self._owns_client = client is None
        self._client = client or httpx.Client(
            base_url=GITHUB_API,
            timeout=20.0,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "GitHubPRService":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()

    def create_pull_request(
        self,
        *,
        owner: str,
        repo: str,
        base: str,
        head: str,
        title: str,
        body: str,
        files: list[FileChange],
        commit_message: str | None = None,
    ) -> dict:
        if not files:
            raise GitHubError("Refusing to open a pull request with no file changes.")

        base_sha = self._branch_sha(owner, repo, base)
        self._create_branch(owner, repo, head, base_sha)
        for change in files:
            self._upsert_file(
                owner,
                repo,
                head,
                change,
                message=commit_message or f"RepoPilot: update {change.path}",
            )
        return self._open_pr(owner, repo, base=base, head=head, title=title, body=body)

    # --- individual REST steps -------------------------------------------------

    def _branch_sha(self, owner: str, repo: str, branch: str) -> str:
        response = self._client.get(f"/repos/{owner}/{repo}/git/ref/heads/{branch}")
        self._raise_for(response, f"resolve base branch '{branch}'")
        return response.json()["object"]["sha"]

    def _create_branch(self, owner: str, repo: str, branch: str, sha: str) -> None:
        response = self._client.post(
            f"/repos/{owner}/{repo}/git/refs",
            json={"ref": f"refs/heads/{branch}", "sha": sha},
        )
        self._raise_for(response, f"create branch '{branch}'")

    def _upsert_file(
        self, owner: str, repo: str, branch: str, change: FileChange, *, message: str
    ) -> None:
        # An update needs the existing blob SHA; a new file must omit it.
        existing = self._client.get(
            f"/repos/{owner}/{repo}/contents/{change.path}", params={"ref": branch}
        )
        payload: dict = {
            "message": message,
            "content": base64.b64encode(change.content.encode("utf-8")).decode("ascii"),
            "branch": branch,
        }
        if existing.status_code == 200:
            payload["sha"] = existing.json()["sha"]

        response = self._client.put(
            f"/repos/{owner}/{repo}/contents/{change.path}", json=payload
        )
        self._raise_for(response, f"commit '{change.path}'")

    def _open_pr(
        self, owner: str, repo: str, *, base: str, head: str, title: str, body: str
    ) -> dict:
        response = self._client.post(
            f"/repos/{owner}/{repo}/pulls",
            json={"title": title, "head": head, "base": base, "body": body},
        )
        self._raise_for(response, "open pull request")
        data = response.json()
        return {
            "status": "created",
            "url": data.get("html_url"),
            "message": f"Pull request #{data.get('number')} opened against {base}.",
        }

    @staticmethod
    def _raise_for(response: httpx.Response, action: str) -> None:
        if response.is_success:
            return
        detail = ""
        try:
            detail = response.json().get("message", "")
        except Exception:
            detail = response.text[:200]
        raise GitHubError(f"Failed to {action}: HTTP {response.status_code} {detail}".strip())
