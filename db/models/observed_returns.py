"""
Observed returns/risk for performance observation (read-only layer).
Does not mutate beliefs or decisions. Append-only ingestion.
"""
from datetime import date, datetime, timezone

from sqlalchemy import Column, String, Date, Integer, Float, DateTime, ForeignKey, UniqueConstraint
from db.session import Base


def _utc_now():
    return datetime.now(timezone.utc)


class ObservedReturnPeriodORM(Base):
    """Portfolio-level return/risk for a period. Ingested only; no auto-compute."""
    __tablename__ = "observed_return_periods"

    id = Column(Integer, primary_key=True, autoincrement=True)
    period_start = Column(Date, nullable=False, index=True)
    period_end = Column(Date, nullable=False, index=True)
    return_pct = Column(Float, nullable=True)  # e.g. 5.2 for 5.2%
    risk_metric = Column(Float, nullable=True)  # e.g. volatility or max drawdown
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=_utc_now)


class BeliefReturnObservationORM(Base):
    """Links a belief to an observed return period (for display/correlation only). Append-only."""
    __tablename__ = "belief_return_observations"

    belief_id = Column(String, primary_key=True, index=True)
    return_period_id = Column(Integer, ForeignKey("observed_return_periods.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, nullable=False, default=_utc_now)
