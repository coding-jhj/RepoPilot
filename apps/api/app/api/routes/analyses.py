from fastapi import APIRouter, Depends

from app.api.deps import services
from app.domain.schemas import AnalysisRequest, AnalysisResponse

router = APIRouter(prefix="/analyses", tags=["analyses"])


@router.post("", response_model=AnalysisResponse)
def create_analysis(payload: AnalysisRequest, app_services: dict = Depends(services)):
    result = app_services["analysis_service"].analyze(
        repo_id=payload.repo_id,
        task=payload.task,
        deep=payload.deep,
        api_key=payload.api_key,
        model=payload.model,
    )
    return result
