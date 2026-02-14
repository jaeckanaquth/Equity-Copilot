from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from db.session import SessionLocal
from core.repositories.artifact_repository import ArtifactRepository
from core.repositories.lifecycle_repository import BeliefLifecycleRepository
from core.repositories.proposal_repository import ProposalRepository
from core.services.introspection_service import IntrospectionService
from core.services.belief_analysis_service import BeliefAnalysisService
from core.services.artifact_integrity_service import ArtifactIntegrityService
from core.services.proposal_engine import ProposalEngine
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
    proposal_repo = ProposalRepository(db)

    proposal_engine = ProposalEngine(artifact_repo, lifecycle_repo, proposal_repo)
    proposal_engine.evaluate()
    proposals = proposal_engine.list_for_display()

    introspection = IntrospectionService(artifact_repo)
    belief_analysis = BeliefAnalysisService(artifact_repo, lifecycle_repo)
    integrity = ArtifactIntegrityService(artifact_repo)

    questions = introspection.get_open_questions()
    stale_beliefs = belief_analysis.get_beliefs_needing_review()
    all_beliefs = belief_analysis.get_all_beliefs_grouped()

    proposals_total = sum(
        sum(len(instances) for instances in clusters.values())
        for clusters in proposals.values()
    )

    return templates.TemplateResponse(
        "weekly_review.html",
        {
            "request": request,
            "proposals": proposals,
            "proposals_total": proposals_total,
            "questions": questions,
            "questions_total": sum(len(v) for v in questions.values()),
            "stale_beliefs": stale_beliefs,
            "stale_beliefs_total": sum(len(v) for v in stale_beliefs.values()),
            "all_beliefs": all_beliefs,
            "all_beliefs_total": sum(len(v) for v in all_beliefs.values()),
            "orphans": integrity.get_orphans(),
        }
    )
