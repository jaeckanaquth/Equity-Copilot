from sqlalchemy import Column, String, DateTime, JSON
from db.session import Base
from datetime import datetime


class ProposalORM(Base):
    __tablename__ = "proposals"

    proposal_id = Column(String, primary_key=True, index=True)
    proposal_type = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    status = Column(String, nullable=False, default="pending", index=True)
    payload = Column(JSON, nullable=False)
