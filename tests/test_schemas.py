"""Schema validation: lifecycle event, reasoning artifact, analysis view."""
from uuid import uuid4
from datetime import datetime, timezone

from core.models.belief_lifecycle_event import (
    BeliefLifecycleEvent,
    LifecycleTrigger,
    LifecycleJustification,
    RecordedBy,
    BeliefState,
    TriggerType,
    BeliefDecisionEvent,
    DecisionPayload,
    DecisionFollowUp,
)
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
from core.models.analysis_view import (
    AnalysisView,
    AnalysisViewInput,
    AnalysisFrame,
    AnalysisOutputs,
    AnalysisOutputField,
    AnalysisConfidence,
    CreatedBy as ViewCreatedBy,
    ConfidenceLevel as ViewConfidenceLevel,
)


def test_belief_lifecycle_event_valid():
    event = BeliefLifecycleEvent(
        event_id=uuid4(),
        occurred_at=datetime.now(timezone.utc),
        recorded_by=RecordedBy.human,
        reasoning_id=uuid4(),
        previous_state=BeliefState.active,
        new_state=BeliefState.under_review,
        trigger=LifecycleTrigger(
            trigger_type=TriggerType.scheduled_review,
            description="Quarterly review",
        ),
        justification=LifecycleJustification(
            summary="Scheduled reassessment of thesis",
            snapshot_ids=[uuid4()],
        ),
    )
    assert event.schema_version == "v1"


def test_belief_decision_event_valid():
    """Decision event has correct shape and serializes for lifecycle storage."""
    event = BeliefDecisionEvent(
        event_id=uuid4(),
        schema_version="v1",
        occurred_at=datetime.now(timezone.utc),
        recorded_by="human",
        reasoning_id=uuid4(),
        event_kind="decision",
        trigger="manual",
        decision=DecisionPayload(
            type="reinforced",
            rationale="Data aligns with thesis.",
            linked_snapshot_ids=[],
        ),
    )
    assert event.schema_version == "v1"
    assert event.event_kind == "decision"
    assert event.decision.type == "reinforced"
    payload = event.model_dump(mode="json")
    assert payload["event_kind"] == "decision"
    assert "decision" in payload
    assert payload["decision"]["type"] == "reinforced"


def test_decision_payload_all_types():
    """All decision types are valid."""
    for dtype in ("reinforced", "slight_tension", "strong_tension", "revised", "abandoned",
                  "confidence_increased", "confidence_decreased", "deferred", "other"):
        payload = DecisionPayload(type=dtype, linked_snapshot_ids=[])
        assert payload.type == dtype


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


def test_analysis_view_minimal_valid():
    view = AnalysisView(
        analysis_view_id=uuid4(),
        created_at=datetime.now(timezone.utc),
        created_by=ViewCreatedBy.human,
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
            confidence_level=ViewConfidenceLevel.medium,
            confidence_rationale="Limited by accounting assumptions",
        ),
    )
    assert view.schema_version == "v1"
