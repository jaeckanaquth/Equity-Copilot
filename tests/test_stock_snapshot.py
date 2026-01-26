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
