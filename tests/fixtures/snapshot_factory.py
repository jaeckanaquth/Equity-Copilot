from decimal import Decimal
from datetime import datetime
from uuid import uuid4

import pytest

from core.models.stock_snapshot import StockSnapshot


@pytest.fixture
def snapshot_factory():
    def _factory(
        *,
        snapshot_id=None,
        as_of="2024-03-31T00:00:00Z",
        revenue_fy=100,
        **overrides,
    ):
        # Handle nested overrides - allow overriding nested fields
        metadata_overrides = overrides.pop("metadata", {})
        company_overrides = overrides.pop("company", {})
        market_state_overrides = overrides.pop("market_state", {})
        financials_overrides = overrides.pop("financials", {})
        balance_sheet_overrides = overrides.pop("balance_sheet", {})
        user_notes_overrides = overrides.pop("user_notes", {})
        
        base = {
            "metadata": {
                "snapshot_id": snapshot_id or uuid4(),
                "as_of": datetime.fromisoformat(as_of.replace("Z", "+00:00")),
                "schema_version": "v1",
                "data_sources": ["test_fixture"],
                **metadata_overrides,
            },
            "company": {
                "ticker": "TEST",
                "exchange": "NSE",
                "company_name": "Test Co",
                "sector": "Test",
                "industry": "Test",
                "country": "IN",
                **company_overrides,
            },
            "market_state": {
                "current_price": Decimal("100"),
                "currency": "INR",
                "market_cap": Decimal("1000000"),
                "shares_outstanding": Decimal("10000"),
                "fifty_two_week_high": Decimal("120"),
                "fifty_two_week_low": Decimal("80"),
                **market_state_overrides,
            },
            "financials": {
                "revenue_fy": Decimal(str(revenue_fy)) if revenue_fy is not None else None,
                "net_profit_fy": Decimal("10"),
                "operating_margin_fy": Decimal("0.1"),
                "quarterly_revenue": [Decimal("20"), Decimal("22"), Decimal("24"), Decimal("26")],
                "quarterly_net_profit": [Decimal("2"), Decimal("2"), Decimal("3"), Decimal("3")],
                **financials_overrides,
            },
            "balance_sheet": {
                "total_assets": Decimal("500"),
                "total_liabilities": Decimal("200"),
                "total_debt": Decimal("100"),
                "cash_and_equivalents": Decimal("50"),
                **balance_sheet_overrides,
            },
            "user_notes": {
                "user_notes": None,
                **user_notes_overrides,
            } if user_notes_overrides else None,
        }
        
        # Apply any remaining top-level overrides (for backward compatibility)
        # These would need to be mapped to nested structures
        if overrides:
            # Map old flat keys to nested structures if needed
            flat_to_nested = {
                "snapshot_id": ("metadata", "snapshot_id"),
                "as_of": ("metadata", "as_of"),
                "schema_version": ("metadata", "schema_version"),
                "data_sources": ("metadata", "data_sources"),
                "ticker": ("company", "ticker"),
                "exchange": ("company", "exchange"),
                "company_name": ("company", "company_name"),
                "sector": ("company", "sector"),
                "industry": ("company", "industry"),
                "country": ("company", "country"),
                "current_price": ("market_state", "current_price"),
                "currency": ("market_state", "currency"),
                "market_cap": ("market_state", "market_cap"),
                "shares_outstanding": ("market_state", "shares_outstanding"),
                "fifty_two_week_high": ("market_state", "fifty_two_week_high"),
                "fifty_two_week_low": ("market_state", "fifty_two_week_low"),
                "revenue_fy": ("financials", "revenue_fy"),
                "net_profit_fy": ("financials", "net_profit_fy"),
                "operating_margin_fy": ("financials", "operating_margin_fy"),
                "quarterly_revenue": ("financials", "quarterly_revenue"),
                "quarterly_net_profit": ("financials", "quarterly_net_profit"),
                "total_assets": ("balance_sheet", "total_assets"),
                "total_liabilities": ("balance_sheet", "total_liabilities"),
                "total_debt": ("balance_sheet", "total_debt"),
                "cash_and_equivalents": ("balance_sheet", "cash_and_equivalents"),
                "user_notes": ("user_notes", "user_notes"),
            }
            
            for key, value in overrides.items():
                if key in flat_to_nested:
                    section, field = flat_to_nested[key]
                    # Convert numeric values to Decimal if needed
                    if isinstance(value, (int, float)) and value is not None:
                        if section in ("market_state", "financials", "balance_sheet"):
                            value = Decimal(str(value))
                    elif isinstance(value, list) and section == "financials":
                        value = [Decimal(str(v)) if v is not None and isinstance(v, (int, float)) else v for v in value]
                    elif key == "user_notes" and value is not None:
                        # Handle user_notes specially - if it's a string, wrap it in a dict
                        if isinstance(value, str):
                            base["user_notes"] = {"user_notes": value}
                            continue
                    base[section][field] = value
        
        return StockSnapshot(**base)

    return _factory
