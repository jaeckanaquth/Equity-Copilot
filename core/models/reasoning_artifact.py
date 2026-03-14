from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

# -----------------------------
# Enums
# -----------------------------

class CreatedBy(str, Enum):
    human = "human"
    system = "system"


class ArtifactType(str, Enum):
    thesis = "thesis"
    risk = "risk"
    question = "question"


class Stance(str, Enum):
    bullish = "bullish"
    bearish = "bearish"
    neutral = "neutral"
    exploratory = "exploratory"


class ConfidenceLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class SubjectEntityType(str, Enum):
    company = "company"
    portfolio = "portfolio"
    position = "position"


# -----------------------------
# Components
# -----------------------------

class ReasoningSubject(BaseModel):
    entity_type: SubjectEntityType
    entity_id: str


class ReasoningReferences(BaseModel):
    snapshot_ids: list[UUID]
    derived_metric_set_ids: list[UUID]
    analysis_view_ids: list[UUID]


class ReasoningClaim(BaseModel):
    statement: str
    stance: Stance


class ReasoningDetail(BaseModel):
    rationale: list[str]
    assumptions: list[str]
    counterpoints: list[str]


class ReasoningConfidence(BaseModel):
    confidence_level: ConfidenceLevel
    confidence_rationale: str


class ReasoningReview(BaseModel):
    review_by: datetime | None
    review_trigger: str | None


# -----------------------------
# Root Object
# -----------------------------

class ReasoningArtifact(BaseModel):
    reasoning_id: UUID
    schema_version: Literal["v1"] = "v1"

    created_at: datetime
    created_by: CreatedBy

    artifact_type: ArtifactType

    subject: ReasoningSubject
    references: ReasoningReferences

    claim: ReasoningClaim
    reasoning: ReasoningDetail

    confidence: ReasoningConfidence
    review: ReasoningReview
