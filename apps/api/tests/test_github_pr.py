import httpx
import pytest

from app.code.diff import apply_patch_to_text, build_git_diff
from app.services.github_service import GitHubService
from app.services.repo_service import RepoService


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


def test_read_file_reads_workspace_and_blocks_escape(tmp_path):
    svc = RepoService(tmp_path)
    workspace = svc.workspace_for("repo_test")
    workspace.mkdir(parents=True)
    (workspace / "a.py").write_text("x = 1\n", encoding="utf-8")

    assert svc.read_file("repo_test", "a.py") == "x = 1\n"
    with pytest.raises(ValueError):
        svc.read_file("repo_test", "../../../etc/passwd")  # escape refused
    with pytest.raises(FileNotFoundError):
        svc.read_file("repo_test", "missing.py")


def test_pr_from_patch_composition_opens_real_pr(tmp_path):
    # What the /github/pr-from-patch route does: read the workspace file, apply the
    # chunk-relative diff to get full content, then open a real PR with that file.
    svc = RepoService(tmp_path)
    workspace = svc.workspace_for("repo_test")
    workspace.mkdir(parents=True)
    full = (
        "def load(path):\n    try:\n        return read(path)\n"
        "    except:\n        return None\n"
    )
    (workspace / "loader.py").write_text(full, encoding="utf-8")

    chunk = "    except:\n        return None"
    fixed = "    except Exception as err:\n        log(err)\n        return None"
    diff = build_git_diff("loader.py", chunk, fixed)

    original = svc.read_file("repo_test", "loader.py")
    new_content = apply_patch_to_text(original, diff, "loader.py")
    assert "except Exception as err:" in new_content
    assert "    except:\n" not in new_content

    calls: list[tuple[str, str]] = []
    result = GitHubService().create_pull_request(
        repo_id="repo_test",
        title="Fix bare except",
        body="by RepoPilot",
        diff=diff,
        confirmed=True,
        token="ghp_fake",
        owner="acme",
        repo="widget",
        base="main",
        head="repopilot/fix",
        files=[{"path": "loader.py", "content": new_content}],
        client=_mock_github(calls),
    )
    assert result["status"] == "created"
    assert ("PUT", "/repos/acme/widget/contents/loader.py") in calls
