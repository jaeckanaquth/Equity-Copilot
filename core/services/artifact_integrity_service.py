from datetime import datetime, timezone
from typing import Dict, List
from core.models.reasoning_artifact import ArtifactType


class ArtifactIntegrityService:

    def __init__(self, artifact_repo):
        self.artifact_repo = artifact_repo

    def get_orphans(self) -> Dict:
        reasoning_artifacts = self.artifact_repo.list_by_type("ReasoningArtifact")
        snapshots = self.artifact_repo.list_by_type("StockSnapshot")

        beliefs_without_snapshots = []
        referenced_snapshot_ids = set()

        for artifact in reasoning_artifacts:
            if artifact.artifact_type in {
                ArtifactType.thesis,
                ArtifactType.risk,
            }:
                if not artifact.references.snapshot_ids:
                    beliefs_without_snapshots.append({
                        "belief_id": str(artifact.reasoning_id),
                        "belief_text": artifact.claim.statement,
                    })
                else:
                    referenced_snapshot_ids.update(
                        str(sid) for sid in artifact.references.snapshot_ids
                    )

        snapshots_without_dependents = []
        now = datetime.now(timezone.utc)
        for snapshot in snapshots:
            sid = str(snapshot.metadata.snapshot_id)
            if sid not in referenced_snapshot_ids:
                age_days = (now - snapshot.metadata.as_of).days
                snapshots_without_dependents.append({
                    "snapshot_id": sid,
                    "ticker": snapshot.company.ticker,
                    "as_of": snapshot.metadata.as_of,
                    "age_days": age_days,
                })

        return {
            "beliefs_without_snapshots": beliefs_without_snapshots,
            "snapshots_without_dependents": snapshots_without_dependents,
        }
