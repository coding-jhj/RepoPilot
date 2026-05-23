from fastapi import APIRouter, Depends

from app.api.deps import services
from app.domain.schemas import PullRequestRequest, PullRequestResponse

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
    )
