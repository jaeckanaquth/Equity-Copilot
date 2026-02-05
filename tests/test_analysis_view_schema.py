from uuid import uuid4
from datetime import datetime, timezone

from core.models.analysis_view import (
    AnalysisView,
    AnalysisViewInput,
    AnalysisFrame,
    AnalysisOutputs,
    AnalysisOutputField,
    AnalysisConfidence,
    CreatedBy,
    ConfidenceLevel,
)


def test_analysis_view_minimal_valid():
    view = AnalysisView(
        analysis_view_id=uuid4(),
        created_at=datetime.now(timezone.utc),
        created_by=CreatedBy.human,
        view_type="valuation_multiple",
        inputs=AnalysisViewInput(
            snapshot_ids=[uuid4()],
            derived_metric_set_ids=[uuid4()],
        ),
        frame=AnalysisFrame(
            intent="Test valuation framing",
            assumptions=["Earnings are normalized"],
            exclusions=["Forward estimates"],
            applicability_limits=["Not valid for banks"],
        ),
        outputs=AnalysisOutputs(
            fields=[
                AnalysisOutputField(
                    field_name="current_multiple",
                    value=15.2,
                    unit="x",
                    derivation_note="Derived from snapshot price and earnings",
                )
            ]
        ),
        confidence=AnalysisConfidence(
            confidence_level=ConfidenceLevel.medium,
            confidence_rationale="Limited by accounting assumptions",
        ),
    )

    assert view.schema_version == "v1"
