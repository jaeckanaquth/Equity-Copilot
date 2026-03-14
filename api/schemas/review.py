from datetime import datetime

from pydantic import BaseModel


class OpenQuestionResponse(BaseModel):
    question_id: str
    question_text: str
    age_days: int
    snapshot_ids: list[str]
    company_tickers: list[str]


class StaleBeliefResponse(BaseModel):
    belief_id: str
    belief_text: str
    age_days_since_review: int
    newer_snapshot_ids: list[str]
    company_tickers: list[str]


class CoverageResponse(BaseModel):
    belief_id: str
    snapshot_ids: list[str]
    coverage_gap: bool


class BeliefOrphanItem(BaseModel):
    belief_id: str
    belief_text: str


class SnapshotOrphanItem(BaseModel):
    snapshot_id: str
    ticker: str | None
    as_of: datetime
    age_days: int


class OrphanResponse(BaseModel):
    beliefs_without_snapshots: list[BeliefOrphanItem]
    snapshots_without_dependents: list[SnapshotOrphanItem]
