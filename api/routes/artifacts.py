"""Create beliefs and questions (artifacts). Read-only review is in review.py."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4, UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session

from db.session import SessionLocal
from core.repositories.artifact_repository import ArtifactRepository
from core.models.reasoning_artifact import (
    ReasoningArtifact,
    ReasoningSubject,
    ReasoningReferences,
    ReasoningClaim,
    ReasoningDetail,
    ReasoningConfidence,
    ReasoningReview,
    CreatedBy,
    ArtifactType,
    Stance,
    ConfidenceLevel,
    SubjectEntityType,
)
from core.templates import templates

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _parse_snapshot_ids(raw: list[str]) -> list[UUID]:
    out = []
    for s in raw:
        if not s or not s.strip():
            continue
        try:
            out.append(UUID(s.strip()))
        except ValueError:
            pass
    return out


def _save_belief(repo: ArtifactRepository, statement: str, snapshot_ids: list[UUID], risk: bool) -> UUID:
    artifact_type = ArtifactType.risk if risk else ArtifactType.thesis
    refs = ReasoningReferences(
        snapshot_ids=snapshot_ids,
        derived_metric_set_ids=[],
        analysis_view_ids=[],
    )
    subject = ReasoningSubject(entity_type=SubjectEntityType.company, entity_id="portfolio")
    artifact = ReasoningArtifact(
        reasoning_id=uuid4(),
        schema_version="v1",
        created_at=datetime.now(timezone.utc),
        created_by=CreatedBy.human,
        artifact_type=artifact_type,
        subject=subject,
        references=refs,
        claim=ReasoningClaim(statement=statement.strip(), stance=Stance.neutral),
        reasoning=ReasoningDetail(rationale=[], assumptions=[], counterpoints=[]),
        confidence=ReasoningConfidence(confidence_level=ConfidenceLevel.medium, confidence_rationale=""),
        review=ReasoningReview(review_by=None, review_trigger=None),
    )
    repo.save(artifact)
    return artifact.reasoning_id


def _save_question(repo: ArtifactRepository, statement: str, snapshot_ids: list[UUID]) -> UUID:
    refs = ReasoningReferences(
        snapshot_ids=snapshot_ids,
        derived_metric_set_ids=[],
        analysis_view_ids=[],
    )
    subject = ReasoningSubject(entity_type=SubjectEntityType.company, entity_id="portfolio")
    artifact = ReasoningArtifact(
        reasoning_id=uuid4(),
        schema_version="v1",
        created_at=datetime.now(timezone.utc),
        created_by=CreatedBy.human,
        artifact_type=ArtifactType.question,
        subject=subject,
        references=refs,
        claim=ReasoningClaim(statement=statement.strip(), stance=Stance.exploratory),
        reasoning=ReasoningDetail(rationale=[], assumptions=[], counterpoints=[]),
        confidence=ReasoningConfidence(confidence_level=ConfidenceLevel.medium, confidence_rationale=""),
        review=ReasoningReview(review_by=None, review_trigger=None),
    )
    repo.save(artifact)
    return artifact.reasoning_id


def _snapshot_list_for_template(repo: ArtifactRepository):
    snapshots = sorted(
        repo.list_by_type("StockSnapshot"),
        key=lambda s: (s.company.ticker or "", s.metadata.as_of),
        reverse=True,
    )
    snapshot_list = []
    for s in snapshots:
        as_of = s.metadata.as_of
        if hasattr(as_of, "date"):
            as_of = as_of.date()
        snapshot_list.append({
            "id": str(s.metadata.snapshot_id),
            "ticker": s.company.ticker or "?",
            "as_of": str(as_of),
        })
    tickers = sorted(set(s["ticker"] for s in snapshot_list))
    return snapshot_list, tickers


@router.get("/create", response_class=HTMLResponse)
def create_artifact_form(request: Request, db: Session = Depends(get_db)):
    """Combined form; redirect to beliefs/new or keep as both."""
    snapshot_list, tickers = _snapshot_list_for_template(ArtifactRepository(db))
    return templates.TemplateResponse(
        "create_artifact.html",
        {"request": request, "snapshots": snapshot_list, "tickers": tickers, "form_mode": "both"},
    )


@router.get("/beliefs/new", response_class=HTMLResponse)
def new_belief_form(request: Request, db: Session = Depends(get_db)):
    """Form to add a belief (thesis or risk)."""
    snapshot_list, tickers = _snapshot_list_for_template(ArtifactRepository(db))
    return templates.TemplateResponse(
        "create_artifact.html",
        {"request": request, "snapshots": snapshot_list, "tickers": tickers, "form_mode": "belief"},
    )


@router.get("/questions/new", response_class=HTMLResponse)
def new_question_form(request: Request, db: Session = Depends(get_db)):
    """Form to add a question."""
    snapshot_list, tickers = _snapshot_list_for_template(ArtifactRepository(db))
    return templates.TemplateResponse(
        "create_artifact.html",
        {"request": request, "snapshots": snapshot_list, "tickers": tickers, "form_mode": "question"},
    )


@router.post("/api/artifacts/belief")
async def create_belief(request: Request, db: Session = Depends(get_db)):
    """Create a thesis (or risk). Redirects to the new belief."""
    form = await request.form()
    statement = form.get("statement") or ""
    snapshot_ids = form.getlist("snapshot_ids")
    risk = form.get("risk") == "true"
    if not statement.strip():
        return RedirectResponse(url="/beliefs/new", status_code=303)
    repo = ArtifactRepository(db)
    ids = _parse_snapshot_ids(snapshot_ids)
    rid = _save_belief(repo, statement.strip(), ids, risk)
    return RedirectResponse(url=f"/beliefs/{rid}", status_code=303)


@router.post("/api/artifacts/question")
async def create_question(request: Request, db: Session = Depends(get_db)):
    """Create a question. Redirects to the new question."""
    form = await request.form()
    statement = form.get("statement") or ""
    snapshot_ids = form.getlist("snapshot_ids")
    if not statement.strip():
        return RedirectResponse(url="/questions/new", status_code=303)
    repo = ArtifactRepository(db)
    ids = _parse_snapshot_ids(snapshot_ids)
    rid = _save_question(repo, statement.strip(), ids)
    return RedirectResponse(url=f"/questions/{rid}", status_code=303)
