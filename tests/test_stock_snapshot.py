import json
import sys
from pathlib import Path
from uuid import UUID
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.models.stock_snapshot import StockSnapshot
from pydantic import ValidationError

IST = ZoneInfo("Asia/Kolkata")


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "stock_snapshot_v1.json"


def load_fixture() -> dict:
    with FIXTURE_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_fixture_loads_into_model():
    data = load_fixture()
    snapshot = StockSnapshot.model_validate(data)

    assert isinstance(snapshot, StockSnapshot)
    assert snapshot.metadata.schema_version == "v1"


def test_snapshot_is_immutable():
    snapshot = StockSnapshot.model_validate(load_fixture())

    with pytest.raises(ValidationError):
        snapshot.company.ticker = "INFY"



def test_as_of_is_ist_timezone():
    snapshot = StockSnapshot.model_validate(load_fixture())

    as_of = snapshot.metadata.as_of
    assert isinstance(as_of, datetime)
    assert as_of.tzinfo is not None
    assert as_of.tzinfo == IST


def test_snapshot_id_is_uuid():
    snapshot = StockSnapshot.model_validate(load_fixture())

    assert isinstance(snapshot.metadata.snapshot_id, UUID)



def test_explicit_nulls_preserved():
    snapshot = StockSnapshot.model_validate(load_fixture())
    dumped = snapshot.model_dump(mode="json")

    assert dumped["financials"]["quarterly_revenue"][2] is None
    assert dumped["balance_sheet"]["total_debt"] is None


# --- Builder (from test_stock_snapshot_builder) ---

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
    from core.builders.stock_snapshot_builder import build_stock_snapshot
    snapshot = build_stock_snapshot(**valid_snapshot_kwargs())
    assert isinstance(snapshot, StockSnapshot)
    assert snapshot.metadata.schema_version == "v1"


def test_builder_fails_on_invalid_input():
    from core.builders.stock_snapshot_builder import build_stock_snapshot
    bad = valid_snapshot_kwargs()
    bad["metadata"]["schema_version"] = "v2"
    with pytest.raises(Exception):
        build_stock_snapshot(**bad)
