from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from db.session import SessionLocal
from core.repositories.artifact_repository import ArtifactRepository
from core.repositories.lifecycle_repository import BeliefLifecycleRepository
from core.services.introspection_service import IntrospectionService
from core.services.belief_analysis_service import BeliefAnalysisService
from core.services.artifact_integrity_service import ArtifactIntegrityService
from core.templates import templates

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/weekly-review", response_class=HTMLResponse)
def weekly_review(request: Request, db: Session = Depends(get_db)):

    artifact_repo = ArtifactRepository(db)
    lifecycle_repo = BeliefLifecycleRepository(db)

    introspection = IntrospectionService(artifact_repo)
    belief_analysis = BeliefAnalysisService(artifact_repo, lifecycle_repo)
    integrity = ArtifactIntegrityService(artifact_repo)

    return templates.TemplateResponse(
        "weekly_review.html",
        {
            "request": request,
            "questions": introspection.get_open_questions(),
            "stale_beliefs": belief_analysis.get_beliefs_needing_review(),
            "orphans": integrity.get_orphans(),
        }
    )
