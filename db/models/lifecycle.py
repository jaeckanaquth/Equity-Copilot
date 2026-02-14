from sqlalchemy import Column, String, DateTime, JSON
from db.session import Base
from datetime import datetime

class BeliefLifecycleEventORM(Base):
    __tablename__ = "belief_lifecycle_events"

    event_id = Column(String, primary_key=True, index=True)
    belief_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    payload = Column(JSON, nullable=False)
