from datetime import datetime, timezone
from uuid import uuid4, UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.session import SessionLocal
from core.repositories.artifact_repository import ArtifactRepository
from core.repositories.lifecycle_repository import BeliefLifecycleRepository
from core.models.reasoning_artifact import ReasoningArtifact, ArtifactType
from core.models.belief_lifecycle_event import BeliefReviewOutcomeEvent, ReviewOutcome
from core.services.belief_analysis_service import BeliefAnalysisService
from core.models.stock_snapshot import StockSnapshot
from core.templates import templates


class ReviewOutcomeBody(BaseModel):
    outcome: str
    note: str | None = None

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/questions/{question_id}", response_class=HTMLResponse)
def question_detail(question_id: str, request: Request, db: Session = Depends(get_db)):
    artifact_repo = ArtifactRepository(db)
    question = artifact_repo.get(question_id)

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if not isinstance(question, ReasoningArtifact) or question.artifact_type != ArtifactType.question:
        raise HTTPException(status_code=404, detail="Question not found")

    return templates.TemplateResponse(
        "question_detail.html",
        {"request": request, "question": question},
    )


@router.get("/beliefs/{belief_id}", response_class=HTMLResponse)
def belief_detail(belief_id: str, request: Request, db: Session = Depends(get_db)):
    artifact_repo = ArtifactRepository(db)
    lifecycle_repo = BeliefLifecycleRepository(db)

    belief = artifact_repo.get(belief_id)

    if not belief:
        raise HTTPException(status_code=404, detail="Belief not found")
    if not isinstance(belief, ReasoningArtifact) or belief.artifact_type not in {
        ArtifactType.thesis,
        ArtifactType.risk,
    }:
        raise HTTPException(status_code=404, detail="Belief not found")

    orm_events = lifecycle_repo.list_for_belief(belief_id)
    lifecycle_events = [
        {"created_at": e.created_at, "payload": e.payload} for e in orm_events
    ]

    analysis = BeliefAnalysisService(artifact_repo, lifecycle_repo)
    grouped = analysis.get_beliefs_needing_review()
    has_newer_snapshots = any(
        item["belief_id"] == belief_id
        for items in grouped.values()
        for item in items
    )

    return templates.TemplateResponse(
        "belief_detail.html",
        {
            "request": request,
            "belief": belief,
            "lifecycle_events": lifecycle_events,
            "has_newer_snapshots": has_newer_snapshots,
        },
    )


@router.post("/api/beliefs/{belief_id}/review-outcome", status_code=201)
def record_review_outcome(
    belief_id: str,
    body: ReviewOutcomeBody,
    db: Session = Depends(get_db),
):
    """Record a manual review outcome (human-judged only)."""
    artifact_repo = ArtifactRepository(db)
    lifecycle_repo = BeliefLifecycleRepository(db)
    belief = artifact_repo.get(belief_id)
    if not belief:
        raise HTTPException(status_code=404, detail="Belief not found")
    if not isinstance(belief, ReasoningArtifact) or belief.artifact_type not in {
        ArtifactType.thesis,
        ArtifactType.risk,
    }:
        raise HTTPException(status_code=404, detail="Belief not found")
    try:
        outcome = ReviewOutcome(body.outcome)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="outcome must be one of: reinforced, slight_tension, strong_tension, inconclusive",
        )
    note = (body.note or "").strip()[:500] or None
    now = datetime.now(timezone.utc)
    event = BeliefReviewOutcomeEvent(
        event_id=uuid4(),
        schema_version="v1",
        occurred_at=now,
        recorded_by="human",
        reasoning_id=UUID(belief_id),
        event_kind="review_outcome",
        trigger="manual_review",
        outcome=outcome,
        note=note,
    )
    lifecycle_repo.append(event)
    return None


@router.get("/snapshots/{snapshot_id}", response_class=HTMLResponse)
def snapshot_detail(snapshot_id: str, request: Request, db: Session = Depends(get_db)):
    artifact_repo = ArtifactRepository(db)
    snapshot = artifact_repo.get(snapshot_id)

    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    if not isinstance(snapshot, StockSnapshot):
        raise HTTPException(status_code=404, detail="Snapshot not found")

    return templates.TemplateResponse(
        "snapshot_detail.html",
        {"request": request, "snapshot": snapshot},
    )
