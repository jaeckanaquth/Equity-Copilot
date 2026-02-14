from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.session import SessionLocal
from core.repositories.artifact_repository import ArtifactRepository
from core.repositories.lifecycle_repository import BeliefLifecycleRepository
from core.services.introspection_service import IntrospectionService
from core.services.belief_analysis_service import BeliefAnalysisService
from core.services.artifact_integrity_service import ArtifactIntegrityService
from api.schemas.review import (
    OpenQuestionResponse,
    StaleBeliefResponse,
    CoverageResponse,
    OrphanResponse,
)
from typing import Dict, List


router = APIRouter()


# -------------------------
# DB Dependency
# -------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------
# Weekly Review Endpoints
# -------------------------

@router.get("/questions", response_model=Dict[str, List[OpenQuestionResponse]])
def open_questions(db: Session = Depends(get_db)):
    artifact_repo = ArtifactRepository(db)
    service = IntrospectionService(artifact_repo)
    return service.get_open_questions()


@router.get("/beliefs/stale", response_model=Dict[str, List[StaleBeliefResponse]])
def stale_beliefs(db: Session = Depends(get_db)):
    artifact_repo = ArtifactRepository(db)
    lifecycle_repo = BeliefLifecycleRepository(db)
    service = BeliefAnalysisService(artifact_repo, lifecycle_repo)
    return service.get_beliefs_needing_review()


@router.get("/beliefs/{belief_id}/coverage", response_model=CoverageResponse)
def belief_coverage(belief_id: str, db: Session = Depends(get_db)):
    artifact_repo = ArtifactRepository(db)
    lifecycle_repo = BeliefLifecycleRepository(db)
    service = BeliefAnalysisService(artifact_repo, lifecycle_repo)
    return service.get_snapshot_coverage(belief_id)


@router.get("/orphans", response_model=OrphanResponse)
def orphaned_artifacts(db: Session = Depends(get_db)):
    artifact_repo = ArtifactRepository(db)
    service = ArtifactIntegrityService(artifact_repo)
    return service.get_orphans()

