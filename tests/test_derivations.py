"""Derived metrics, determinism, valuation multiple view."""
from uuid import uuid4
from datetime import datetime, timezone

from core.derivations.assemble import build_revenue_yoy_metric_set
from core.derivations.compute import compute_revenue_fy_percent_change
from core.views.valuation_multiple import build_valuation_multiple_view
from core.models.analysis_view import (
    AnalysisFrame,
    AnalysisConfidence,
    CreatedBy,
    ConfidenceLevel,
)
from core.models.derived_metrics import DerivedMetric, DerivedMetricSet, MetricType, SnapshotRef


def test_deterministic_output(snapshot_factory):
    s1 = snapshot_factory(as_of="2024-03-31T00:00:00Z", revenue_fy=100)
    s2 = snapshot_factory(as_of="2025-03-31T00:00:00Z", revenue_fy=120)
    d1 = build_revenue_yoy_metric_set([s1, s2])
    d2 = build_revenue_yoy_metric_set([s1, s2])
    assert d1.metrics[0].value == d2.metrics[0].value
    assert d1.metrics[0].formula == d2.metrics[0].formula


def test_revenue_percent_change_basic(snapshot_factory):
    older = snapshot_factory(revenue_fy=100)
    newer = snapshot_factory(revenue_fy=120)
    assert compute_revenue_fy_percent_change(older, newer) == 0.2


def test_revenue_percent_change_null_safe(snapshot_factory):
    older = snapshot_factory(revenue_fy=None)
    newer = snapshot_factory(revenue_fy=120)
    assert compute_revenue_fy_percent_change(older, newer) is None


def test_build_valuation_multiple_view_basic():
    now = datetime.now(timezone.utc)
    sid1, sid2 = uuid4(), uuid4()
    dms = DerivedMetricSet(
        derived_set_id=uuid4(),
        created_at=now,
        computation_engine="test",
        input_snapshots=[
            SnapshotRef(snapshot_id=sid1, as_of=now),
            SnapshotRef(snapshot_id=sid2, as_of=now),
        ],
        metrics=[
            DerivedMetric(
                metric_name="current_valuation_multiple",
                metric_type=MetricType.ratio,
                value=15.0,
                unit="x",
                formula="",
                inputs=[],
                computed_at=now,
            ),
            DerivedMetric(
                metric_name="reference_multiple_min",
                metric_type=MetricType.ratio,
                value=10.0,
                unit="x",
                formula="",
                inputs=[],
                computed_at=now,
            ),
            DerivedMetric(
                metric_name="reference_multiple_max",
                metric_type=MetricType.ratio,
                value=20.0,
                unit="x",
                formula="",
                inputs=[],
                computed_at=now,
            ),
            DerivedMetric(
                metric_name="reference_multiple_median",
                metric_type=MetricType.ratio,
                value=14.0,
                unit="x",
                formula="",
                inputs=[],
                computed_at=now,
            ),
        ],
    )
    view = build_valuation_multiple_view(
        analysis_view_id=uuid4(),
        created_at=now,
        created_by=CreatedBy.human,
        snapshot_ids=[uuid4()],
        derived_metric_sets=[dms],
        frame=AnalysisFrame(
            intent="Test valuation lens",
            assumptions=["Earnings normalized"],
            exclusions=["Forward estimates"],
            applicability_limits=["Not valid for banks"],
        ),
        confidence=AnalysisConfidence(
            confidence_level=ConfidenceLevel.medium,
            confidence_rationale="Test confidence",
        ),
    )
    assert view.view_type == "valuation_multiple"
    assert len(view.outputs.fields) == 5
