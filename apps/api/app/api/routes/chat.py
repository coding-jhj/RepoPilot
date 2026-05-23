from fastapi import APIRouter, Depends

from app.api.deps import services
from app.domain.schemas import ChatRequest, ChatResponse, EvidenceResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, app_services: dict = Depends(services)):
    chunks = app_services["retriever"].search(
        payload.question,
        repo_id=payload.repo_id,
        limit=4,
    )
    evidence = [
        EvidenceResponse(
            path=chunk.path,
            start_line=chunk.start_line,
            end_line=chunk.end_line,
        )
        for chunk in chunks
    ]
    if not chunks:
        answer = "No indexed evidence is available yet. Import and index a repo first."
    else:
        paths = ", ".join(chunk.path for chunk in chunks)
        answer = f"Grounded answer from retrieved code evidence: {paths}"
    return ChatResponse(answer=answer, evidence=evidence)
