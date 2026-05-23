from fastapi import APIRouter, Depends

from app.api.deps import services
from app.domain.schemas import PatchRequest, PatchResponse

router = APIRouter(prefix="/patches", tags=["patches"])


@router.post("", response_model=PatchResponse)
def create_patch(payload: PatchRequest, app_services: dict = Depends(services)):
    patch_service = app_services["patch_service"]
    diff = patch_service.draft_patch(payload.instruction, payload.approved_paths)
    report = patch_service.validate(diff, payload.approved_paths)
    return PatchResponse(
        diff=diff,
        valid=report.valid,
        touched_paths=report.touched_paths,
        messages=report.messages,
    )
