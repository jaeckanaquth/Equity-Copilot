from __future__ import annotations

from typing import Optional, Dict, Any

from core.models.stock_snapshot import (
    StockSnapshot,
    SnapshotMetadata,
    CompanyIdentity,
    MarketState,
    FinancialSummary,
    BalanceSheetSignals,
    UserNotes,
)


def build_stock_snapshot(
    *,
    metadata: Dict[str, Any],
    company: Dict[str, Any],
    market_state: Dict[str, Any],
    financials: Dict[str, Any],
    balance_sheet: Dict[str, Any],
    user_notes: Optional[Dict[str, Any]] = None,
) -> StockSnapshot:
    """
    Construct a StockSnapshot v1 from explicit inputs.

    This function:
    - Performs no enrichment
    - Performs no defaulting
    - Performs no interpretation
    - Delegates all validation to Pydantic models

    Any invalid input MUST raise a validation error.
    """

    return StockSnapshot(
        metadata=SnapshotMetadata(**metadata),
        company=CompanyIdentity(**company),
        market_state=MarketState(**market_state),
        financials=FinancialSummary(**financials),
        balance_sheet=BalanceSheetSignals(**balance_sheet),
        user_notes=UserNotes(**user_notes) if user_notes is not None else None,
    )
