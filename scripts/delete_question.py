"""
Delete a question artifact by ID or by statement match.
Use to remove e.g. the "weekly AWS prediction" style question.

  conda activate snow
  python scripts/delete_question.py --match "prediction" "AWS"   # delete questions containing both
  python scripts/delete_question.py --id <uuid>                 # delete by artifact ID
  python scripts/delete_question.py --dry-run --match "prediction" "AWS"  # show only
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.models.artifact import ArtifactORM
from db.models.question_answer import QuestionAnswerORM
from db.session import SessionLocal


def _statement_from_payload(payload: dict) -> str:
    claim = (payload or {}).get("claim") or {}
    if isinstance(claim, dict):
        return (claim.get("statement") or "").strip()
    return ""


def main():
    ap = argparse.ArgumentParser(description="Delete a question by ID or by statement text match.")
    ap.add_argument("--id", dest="artifact_id", help="Question artifact ID (UUID) to delete")
    ap.add_argument("--match", nargs="+", metavar="WORD", help="Delete questions whose statement contains all of these words (case-insensitive)")
    ap.add_argument("--dry-run", action="store_true", help="Only list matching questions, do not delete")
    args = ap.parse_args()

    if not args.artifact_id and not args.match:
        ap.error("Use --id <uuid> or --match WORD [WORD ...]")
    if args.artifact_id and args.match:
        ap.error("Use either --id or --match, not both")

    db = SessionLocal()
    try:
        if args.artifact_id:
            row = db.query(ArtifactORM).filter_by(artifact_id=args.artifact_id).first()
            if not row:
                print(f"No artifact with id {args.artifact_id}")
                return 1
            at = (row.payload or {}).get("artifact_type")
            if at != "question":
                print(f"Artifact {args.artifact_id} is not a question (type={at}). Refusing to delete.")
                return 1
            to_delete = [row]
        else:
            words = [w.lower() for w in args.match]
            rows = (
                db.query(ArtifactORM)
                .filter_by(artifact_type="ReasoningArtifact")
                .all()
            )
            to_delete = []
            for r in rows:
                at = (r.payload or {}).get("artifact_type")
                if at != "question":
                    continue
                st = _statement_from_payload(r.payload).lower()
                if all(w in st for w in words):
                    to_delete.append(r)

        if not to_delete:
            print("No matching question(s) found.")
            return 0

        for r in to_delete:
            st = _statement_from_payload(r.payload)
            print(f"  {r.artifact_id}  {st[:80]}{'...' if len(st) > 80 else ''}")
        if args.dry_run:
            print(f"[dry-run] Would delete {len(to_delete)} question(s).")
            return 0

        for r in to_delete:
            qid = r.artifact_id
            db.query(QuestionAnswerORM).filter_by(question_id=qid).delete(synchronize_session=False)
            db.query(ArtifactORM).filter_by(artifact_id=qid).delete(synchronize_session=False)
        db.commit()
        print(f"Deleted {len(to_delete)} question(s).")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
