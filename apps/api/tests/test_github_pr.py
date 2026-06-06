import httpx

from app.services.github_service import GitHubService


def _mock_github(calls: list[tuple[str, str]]):
    """An httpx client whose transport fakes the GitHub PR endpoints.

    Records (method, path) for every call so the test can assert the sequence.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, request.url.path))
        path = request.url.path
        if request.method == "GET" and path.endswith("/git/ref/heads/main"):
            return httpx.Response(200, json={"object": {"sha": "basesha123"}})
        if request.method == "POST" and path.endswith("/git/refs"):
            return httpx.Response(201, json={})
        if request.method == "GET" and "/contents/" in path:
            return httpx.Response(404, json={"message": "Not Found"})  # new file
        if request.method == "PUT" and "/contents/" in path:
            return httpx.Response(201, json={"content": {"sha": "blobsha"}})
        if request.method == "POST" and path.endswith("/pulls"):
            return httpx.Response(
                201,
                json={"html_url": "https://github.com/acme/widget/pull/7", "number": 7},
            )
        return httpx.Response(500, json={"message": "unexpected"})

    return httpx.Client(base_url="https://api.github.com", transport=httpx.MockTransport(handler))


def test_real_pr_is_created_when_token_and_files_present():
    calls: list[tuple[str, str]] = []
    result = GitHubService().create_pull_request(
        repo_id="repo_1",
        title="Fix typo",
        body="Patch by RepoPilot",
        diff="",
        confirmed=True,
        token="ghp_fake",
        owner="acme",
        repo="widget",
        base="main",
        head="repopilot/patch-test",
        files=[{"path": "README.md", "content": "# Hello\n"}],
        client=_mock_github(calls),
    )

    assert result["status"] == "created"
    assert result["url"] == "https://github.com/acme/widget/pull/7"
    # Branch -> commit -> PR, in order.
    assert ("GET", "/repos/acme/widget/git/ref/heads/main") in calls
    assert ("POST", "/repos/acme/widget/git/refs") in calls
    assert ("PUT", "/repos/acme/widget/contents/README.md") in calls
    assert calls[-1] == ("POST", "/repos/acme/widget/pulls")


def test_blocked_without_confirmation():
    result = GitHubService().create_pull_request(
        repo_id="repo_1", title="t", body="b", diff="", confirmed=False, token="ghp_fake"
    )
    assert result["status"] == "blocked"
    assert result["url"] is None


def test_mocked_when_no_token():
    result = GitHubService().create_pull_request(
        repo_id="repo_xyz9", title="t", body="b", diff="", confirmed=True
    )
    assert result["status"] == "mocked"
    assert result["url"].endswith("/pull/xyz9")


def test_error_when_token_but_missing_repo_or_files():
    result = GitHubService().create_pull_request(
        repo_id="repo_1", title="t", body="b", diff="", confirmed=True, token="ghp_fake"
    )
    assert result["status"] == "error"
    assert "owner" in result["message"]
