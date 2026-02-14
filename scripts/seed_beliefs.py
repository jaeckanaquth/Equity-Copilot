"""
One-off: add the MSFT/AMZN/JPM and comparative beliefs from the example set.
Uses all snapshots per ticker for each belief. Run after import_snapshots.

  conda activate snow
  python scripts/seed_beliefs.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.session import SessionLocal
from core.repositories.artifact_repository import ArtifactRepository
from scripts.add_artifact import add_belief

# (statement, risk, list of tickers for snapshot refs)
BELIEFS = [
    # Microsoft
    ("Azure-led revenue mix will support operating margin expansion over the next two quarters.", False, ["MSFT"]),
    ("AI-related infrastructure investment will not materially compress free cash flow in FY25.", True, ["MSFT"]),
    ("Microsoft's enterprise demand remains structurally resilient despite macro uncertainty.", False, ["MSFT"]),
    # Amazon
    ("AWS growth stabilization will drive consolidated operating margin expansion.", False, ["AMZN"]),
    ("Retail operating income remains vulnerable to demand normalization.", True, ["AMZN"]),
    ("Amazon's profitability trajectory is increasingly dependent on AWS rather than retail recovery.", False, ["AMZN"]),
    # JPMorgan
    ("Net interest margin has peaked and will compress as rates stabilize.", False, ["JPM"]),
    ("Credit costs will remain contained despite macro slowdown risk.", True, ["JPM"]),
    ("Trading and fee income will not materially offset potential NIM compression.", False, ["JPM"]),
    # Comparative
    ("Microsoft's cloud margin profile is structurally more stable than Amazon's.", False, ["MSFT", "AMZN"]),
    ("AWS revenue growth will outpace Azure growth over the next two quarters.", False, ["MSFT", "AMZN"]),
    ("JPMorgan earnings volatility is lower than large-cap tech peers in this cycle.", False, ["JPM", "MSFT", "AMZN"]),
]


def snapshot_ids_by_ticker(repo: ArtifactRepository) -> dict[str, list]:
    out = {}
    for s in repo.list_by_type("StockSnapshot"):
        t = (s.company.ticker or "").strip()
        if not t:
            continue
        if t not in out:
            out[t] = []
        out[t].append(s.metadata.snapshot_id)
    return out


def main():
    db = SessionLocal()
    repo = ArtifactRepository(db)
    db.close()

    by_ticker = snapshot_ids_by_ticker(repo)
    for statement, risk, tickers in BELIEFS:
        ids = []
        for t in tickers:
            ids.extend(by_ticker.get(t, []))
        add_belief(statement, ids, risk)
    print("Done. View Weekly Review: /weekly-review")


if __name__ == "__main__":
    main()
