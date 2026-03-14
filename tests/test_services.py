"""Services: artifact integrity, belief analysis, introspection."""
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from core.exceptions import ArtifactConflictError
from core.models.reasoning_artifact import ArtifactType
from core.services.artifact_integrity_service import ArtifactIntegrityService
from core.services.belief_analysis_service import BeliefAnalysisService
from core.services.introspection_service import IntrospectionService
from tests.fixtures.artifact_factory import reasoning_artifact_factory


def test_artifact_conflict_on_duplicate_save(artifact_repo):
    """Saving the same artifact twice raises ArtifactConflictError (409)."""
    belief = reasoning_artifact_factory(snapshot_ids=[], statement="One")
    artifact_repo.save(belief)
    with pytest.raises(ArtifactConflictError) as exc_info:
        artifact_repo.save(belief)
    assert "immutable" in str(exc_info.value).lower()


def test_orphan_belief_detected(artifact_repo):
    belief = reasoning_artifact_factory(snapshot_ids=[])
    artifact_repo.save(belief)
    service = ArtifactIntegrityService(artifact_repo)
    orphans = service.get_orphans()
    assert str(belief.reasoning_id) in [
        b["belief_id"] for b in orphans["beliefs_without_snapshots"]
    ]


def test_stale_belief_detected(artifact_repo, lifecycle_repo, snapshot_factory):
    """Belief references old snapshot; a newer snapshot (same ticker) triggers 'needs review'."""
    old_snapshot_id = uuid4()
    belief = reasoning_artifact_factory(
        created_at=datetime.now(UTC) - timedelta(days=30),
        snapshot_ids=[old_snapshot_id],
    )
    old_as_of = (datetime.now(UTC) - timedelta(days=35)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    newer_as_of = (datetime.now(UTC) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    old_snapshot = snapshot_factory(snapshot_id=old_snapshot_id, as_of=old_as_of)
    new_snapshot = snapshot_factory(snapshot_id=uuid4(), as_of=newer_as_of)  # same ticker TEST
    artifact_repo.save(belief)
    artifact_repo.save(old_snapshot)
    artifact_repo.save(new_snapshot)
    service = BeliefAnalysisService(artifact_repo, lifecycle_repo)
    results = service.get_beliefs_needing_review()
    assert "TEST" in results
    assert len(results["TEST"]) == 1
    assert results["TEST"][0]["belief_id"] == str(belief.reasoning_id)


def test_snapshot_coverage_gap(artifact_repo, lifecycle_repo):
    belief = reasoning_artifact_factory(snapshot_ids=[])
    artifact_repo.save(belief)
    service = BeliefAnalysisService(artifact_repo, lifecycle_repo)
    coverage = service.get_snapshot_coverage(str(belief.reasoning_id))
    assert coverage["coverage_gap"] is True


def test_get_open_questions(artifact_repo):
    question = reasoning_artifact_factory(
        artifact_type=ArtifactType.question,
        created_at=datetime.now(UTC) - timedelta(days=10),
        snapshot_ids=[],
    )
    artifact_repo.save(question)
    service = IntrospectionService(artifact_repo)
    results = service.get_open_questions()
    assert "uncoupled" in results
    assert len(results["uncoupled"]) == 1
    assert results["uncoupled"][0]["age_days"] >= 10
    assert results["uncoupled"][0]["question_id"] == str(question.reasoning_id)
