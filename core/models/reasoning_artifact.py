from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field
from typing_extensions import Literal


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
    snapshot_ids: List[UUID]
    derived_metric_set_ids: List[UUID]
    analysis_view_ids: List[UUID]


class ReasoningClaim(BaseModel):
    statement: str
    stance: Stance


class ReasoningDetail(BaseModel):
    rationale: List[str]
    assumptions: List[str]
    counterpoints: List[str]


class ReasoningConfidence(BaseModel):
    confidence_level: ConfidenceLevel
    confidence_rationale: str


class ReasoningReview(BaseModel):
    review_by: Optional[datetime]
    review_trigger: Optional[str]


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
