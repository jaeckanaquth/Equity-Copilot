"""
Add a belief (thesis/risk) or question by statement and optional snapshot refs.

Usage:
  python scripts/add_artifact.py list-snapshots
  python scripts/add_artifact.py belief "MSFT cloud growth will decelerate." [--snapshots ID1 ID2 ...] [--risk]
  python scripts/add_artifact.py question "What is the margin trajectory for AWS?" [--snapshots ID1 ID2 ...]
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4, UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.session import SessionLocal
from core.repositories.artifact_repository import ArtifactRepository
from core.models.reasoning_artifact import (
    ReasoningArtifact,
    ReasoningSubject,
    ReasoningReferences,
    ReasoningClaim,
    ReasoningDetail,
    ReasoningConfidence,
    ReasoningReview,
    CreatedBy,
    ArtifactType,
    Stance,
    ConfidenceLevel,
    SubjectEntityType,
)


def list_snapshots():
    db = SessionLocal()
    repo = ArtifactRepository(db)
    snapshots = repo.list_by_type("StockSnapshot")
    db.close()
    if not snapshots:
        print("No snapshots. Run: python scripts/import_snapshots.py --clear")
        return
    print("\nSnapshots (use these IDs for --snapshots):\n")
    for s in sorted(snapshots, key=lambda x: (x.company.ticker or "", x.metadata.as_of), reverse=True):
        ticker = s.company.ticker or "?"
        as_of = s.metadata.as_of.date() if hasattr(s.metadata.as_of, "date") else s.metadata.as_of
        rev = s.financials.revenue_fy if s.financials and s.financials.revenue_fy else "—"
        print(f"  {s.metadata.snapshot_id}  {ticker}  {as_of}  revenue={rev}")
    print()


def _parse_snapshot_ids(raw: list[str]) -> list[UUID]:
    out = []
    for s in raw:
        s = s.strip()
        if not s:
            continue
        try:
            out.append(UUID(s))
        except ValueError:
            print(f"Warning: invalid UUID ignored: {s}")
    return out


def add_belief(statement: str, snapshot_ids: list[UUID], risk: bool):
    artifact_type = ArtifactType.risk if risk else ArtifactType.thesis
    refs = ReasoningReferences(
        snapshot_ids=snapshot_ids,
        derived_metric_set_ids=[],
        analysis_view_ids=[],
    )
    subject = ReasoningSubject(entity_type=SubjectEntityType.company, entity_id="portfolio")
    artifact = ReasoningArtifact(
        reasoning_id=uuid4(),
        schema_version="v1",
        created_at=datetime.now(timezone.utc),
        created_by=CreatedBy.human,
        artifact_type=artifact_type,
        subject=subject,
        references=refs,
        claim=ReasoningClaim(statement=statement, stance=Stance.neutral),
        reasoning=ReasoningDetail(rationale=[], assumptions=[], counterpoints=[]),
        confidence=ReasoningConfidence(confidence_level=ConfidenceLevel.medium, confidence_rationale=""),
        review=ReasoningReview(review_by=None, review_trigger=None),
    )
    db = SessionLocal()
    repo = ArtifactRepository(db)
    repo.save(artifact)
    db.close()
    print(f"Created {artifact_type.value}: {artifact.reasoning_id}")
    print(f"  {statement[:80]}{'...' if len(statement) > 80 else ''}")
    print(f"  Snapshots: {len(snapshot_ids)}")
    print(f"  View: /beliefs/{artifact.reasoning_id}")


def add_question(statement: str, snapshot_ids: list[UUID]):
    refs = ReasoningReferences(
        snapshot_ids=snapshot_ids,
        derived_metric_set_ids=[],
        analysis_view_ids=[],
    )
    subject = ReasoningSubject(entity_type=SubjectEntityType.company, entity_id="portfolio")
    artifact = ReasoningArtifact(
        reasoning_id=uuid4(),
        schema_version="v1",
        created_at=datetime.now(timezone.utc),
        created_by=CreatedBy.human,
        artifact_type=ArtifactType.question,
        subject=subject,
        references=refs,
        claim=ReasoningClaim(statement=statement, stance=Stance.exploratory),
        reasoning=ReasoningDetail(rationale=[], assumptions=[], counterpoints=[]),
        confidence=ReasoningConfidence(confidence_level=ConfidenceLevel.medium, confidence_rationale=""),
        review=ReasoningReview(review_by=None, review_trigger=None),
    )
    db = SessionLocal()
    repo = ArtifactRepository(db)
    repo.save(artifact)
    db.close()
    print(f"Created question: {artifact.reasoning_id}")
    print(f"  {statement[:80]}{'...' if len(statement) > 80 else ''}")
    print(f"  Snapshots: {len(snapshot_ids)}")
    print(f"  View: /questions/{artifact.reasoning_id}")


def main():
    import argparse
    p = argparse.ArgumentParser(description="Add a belief or question, or list snapshots.")
    sub = p.add_subparsers(dest="cmd", required=True)
    # list-snapshots
    sub.add_parser("list-snapshots", help="List snapshot IDs for --snapshots")
    # belief
    b = sub.add_parser("belief", help="Add a thesis (or risk with --risk)")
    b.add_argument("statement", help="Belief statement")
    b.add_argument("--snapshots", nargs="*", default=[], help="Snapshot UUIDs to reference")
    b.add_argument("--risk", action="store_true", help="Create as risk instead of thesis")
    # question
    q = sub.add_parser("question", help="Add a research question")
    q.add_argument("statement", help="Question text")
    q.add_argument("--snapshots", nargs="*", default=[], help="Snapshot UUIDs to reference")

    args = p.parse_args()
    if args.cmd == "list-snapshots":
        list_snapshots()
        return
    if args.cmd == "belief":
        add_belief(args.statement, _parse_snapshot_ids(args.snapshots), getattr(args, "risk", False))
        return
    if args.cmd == "question":
        add_question(args.statement, _parse_snapshot_ids(args.snapshots))
        return


if __name__ == "__main__":
    main()
