from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Literal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator
from zoneinfo import ZoneInfo


IST = ZoneInfo("Asia/Kolkata")


# -----------------------------
# 4.1 Snapshot Metadata
# -----------------------------
class SnapshotMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    snapshot_id: UUID
    as_of: datetime
    schema_version: Literal["v1"] = Field(default="v1")
    data_sources: Optional[List[str]]

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

    ticker: Optional[str]
    exchange: Optional[str]
    company_name: Optional[str]
    sector: Optional[str]
    industry: Optional[str]
    country: Optional[str]


# -----------------------------
# 4.3 Market State (Observed)
# -----------------------------
class MarketState(BaseModel):
    model_config = ConfigDict(frozen=True)

    current_price: Optional[Decimal]
    currency: Optional[str]
    market_cap: Optional[Decimal]
    shares_outstanding: Optional[Decimal]
    fifty_two_week_high: Optional[Decimal]
    fifty_two_week_low: Optional[Decimal]


# -----------------------------
# 4.4 Financial Summary
# -----------------------------
class FinancialSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    # Annual (last completed FY)
    revenue_fy: Optional[Decimal]
    net_profit_fy: Optional[Decimal]
    operating_margin_fy: Optional[Decimal]

    # Recent quarters (oldest → newest)
    quarterly_revenue: Optional[List[Optional[Decimal]]]
    quarterly_net_profit: Optional[List[Optional[Decimal]]]


# -----------------------------
# 4.5 Balance Sheet Signals
# -----------------------------
class BalanceSheetSignals(BaseModel):
    model_config = ConfigDict(frozen=True)

    total_assets: Optional[Decimal]
    total_liabilities: Optional[Decimal]
    total_debt: Optional[Decimal]
    cash_and_equivalents: Optional[Decimal]


# -----------------------------
# 4.6 User Notes
# -----------------------------
class UserNotes(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_notes: Optional[str]


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
    user_notes: Optional[UserNotes]
