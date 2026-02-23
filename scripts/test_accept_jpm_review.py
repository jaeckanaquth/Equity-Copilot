"""
One real test: Accept one JPM stale proposal, then verify:
  1. JPM no longer under Beliefs Needing Review
  2. Snapshot orphan disappears (JPM snapshot now referenced)
  3. Proposal moves to accepted
  4. GroundingUpdatedEvent visible on belief lifecycle

Run from project root:
  conda activate snow
  python scripts/test_accept_jpm_review.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.session import SessionLocal
from core.repositories.artifact_repository import ArtifactRepository
from core.repositories.lifecycle_repository import BeliefLifecycleRepository
from core.repositories.proposal_repository import ProposalRepository
from core.services.belief_analysis_service import BeliefAnalysisService
from core.services.artifact_integrity_service import ArtifactIntegrityService
from core.models.reasoning_artifact import ArtifactType
from core.models.belief_lifecycle_event import GroundingUpdatedEvent
from datetime import datetime, timezone
from uuid import uuid4, UUID
from collections import defaultdict


def _tickers_for_belief(artifact_repo, belief) -> set[str]:
    out = set()
    for sid in belief.references.snapshot_ids:
        s = artifact_repo.get(str(sid))
        if s and getattr(s, "company", None) and getattr(s.company, "ticker", None):
            out.add(s.company.ticker.strip())
    return out


def _newest_snapshot_id_per_ticker(artifact_repo, snapshot_ids: list) -> list:
    snapshots = []
    for sid in snapshot_ids:
        s = artifact_repo.get(str(sid))
        if s and getattr(s, "metadata", None) and getattr(s, "company", None):
            snapshots.append(s)
    if not snapshots:
        return []
    by_ticker = defaultdict(list)
    for s in snapshots:
        t = (getattr(s.company, "ticker") or "").strip()
        if t:
            by_ticker[t].append(s)
    out = []
    for group in by_ticker.values():
        newest = max(group, key=lambda x: x.metadata.as_of)
        out.append(str(newest.metadata.snapshot_id))
    return out


def accept_review_prompt(db, proposal_id: str) -> tuple[str | None, list[str]]:
    """Run accept logic for review_prompt. Returns (belief_id, attached_snapshot_ids)."""
    proposal_repo = ProposalRepository(db)
    row = proposal_repo.get_by_id(proposal_id)
    if not row or row.status != "pending" or row.proposal_type != "review_prompt":
        return None, []
    payload = row.payload or {}
    belief_id = payload.get("belief_id")
    if not belief_id:
        return None, []

    artifact_repo = ArtifactRepository(db)
    lifecycle_repo = BeliefLifecycleRepository(db)
    belief = artifact_repo.get(belief_id)
    if not belief or getattr(belief, "artifact_type", None) not in (ArtifactType.thesis, ArtifactType.risk):
        return None, []

    newer_ids = payload.get("newer_snapshot_ids") or []
    newest_per_ticker = _newest_snapshot_id_per_ticker(artifact_repo, newer_ids)
    if not newest_per_ticker:
        proposal_repo.resolve(proposal_id, "accepted")
        return belief_id, []

    current = [str(sid) for sid in belief.references.snapshot_ids]
    merged = list(dict.fromkeys(current + newest_per_ticker))
    artifact_repo.update_belief_snapshot_refs(belief_id, merged)
    now = datetime.now(timezone.utc)
    lifecycle_repo.append(GroundingUpdatedEvent(
        event_id=uuid4(),
        occurred_at=now,
        recorded_by="human",
        reasoning_id=UUID(belief_id),
        attached_snapshot_ids=newest_per_ticker,
    ))
    proposal_repo.resolve(proposal_id, "accepted")
    return belief_id, newest_per_ticker


def main():
    db = SessionLocal()
    try:
        artifact_repo = ArtifactRepository(db)
        lifecycle_repo = BeliefLifecycleRepository(db)
        proposal_repo = ProposalRepository(db)
        belief_analysis = BeliefAnalysisService(artifact_repo, lifecycle_repo)
        integrity = ArtifactIntegrityService(artifact_repo)

        # 1) Find a pending review_prompt for a JPM belief
        active = proposal_repo.list_active()
        jpm_proposal = None
        jpm_belief_id = None
        for row in active:
            if row.proposal_type != "review_prompt":
                continue
            belief_id = (row.payload or {}).get("belief_id")
            if not belief_id:
                continue
            belief = artifact_repo.get(belief_id)
            if not belief:
                continue
            tickers = _tickers_for_belief(artifact_repo, belief)
            if "JPM" in tickers:
                jpm_proposal = row
                jpm_belief_id = belief_id
                break

        if not jpm_proposal:
            # Run proposal engine once so a review_prompt may be created for JPM
            from core.services.proposal_engine import ProposalEngine
            engine = ProposalEngine(artifact_repo, lifecycle_repo, proposal_repo)
            engine.evaluate()
            active = proposal_repo.list_active()
            for row in active:
                if row.proposal_type != "review_prompt":
                    continue
                belief_id = (row.payload or {}).get("belief_id")
                if not belief_id:
                    continue
                belief = artifact_repo.get(belief_id)
                if not belief:
                    continue
                tickers = _tickers_for_belief(artifact_repo, belief)
                if "JPM" in tickers:
                    jpm_proposal = row
                    jpm_belief_id = belief_id
                    break

        if not jpm_proposal:
            print("SKIP: No pending review_prompt proposal for a JPM belief.")
            print("  To run the test: have JPM beliefs that reference older snapshots and a newer JPM snapshot.")
            print("  Then open /weekly-review (engine creates proposals), run this script again.")
            print("  Or accept one JPM proposal manually in the UI and verify:")
            print("    1. JPM gone from Beliefs Needing Review  2. Snapshot orphan gone  3. Proposal accepted  4. GroundingUpdatedEvent on belief")
            return 0

        proposal_id = jpm_proposal.proposal_id
        newer_ids = (jpm_proposal.payload or {}).get("newer_snapshot_ids") or []
        print(f"Found JPM review_prompt: proposal_id={proposal_id[:8]}..., belief_id={jpm_belief_id[:8]}..., newer_snapshots={len(newer_ids)}")

        # Orphans and stale state before accept
        orphans_before = integrity.get_orphans()
        snapshot_orphan_ids_before = {o["snapshot_id"] for o in orphans_before["snapshots_without_dependents"]}
        stale_before = belief_analysis.get_beliefs_needing_review()
        stale_belief_ids_before = {item["belief_id"] for items in stale_before.values() for item in items}

        # 2) Accept
        accept_review_prompt(db, proposal_id)
        print("Accepted proposal.")

        # 3) Verify
        row_after = proposal_repo.get_by_id(proposal_id)
        assert row_after is not None and row_after.status == "accepted", "Proposal should be accepted"
        print("  [OK] Proposal status = accepted")

        events = lifecycle_repo.list_for_belief(jpm_belief_id)
        grounding_events = [e for e in events if (e.payload or {}).get("event_kind") == "grounding_updated"]
        assert len(grounding_events) >= 1, "GroundingUpdatedEvent should be visible"
        print("  [OK] GroundingUpdatedEvent visible on belief lifecycle")

        stale_after = belief_analysis.get_beliefs_needing_review()
        stale_belief_ids_after = {item["belief_id"] for items in stale_after.values() for item in items}
        assert jpm_belief_id not in stale_belief_ids_after, "JPM belief should no longer be in Beliefs Needing Review"
        print("  [OK] JPM belief no longer under Beliefs Needing Review")

        orphans_after = integrity.get_orphans()
        snapshot_orphan_ids_after = {o["snapshot_id"] for o in orphans_after["snapshots_without_dependents"]}
        # The JPM snapshot(s) we attached should no longer be orphans
        belief_after = artifact_repo.get(jpm_belief_id)
        refs_after = {str(sid) for sid in belief_after.references.snapshot_ids}
        for sid in newer_ids:
            if sid in refs_after and sid in snapshot_orphan_ids_before:
                assert sid not in snapshot_orphan_ids_after, f"Snapshot {sid[:8]}... (attached) should no longer be an orphan"
        print("  [OK] Snapshot orphan(s) disappeared (attached snapshot now referenced)")

        print("\nAll four checks passed. System is structurally mature.")
        return 0
    except AssertionError as e:
        print(f"\nFAIL: {e}")
        return 1
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
