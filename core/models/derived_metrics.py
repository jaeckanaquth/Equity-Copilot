from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class MetricType(str, Enum):
    ratio = "ratio"
    delta = "delta"
    percent_change = "percent_change"
    absolute = "absolute"


class MetricInputRef(BaseModel):
    field_ref: str
    snapshot_id: UUID


class DerivedMetric(BaseModel):
    metric_name: str
    metric_type: MetricType

    value: Optional[float]
    unit: Optional[str]

    formula: str
    inputs: List[MetricInputRef]

    computed_at: datetime


class SnapshotRef(BaseModel):
    snapshot_id: UUID
    as_of: datetime


class DerivedMetricSet(BaseModel):
    derived_set_id: UUID
    schema_version: Literal["v1"] = "v1"

    created_at: datetime
    computation_engine: str

    input_snapshots: List[SnapshotRef]
    metrics: List[DerivedMetric]

    @field_validator("input_snapshots")
    @classmethod
    def must_have_at_least_two_snapshots(cls, v):
        if len(v) < 2:
            raise ValueError("DerivedMetricSet requires at least two snapshots")
        return v
