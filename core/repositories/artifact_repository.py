from sqlalchemy.orm import Session
from pydantic import BaseModel

from db.models.artifact import ArtifactORM
from core.models.stock_snapshot import StockSnapshot
from core.models.reasoning_artifact import ReasoningArtifact


def _get_artifact_pk(artifact: BaseModel) -> str:
    if isinstance(artifact, StockSnapshot):
        return str(artifact.metadata.snapshot_id)
    if isinstance(artifact, ReasoningArtifact):
        return str(artifact.reasoning_id)
    raise ValueError(f"Unknown artifact type: {type(artifact).__name__}")


def _get_created_at(artifact: BaseModel):
    if isinstance(artifact, StockSnapshot):
        return artifact.metadata.as_of
    if isinstance(artifact, ReasoningArtifact):
        return artifact.created_at
    raise ValueError(f"Unknown artifact type: {type(artifact).__name__}")


def _get_schema_version(artifact: BaseModel) -> str:
    if isinstance(artifact, StockSnapshot):
        return artifact.metadata.schema_version
    if isinstance(artifact, ReasoningArtifact):
        return artifact.schema_version
    raise ValueError(f"Unknown artifact type: {type(artifact).__name__}")


class ArtifactRepository:

    def __init__(self, db: Session):
        self.db = db

    def save(self, artifact: BaseModel):
        pk = _get_artifact_pk(artifact)
        existing = self.db.query(ArtifactORM).filter_by(artifact_id=pk).first()
        if existing:
            raise Exception("Artifacts are immutable. Update not allowed.")

        orm_obj = ArtifactORM(
            artifact_id=pk,
            artifact_type=artifact.__class__.__name__,
            schema_version=_get_schema_version(artifact),
            created_at=_get_created_at(artifact),
            payload=artifact.model_dump(mode="json"),
        )
        self.db.add(orm_obj)
        self.db.commit()

    def get(self, artifact_id: str):
        obj = self.db.query(ArtifactORM).filter_by(artifact_id=artifact_id).first()
        if not obj:
            return None
        return _rehydrate(obj.artifact_type, obj.payload)


    def list_by_type(self, artifact_type: str):
        objs = self.db.query(ArtifactORM).filter_by(artifact_type=artifact_type).all()
        return [_rehydrate(o.artifact_type, o.payload) for o in objs]


def _rehydrate(artifact_type: str, payload: dict):
    if artifact_type == "StockSnapshot":
        return StockSnapshot(**payload)
    elif artifact_type == "ReasoningArtifact":
        return ReasoningArtifact(**payload)
    else:
        raise Exception(f"Unknown artifact type: {artifact_type}")