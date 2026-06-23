from fastapi import APIRouter, Depends

from app.api.deps import services
from app.code.diff import apply_patch_to_text
from app.domain.schemas import (
    PullRequestFromPatchRequest,
    PullRequestRequest,
    PullRequestResponse,
)

router = APIRouter(prefix="/github", tags=["github"])


@router.post("/pr", response_model=PullRequestResponse)
def create_pull_request(
    payload: PullRequestRequest, app_services: dict = Depends(services)
):
    return app_services["github_service"].create_pull_request(
        repo_id=payload.repo_id,
        title=payload.title,
        body=payload.body,
        diff=payload.diff,
        confirmed=payload.confirmed,
        token=payload.token,
        owner=payload.owner,
        repo=payload.repo,
        base=payload.base,
        head=payload.head,
        files=[file.model_dump() for file in payload.files] if payload.files else None,
    )


@router.post("/pr-from-patch", response_model=PullRequestResponse)
def create_pull_request_from_patch(
    payload: PullRequestFromPatchRequest, app_services: dict = Depends(services)
):
    """Turn one patch into a real PR: read the workspace file, apply the diff to
    get full new content, then hand it to the same opt-in PR flow."""
    if payload.confirmed and payload.token:
        repo_service = app_services["repo_service"]
        try:
            original = repo_service.read_file(payload.repo_id, payload.path)
        except (ValueError, FileNotFoundError, OSError) as exc:
            return PullRequestResponse(
                status="error", url=None, message=f"Cannot read {payload.path}: {exc}"
            )
        try:
            new_content = apply_patch_to_text(original, payload.diff, payload.path)
        except ValueError as exc:
            return PullRequestResponse(status="error", url=None, message=str(exc))
        files = [{"path": payload.path, "content": new_content}]
    else:
        # No token or unconfirmed: the service returns a mocked/blocked response
        # without ever touching the workspace, so no files are needed.
        files = None

    return app_services["github_service"].create_pull_request(
        repo_id=payload.repo_id,
        title=payload.title,
        body=payload.body,
        diff=payload.diff,
        confirmed=payload.confirmed,
        token=payload.token,
        owner=payload.owner,
        repo=payload.repo,
        base=payload.base,
        head=payload.head,
        files=files,
    )
