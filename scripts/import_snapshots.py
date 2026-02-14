"""
Yahoo Finance → StockSnapshot ingestion.

Architecture rule:
- Produces StockSnapshot objects only.
- Never bypasses Phase 1 model.
- Never auto-creates beliefs, proposals, or runs LLM.
- Snapshots are immutable: if one for this ticker+quarter exists → skip.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid5, UUID

# Project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yfinance as yf
from zoneinfo import ZoneInfo

from db.session import SessionLocal
from db.models.artifact import ArtifactORM
from db.models.lifecycle import BeliefLifecycleEventORM
from db.models.proposal import ProposalORM
from core.repositories.artifact_repository import ArtifactRepository
from core.models.stock_snapshot import (
    StockSnapshot,
    SnapshotMetadata,
    CompanyIdentity,
    MarketState,
    FinancialSummary,
    BalanceSheetSignals,
    UserNotes,
)

IST = ZoneInfo("Asia/Kolkata")
# Deterministic snapshot_id so re-run skips existing (immutable).
NAMESPACE_SNAPSHOT = uuid5(UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8"), "equity-copilot.io/snapshot")

# Default tickers; override via CLI or env.
DEFAULT_TICKERS = ["MSFT", "AMZN", "JPM"]
# How many quarters to pull per ticker.
MAX_QUARTERS = 8


def _safe_decimal(value, default=None):
    if value is None:
        return default
    try:
        f = float(value)
        if f != f:  # NaN
            return default
        return Decimal(str(f))
    except (TypeError, ValueError):
        return default


def _quarter_end_to_ist(dt) -> datetime:
    """Convert quarter-end (naive or aware) to IST for as_of."""
    if hasattr(dt, "to_pydatetime"):
        dt = dt.to_pydatetime()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(IST)


def _get_row(df, *names):
    """First matching index row as Series; df can be None."""
    if df is None or (hasattr(df, "empty") and df.empty):
        return None
    for name in names:
        try:
            out = df.loc[name]
            return out.iloc[0] if hasattr(out, "ndim") and out.ndim > 1 else out
        except (KeyError, TypeError):
            continue
    return None


def build_snapshots_from_yahoo(ticker: str, max_quarters: int = MAX_QUARTERS) -> list[StockSnapshot]:
    """
    Fetch quarterly income statement from Yahoo, map to StockSnapshot.
    One snapshot per quarter. No overwrite: caller must skip if snapshot_id exists.
    """
    t = yf.Ticker(ticker)
    fin = getattr(t, "quarterly_financials", None)
    if fin is None:
        fin = getattr(t, "quarterly_income_stmt", None)
    if fin is None or (hasattr(fin, "empty") and fin.empty):
        return []

    info = getattr(t, "info", None) or {}
    company_name = info.get("longName") or info.get("shortName") or ticker
    sector = info.get("sector")
    industry = info.get("industry")
    country = info.get("country")

    snapshots = []
    columns = list(fin.columns)[:max_quarters]

    for col in columns:
        try:
            period_end = col.to_pydatetime() if hasattr(col, "to_pydatetime") else col
        except Exception:
            continue

        snapshot_id = uuid5(NAMESPACE_SNAPSHOT, f"{ticker}_{period_end.date()!s}")

        def _cell(row, c):
            if row is None or c not in row.index:
                return None
            v = row[c]
            return v.item() if hasattr(v, "item") and hasattr(v, "ndim") and v.ndim == 0 else v

        row = _get_row(fin, "Total Revenue", "Revenue", "Operating Revenue")
        revenue = _safe_decimal(_cell(row, col))

        row = _get_row(fin, "Operating Income", "EBIT", "Operating Earnings")
        op_income = _safe_decimal(_cell(row, col))

        row = _get_row(fin, "Net Income", "Net Income Common Stockholders")
        net_income = _safe_decimal(_cell(row, col))

        if revenue is None:
            continue

        operating_margin = None
        if op_income is not None and revenue and revenue != 0:
            operating_margin = (op_income / revenue) * 100

        metadata = SnapshotMetadata(
            snapshot_id=snapshot_id,
            as_of=_quarter_end_to_ist(period_end),
            schema_version="v1",
            data_sources=["Yahoo Finance"],
        )
        company = CompanyIdentity(
            ticker=ticker,
            exchange=info.get("exchange"),
            company_name=company_name,
            sector=sector,
            industry=industry,
            country=country,
        )
        market = MarketState(
            current_price=None,
            currency=info.get("currency"),
            market_cap=None,
            shares_outstanding=None,
            fifty_two_week_high=None,
            fifty_two_week_low=None,
        )
        financials = FinancialSummary(
            revenue_fy=revenue,
            net_profit_fy=net_income,
            operating_margin_fy=operating_margin,
            quarterly_revenue=[revenue],
            quarterly_net_profit=[net_income],
        )
        balance_sheet = BalanceSheetSignals(
            total_assets=None,
            total_liabilities=None,
            total_debt=None,
            cash_and_equivalents=None,
        )

        snapshot = StockSnapshot(
            metadata=metadata,
            company=company,
            market_state=market,
            financials=financials,
            balance_sheet=balance_sheet,
            user_notes=None,
        )
        snapshots.append(snapshot)

    return snapshots


def clear_all_data(db) -> None:
    """Remove all artifacts, lifecycle events, and proposals. Use with care."""
    db.query(ProposalORM).delete()
    db.query(BeliefLifecycleEventORM).delete()
    db.query(ArtifactORM).delete()
    db.commit()


def main(
    tickers: list[str] | None = None,
    max_quarters: int = MAX_QUARTERS,
    clear_first: bool = False,
):
    tickers = tickers or DEFAULT_TICKERS
    db = SessionLocal()
    repo = ArtifactRepository(db)

    if clear_first:
        clear_all_data(db)
        print("Cleared all artifacts, lifecycle events, and proposals.\n")

    saved = 0
    skipped = 0

    for ticker in tickers:
        try:
            snapshots = build_snapshots_from_yahoo(ticker, max_quarters=max_quarters)
        except Exception as e:
            print(f"[{ticker}] Fetch error: {e}")
            continue

        for s in snapshots:
            sid = str(s.metadata.snapshot_id)
            if repo.get(sid) is not None:
                skipped += 1
                continue
            try:
                repo.save(s)
                saved += 1
                print(f"  + {ticker} {s.metadata.as_of.date()} (revenue={s.financials.revenue_fy})")
            except Exception as e:
                print(f"  ! {ticker} {s.metadata.as_of.date()} save error: {e}")

    db.close()
    print(f"\nDone: {saved} saved, {skipped} skipped (already exist).")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Import quarterly financials from Yahoo into StockSnapshots.")
    p.add_argument("tickers", nargs="*", default=None, help="Tickers (e.g. MSFT AMZN JPM). Default: MSFT AMZN JPM")
    p.add_argument("-q", "--quarters", type=int, default=MAX_QUARTERS, help="Max quarters per ticker")
    p.add_argument("--clear", action="store_true", help="Remove all data first (artifacts, lifecycle, proposals)")
    args = p.parse_args()
    main(
        tickers=args.tickers or DEFAULT_TICKERS,
        max_quarters=args.quarters,
        clear_first=args.clear,
    )
