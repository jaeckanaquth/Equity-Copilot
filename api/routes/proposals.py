"""Proposal lifecycle: accept / reject + audit."""
from datetime import UTC, datetime
from urllib.parse import quote
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session

from api.deps import get_db
from core.models.belief_lifecycle_event import GroundingUpdatedEvent
from core.models.reasoning_artifact import ArtifactType
from core.repositories.artifact_repository import ArtifactRepository
from core.repositories.lifecycle_repository import BeliefLifecycleRepository
from core.repositories.proposal_repository import ProposalRepository
from core.services.proposal_engine import ProposalEngine
from core.templates import templates

router = APIRouter()


def _is_fetch(request: Request) -> bool:
    """True if request is from fetch/XHR (no page refresh desired)."""
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _newest_snapshot_id_per_ticker(artifact_repo, snapshot_ids: list[str]) -> list[str]:
    """From the given snapshot IDs, return one snapshot per ticker (the newest as_of)."""
    snapshots = []
    for sid in snapshot_ids:
        s = artifact_repo.get(sid)
        if s and getattr(s, "metadata", None) and getattr(s, "company", None):
            snapshots.append(s)
    if not snapshots:
        return []
    # Group by ticker, keep max as_of per ticker
    from collections import defaultdict
    by_ticker = defaultdict(list)
    for s in snapshots:
        t = (getattr(s.company, "ticker") or "").strip()
        if t:
            by_ticker[t].append(s)
    out = []
    for ticker, group in by_ticker.items():
        newest = max(group, key=lambda x: x.metadata.as_of)
        out.append(str(newest.metadata.snapshot_id))
    return out


@router.post("/proposals/{proposal_id}/accept")
def accept_proposal(proposal_id: str, request: Request, db=Depends(get_db)):
    """Acknowledge proposal. For review_prompt: attach newest snapshot per ticker, then resolve."""
    proposal_repo = ProposalRepository(db)
    row = proposal_repo.get_by_id(proposal_id)
    if not row:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if row.status != "pending":
        if _is_fetch(request):
            return Response(status_code=204)
        return RedirectResponse(url="/weekly-review", status_code=303)

    payload = row.payload or {}
    grounding_detail = None
    if row.proposal_type == "review_prompt" and payload.get("belief_id"):
        artifact_repo = ArtifactRepository(db)
        lifecycle_repo = BeliefLifecycleRepository(db)
        belief_id = payload["belief_id"]
        belief = artifact_repo.get(belief_id)
        if belief and getattr(belief, "artifact_type", None) in (ArtifactType.thesis, ArtifactType.risk):
            newer_ids = payload.get("newer_snapshot_ids") or []
            newest_per_ticker = _newest_snapshot_id_per_ticker(artifact_repo, newer_ids)
            if newest_per_ticker:
                current = [str(sid) for sid in belief.references.snapshot_ids]
                merged = list(dict.fromkeys(current + newest_per_ticker))
                artifact_repo.update_belief_snapshot_refs(belief_id, merged)
                now = datetime.now(UTC)
                lifecycle_repo.append(GroundingUpdatedEvent(
                    event_id=uuid4(),
                    occurred_at=now,
                    recorded_by="human",
                    reasoning_id=UUID(belief_id),
                    attached_snapshot_ids=newest_per_ticker,
                ))
                parts = []
                for sid in newest_per_ticker:
                    s = artifact_repo.get(sid)
                    if s and getattr(s, "company", None) and getattr(s, "metadata", None):
                        ticker = (getattr(s.company, "ticker") or "").strip() or "?"
                        as_of = getattr(s.metadata, "as_of", None)
                        parts.append(f"{ticker} {as_of}" if as_of else ticker)
                grounding_detail = ", ".join(parts) if parts else None

    proposal_repo.resolve(proposal_id, "accepted")
    if _is_fetch(request):
        return Response(status_code=204)
    url = "/weekly-review"
    if grounding_detail:
        url = f"/weekly-review?grounding_updated=1&detail={quote(grounding_detail)}"
    return RedirectResponse(url=url, status_code=303)


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
