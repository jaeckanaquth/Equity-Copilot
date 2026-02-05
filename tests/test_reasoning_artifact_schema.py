from uuid import uuid4
from datetime import datetime, timezone

from core.models.reasoning_artifact import (
    ReasoningArtifact,
    ReasoningSubject,
    ReasoningReferences,
    ReasoningClaim,
    ReasoningDetail,
    ReasoningConfidence,
    ReasoningReview,
    CreatedBy,
    ArtifactType,
    Stance,
    ConfidenceLevel,
    SubjectEntityType,
)


def test_reasoning_artifact_thesis_valid():
    artifact = ReasoningArtifact(
        reasoning_id=uuid4(),
        created_at=datetime.now(timezone.utc),
        created_by=CreatedBy.human,
        artifact_type=ArtifactType.thesis,
        subject=ReasoningSubject(
            entity_type=SubjectEntityType.company,
            entity_id="TICKER:ABC",
        ),
        references=ReasoningReferences(
            snapshot_ids=[uuid4()],
            derived_metric_set_ids=[uuid4()],
            analysis_view_ids=[uuid4()],
        ),
        claim=ReasoningClaim(
            statement="Valuation appears optimistic given growth volatility.",
            stance=Stance.bearish,
        ),
        reasoning=ReasoningDetail(
            rationale=["Growth dispersion is high."],
            assumptions=["Past growth reflects operating volatility."],
            counterpoints=["Volatility may be temporary."],
        ),
        confidence=ReasoningConfidence(
            confidence_level=ConfidenceLevel.medium,
            confidence_rationale="Limited forward visibility.",
        ),
        review=ReasoningReview(
            review_by=None,
            review_trigger="Next earnings release",
        ),
    )

    assert artifact.schema_version == "v1"
