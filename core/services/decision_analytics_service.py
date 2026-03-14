"""
Decision Analytics Layer.

Descriptive analytics over the decision log: durability, tension density, trajectory patterns.
No writes. No stored metrics. Pure computation. Never evaluative or predictive.
"""
from datetime import UTC, datetime
from typing import Any

from core.models.reasoning_artifact import ArtifactType
from core.services.decision_projection_service import DecisionProjectionService


def _parse_occurred_at(payload: dict, fallback_created_at: datetime | None) -> datetime | None:
    occ = payload.get("occurred_at")
    if isinstance(occ, datetime):
        return occ
    if isinstance(occ, str):
        try:
            return datetime.fromisoformat(occ.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass
    return fallback_created_at


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def _classify_trajectory(sequence: list[str]) -> str:
    """
    Purely descriptive classification. Never stored. Not evaluative.
    Returns: stable | gradual_degradation | sudden_collapse | oscillatory | other
    """
    if not sequence:
        return "other"
    types = sequence
    tension_or_end = {"slight_tension", "strong_tension", "abandoned", "revised"}

    all_reinforced = all(t == "reinforced" for t in types)
    if all_reinforced:
        return "stable"

    has_reinforced_after_tension = False
    for i in range(1, len(types)):
        if types[i] == "reinforced" and types[i - 1] in tension_or_end:
            has_reinforced_after_tension = True
            break
    if has_reinforced_after_tension:
        return "oscillatory"

    if len(types) <= 2 and any(t in ("strong_tension", "abandoned") for t in types):
        return "sudden_collapse"

    if any(t in tension_or_end for t in types):
        return "gradual_degradation"

    return "other"


class DecisionAnalyticsService:
    """
    Read-only analytics over the decision lifecycle stream.
    No DB writes. No cached metrics. Descriptive only — no quality scoring or prediction.
    """

    def __init__(self, artifact_repo, lifecycle_repo):
        self.artifact_repo = artifact_repo
        self.lifecycle_repo = lifecycle_repo
        self._projection = DecisionProjectionService(artifact_repo, lifecycle_repo)

    def get_decision_summary(self, since: datetime | None = None) -> dict[str, int]:
        """Counts of decision events by type (since= optional). Delegates to projection."""
        return self._projection.get_decision_summary(since=since)

    def get_belief_durability(self) -> dict[str, Any]:
        """
        Durability = time from belief creation to first non-reinforced decision.
        Returns median_days, mean_days, distribution buckets, and per-belief list.
        Beliefs with only reinforced decisions have no 'first failure' and are listed with durability_days=None.
        """
        artifacts = self.artifact_repo.list_by_type("ReasoningArtifact")
        beliefs = [
            a for a in artifacts
            if a.artifact_type in {ArtifactType.thesis, ArtifactType.risk}
        ]

        durabilities: list[int | None] = []
        per_belief: list[dict[str, Any]] = []

        for artifact in beliefs:
            belief_id = str(artifact.reasoning_id)
            created_at = _ensure_utc(artifact.created_at) if artifact.created_at else None
            if not created_at:
                per_belief.append({"belief_id": belief_id, "durability_days": None, "reason": "no_created_at"})
                continue

            timeline = self._projection.get_decision_timeline(belief_id)
            first_non_reinforced_at: datetime | None = None
            for entry in timeline:
                if entry.get("type") != "reinforced":
                    occ = entry.get("occurred_at")
                    if isinstance(occ, str):
                        try:
                            first_non_reinforced_at = datetime.fromisoformat(occ.replace("Z", "+00:00"))
                        except (ValueError, TypeError):
                            pass
                    elif isinstance(occ, datetime):
                        first_non_reinforced_at = occ
                    break

            if first_non_reinforced_at is None:
                per_belief.append({"belief_id": belief_id, "durability_days": None, "reason": "only_reinforced"})
                continue

            first_non_reinforced_at = _ensure_utc(first_non_reinforced_at)
            delta = first_non_reinforced_at - created_at
            days = max(0, delta.days)
            durabilities.append(days)
            per_belief.append({"belief_id": belief_id, "durability_days": days})

        durabilities_non_none = [d for d in durabilities if d is not None]
        n = len(durabilities_non_none)
        if n == 0:
            median_days = None
            mean_days = None
            distribution = {"0_30": 0, "31_90": 0, "91_180": 0, "181_plus": 0}
        else:
            sorted_d = sorted(durabilities_non_none)
            mid = n // 2
            median_days = (sorted_d[mid] + sorted_d[mid - 1]) / 2.0 if n % 2 == 0 else float(sorted_d[mid])
            mean_days = sum(sorted_d) / n
            distribution = {"0_30": 0, "31_90": 0, "91_180": 0, "181_plus": 0}
            for d in sorted_d:
                if d <= 30:
                    distribution["0_30"] += 1
                elif d <= 90:
                    distribution["31_90"] += 1
                elif d <= 180:
                    distribution["91_180"] += 1
                else:
                    distribution["181_plus"] += 1

        return {
            "median_days": median_days,
            "mean_days": mean_days,
            "beliefs_with_first_non_reinforced": n,
            "beliefs_only_reinforced": len(per_belief) - n,
            "distribution_days": distribution,
            "per_belief": per_belief,
        }

    def get_tension_density(self) -> dict[str, Any]:
        """
        % of beliefs whose current decision is slight_tension or strong_tension.
        Systemic stress indicator. Descriptive only.
        """
        artifacts = self.artifact_repo.list_by_type("ReasoningArtifact")
        beliefs = [
            a for a in artifacts
            if a.artifact_type in {ArtifactType.thesis, ArtifactType.risk}
        ]
        total = len(beliefs)
        if total == 0:
            return {
                "total_beliefs": 0,
                "under_tension": 0,
                "slight_tension_count": 0,
                "strong_tension_count": 0,
                "tension_density_pct": 0.0,
            }

        slight = 0
        strong = 0
        for artifact in beliefs:
            current = self._projection.get_current_decision_state(str(artifact.reasoning_id))
            if not current:
                continue
            t = current.get("type")
            if t == "slight_tension":
                slight += 1
            elif t == "strong_tension":
                strong += 1

        under_tension = slight + strong
        pct = (under_tension / total * 100.0) if total else 0.0

        return {
            "total_beliefs": total,
            "under_tension": under_tension,
            "slight_tension_count": slight,
            "strong_tension_count": strong,
            "tension_density_pct": round(pct, 2),
        }

    def get_trajectory_patterns(self) -> dict[str, Any]:
        """
        Per-belief decision sequence classified as stable | gradual_degradation | sudden_collapse | oscillatory | other.
        Labels are derived only — never persisted. Descriptive, not evaluative.
        """
        artifacts = self.artifact_repo.list_by_type("ReasoningArtifact")
        beliefs = [
            a for a in artifacts
            if a.artifact_type in {ArtifactType.thesis, ArtifactType.risk}
        ]

        trajectories: list[dict[str, Any]] = []
        counts: dict[str, int] = {}

        for artifact in beliefs:
            belief_id = str(artifact.reasoning_id)
            timeline = self._projection.get_decision_timeline(belief_id)
            sequence = [e.get("type", "other") for e in timeline]
            tag = _classify_trajectory(sequence)
            trajectories.append({
                "belief_id": belief_id,
                "trajectory": tag,
                "sequence": sequence,
            })
            counts[tag] = counts.get(tag, 0) + 1

        return {
            "trajectories": trajectories,
            "counts_by_trajectory": counts,
        }
