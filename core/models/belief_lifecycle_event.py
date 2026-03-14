from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from core.models.reasoning_artifact import ConfidenceLevel

# -----------------------------
# Enums
# -----------------------------

class RecordedBy(str, Enum):
    human = "human"
    system = "system"


class BeliefState(str, Enum):
    active = "active"
    under_review = "under_review"
    superseded = "superseded"
    invalidated = "invalidated"
    retired = "retired"


class TriggerType(str, Enum):
    scheduled_review = "scheduled_review"
    data_update = "data_update"
    external_event = "external_event"
    manual = "manual"


# -----------------------------
# Components
# -----------------------------

class LifecycleTrigger(BaseModel):
    trigger_type: TriggerType
    description: str


class LifecycleJustification(BaseModel):
    summary: str

    snapshot_ids: list[UUID] = []
    derived_metric_set_ids: list[UUID] = []
    analysis_view_ids: list[UUID] = []
    reasoning_artifact_ids: list[UUID] = []


# -----------------------------
# Root Object
# -----------------------------

class BeliefLifecycleEvent(BaseModel):
    event_id: UUID
    schema_version: Literal["v1"] = "v1"

    occurred_at: datetime
    recorded_by: RecordedBy

    reasoning_id: UUID

    previous_state: BeliefState
    new_state: BeliefState

    trigger: LifecycleTrigger
    justification: LifecycleJustification


# -----------------------------
# Manual review outcome (human-judged only)
# -----------------------------

class ReviewOutcome(str, Enum):
    reinforced = "reinforced"
    slight_tension = "slight_tension"
    strong_tension = "strong_tension"
    inconclusive = "inconclusive"


class BeliefReviewOutcomeEvent(BaseModel):
    event_id: UUID
    schema_version: Literal["v1"] = "v1"
    occurred_at: datetime
    recorded_by: Literal["human"] = "human"
    reasoning_id: UUID
    event_kind: Literal["review_outcome"] = "review_outcome"
    trigger: Literal["manual_review"] = "manual_review"
    outcome: ReviewOutcome
    note: str | None = None


class GroundingUpdatedEvent(BaseModel):
    """Recorded when user Accepts a review_prompt and system attaches newest snapshot per ticker."""
    event_id: UUID
    schema_version: Literal["v1"] = "v1"
    occurred_at: datetime
    recorded_by: Literal["human"] = "human"
    reasoning_id: UUID
    event_kind: Literal["grounding_updated"] = "grounding_updated"
    trigger: Literal["review_prompt_accepted"] = "review_prompt_accepted"
    attached_snapshot_ids: list[str] = []


# -----------------------------
# Belief decision (structural, human-only, append-only)
# -----------------------------

DecisionType = Literal[
    "reinforced",
    "slight_tension",
    "strong_tension",
    "revised",
    "abandoned",
    "confidence_increased",
    "confidence_decreased",
    "deferred",
    "other",
]

DecisionTrigger = Literal["manual", "record_outcome", "cadence_mark", "proposal_accept"]


class DecisionFollowUp(BaseModel):
    action: Literal["none", "set_cadence", "archive", "reseed_beliefs", "notify"] | None = "none"
    params: dict | None = None


class DecisionPayload(BaseModel):
    type: DecisionType
    sub_type: str | None = None
    rationale: str | None = None
    linked_snapshot_ids: list[UUID] = []
    related_lifecycle_event_ids: list[UUID] = []
    follow_up: DecisionFollowUp | None = None
    metadata: dict | None = None


class BeliefDecisionEvent(BaseModel):
    """Append-only decision record. Stored as lifecycle event with event_kind='decision'."""
    event_id: UUID
    schema_version: Literal["v1"] = "v1"
    occurred_at: datetime
    recorded_by: Literal["human"] = "human"
    reasoning_id: UUID
    event_kind: Literal["decision"] = "decision"
    trigger: DecisionTrigger = "manual"
    decision: DecisionPayload


# -----------------------------
# Manual confidence (human-set only; no auto-scoring)
# -----------------------------


class BeliefConfidenceEvent(BaseModel):
    """Stored as lifecycle event with event_kind='confidence'. Latest defines current confidence."""
    event_id: UUID
    schema_version: Literal["v1"] = "v1"
    occurred_at: datetime
    recorded_by: Literal["human"] = "human"
    reasoning_id: UUID
    event_kind: Literal["confidence"] = "confidence"
    trigger: Literal["manual"] = "manual"
    confidence_level: ConfidenceLevel
    rationale: str | None = None
