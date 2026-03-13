from datetime import date, datetime, timezone

from sqlalchemy import Column, String, Date, Integer, DateTime
from db.session import Base


def _utc_now():
    return datetime.now(timezone.utc)


class BeliefReviewCadenceORM(Base):
    __tablename__ = "belief_review_cadence"

    belief_id = Column(String, primary_key=True, index=True)
    next_review_by = Column(Date, nullable=False)
    cadence_days = Column(Integer, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=_utc_now)
