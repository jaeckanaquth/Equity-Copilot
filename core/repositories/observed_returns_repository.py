"""
Read-only layer: observed return periods and optional belief–period links.
Does not mutate beliefs or decisions.
"""
from datetime import date

from sqlalchemy.orm import Session

from db.models.observed_returns import BeliefReturnObservationORM, ObservedReturnPeriodORM


class ObservedReturnsRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_periods(self):
        """All return periods, newest first."""
        return (
            self.db.query(ObservedReturnPeriodORM)
            .order_by(ObservedReturnPeriodORM.period_start.desc())
            .all()
        )

    def get_period(self, period_id: int) -> ObservedReturnPeriodORM | None:
        return self.db.query(ObservedReturnPeriodORM).filter_by(id=period_id).first()

    def add_period(
        self,
        period_start: date,
        period_end: date,
        return_pct: float | None = None,
        risk_metric: float | None = None,
        notes: str | None = None,
    ) -> int:
        row = ObservedReturnPeriodORM(
            period_start=period_start,
            period_end=period_end,
            return_pct=return_pct,
            risk_metric=risk_metric,
            notes=(notes or "").strip()[:1000] or None,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row.id

    def list_observations_for_belief(self, belief_id: str):
        """Return period IDs linked to this belief."""
        rows = (
            self.db.query(BeliefReturnObservationORM.return_period_id)
            .filter_by(belief_id=belief_id)
            .all()
        )
        return [r[0] for r in rows]

    def get_periods_for_belief(self, belief_id: str):
        """Return period rows linked to this belief (for display)."""
        obs = (
            self.db.query(BeliefReturnObservationORM)
            .filter_by(belief_id=belief_id)
            .all()
        )
        if not obs:
            return []
        period_ids = [o.return_period_id for o in obs]
        return self.db.query(ObservedReturnPeriodORM).filter(
            ObservedReturnPeriodORM.id.in_(period_ids)
        ).all()

    def link_belief_to_period(self, belief_id: str, return_period_id: int) -> bool:
        """Link a belief to an observed return period. Idempotent (re-link same pair no-op)."""
        period = self.get_period(return_period_id)
        if not period:
            return False
        existing = (
            self.db.query(BeliefReturnObservationORM)
            .filter_by(belief_id=belief_id, return_period_id=return_period_id)
            .first()
        )
        if existing:
            return True
        self.db.add(BeliefReturnObservationORM(
            belief_id=belief_id,
            return_period_id=return_period_id,
        ))
        self.db.commit()
        return True

    def unlink_belief_from_period(self, belief_id: str, return_period_id: int) -> bool:
        """Remove link between belief and period."""
        row = (
            self.db.query(BeliefReturnObservationORM)
            .filter_by(belief_id=belief_id, return_period_id=return_period_id)
            .first()
        )
        if not row:
            return False
        self.db.delete(row)
        self.db.commit()
        return True
