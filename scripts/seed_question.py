"""Create a question artifact for testing the weekly review page.

Run from project root: python scripts/seed_question.py

Wait 1–2 minutes, then refresh /weekly-review.
The question should appear in Open Questions (age_days will increment after 24h).
"""
import sys
from pathlib import Path

# Ensure project root is on path when run as script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.session import SessionLocal
from core.repositories.artifact_repository import ArtifactRepository
from tests.fixtures.artifact_factory import reasoning_artifact_factory
from core.models.reasoning_artifact import ArtifactType


def main():
    db = SessionLocal()
    try:
        repo = ArtifactRepository(db)
        question = reasoning_artifact_factory(
            artifact_type=ArtifactType.question,
            snapshot_ids=[],
            statement="Test question for weekly review",
        )
        repo.save(question)
        print(f"Created question: {question.reasoning_id}")
        print("Wait 1–2 minutes, then refresh /weekly-review")
    finally:
        db.close()


if __name__ == "__main__":
    main()
