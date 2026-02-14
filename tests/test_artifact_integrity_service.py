from core.services.artifact_integrity_service import ArtifactIntegrityService
from tests.fixtures.artifact_factory import reasoning_artifact_factory


def test_orphan_belief_detected(artifact_repo):
    belief = reasoning_artifact_factory(snapshot_ids=[])

    artifact_repo.save(belief)

    service = ArtifactIntegrityService(artifact_repo)
    orphans = service.get_orphans()

    assert str(belief.reasoning_id) in orphans["beliefs_without_snapshots"]
