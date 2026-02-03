from datetime import datetime, timezone
from uuid import uuid4

from core.derivations.compute import compute_revenue_fy_percent_change
from core.models.derived_metrics import (
    DerivedMetric,
    DerivedMetricSet,
    MetricInputRef,
    MetricType,
    SnapshotRef,
)
from core.models.stock_snapshot import StockSnapshot


def build_revenue_yoy_metric_set(
    snapshots: list[StockSnapshot],
) -> DerivedMetricSet:
    if len(snapshots) < 2:
        raise ValueError("At least two snapshots required")

    snapshots_sorted = sorted(snapshots, key=lambda s: s.metadata.as_of)
    older, newer = snapshots_sorted[-2], snapshots_sorted[-1]

    value = compute_revenue_fy_percent_change(older, newer)
    now = datetime.now(timezone.utc)

    metric = DerivedMetric(
        metric_name="revenue_fy_yoy_percent_change",
        metric_type=MetricType.percent_change,
        value=value,
        unit="%",
        formula="(revenue_fy_new - revenue_fy_old) / |revenue_fy_old|",
        inputs=[
            MetricInputRef(
                field_ref="snapshot.revenue_fy",
                snapshot_id=older.metadata.snapshot_id,
            ),
            MetricInputRef(
                field_ref="snapshot.revenue_fy",
                snapshot_id=newer.metadata.snapshot_id,
            ),
        ],
        computed_at=now,
    )

    return DerivedMetricSet(
        derived_set_id=uuid4(),
        created_at=now,
        computation_engine="equity_copilot.derived.v1",
        input_snapshots=[
            SnapshotRef(snapshot_id=s.metadata.snapshot_id, as_of=s.metadata.as_of)
            for s in snapshots_sorted
        ],
        metrics=[metric],
    )
