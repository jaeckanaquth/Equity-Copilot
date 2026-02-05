from __future__ import annotations

from datetime import datetime
from typing import Dict
from uuid import UUID

from core.models.analysis_view import (
    AnalysisView,
    AnalysisViewInput,
    AnalysisFrame,
    AnalysisOutputs,
    AnalysisOutputField,
    AnalysisConfidence,
    CreatedBy,
)
from core.models.derived_metrics import DerivedMetricSet


REQUIRED_METRICS = {
    "current_multiple": "current_valuation_multiple",
    "reference_multiple_min": "reference_multiple_min",
    "reference_multiple_max": "reference_multiple_max",
    "reference_multiple_median": "reference_multiple_median",
}


def build_valuation_multiple_view(
    *,
    analysis_view_id: UUID,
    created_at: datetime,
    created_by: CreatedBy,
    snapshot_ids: list[UUID],
    derived_metric_sets: list[DerivedMetricSet],
    frame: AnalysisFrame,
    confidence: AnalysisConfidence,
) -> AnalysisView:
    if not snapshot_ids:
        raise ValueError("valuation_multiple view requires at least one snapshot_id")

    if not derived_metric_sets:
        raise ValueError("valuation_multiple view requires derived metric sets")

    # -------------------------
    # Collect metrics by name
    # -------------------------
    metric_index: Dict[str, float | None] = {}

    for dms in derived_metric_sets:
        for metric in dms.metrics:
            metric_index[metric.metric_name] = metric.value

    # -------------------------
    # Validate required metrics
    # -------------------------
    missing = [
        name for name in REQUIRED_METRICS.values()
        if name not in metric_index
    ]
    if missing:
        raise ValueError(
            f"Missing required derived metrics for valuation_multiple: {missing}"
        )

    # -------------------------
    # Build output fields
    # -------------------------
    outputs = []

    for field_name, metric_name in REQUIRED_METRICS.items():
        outputs.append(
            AnalysisOutputField(
                field_name=field_name,
                value=metric_index.get(metric_name),
                unit="x",
                derivation_note=f"Derived from metric '{metric_name}'",
            )
        )

    # -------------------------
    # Position within range
    # -------------------------
    current = metric_index.get("current_valuation_multiple")
    min_val = metric_index.get("reference_multiple_min")
    max_val = metric_index.get("reference_multiple_max")

    position_value = None
    position_note = (
        "Position not computed due to missing reference range or current value"
    )

    if (
        current is not None
        and min_val is not None
        and max_val is not None
        and max_val != min_val
    ):
        position_value = (current - min_val) / (max_val - min_val)
        position_note = (
            "Computed as (current - min) / (max - min) using reference multiples"
        )

    outputs.append(
        AnalysisOutputField(
            field_name="position_within_reference_range",
            value=position_value,
            unit="%",
            derivation_note=position_note,
        )
    )

    # -------------------------
    # Assemble AnalysisView
    # -------------------------
    return AnalysisView(
        analysis_view_id=analysis_view_id,
        created_at=created_at,
        created_by=created_by,
        view_type="valuation_multiple",
        inputs=AnalysisViewInput(
            snapshot_ids=snapshot_ids,
            derived_metric_set_ids=[dms.derived_set_id for dms in derived_metric_sets],
        ),
        frame=frame,
        outputs=AnalysisOutputs(fields=outputs),
        confidence=confidence,
    )
