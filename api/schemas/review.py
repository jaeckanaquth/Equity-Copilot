from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class OpenQuestionResponse(BaseModel):
    question_id: str
    question_text: str
    age_days: int
    snapshot_ids: List[str]
    company_tickers: List[str]


class StaleBeliefResponse(BaseModel):
    belief_id: str
    belief_text: str
    age_days_since_review: int
    newer_snapshot_ids: List[str]
    company_tickers: List[str]


class CoverageResponse(BaseModel):
    belief_id: str
    snapshot_ids: List[str]
    coverage_gap: bool


class BeliefOrphanItem(BaseModel):
    belief_id: str
    belief_text: str


class SnapshotOrphanItem(BaseModel):
    snapshot_id: str
    ticker: Optional[str]
    as_of: datetime
    age_days: int


class OrphanResponse(BaseModel):
    beliefs_without_snapshots: List[BeliefOrphanItem]
    snapshots_without_dependents: List[SnapshotOrphanItem]
