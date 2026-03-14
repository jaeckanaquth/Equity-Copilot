from datetime import UTC, datetime

from sqlalchemy import JSON, Column, DateTime, String

from db.session import Base


def _utc_now():
    return datetime.now(UTC)


class BeliefLifecycleEventORM(Base):
    __tablename__ = "belief_lifecycle_events"

    event_id = Column(String, primary_key=True, index=True)
    belief_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=_utc_now)
    payload = Column(JSON, nullable=False)
