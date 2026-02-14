from pydantic import BaseModel
from datetime import datetime
from typing import List


class OpenQuestionResponse(BaseModel):
    question_id: str
    created_at: datetime
    age_days: int
    snapshot_ids: List[str]

class StaleBeliefResponse(BaseModel):
    belief_id: str
    last_review: datetime
    newer_snapshot_ids: List[str]

class CoverageResponse(BaseModel):
    belief_id: str
    snapshot_ids: List[str]
    coverage_gap: bool

class OrphanResponse(BaseModel):
    beliefs_without_snapshots: List[str]
    snapshots_without_dependents: List[str]
