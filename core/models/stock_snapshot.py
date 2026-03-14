from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_validator

IST = ZoneInfo("Asia/Kolkata")


# -----------------------------
# 4.1 Snapshot Metadata
# -----------------------------
class SnapshotMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    snapshot_id: UUID
    as_of: datetime
    schema_version: Literal["v1"] = Field(default="v1")
    data_sources: list[str] | None

    @field_validator("as_of")
    @classmethod
    def enforce_ist_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("as_of must be timezone-aware (IST required)")
        return value.astimezone(IST)


# -----------------------------
# 4.2 Company Identity
# -----------------------------
class CompanyIdentity(BaseModel):
    model_config = ConfigDict(frozen=True)

    ticker: str | None
    exchange: str | None
    company_name: str | None
    sector: str | None
    industry: str | None
    country: str | None


# -----------------------------
# 4.3 Market State (Observed)
# -----------------------------
class MarketState(BaseModel):
    model_config = ConfigDict(frozen=True)

    current_price: Decimal | None
    currency: str | None
    market_cap: Decimal | None
    shares_outstanding: Decimal | None
    fifty_two_week_high: Decimal | None
    fifty_two_week_low: Decimal | None


# -----------------------------
# 4.4 Financial Summary
# -----------------------------
class FinancialSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    # Annual (last completed FY)
    revenue_fy: Decimal | None
    net_profit_fy: Decimal | None
    operating_margin_fy: Decimal | None

    # Recent quarters (oldest → newest)
    quarterly_revenue: list[Decimal | None] | None
    quarterly_net_profit: list[Decimal | None] | None


# -----------------------------
# 4.5 Balance Sheet Signals
# -----------------------------
class BalanceSheetSignals(BaseModel):
    model_config = ConfigDict(frozen=True)

    total_assets: Decimal | None
    total_liabilities: Decimal | None
    total_debt: Decimal | None
    cash_and_equivalents: Decimal | None


# -----------------------------
# 4.6 User Notes
# -----------------------------
class UserNotes(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_notes: str | None


# -----------------------------
# 4. Snapshot Root
# -----------------------------
class StockSnapshot(BaseModel):
    """
    StockSnapshot v1
    Immutable, factual, time-bound record of one publicly listed company.
    """
    model_config = ConfigDict(frozen=True)

    metadata: SnapshotMetadata
    company: CompanyIdentity
    market_state: MarketState
    financials: FinancialSummary
    balance_sheet: BalanceSheetSignals
    user_notes: UserNotes | None
