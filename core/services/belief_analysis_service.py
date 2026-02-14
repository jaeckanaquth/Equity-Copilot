from datetime import datetime
from typing import List, Dict
from core.models.reasoning_artifact import ArtifactType
from core.models.stock_snapshot import StockSnapshot
from core.models.reasoning_artifact import ReasoningArtifact


class BeliefAnalysisService:

    def __init__(self, artifact_repo, lifecycle_repo):
        self.artifact_repo = artifact_repo
        self.lifecycle_repo = lifecycle_repo

    # ---------------------------
    # Q3 — Beliefs Needing Review
    # ---------------------------
    def get_beliefs_needing_review(self) -> List[Dict]:

        artifacts = self.artifact_repo.list_by_type("ReasoningArtifact")
        snapshots = self.artifact_repo.list_by_type("StockSnapshot")

        results = []

        for artifact in artifacts:
            if artifact.artifact_type not in {
                ArtifactType.thesis,
                ArtifactType.risk,
            }:
                continue

            lifecycle_events = self.lifecycle_repo.list_for_belief(
                str(artifact.reasoning_id)
            )

            last_review = (
                lifecycle_events[-1].created_at
                if lifecycle_events
                else artifact.created_at
            )

            newer_snapshots = [
                s for s in snapshots
                if s.metadata.as_of > last_review
            ]

            if newer_snapshots:
                results.append({
                    "belief_id": str(artifact.reasoning_id),
                    "last_review": last_review,
                    "newer_snapshot_ids": [
                        str(s.metadata.snapshot_id) for s in newer_snapshots
                    ],
                })

        return results

    # ---------------------------
    # Q1 — Snapshot Coverage
    # ---------------------------
    def get_snapshot_coverage(self, belief_id: str) -> Dict:
        belief: ReasoningArtifact | None = self.artifact_repo.get(belief_id)
        if not belief:
            raise ValueError(f"Belief not found: {belief_id}")

        if belief.artifact_type not in {
            ArtifactType.thesis,
            ArtifactType.risk,
        }:
            raise ValueError("Coverage only valid for beliefs")

        snapshot_ids = belief.references.snapshot_ids

        coverage_gap = False

        if not snapshot_ids:
            coverage_gap = True
        else:
            for sid in snapshot_ids:
                snapshot: StockSnapshot = self.artifact_repo.get(str(sid))
                if not snapshot:
                    coverage_gap = True
                    break
                if snapshot.metadata.as_of < belief.created_at:
                    coverage_gap = True
                    break

        return {
            "belief_id": str(belief.reasoning_id),
            "snapshot_ids": [str(sid) for sid in snapshot_ids],
            "coverage_gap": coverage_gap,
        }
