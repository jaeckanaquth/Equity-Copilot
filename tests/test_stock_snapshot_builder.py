import pytest

from core.builders.stock_snapshot_builder import build_stock_snapshot
from core.models.stock_snapshot import StockSnapshot


def valid_snapshot_kwargs():
    return dict(
        metadata={
            "snapshot_id": "9a2f6e7a-3e9a-4c91-b6d2-0c3e8f6b9c41",
            "as_of": "2026-01-26T18:30:00+05:30",
            "schema_version": "v1",
            "data_sources": ["manual"],
        },
        company={
            "ticker": "TCS",
            "exchange": "NSE",
            "company_name": "Tata Consultancy Services Ltd",
            "sector": "IT",
            "industry": "IT Services",
            "country": "India",
        },
        market_state={
            "current_price": 3890.5,
            "currency": "INR",
            "market_cap": 14200000000000,
            "shares_outstanding": 3650000000,
            "fifty_two_week_high": 4254.75,
            "fifty_two_week_low": 3050.1,
        },
        financials={
            "revenue_fy": 240893000000,
            "net_profit_fy": 44302000000,
            "operating_margin_fy": 0.248,
            "quarterly_revenue": [58000000000, None],
            "quarterly_net_profit": [11000000000],
        },
        balance_sheet={
            "total_assets": 153000000000,
            "total_liabilities": 48000000000,
            "total_debt": None,
            "cash_and_equivalents": 76000000000,
        },
        user_notes={
            "user_notes": "Manual snapshot for testing"
        },
    )


def test_builder_creates_valid_snapshot():
    snapshot = build_stock_snapshot(**valid_snapshot_kwargs())

    assert isinstance(snapshot, StockSnapshot)
    assert snapshot.metadata.schema_version == "v1"


def test_builder_fails_on_invalid_input():
    bad = valid_snapshot_kwargs()
    bad["metadata"]["schema_version"] = "v2"

    with pytest.raises(Exception):
        build_stock_snapshot(**bad)
