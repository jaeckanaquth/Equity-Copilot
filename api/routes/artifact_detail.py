from datetime import datetime, timezone
from uuid import uuid4, UUID

from fastapi import APIRouter, Depends, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.session import SessionLocal
from core.repositories.artifact_repository import ArtifactRepository
from core.repositories.lifecycle_repository import BeliefLifecycleRepository
from core.repositories.cadence_repository import CadenceRepository
from core.repositories.question_answer_repository import QuestionAnswerRepository
from core.repositories.observed_returns_repository import ObservedReturnsRepository
from core.models.reasoning_artifact import ReasoningArtifact, ArtifactType, ConfidenceLevel
from core.models.belief_lifecycle_event import (
    BeliefReviewOutcomeEvent,
    ReviewOutcome,
    BeliefDecisionEvent,
    DecisionPayload,
    DecisionFollowUp,
    BeliefConfidenceEvent,
)
from core.services.belief_analysis_service import BeliefAnalysisService
from core.services.decision_projection_service import DecisionProjectionService
from core.models.stock_snapshot import StockSnapshot
from core.templates import templates


class ReviewOutcomeBody(BaseModel):
    outcome: str
    note: str | None = None


class DecisionFollowUpBody(BaseModel):
    action: str | None = "none"
    params: dict | None = None


class RecordDecisionBody(BaseModel):
    type: str
    sub_type: str | None = None
    rationale: str | None = None
    linked_snapshot_ids: list[str] = []
    related_lifecycle_event_ids: list[str] = []
    follow_up: DecisionFollowUpBody | None = None
    metadata: dict | None = None


class QuestionAnswerBody(BaseModel):
    answer: str


class CadenceBody(BaseModel):
    next_review_by: str
    cadence_days: int | None = None


class ConfidenceBody(BaseModel):
    confidence_level: str  # low | medium | high
    rationale: str | None = None


class ReturnObservationBody(BaseModel):
    return_period_id: int


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
    answer_repo = QuestionAnswerRepository(db)
    question = artifact_repo.get(question_id)

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if not isinstance(question, ReasoningArtifact) or question.artifact_type != ArtifactType.question:
        raise HTTPException(status_code=404, detail="Question not found")

    answer = answer_repo.get(question_id)

    return templates.TemplateResponse(
        "question_detail.html",
        {"request": request, "question": question, "answer": answer},
    )


@router.post("/api/questions/{question_id}/answer", status_code=303)
def submit_question_answer(
    question_id: str,
    answer: str = Form(""),
    db: Session = Depends(get_db),
):
    """Record or update your answer (form field: answer). Question disappears from Open Questions once answered."""
    artifact_repo = ArtifactRepository(db)
    answer_repo = QuestionAnswerRepository(db)
    question = artifact_repo.get(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if not isinstance(question, ReasoningArtifact) or question.artifact_type != ArtifactType.question:
        raise HTTPException(status_code=404, detail="Question not found")
    text = (answer or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="answer cannot be empty")
    answer_repo.set(question_id, text[:10000])
    return RedirectResponse(url=f"/questions/{question_id}", status_code=303)


@router.get("/beliefs/{belief_id}", response_class=HTMLResponse)
def belief_detail(belief_id: str, request: Request, db: Session = Depends(get_db)):
    artifact_repo = ArtifactRepository(db)
    lifecycle_repo = BeliefLifecycleRepository(db)
    cadence_repo = CadenceRepository(db)

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

    # Most recently attached snapshot IDs (from latest grounding_updated event)
    latest_attached_ids = set()
    for e in reversed(orm_events):
        p = e.payload or {}
        if p.get("event_kind") == "grounding_updated":
            latest_attached_ids = set(p.get("attached_snapshot_ids") or [])
            break

    referenced_snapshots = []
    for sid in belief.references.snapshot_ids:
        sid_str = str(sid)
        snap = artifact_repo.get(sid_str)
        if not snap or not getattr(snap, "metadata", None):
            referenced_snapshots.append({"snapshot_id": sid_str, "ticker": "—", "as_of": "—", "is_latest_grounding": False})
            continue
        ticker = (getattr(getattr(snap, "company", None), "ticker", None) or "").strip() or "—"
        as_of = getattr(snap.metadata, "as_of", None)
        as_of_str = str(as_of) if as_of else "—"
        referenced_snapshots.append({
            "snapshot_id": sid_str,
            "ticker": ticker,
            "as_of": as_of_str,
            "is_latest_grounding": sid_str in latest_attached_ids,
        })

    analysis = BeliefAnalysisService(artifact_repo, lifecycle_repo)
    grouped = analysis.get_beliefs_needing_review()
    has_newer_snapshots = any(
        item["belief_id"] == belief_id
        for items in grouped.values()
        for item in items
    )

    projection = DecisionProjectionService(artifact_repo, lifecycle_repo)
    current_decision_state = projection.get_current_decision_state(belief_id)
    decision_timeline = projection.get_decision_timeline(belief_id)

    cadence_row = cadence_repo.get(belief_id)
    cadence = None
    if cadence_row:
        cadence = {
            "next_review_by": cadence_row.next_review_by.isoformat() if cadence_row.next_review_by else None,
            "cadence_days": cadence_row.cadence_days,
        }

    # Current confidence from latest event_kind=="confidence"
    current_confidence = None
    for e in reversed(orm_events):
        p = e.payload or {}
        if p.get("event_kind") == "confidence":
            occ = e.created_at
            current_confidence = {
                "level": p.get("confidence_level", ""),
                "rationale": p.get("rationale"),
                "occurred_at": str(occ)[:10] if occ else None,
            }
            break

    return templates.TemplateResponse(
        "belief_detail.html",
        {
            "request": request,
            "belief": belief,
            "lifecycle_events": lifecycle_events,
            "referenced_snapshots": referenced_snapshots,
            "has_newer_snapshots": has_newer_snapshots,
            "current_decision_state": current_decision_state,
            "decision_timeline": decision_timeline,
            "cadence": cadence,
            "current_confidence": current_confidence,
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
    cadence_repo = CadenceRepository(db)
    cadence_row = cadence_repo.get(belief_id)
    if cadence_row and cadence_row.cadence_days is not None:
        from datetime import date, timedelta
        today = datetime.now(timezone.utc).date()
        cadence_repo.set(belief_id, today + timedelta(days=cadence_row.cadence_days), cadence_row.cadence_days)
    return None


@router.post("/api/beliefs/{belief_id}/cadence", status_code=201)
def set_cadence(
    belief_id: str,
    body: CadenceBody,
    db: Session = Depends(get_db),
):
    """Set or update review cadence for a belief. User-set only."""
    artifact_repo = ArtifactRepository(db)
    cadence_repo = CadenceRepository(db)
    belief = artifact_repo.get(belief_id)
    if not belief:
        raise HTTPException(status_code=404, detail="Belief not found")
    if not isinstance(belief, ReasoningArtifact) or belief.artifact_type not in {
        ArtifactType.thesis,
        ArtifactType.risk,
    }:
        raise HTTPException(status_code=404, detail="Belief not found")
    try:
        from datetime import datetime
        next_date = datetime.strptime(body.next_review_by.strip()[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="next_review_by must be YYYY-MM-DD")
    cadence_days = body.cadence_days
    if cadence_days is not None and (not isinstance(cadence_days, int) or cadence_days < 1):
        cadence_days = None
    cadence_repo.set(belief_id, next_date, cadence_days)
    return None


@router.delete("/api/beliefs/{belief_id}/cadence", status_code=204)
def delete_cadence(
    belief_id: str,
    db: Session = Depends(get_db),
):
    """Clear review cadence for a belief."""
    artifact_repo = ArtifactRepository(db)
    cadence_repo = CadenceRepository(db)
    belief = artifact_repo.get(belief_id)
    if not belief:
        raise HTTPException(status_code=404, detail="Belief not found")
    if not isinstance(belief, ReasoningArtifact) or belief.artifact_type not in {
        ArtifactType.thesis,
        ArtifactType.risk,
    }:
        raise HTTPException(status_code=404, detail="Belief not found")
    if not cadence_repo.delete(belief_id):
        raise HTTPException(status_code=404, detail="No cadence set for this belief")
    return None


@router.post("/api/beliefs/{belief_id}/confidence", status_code=201)
def set_confidence(
    belief_id: str,
    body: ConfidenceBody,
    db: Session = Depends(get_db),
):
    """Set confidence for a belief (human-only, stored as lifecycle event)."""
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
    level = (body.confidence_level or "").strip().lower()
    if level not in ("low", "medium", "high"):
        raise HTTPException(
            status_code=400,
            detail="confidence_level must be one of: low, medium, high",
        )
    rationale = (body.rationale or "").strip()[:500] or None
    now = datetime.now(timezone.utc)
    event = BeliefConfidenceEvent(
        event_id=uuid4(),
        schema_version="v1",
        occurred_at=now,
        recorded_by="human",
        reasoning_id=UUID(belief_id),
        event_kind="confidence",
        trigger="manual",
        confidence_level=ConfidenceLevel(level),
        rationale=rationale,
    )
    lifecycle_repo.append(event)
    return None


@router.post("/api/beliefs/{belief_id}/return-observation", status_code=201)
def link_belief_return_observation(
    belief_id: str,
    body: ReturnObservationBody,
    db: Session = Depends(get_db),
):
    """Link a belief to an observed return period (for display/correlation). Does not mutate belief or decisions."""
    artifact_repo = ArtifactRepository(db)
    returns_repo = ObservedReturnsRepository(db)
    belief = artifact_repo.get(belief_id)
    if not belief:
        raise HTTPException(status_code=404, detail="Belief not found")
    if not isinstance(belief, ReasoningArtifact) or belief.artifact_type not in {
        ArtifactType.thesis,
        ArtifactType.risk,
    }:
        raise HTTPException(status_code=404, detail="Belief not found")
    if not returns_repo.link_belief_to_period(belief_id, body.return_period_id):
        raise HTTPException(status_code=404, detail="Return period not found")
    return None


@router.delete("/api/beliefs/{belief_id}/return-observation/{return_period_id}", status_code=204)
def unlink_belief_return_observation(
    belief_id: str,
    return_period_id: int,
    db: Session = Depends(get_db),
):
    """Remove link between belief and observed return period."""
    artifact_repo = ArtifactRepository(db)
    returns_repo = ObservedReturnsRepository(db)
    belief = artifact_repo.get(belief_id)
    if not belief:
        raise HTTPException(status_code=404, detail="Belief not found")
    if not isinstance(belief, ReasoningArtifact) or belief.artifact_type not in {
        ArtifactType.thesis,
        ArtifactType.risk,
    }:
        raise HTTPException(status_code=404, detail="Belief not found")
    if not returns_repo.unlink_belief_from_period(belief_id, return_period_id):
        raise HTTPException(status_code=404, detail="Link not found")
    return None


DECISION_TYPES = frozenset({
    "reinforced", "slight_tension", "strong_tension", "revised", "abandoned",
    "confidence_increased", "confidence_decreased", "deferred", "other",
})


@router.post("/api/beliefs/{belief_id}/decision", status_code=201)
def record_decision(
    belief_id: str,
    body: RecordDecisionBody,
    db: Session = Depends(get_db),
):
    """Record a human-judged decision for a belief (append-only). Does not mutate belief text or snapshots."""
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
    if body.type not in DECISION_TYPES:
        raise HTTPException(
            status_code=400,
            detail="decision type must be one of: reinforced, slight_tension, strong_tension, revised, abandoned, confidence_increased, confidence_decreased, deferred, other",
        )
    # Build payload; convert string IDs to UUIDs where needed
    linked = []
    for s in body.linked_snapshot_ids or []:
        try:
            linked.append(UUID(s))
        except (ValueError, TypeError):
            pass
    related = []
    for s in body.related_lifecycle_event_ids or []:
        try:
            related.append(UUID(s))
        except (ValueError, TypeError):
            pass
    follow_up = None
    if body.follow_up:
        follow_up = DecisionFollowUp(
            action=body.follow_up.action or "none",
            params=body.follow_up.params,
        )
    decision_payload = DecisionPayload(
        type=body.type,
        sub_type=(body.sub_type or "").strip() or None,
        rationale=(body.rationale or "").strip()[:2000] or None,
        linked_snapshot_ids=linked,
        related_lifecycle_event_ids=related,
        follow_up=follow_up,
        metadata=body.metadata,
    )
    now = datetime.now(timezone.utc)
    event = BeliefDecisionEvent(
        event_id=uuid4(),
        schema_version="v1",
        occurred_at=now,
        recorded_by="human",
        reasoning_id=UUID(belief_id),
        event_kind="decision",
        trigger="manual",
        decision=decision_payload,
    )
    lifecycle_repo.append(event)

    # Optional follow-up: set_cadence (no other mutation)
    if follow_up and follow_up.action == "set_cadence" and follow_up.params:
        p = follow_up.params
        next_review_by = p.get("next_review_by")
        cadence_days = p.get("cadence_days")
        if next_review_by:
            try:
                next_date = datetime.strptime(str(next_review_by).strip()[:10], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                next_date = None
            if next_date is not None:
                cd = None
                if cadence_days is not None:
                    try:
                        cd = int(cadence_days)
                        if cd < 1:
                            cd = None
                    except (ValueError, TypeError):
                        pass
                cadence_repo = CadenceRepository(db)
                cadence_repo.set(belief_id, next_date, cd)

    return None


@router.get("/api/beliefs/{belief_id}/decisions")
def list_decisions(belief_id: str, db: Session = Depends(get_db)):
    """List decision lifecycle events for a belief (append-only history)."""
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
    decisions = [
        {"created_at": e.created_at.isoformat(), "payload": e.payload}
        for e in orm_events
        if (e.payload or {}).get("event_kind") == "decision"
    ]
    return {"decisions": decisions}


@router.get("/api/decisions")
def list_decisions_report(
    db: Session = Depends(get_db),
    type: str | None = Query(None, description="Filter by decision type, e.g. strong_tension"),
    since: str | None = Query(None, description="ISO date, e.g. 2026-01-01"),
):
    """List decision events across all beliefs for reporting. Optional filters: type, since."""
    lifecycle_repo = BeliefLifecycleRepository(db)
    since_dt = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            since_dt = None
    rows = lifecycle_repo.list_decision_events(since=since_dt, decision_type=type)
    decisions = [
        {"belief_id": r.belief_id, "created_at": r.created_at.isoformat(), "payload": r.payload}
        for r in rows
    ]
    return {"decisions": decisions}


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
