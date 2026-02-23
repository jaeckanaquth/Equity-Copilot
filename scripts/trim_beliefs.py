"""
Trim beliefs to target: 2–3 per company, 1–2 comparative, ~7–8 total.
Keeps oldest within each group; deletes excess. Run after dedupe.

  conda activate snow
  python scripts/trim_beliefs.py
  python scripts/trim_beliefs.py --dry-run
  python scripts/trim_beliefs.py --per-company 3 --comparative 2 --total 10
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from collections import defaultdict
from typing import Set

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.session import SessionLocal
from db.models.artifact import ArtifactORM
from db.models.lifecycle import BeliefLifecycleEventORM


def _tickers_from_payload(artifact_repo, payload: dict) -> Set[str]:
    refs = (payload or {}).get("references") or {}
    sids = refs.get("snapshot_ids") or []
    tickers = set()
    for sid in sids:
        s = artifact_repo.get(str(sid))
        if s and getattr(s, "company", None) and getattr(s.company, "ticker", None):
            tickers.add(s.company.ticker.strip())
    return tickers


def main():
    ap = argparse.ArgumentParser(description="Trim beliefs to 2–3 per company, 1–2 comparative, ~7–8 total.")
    ap.add_argument("--per-company", type=int, default=3, help="Max beliefs per single company (default 3)")
    ap.add_argument("--comparative", type=int, default=2, help="Max comparative (multi-company) beliefs (default 2)")
    ap.add_argument("--total", type=int, default=8, help="Max total beliefs (default 8)")
    ap.add_argument("--dry-run", action="store_true", help="Only print what would be kept/deleted")
    args = ap.parse_args()

    db = SessionLocal()
    try:
        from core.repositories.artifact_repository import ArtifactRepository
        artifact_repo = ArtifactRepository(db)

        rows = (
            db.query(ArtifactORM)
            .filter_by(artifact_type="ReasoningArtifact")
            .all()
        )
        beliefs = []
        for r in rows:
            at = (r.payload or {}).get("artifact_type")
            if at not in ("thesis", "risk"):
                continue
            tickers = _tickers_from_payload(artifact_repo, r.payload)
            beliefs.append({
                "artifact_id": r.artifact_id,
                "created_at": r.created_at,
                "tickers": tickers,
                "statement": ((r.payload or {}).get("claim") or {}).get("statement") or "",
            })

        if not beliefs:
            print("No beliefs found.")
            return 0

        # Single-ticker vs comparative
        single = defaultdict(list)  # ticker -> [beliefs by created_at asc]
        comparative = []
        for b in beliefs:
            if len(b["tickers"]) == 0:
                comparative.append(b)  # no snapshots → treat as comparative for trimming
            elif len(b["tickers"]) == 1:
                t = next(iter(b["tickers"]))
                single[t].append(b)
            else:
                comparative.append(b)

        for t in single:
            single[t].sort(key=lambda x: x["created_at"])
        comparative.sort(key=lambda x: x["created_at"])

        # Keep oldest up to limit per group
        kept_ids = set()
        for t, group in single.items():
            for b in group[: args.per_company]:
                kept_ids.add(b["artifact_id"])
        for b in comparative[: args.comparative]:
            kept_ids.add(b["artifact_id"])

        # If over total cap, drop newest globally until at cap
        all_kept = [b for b in beliefs if b["artifact_id"] in kept_ids]
        all_kept.sort(key=lambda x: x["created_at"])
        while len(kept_ids) > args.total and all_kept:
            drop = all_kept.pop(-1)
            kept_ids.discard(drop["artifact_id"])

        to_delete = [b for b in beliefs if b["artifact_id"] not in kept_ids]
        if not to_delete:
            print("No excess beliefs; already at or below target.")
            return 0

        print(f"Keeping {len(kept_ids)} belief(s), deleting {len(to_delete)}.")
        for b in to_delete:
            print(f"  DELETE {b['artifact_id'][:8]}...  {b['statement'][:60]}...")
        if args.dry_run:
            print("[dry-run] No changes made.")
            return 0

        for b in to_delete:
            aid = b["artifact_id"]
            db.query(BeliefLifecycleEventORM).filter(BeliefLifecycleEventORM.belief_id == aid).delete(
                synchronize_session=False
            )
            db.query(ArtifactORM).filter(ArtifactORM.artifact_id == aid).delete(synchronize_session=False)
        db.commit()
        print("Done.")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
