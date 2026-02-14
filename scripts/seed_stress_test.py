"""Stress-test the weekly review with varied, realistic data.

Run from project root: python scripts/seed_stress_test.py

Creates:
- 3 tickers (RELIANCE, TCS, INFY) with multiple snapshots each
- 5 open questions (uncoupled, single-company, multi-company)
- 6 beliefs: orphans, coupled, stale (with/without lifecycle events)
- Snapshots with no dependents (orphans)
"""
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.session import SessionLocal
from core.repositories.artifact_repository import ArtifactRepository
from core.repositories.lifecycle_repository import BeliefLifecycleRepository
from core.models.reasoning_artifact import ArtifactType
from core.models.belief_lifecycle_event import (
    BeliefLifecycleEvent,
    BeliefState,
    TriggerType,
    LifecycleTrigger,
    LifecycleJustification,
    RecordedBy,
)
from tests.fixtures.artifact_factory import reasoning_artifact_factory
from tests.fixtures.snapshot_factory import make_snapshot


def main():
    db = SessionLocal()
    try:
        artifact_repo = ArtifactRepository(db)
        lifecycle_repo = BeliefLifecycleRepository(db)
        now = datetime.now(timezone.utc)

        # --- Snapshots for 3 companies (various as_of) ---
        tickers = ["RELIANCE", "TCS", "INFY"]
        snapshots_by_ticker = {}

        for ticker in tickers:
            snapshots = []
            for i in range(3):
                as_of = now - timedelta(days=90 - i * 30)
                snap = make_snapshot(
                    as_of=as_of,
                    revenue_fy=100 + i * 50,
                    company={"ticker": ticker},
                )
                artifact_repo.save(snap)
                snapshots.append(snap)
            snapshots_by_ticker[ticker] = snapshots

        # --- 2 orphan snapshots (no belief references them) ---
        orphan_snap1 = make_snapshot(
            as_of=now - timedelta(days=60),
            company={"ticker": "HDFC"},
        )
        orphan_snap2 = make_snapshot(
            as_of=now - timedelta(days=45),
            company={"ticker": "ICICI"},
        )
        artifact_repo.save(orphan_snap1)
        artifact_repo.save(orphan_snap2)

        # --- Open Questions (5) ---
        questions = []
        # Uncoupled
        q1 = reasoning_artifact_factory(
            artifact_type=ArtifactType.question,
            created_at=now - timedelta(days=25),
            snapshot_ids=[],
            statement="How does management plan to address margin compression in FY25?",
        )
        # Single company
        q2 = reasoning_artifact_factory(
            artifact_type=ArtifactType.question,
            created_at=now - timedelta(days=15),
            snapshot_ids=[snapshots_by_ticker["RELIANCE"][0].metadata.snapshot_id],
            statement="Is the digital initiative capex sustainable at current run rate?",
        )
        # Multi-company
        q3 = reasoning_artifact_factory(
            artifact_type=ArtifactType.question,
            created_at=now - timedelta(days=8),
            snapshot_ids=[
                snapshots_by_ticker["TCS"][1].metadata.snapshot_id,
                snapshots_by_ticker["INFY"][1].metadata.snapshot_id,
            ],
            statement="Which IT major has better deal pipeline visibility for next quarter?",
        )
        # Single company, older
        q4 = reasoning_artifact_factory(
            artifact_type=ArtifactType.question,
            created_at=now - timedelta(days=45),
            snapshot_ids=[snapshots_by_ticker["TCS"][0].metadata.snapshot_id],
            statement="When will attrition normalize to pre-COVID levels?",
        )
        # Uncoupled, very old
        q5 = reasoning_artifact_factory(
            artifact_type=ArtifactType.question,
            created_at=now - timedelta(days=60),
            snapshot_ids=[],
            statement="Need to review sector allocation assumptions.",
        )

        for q in [q1, q2, q3, q4, q5]:
            artifact_repo.save(q)
            questions.append(q)

        # --- Beliefs (6) ---
        rel_snap = snapshots_by_ticker["RELIANCE"][0]
        tcs_snap = snapshots_by_ticker["TCS"][0]
        infy_snap = snapshots_by_ticker["INFY"][0]
        newer_snap = make_snapshot(
            as_of=now - timedelta(days=5),
            company={"ticker": "RELIANCE"},
        )
        artifact_repo.save(newer_snap)

        # Orphan belief 1
        b1 = reasoning_artifact_factory(
            created_at=now - timedelta(days=20),
            snapshot_ids=[],
            statement="Revenue growth will accelerate in H2 FY25.",
        )
        # Orphan belief 2
        b2 = reasoning_artifact_factory(
            created_at=now - timedelta(days=10),
            snapshot_ids=[],
            statement="Competition from Jio Platforms is structural.",
        )
        # Coupled, not stale
        b3 = reasoning_artifact_factory(
            created_at=now - timedelta(days=5),
            snapshot_ids=[rel_snap.metadata.snapshot_id],
            statement="Retail and digital will drive next leg of growth.",
        )
        # Stale: belief old, newer snapshot exists (no lifecycle)
        b4 = reasoning_artifact_factory(
            created_at=now - timedelta(days=40),
            snapshot_ids=[rel_snap.metadata.snapshot_id],
            statement="Energy vertical margins under pressure.",
        )
        # Stale: belief with lifecycle event, but newer snapshot exists
        b5 = reasoning_artifact_factory(
            created_at=now - timedelta(days=50),
            snapshot_ids=[tcs_snap.metadata.snapshot_id],
            statement="Attrition headwind persists through FY25.",
        )
        # Multi-snapshot belief, stale
        b6 = reasoning_artifact_factory(
            created_at=now - timedelta(days=35),
            snapshot_ids=[
                tcs_snap.metadata.snapshot_id,
                infy_snap.metadata.snapshot_id,
            ],
            statement="Both leaders losing share to midcaps in cost-sensitive deals.",
        )

        for belief in [b1, b2, b3, b4, b5, b6]:
            artifact_repo.save(belief)

        # Lifecycle event for b5 (so last_review is recent, but newer snap exists)
        lifecycle_event = BeliefLifecycleEvent(
            event_id=uuid4(),
            occurred_at=now - timedelta(days=20),
            recorded_by=RecordedBy.human,
            reasoning_id=b5.reasoning_id,
            previous_state=BeliefState.active,
            new_state=BeliefState.under_review,
            trigger=LifecycleTrigger(
                trigger_type=TriggerType.scheduled_review,
                description="Quarterly review",
            ),
            justification=LifecycleJustification(
                summary="Revisit after Q3 attrition data",
                snapshot_ids=[],
                derived_metric_set_ids=[],
                analysis_view_ids=[],
                reasoning_artifact_ids=[],
            ),
        )
        lifecycle_repo.append(lifecycle_event)

        # Add one more lifecycle for b6
        lifecycle_event_2 = BeliefLifecycleEvent(
            event_id=uuid4(),
            occurred_at=now - timedelta(days=10),
            recorded_by=RecordedBy.human,
            reasoning_id=b6.reasoning_id,
            previous_state=BeliefState.under_review,
            new_state=BeliefState.active,
            trigger=LifecycleTrigger(
                trigger_type=TriggerType.manual,
                description="Manual refresh",
            ),
            justification=LifecycleJustification(
                summary="Still valid",
                snapshot_ids=[tcs_snap.metadata.snapshot_id, infy_snap.metadata.snapshot_id],
                derived_metric_set_ids=[],
                analysis_view_ids=[],
                reasoning_artifact_ids=[],
            ),
        )
        lifecycle_repo.append(lifecycle_event_2)

        print("Stress test seed complete.")
        print("  Questions: 5 (uncoupled, single-company, multi-company)")
        print("  Beliefs: 6 (2 orphans, 1 coupled, 3 stale)")
        print("  Snapshots: 11 (9 referenced, 2 orphan)")
        print("  Lifecycle events: 2")
        print("Refresh /weekly-review and click through drilldowns.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
