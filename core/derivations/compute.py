from typing import Optional

from core.models.stock_snapshot import StockSnapshot


def compute_revenue_fy_percent_change(
    older: StockSnapshot,
    newer: StockSnapshot,
) -> Optional[float]:
    old = older.financials.revenue_fy
    new = newer.financials.revenue_fy

    if old is None or old == 0 or new is None:
        return None

    return float((new - old) / abs(old))
