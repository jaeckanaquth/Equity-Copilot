from datetime import datetime, timezone
from core.models.reasoning_artifact import ArtifactType


class IntrospectionService:

    def __init__(self, artifact_repo):
        self.artifact_repo = artifact_repo

    def get_open_questions(self):
        artifacts = self.artifact_repo.list_by_type("ReasoningArtifact")

        results = []

        for artifact in artifacts:
            if artifact.artifact_type != ArtifactType.question:
                continue

            age_days = (datetime.now(timezone.utc) - artifact.created_at).days

            results.append({
                "question_id": str(artifact.reasoning_id),
                "created_at": artifact.created_at,
                "age_days": age_days,
                "snapshot_ids": [
                    str(sid) for sid in artifact.references.snapshot_ids
                ],
            })

        return results
