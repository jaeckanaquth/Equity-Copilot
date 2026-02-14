from datetime import datetime, timedelta, timezone

from core.models.reasoning_artifact import ArtifactType
from core.services.introspection_service import IntrospectionService
from tests.fixtures.artifact_factory import reasoning_artifact_factory


def test_get_open_questions(artifact_repo):
    question = reasoning_artifact_factory(
        artifact_type=ArtifactType.question,
        created_at=datetime.now(timezone.utc) - timedelta(days=10),
        snapshot_ids=[],
    )

    artifact_repo.save(question)

    service = IntrospectionService(artifact_repo)
    results = service.get_open_questions()

    assert len(results) == 1
    assert results[0]["age_days"] >= 10
    assert results[0]["question_id"] == str(question.reasoning_id)
