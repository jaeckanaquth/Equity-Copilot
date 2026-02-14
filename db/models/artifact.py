from sqlalchemy import Column, String, DateTime, JSON
from db.session import Base
from datetime import datetime

class ArtifactORM(Base):
    __tablename__ = "artifacts"

    artifact_id = Column(String, primary_key=True, index=True)
    artifact_type = Column(String, nullable=False, index=True)
    schema_version = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    payload = Column(JSON, nullable=False)
