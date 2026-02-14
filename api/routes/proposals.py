"""Proposal lifecycle: accept / reject + audit."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse, Response, HTMLResponse
from sqlalchemy.orm import Session

from db.session import SessionLocal
from core.repositories.artifact_repository import ArtifactRepository
from core.repositories.lifecycle_repository import BeliefLifecycleRepository
from core.repositories.proposal_repository import ProposalRepository
from core.services.proposal_engine import ProposalEngine
from core.templates import templates

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _is_fetch(request: Request) -> bool:
    """True if request is from fetch/XHR (no page refresh desired)."""
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


@router.post("/proposals/{proposal_id}/accept")
def accept_proposal(proposal_id: str, request: Request, db=Depends(get_db)):
    """Acknowledge proposal — user will act on it."""
    ProposalRepository(db).resolve(proposal_id, "accepted")
    if _is_fetch(request):
        return Response(status_code=204)
    return RedirectResponse(url="/weekly-review", status_code=303)


@router.post("/proposals/{proposal_id}/reject")
def reject_proposal(proposal_id: str, request: Request, db=Depends(get_db)):
    """Dismiss proposal — user declines to act."""
    ProposalRepository(db).resolve(proposal_id, "rejected")
    if _is_fetch(request):
        return Response(status_code=204)
    return RedirectResponse(url="/weekly-review", status_code=303)


@router.get("/proposals/history", response_class=HTMLResponse)
def proposal_history(request: Request, db: Session = Depends(get_db)):
    """Audit view: all proposals grouped by type and status. Includes condition_state."""
    artifact_repo = ArtifactRepository(db)
    lifecycle_repo = BeliefLifecycleRepository(db)
    proposal_repo = ProposalRepository(db)
    engine = ProposalEngine(artifact_repo, lifecycle_repo, proposal_repo)
    history = engine.get_history_for_display()

    total = sum(
        len(item)
        for by_type in history.values()
        for item in by_type.values()
    )

    return templates.TemplateResponse(
        "proposal_history.html",
        {
            "request": request,
            "history": history,
            "history_total": total,
        },
    )
