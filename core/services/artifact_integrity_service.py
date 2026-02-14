from typing import Dict, List
from core.models.reasoning_artifact import ArtifactType


class ArtifactIntegrityService:

    def __init__(self, artifact_repo):
        self.artifact_repo = artifact_repo

    def get_orphans(self) -> Dict:

        reasoning_artifacts = self.artifact_repo.list_by_type("ReasoningArtifact")
        snapshots = self.artifact_repo.list_by_type("StockSnapshot")

        beliefs_without_snapshots: List[str] = []
        referenced_snapshot_ids = set()

        for artifact in reasoning_artifacts:

            if artifact.artifact_type in {
                ArtifactType.thesis,
                ArtifactType.risk,
            }:

                if not artifact.references.snapshot_ids:
                    beliefs_without_snapshots.append(
                        str(artifact.reasoning_id)
                    )
                else:
                    referenced_snapshot_ids.update(
                        str(sid) for sid in artifact.references.snapshot_ids
                    )

        snapshots_without_dependents = [
            str(s.metadata.snapshot_id)
            for s in snapshots
            if str(s.metadata.snapshot_id) not in referenced_snapshot_ids
        ]

        return {
            "beliefs_without_snapshots": beliefs_without_snapshots,
            "snapshots_without_dependents": snapshots_without_dependents,
        }
