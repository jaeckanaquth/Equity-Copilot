"""Factory for creating valid ReasoningArtifact instances in tests."""
from datetime import datetime, timezone
from uuid import uuid4

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


def reasoning_artifact_factory(
    *,
    reasoning_id=None,
    artifact_type=ArtifactType.thesis,
    created_at=None,
    snapshot_ids=None,
    statement="Test statement.",
    **overrides,
):
    """Create a valid ReasoningArtifact with sensible defaults."""
    rid = reasoning_id or uuid4()
    created = created_at or datetime.now(timezone.utc)
    snapshot_ids = snapshot_ids or []

    base = {
        "reasoning_id": rid,
        "created_at": created,
        "created_by": CreatedBy.human,
        "artifact_type": artifact_type,
        "subject": ReasoningSubject(
            entity_type=SubjectEntityType.company,
            entity_id="TICKER:TEST",
        ),
        "references": ReasoningReferences(
            snapshot_ids=snapshot_ids,
            derived_metric_set_ids=[],
            analysis_view_ids=[],
        ),
        "claim": ReasoningClaim(
            statement=statement,
            stance=Stance.neutral,
        ),
        "reasoning": ReasoningDetail(
            rationale=["Test rationale"],
            assumptions=[],
            counterpoints=[],
        ),
        "confidence": ReasoningConfidence(
            confidence_level=ConfidenceLevel.medium,
            confidence_rationale="Test",
        ),
        "review": ReasoningReview(
            review_by=None,
            review_trigger=None,
        ),
    }
    base.update(overrides)
    return ReasoningArtifact(**base)
