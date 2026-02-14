"""
Phase 3.2 — Deterministic proposal engine.

Generates structural proposals only. No LLM. No synthesis.

Status: pending | accepted | rejected | expired (no deletion).

Critical rule: Accept/Reject are acknowledgments only. They do NOT:
  - Add snapshot reference
  - Create lifecycle event on belief
  - Modify any artifact
"""
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any
from uuid import uuid4


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

from core.services.belief_analysis_service import BeliefAnalysisService
from core.services.artifact_integrity_service import ArtifactIntegrityService


TTL_DAYS = 30


class ProposalEngine:

    def __init__(self, artifact_repo, lifecycle_repo, proposal_repo):
        self.artifact_repo = artifact_repo
        self.lifecycle_repo = lifecycle_repo
        self.proposal_repo = proposal_repo
        self._belief_analysis = BeliefAnalysisService(artifact_repo, lifecycle_repo)
        self._integrity = ArtifactIntegrityService(artifact_repo)

    def evaluate(self):
        """Run deterministic evaluation. Canonical order: expire first, generate after."""
        self._expire_ttl()
        self._expire_resolved_conditions()
        self._generate_missing_grounding()
        self._generate_stale()

    def _expire_ttl(self):
        """Expire pending proposals older than TTL."""
        self.proposal_repo.expire_older_than_days(TTL_DAYS)

    def _expire_resolved_conditions(self):
        """If condition false → expire all non-expired proposals of that type.
        Clean false→true transitions: expiration clears slate when world changes."""
        stale_belief_ids = {
            item["belief_id"]
            for items in self._belief_analysis.get_beliefs_needing_review().values()
            for item in items
        }
        for row in self.proposal_repo.list_non_expired_by_type("review_prompt"):
            belief_id = row.payload.get("belief_id")
            if belief_id and belief_id not in stale_belief_ids:
                self.proposal_repo.expire(row.proposal_id)

        ungrounded_belief_ids = {
            b["belief_id"] for b in self._integrity.get_orphans()["beliefs_without_snapshots"]
        }
        for row in self.proposal_repo.list_non_expired_by_type("missing_grounding"):
            belief_id = row.payload.get("belief_id")
            if belief_id and belief_id not in ungrounded_belief_ids:
                self.proposal_repo.expire(row.proposal_id)

    def _generate_stale(self):
        grouped = self._belief_analysis.get_beliefs_needing_review()
        for items in grouped.values():
            for item in items:
                belief_id = item["belief_id"]
                if self.proposal_repo.exists_for_belief(belief_id, "review_prompt"):
                    continue
                self.proposal_repo.create({
                    "proposal_id": str(uuid4()),
                    "proposal_type": "review_prompt",
                    "payload": {
                        "belief_id": belief_id,
                        "belief_text": item["belief_text"],
                        "newer_snapshot_ids": item["newer_snapshot_ids"],
                        "age_days_since_review": item["age_days_since_review"],
                        "condition_state": {
                            "type": "stale",
                            "triggered_at": _now_iso(),
                        },
                    },
                })

    def _generate_missing_grounding(self):
        orphans = self._integrity.get_orphans()
        for item in orphans["beliefs_without_snapshots"]:
            belief_id = item["belief_id"]
            if self.proposal_repo.exists_for_belief(belief_id, "missing_grounding"):
                continue
            self.proposal_repo.create({
                "proposal_id": str(uuid4()),
                "proposal_type": "missing_grounding",
                "payload": {
                    "belief_id": belief_id,
                    "belief_text": item["belief_text"],
                    "condition_state": {
                        "type": "missing_grounding",
                        "triggered_at": _now_iso(),
                    },
                },
            })

    def get_history_for_display(self) -> Dict[str, Dict[str, List[dict]]]:
        """
        Proposal history grouped by (proposal_type, status). Instance-level. Transparency > compression.
        Includes condition_state for audit. Sorted newest-first within each bucket.
        """
        rows = self.proposal_repo.list_all()
        now = datetime.now(timezone.utc)
        grouped: Dict[str, Dict[str, List[dict]]] = defaultdict(lambda: defaultdict(list))

        for row in rows:
            created = row.created_at
            if created and created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            age_days = (now - created).days if created else 0
            item = {
                "proposal_id": row.proposal_id,
                "belief_id": row.payload.get("belief_id", ""),
                "belief_text": row.payload.get("belief_text", ""),
                "created_at": row.created_at.isoformat() if row.created_at else "",
                "status": row.status,
                "age_days": age_days,
                "condition_state": row.payload.get("condition_state"),
            }
            grouped[row.proposal_type][row.status].append(item)

        # Sort each bucket newest-first (list_all is already desc, but we group so re-sort)
        for ptype in grouped:
            for status in grouped[ptype]:
                grouped[ptype][status].sort(
                    key=lambda x: x["created_at"],
                    reverse=True,
                )

        return dict(grouped)

    def list_for_display(self) -> Dict[str, Dict[str, List[dict]]]:
        """
        Return proposals clustered by (proposal_type, belief_text) for display.
        Grouping key = exact string equality. No normalization.
        """
        active = self.proposal_repo.list_active()
        now = datetime.utcnow()
        grouped: Dict[str, Dict[str, List[dict]]] = defaultdict(lambda: defaultdict(list))

        for row in active:
            age_days = (now - row.created_at).days
            belief_text = row.payload.get("belief_text", "")
            instance = {
                "proposal_id": row.proposal_id,
                "belief_id": row.payload["belief_id"],
                "belief_text": belief_text,
                "age_days": age_days,
                "proposal_type": row.proposal_type,
                "condition_state": row.payload.get("condition_state"),
            }
            grouped[row.proposal_type][belief_text].append(instance)

        return dict(grouped)
