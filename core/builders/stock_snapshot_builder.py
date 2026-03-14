from __future__ import annotations

from typing import Any

from core.models.stock_snapshot import (
    BalanceSheetSignals,
    CompanyIdentity,
    FinancialSummary,
    MarketState,
    SnapshotMetadata,
    StockSnapshot,
    UserNotes,
)


def build_stock_snapshot(
    *,
    metadata: dict[str, Any],
    company: dict[str, Any],
    market_state: dict[str, Any],
    financials: dict[str, Any],
    balance_sheet: dict[str, Any],
    user_notes: dict[str, Any] | None = None,
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
