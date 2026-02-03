from core.derivations.compute import compute_revenue_fy_percent_change
from core.models.stock_snapshot import StockSnapshot


def test_revenue_percent_change_basic(snapshot_factory):
    older = snapshot_factory(revenue_fy=100)
    newer = snapshot_factory(revenue_fy=120)

    result = compute_revenue_fy_percent_change(older, newer)

    assert result == 0.2


def test_revenue_percent_change_null_safe(snapshot_factory):
    older = snapshot_factory(revenue_fy=None)
    newer = snapshot_factory(revenue_fy=120)

    assert compute_revenue_fy_percent_change(older, newer) is None
