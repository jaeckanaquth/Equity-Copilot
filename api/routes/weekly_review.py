from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import date

from db.session import SessionLocal
from core.repositories.artifact_repository import ArtifactRepository
from core.repositories.lifecycle_repository import BeliefLifecycleRepository
from core.repositories.cadence_repository import CadenceRepository
from core.repositories.proposal_repository import ProposalRepository
from core.repositories.question_answer_repository import QuestionAnswerRepository
from core.services.introspection_service import IntrospectionService
from core.services.belief_analysis_service import BeliefAnalysisService
from core.services.artifact_integrity_service import ArtifactIntegrityService
from core.services.proposal_engine import ProposalEngine
from core.templates import templates
from core.models.reasoning_artifact import ReasoningArtifact, ArtifactType

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

    answer_repo = QuestionAnswerRepository(db)
    introspection = IntrospectionService(artifact_repo, answer_repo.answered_question_ids())
    belief_analysis = BeliefAnalysisService(artifact_repo, lifecycle_repo)
    integrity = ArtifactIntegrityService(artifact_repo)

    questions = introspection.get_open_questions()
    stale_beliefs = belief_analysis.get_beliefs_needing_review()
    all_beliefs = belief_analysis.get_all_beliefs_grouped()

    cadence_repo = CadenceRepository(db)
    today = date.today()
    cadence_rows = cadence_repo.list_due(today)
    cadence_due = []
    for row in cadence_rows:
        belief = artifact_repo.get(row.belief_id)
        if not belief or not isinstance(belief, ReasoningArtifact) or belief.artifact_type not in {ArtifactType.thesis, ArtifactType.risk}:
            continue
        tickers = set()
        for sid in belief.references.snapshot_ids:
            snap = artifact_repo.get(str(sid))
            if snap and getattr(snap, "company", None) and getattr(snap.company, "ticker", None):
                tickers.add(snap.company.ticker)
        company = ", ".join(sorted(tickers)) if tickers else "uncoupled"
        cadence_due.append({
            "belief_id": row.belief_id,
            "belief_text": belief.claim.statement or "",
            "next_review_by": row.next_review_by.isoformat() if row.next_review_by else "",
            "cadence_days": row.cadence_days,
            "company": company,
        })

    proposals_total = sum(
        sum(len(instances) for instances in clusters.values())
        for clusters in proposals.values()
    )

    grounding_updated = request.query_params.get("grounding_updated") == "1"
    grounding_detail = request.query_params.get("detail", "")

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
            "cadence_due": cadence_due,
            "cadence_due_total": len(cadence_due),
            "all_beliefs": all_beliefs,
            "all_beliefs_total": sum(len(v) for v in all_beliefs.values()),
            "orphans": integrity.get_orphans(),
            "grounding_updated": grounding_updated,
            "grounding_detail": grounding_detail,
        }
    )
