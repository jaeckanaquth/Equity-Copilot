from datetime import UTC, datetime

from sqlalchemy import JSON, Column, DateTime, String

from db.session import Base


def _utc_now():
    return datetime.now(UTC)


class ArtifactORM(Base):
    __tablename__ = "artifacts"

    artifact_id = Column(String, primary_key=True, index=True)
    artifact_type = Column(String, nullable=False, index=True)
    schema_version = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=_utc_now)
    payload = Column(JSON, nullable=False)
