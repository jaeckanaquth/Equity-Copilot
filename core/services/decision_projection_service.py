"""
Derived Decision State Layer.

Read-only projections over lifecycle decision events.
No persistence. No new tables. Computed every time.
"""
from datetime import datetime
from typing import Any

from core.models.reasoning_artifact import ArtifactType


def _occurred_at_key(e: Any) -> tuple:
    """Sort key: (occurred_at, created_at) for deterministic ordering. Tie-break with created_at."""
    payload = e.payload or {}
    occ = payload.get("occurred_at")
    if isinstance(occ, str):
        try:
            occ = datetime.fromisoformat(occ.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            occ = e.created_at
    if occ is None:
        occ = e.created_at
    return (occ, e.created_at)


class DecisionProjectionService:
    """Computes derived views over decision lifecycle events. No writes."""

    def __init__(self, artifact_repo, lifecycle_repo):
        self.artifact_repo = artifact_repo
        self.lifecycle_repo = lifecycle_repo

    def get_current_decision_state(self, belief_id: str) -> dict | None:
        """
        The most recent event_kind='decision' for this belief, by occurred_at (tie-break created_at).
        Returns None if no decision events. Not stored — derived.
        """
        events = self.lifecycle_repo.list_for_belief(belief_id)
        decisions = [e for e in events if (e.payload or {}).get("event_kind") == "decision"]
        if not decisions:
            return None
        latest = max(decisions, key=_occurred_at_key)
        payload = latest.payload or {}
        return {
            "occurred_at": payload.get("occurred_at"),
            "created_at": latest.created_at.isoformat() if latest.created_at else None,
            "type": (payload.get("decision") or {}).get("type"),
            "rationale": (payload.get("decision") or {}).get("rationale"),
            "event_id": latest.event_id,
        }

    def get_decision_timeline(self, belief_id: str) -> list[dict]:
        """
        Decision-only timeline for this belief, chronological (oldest first).
        Computed from lifecycle stream. No separate table.
        """
        events = self.lifecycle_repo.list_for_belief(belief_id)
        decisions = [e for e in events if (e.payload or {}).get("event_kind") == "decision"]
        if not decisions:
            return []
        sorted_decisions = sorted(decisions, key=_occurred_at_key)
        result = []
        for e in sorted_decisions:
            payload = e.payload or {}
            dec = payload.get("decision") or {}
            occ = payload.get("occurred_at") or (e.created_at.isoformat() if e.created_at else "")
            if isinstance(occ, datetime):
                occ = occ.isoformat()
            result.append({
                "occurred_at": occ,
                "type": dec.get("type", "decision"),
                "rationale": dec.get("rationale"),
            })
        return result

    def get_beliefs_by_current_decision(self, decision_type: str) -> list[dict]:
        """
        Beliefs whose current (latest) decision has type == decision_type.
        Read-only; current state computed per belief.
        """
        artifacts = self.artifact_repo.list_by_type("ReasoningArtifact")
        out = []
        for artifact in artifacts:
            if artifact.artifact_type not in {ArtifactType.thesis, ArtifactType.risk}:
                continue
            belief_id = str(artifact.reasoning_id)
            current = self.get_current_decision_state(belief_id)
            if current and current.get("type") == decision_type:
                out.append({
                    "belief_id": belief_id,
                    "belief_text": artifact.claim.statement[:200] if artifact.claim.statement else "",
                    "artifact_type": artifact.artifact_type.value,
                    "current_decision": current,
                })
        return out

    def get_decision_summary(self, since: datetime | None = None) -> dict[str, int]:
        """
        Counts of decision events by type in the given window (since=). If since is None, all time.
        Returns e.g. {"reinforced": 12, "slight_tension": 5, ...}.
        """
        rows = self.lifecycle_repo.list_decision_events(since=since)
        counts: dict[str, int] = {}
        for r in rows:
            dt = (r.payload or {}).get("decision") or {}
            t = dt.get("type") or "other"
            counts[t] = counts.get(t, 0) + 1
        # Ensure all known types exist (0 if absent)
        for key in (
            "reinforced", "slight_tension", "strong_tension", "revised", "abandoned",
            "confidence_increased", "confidence_decreased", "deferred", "other"
        ):
            counts.setdefault(key, 0)
        return counts
