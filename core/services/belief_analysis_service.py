from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List
from core.models.reasoning_artifact import ArtifactType
from core.models.stock_snapshot import StockSnapshot
from core.models.reasoning_artifact import ReasoningArtifact


def _ensure_utc(dt: datetime) -> datetime:
    """Normalize datetime for comparison (ORM/store may return naive)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class BeliefAnalysisService:

    def __init__(self, artifact_repo, lifecycle_repo):
        self.artifact_repo = artifact_repo
        self.lifecycle_repo = lifecycle_repo

    # ---------------------------
    # Q3 — Beliefs Needing Review
    # ---------------------------
    def get_beliefs_needing_review(self) -> Dict[str, List]:
        artifacts = self.artifact_repo.list_by_type("ReasoningArtifact")
        snapshots = self.artifact_repo.list_by_type("StockSnapshot")
        now = datetime.now(timezone.utc)

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
            last_review = _ensure_utc(last_review)

            tickers = set()
            for sid in artifact.references.snapshot_ids:
                snapshot = self.artifact_repo.get(str(sid))
                if snapshot and snapshot.company.ticker:
                    tickers.add(snapshot.company.ticker)

            newer_snapshots = [
                s for s in snapshots
                if s.metadata.as_of > last_review and s.company.ticker in tickers
            ]

            if newer_snapshots and tickers:
                age_days_since_review = (now - last_review).days

                results.append({
                    "belief_id": str(artifact.reasoning_id),
                    "belief_text": artifact.claim.statement,
                    "age_days_since_review": age_days_since_review,
                    "newer_snapshot_ids": [
                        str(s.metadata.snapshot_id) for s in newer_snapshots
                    ],
                    "company_tickers": sorted(list(tickers)),
                })

        results.sort(key=lambda x: x["age_days_since_review"], reverse=True)

        grouped = defaultdict(list)
        for item in results:
            if not item["company_tickers"]:
                grouped["uncoupled"].append(item)
            else:
                key = ", ".join(item["company_tickers"])
                grouped[key].append(item)

        return dict(grouped)

    # ---------------------------
    # All beliefs (for visibility)
    # ---------------------------
    def get_all_beliefs_grouped(self) -> Dict[str, List]:
        """Return all theses and risks grouped by company ticker (for display)."""
        artifacts = self.artifact_repo.list_by_type("ReasoningArtifact")
        results = []
        for artifact in artifacts:
            if artifact.artifact_type not in {
                ArtifactType.thesis,
                ArtifactType.risk,
            }:
                continue
            tickers = set()
            for sid in artifact.references.snapshot_ids:
                snapshot = self.artifact_repo.get(str(sid))
                if snapshot and snapshot.company.ticker:
                    tickers.add(snapshot.company.ticker)
            results.append({
                "belief_id": str(artifact.reasoning_id),
                "belief_text": artifact.claim.statement,
                "artifact_type": artifact.artifact_type.value,
                "company_tickers": sorted(list(tickers)),
            })
        grouped = defaultdict(list)
        for item in results:
            key = ", ".join(item["company_tickers"]) if item["company_tickers"] else "uncoupled"
            grouped[key].append(item)
        return dict(grouped)

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
                if snapshot.metadata.as_of < _ensure_utc(belief.created_at):
                    coverage_gap = True
                    break

        return {
            "belief_id": str(belief.reasoning_id),
            "snapshot_ids": [str(sid) for sid in snapshot_ids],
            "coverage_gap": coverage_gap,
        }
