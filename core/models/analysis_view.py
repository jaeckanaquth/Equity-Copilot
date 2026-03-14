from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, field_validator

# -----------------------------
# Enums
# -----------------------------

class CreatedBy(str, Enum):
    human = "human"
    system = "system"


class ConfidenceLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


# -----------------------------
# Core Components
# -----------------------------

class AnalysisViewInput(BaseModel):
    snapshot_ids: list[UUID]
    derived_metric_set_ids: list[UUID]

    @field_validator("snapshot_ids")
    @classmethod
    def must_have_at_least_one_snapshot(cls, v):
        if not v:
            raise ValueError("AnalysisView must reference at least one snapshot")
        return v


class AnalysisFrame(BaseModel):
    intent: str

    assumptions: list[str]
    exclusions: list[str]
    applicability_limits: list[str]


class AnalysisOutputField(BaseModel):
    field_name: str
    value: float | str | None
    unit: str | None
    derivation_note: str


class AnalysisOutputs(BaseModel):
    fields: list[AnalysisOutputField]

    @field_validator("fields")
    @classmethod
    def must_have_at_least_one_field(cls, v):
        if not v:
            raise ValueError("AnalysisView must contain at least one output field")
        return v


class AnalysisConfidence(BaseModel):
    confidence_level: ConfidenceLevel
    confidence_rationale: str


# -----------------------------
# Root Object
# -----------------------------

class AnalysisView(BaseModel):
    analysis_view_id: UUID
    schema_version: Literal["v1"] = "v1"

    created_at: datetime
    created_by: CreatedBy

    view_type: str

    inputs: AnalysisViewInput
    frame: AnalysisFrame
    outputs: AnalysisOutputs
    confidence: AnalysisConfidence
