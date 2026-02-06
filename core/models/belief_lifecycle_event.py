from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List
from uuid import UUID

from pydantic import BaseModel
from typing_extensions import Literal


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

    snapshot_ids: List[UUID] = []
    derived_metric_set_ids: List[UUID] = []
    analysis_view_ids: List[UUID] = []
    reasoning_artifact_ids: List[UUID] = []


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
