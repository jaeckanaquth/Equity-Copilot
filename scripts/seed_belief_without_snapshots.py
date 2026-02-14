"""Seed a belief without snapshot references for testing the weekly review page.

Run from project root: python scripts/seed_belief_without_snapshots.py

Then refresh /weekly-review. You should see the belief under "Beliefs without Snapshots".
"""
import sys
from pathlib import Path

# Ensure project root is on path when run as script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.session import SessionLocal
from core.repositories.artifact_repository import ArtifactRepository
from tests.fixtures.artifact_factory import reasoning_artifact_factory


def main():
    db = SessionLocal()
    try:
        repo = ArtifactRepository(db)
        belief = reasoning_artifact_factory(snapshot_ids=[], statement="Test belief (no snapshots)")
        repo.save(belief)
        print(f"Created belief: {belief.reasoning_id}")
        print("Refresh /weekly-review — it should appear under 'Beliefs without Snapshots'")
    finally:
        db.close()


if __name__ == "__main__":
    main()
