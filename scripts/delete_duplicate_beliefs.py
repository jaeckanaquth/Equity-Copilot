"""
Delete duplicate beliefs: same statement + type (thesis/risk). Keeps the oldest per group.
Also removes lifecycle events for deleted belief IDs.

  conda activate snow
  python scripts/delete_duplicate_beliefs.py
"""
from __future__ import annotations

import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.session import SessionLocal
from db.models.artifact import ArtifactORM
from db.models.lifecycle import BeliefLifecycleEventORM


def main():
    db = SessionLocal()
    try:
        rows = (
            db.query(ArtifactORM)
            .filter_by(artifact_type="ReasoningArtifact")
            .all()
        )
        # Only thesis/risk (beliefs)
        belief_rows = []
        for r in rows:
            at = (r.payload or {}).get("artifact_type")
            if at not in ("thesis", "risk"):
                continue
            statement = (r.payload or {}).get("claim") or {}
            if isinstance(statement, dict):
                statement = statement.get("statement") or ""
            else:
                statement = ""
            belief_rows.append((r.artifact_id, r.created_at, statement, at))

        # Group by (statement, artifact_type)
        groups = defaultdict(list)
        for aid, created_at, statement, at in belief_rows:
            key = (statement.strip(), at)
            groups[key].append((aid, created_at))

        # Keep oldest per group; collect duplicate ids
        to_delete = []
        for key, items in groups.items():
            if len(items) <= 1:
                continue
            items.sort(key=lambda x: x[1])
            kept_id = items[0][0]
            for aid, _ in items[1:]:
                to_delete.append(aid)

        if not to_delete:
            print("No duplicate beliefs found.")
            return

        print(f"Deleting {len(to_delete)} duplicate belief(s). Keeping oldest per (statement, type).")
        for aid in to_delete:
            db.query(BeliefLifecycleEventORM).filter(
                BeliefLifecycleEventORM.belief_id == aid
            ).delete(synchronize_session=False)
            db.query(ArtifactORM).filter(ArtifactORM.artifact_id == aid).delete(
                synchronize_session=False
            )
        db.commit()
        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
