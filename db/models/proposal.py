from datetime import UTC, datetime

from sqlalchemy import JSON, Column, DateTime, String

from db.session import Base


def _utc_now():
    return datetime.now(UTC)


class ProposalORM(Base):
    __tablename__ = "proposals"

    proposal_id = Column(String, primary_key=True, index=True)
    proposal_type = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=_utc_now)
    status = Column(String, nullable=False, default="pending", index=True)
    payload = Column(JSON, nullable=False)
