"""Add a snapshot with as_of newer than existing beliefs (no lifecycle event).

Run from project root: python scripts/seed_snapshot_newer_than_belief.py

Then refresh /weekly-review. Beliefs Needing Review should be populated.
If not, temporal logic is broken.
"""
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Ensure project root is on path when run as script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.session import SessionLocal
from core.repositories.artifact_repository import ArtifactRepository
from tests.fixtures.snapshot_factory import make_snapshot


def main():
    db = SessionLocal()
    try:
        repo = ArtifactRepository(db)
        # as_of = now + 1 hour ensures snapshot is newer than any existing belief
        newer_as_of = datetime.now(timezone.utc) + timedelta(hours=1)
        snapshot = make_snapshot(as_of=newer_as_of)
        repo.save(snapshot)
        print(f"Created snapshot: {snapshot.metadata.snapshot_id}")
        print(f"  as_of: {snapshot.metadata.as_of}")
        print("Refresh /weekly-review — Beliefs Needing Review should be populated")
    finally:
        db.close()


if __name__ == "__main__":
    main()
