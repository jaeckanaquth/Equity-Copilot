"""
Derivations module for Phase 2.1.

This module contains pure computation functions and deterministic assembly logic
for deriving metrics from StockSnapshot v1 data.
"""

from core.derivations.compute import compute_revenue_fy_percent_change
from core.derivations.assemble import build_revenue_yoy_metric_set

__all__ = [
    "compute_revenue_fy_percent_change",
    "build_revenue_yoy_metric_set",
]
