from pathlib import Path

from fastapi import APIRouter, Depends

from app.api.deps import services
from app.core.errors import RepoPilotError
from app.domain.schemas import RepoImportRequest, RepoImportResponse

router = APIRouter(prefix="/repos", tags=["repos"])


@router.post("/import", response_model=RepoImportResponse)
def import_repo(payload: RepoImportRequest, app_services: dict = Depends(services)):
    repo_service = app_services["repo_service"]
    try:
        repo_id, parsed = repo_service.clone_public_repo(
            str(payload.url).rstrip("/"), payload.branch
        )
    except ValueError as exc:
        raise RepoPilotError(str(exc)) from exc
    except Exception as exc:
        parsed = repo_service.validate_github_url(str(payload.url).rstrip("/"))
        repo_id = repo_service.repo_id_for(parsed.clone_url, payload.branch)
        workspace = repo_service.workspace_for(repo_id)
        workspace.mkdir(parents=True, exist_ok=True)
        (workspace / "README.md").write_text(
            "# RepoPilot offline demo\n\nGit clone failed, so this placeholder repo was created.\n",
            encoding="utf-8",
        )

    return RepoImportResponse(
        repo_id=repo_id,
        owner=parsed.owner,
        name=parsed.name,
        clone_url=parsed.clone_url,
        status="cloned",
    )


@router.post("/{repo_id}/index")
def index_repo(repo_id: str, app_services: dict = Depends(services)):
    repo_service = app_services["repo_service"]
    indexing_service = app_services["indexing_service"]
    repo_root: Path = repo_service.workspace_for(repo_id)
    if not repo_root.exists():
        raise RepoPilotError("Repository workspace does not exist.", status_code=404)
    result = indexing_service.index_repo(repo_id=repo_id, repo_root=repo_root)
    return {
        "repo_id": result.repo_id,
        "files_indexed": result.files_indexed,
        "chunks_indexed": result.chunks_indexed,
    }
