"""Read-only report endpoints (derived decision state). Decision analytics."""
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel

from db.session import SessionLocal
from core.repositories.artifact_repository import ArtifactRepository
from core.repositories.lifecycle_repository import BeliefLifecycleRepository
from core.services.decision_projection_service import DecisionProjectionService
from core.services.decision_analytics_service import DecisionAnalyticsService
from core.repositories.observed_returns_repository import ObservedReturnsRepository


class PortfolioReturnPeriodBody(BaseModel):
    period_start: str  # YYYY-MM-DD
    period_end: str
    return_pct: float | None = None
    risk_metric: float | None = None
    notes: str | None = None


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/api/reports/beliefs")
def report_beliefs_by_decision(
    decision: str = Query(..., description="Filter by current decision type, e.g. strong_tension"),
    db=Depends(get_db),
):
    """
    Beliefs whose current (latest) decision has the given type.
    Read-only; current state is computed, not stored.
    """
    artifact_repo = ArtifactRepository(db)
    lifecycle_repo = BeliefLifecycleRepository(db)
    projection = DecisionProjectionService(artifact_repo, lifecycle_repo)
    beliefs = projection.get_beliefs_by_current_decision(decision_type=decision)
    return {"decision_filter": decision, "beliefs": beliefs}


@router.get("/api/reports/decision-summary")
def report_decision_summary(
    since: str | None = Query(None, description="ISO date, e.g. 2026-01-01"),
    db=Depends(get_db),
):
    """
    Counts of decision events by type (since= optional). Derived from lifecycle; not stored.
    """
    artifact_repo = ArtifactRepository(db)
    lifecycle_repo = BeliefLifecycleRepository(db)
    projection = DecisionProjectionService(artifact_repo, lifecycle_repo)
    since_dt = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            since_dt = None
    summary = projection.get_decision_summary(since=since_dt)
    return {"since": since, "summary": summary}


@router.get("/api/reports/durability")
def report_durability(db=Depends(get_db)):
    """
    Belief durability: time from creation to first non-reinforced decision.
    Median, mean, distribution buckets, per-belief list. Derived only — not stored.
    """
    artifact_repo = ArtifactRepository(db)
    lifecycle_repo = BeliefLifecycleRepository(db)
    analytics = DecisionAnalyticsService(artifact_repo, lifecycle_repo)
    return analytics.get_belief_durability()


@router.get("/api/reports/tension-density")
def report_tension_density(db=Depends(get_db)):
    """
    % of beliefs currently under slight or strong tension. Systemic stress.
    Descriptive only; derived from current decision projection.
    """
    artifact_repo = ArtifactRepository(db)
    lifecycle_repo = BeliefLifecycleRepository(db)
    analytics = DecisionAnalyticsService(artifact_repo, lifecycle_repo)
    return analytics.get_tension_density()


@router.get("/api/reports/trajectories")
def report_trajectories(db=Depends(get_db)):
    """
    Per-belief decision sequence classified: stable, gradual_degradation, sudden_collapse, oscillatory.
    Labels are derived only — never persisted. Descriptive, not evaluative.
    """
    artifact_repo = ArtifactRepository(db)
    lifecycle_repo = BeliefLifecycleRepository(db)
    analytics = DecisionAnalyticsService(artifact_repo, lifecycle_repo)
    return analytics.get_trajectory_patterns()


@router.get("/api/reports/portfolio-returns")
def get_portfolio_returns(db=Depends(get_db)):
    """
    List all observed return periods (portfolio-level). Read-only view.
    Does not mutate reasoning layer.
    """
    repo = ObservedReturnsRepository(db)
    periods = repo.list_periods()
    return {
        "portfolio_returns": [
            {
                "id": p.id,
                "period_start": p.period_start.isoformat() if p.period_start else None,
                "period_end": p.period_end.isoformat() if p.period_end else None,
                "return_pct": p.return_pct,
                "risk_metric": p.risk_metric,
                "notes": p.notes,
            }
            for p in periods
        ]
    }


@router.post("/api/reports/portfolio-returns", status_code=201)
def add_portfolio_return(body: PortfolioReturnPeriodBody, db=Depends(get_db)):
    """
    Ingest one observed return period. Does not mutate beliefs or decisions.
    """
    repo = ObservedReturnsRepository(db)
    try:
        start = datetime.strptime(body.period_start.strip()[:10], "%Y-%m-%d").date()
        end = datetime.strptime(body.period_end.strip()[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="period_start and period_end must be YYYY-MM-DD")
    if start > end:
        raise HTTPException(status_code=400, detail="period_start must be <= period_end")
    period_id = repo.add_period(
        period_start=start,
        period_end=end,
        return_pct=body.return_pct,
        risk_metric=body.risk_metric,
        notes=body.notes,
    )
    return {"id": period_id}


@router.get("/api/reports/observed-outcomes")
def report_observed_outcomes(
    format: str | None = Query("json", description="json or csv"),
    db=Depends(get_db),
):
    """
    Beliefs with current decision and linked returns (when available).
    Includes portfolio return periods. Read-only; never drives mutation.
    """
    from fastapi.responses import PlainTextResponse
    import csv
    import io

    from core.models.reasoning_artifact import ArtifactType

    artifact_repo = ArtifactRepository(db)
    lifecycle_repo = BeliefLifecycleRepository(db)
    projection = DecisionProjectionService(artifact_repo, lifecycle_repo)
    returns_repo = ObservedReturnsRepository(db)
    portfolio_periods = returns_repo.list_periods()
    portfolio_returns = [
        {
            "id": p.id,
            "period_start": p.period_start.isoformat() if p.period_start else None,
            "period_end": p.period_end.isoformat() if p.period_end else None,
            "return_pct": p.return_pct,
            "risk_metric": p.risk_metric,
            "notes": p.notes,
        }
        for p in portfolio_periods
    ]

    all_artifacts = artifact_repo.list_by_type("ReasoningArtifact")
    rows = []
    for b in all_artifacts:
        if getattr(b, "artifact_type", None) not in (ArtifactType.thesis, ArtifactType.risk):
            continue
        bid = str(getattr(b, "reasoning_id", ""))
        if not bid or not getattr(b, "claim", None):
            continue
        state = projection.get_current_decision_state(bid)
        occ = state.get("occurred_at") if state else None
        if hasattr(occ, "isoformat"):
            occ = occ.isoformat()
        elif occ is not None:
            occ = str(occ)
        # Link to observed return: use latest linked period's return_pct
        linked_periods = returns_repo.get_periods_for_belief(bid)
        returns_placeholder = None
        if linked_periods:
            latest = max(linked_periods, key=lambda p: p.period_end or "")
            returns_placeholder = latest.return_pct
        rows.append({
            "belief_id": bid,
            "belief_text_snippet": (b.claim.statement or "")[:200],
            "current_decision_type": state.get("type") if state else None,
            "latest_decision_at": occ,
            "returns_placeholder": returns_placeholder,
        })
    if format == "csv":
        out = io.StringIO()
        writer = csv.DictWriter(
            out,
            fieldnames=["belief_id", "belief_text_snippet", "current_decision_type", "latest_decision_at", "returns_placeholder"],
        )
        writer.writeheader()
        writer.writerows(rows)
        return PlainTextResponse(out.getvalue(), media_type="text/csv")
    return {"portfolio_returns": portfolio_returns, "observed_outcomes": rows}
