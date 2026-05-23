from pathlib import Path

import pytest

from app.services.repo_service import RepoService


def test_validate_github_url_accepts_public_https_repo():
    parsed = RepoService.validate_github_url("https://github.com/example/project")

    assert parsed.owner == "example"
    assert parsed.name == "project"
    assert parsed.clone_url == "https://github.com/example/project.git"


@pytest.mark.parametrize(
    "url",
    [
        "https://evil.com/example/project",
        "git@github.com:example/project.git",
        "https://github.com/example",
        "https://github.com/example/project/../../secret",
    ],
)
def test_validate_github_url_rejects_unsafe_or_unsupported_urls(url):
    with pytest.raises(ValueError):
        RepoService.validate_github_url(url)


def test_workspace_path_is_stable_and_stays_inside_root(tmp_path: Path):
    service = RepoService(workspace_root=tmp_path)

    workspace = service.workspace_for("repo_123")

    assert workspace == tmp_path / "repo_123"
    assert workspace.resolve().is_relative_to(tmp_path.resolve())
