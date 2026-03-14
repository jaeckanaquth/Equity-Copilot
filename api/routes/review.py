from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.deps import get_db
from api.schemas.review import (
    CoverageResponse,
    OpenQuestionResponse,
    OrphanResponse,
    StaleBeliefResponse,
)
from core.repositories.artifact_repository import ArtifactRepository
from core.repositories.lifecycle_repository import BeliefLifecycleRepository
from core.repositories.question_answer_repository import QuestionAnswerRepository
from core.services.artifact_integrity_service import ArtifactIntegrityService
from core.services.belief_analysis_service import BeliefAnalysisService
from core.services.introspection_service import IntrospectionService

router = APIRouter()


# -------------------------
# Weekly Review Endpoints
# -------------------------

@router.get("/questions", response_model=dict[str, list[OpenQuestionResponse]])
def open_questions(db: Session = Depends(get_db)):
    artifact_repo = ArtifactRepository(db)
    answer_repo = QuestionAnswerRepository(db)
    service = IntrospectionService(artifact_repo, answer_repo.answered_question_ids())
    return service.get_open_questions()


@router.get("/beliefs/stale", response_model=dict[str, list[StaleBeliefResponse]])
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

