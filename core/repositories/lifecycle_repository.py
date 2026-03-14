from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.models.lifecycle import BeliefLifecycleEventORM


class BeliefLifecycleRepository:

    def __init__(self, db: Session):
        self.db = db

    def append(self, event: BaseModel):
        belief_id = getattr(event, "belief_id", str(getattr(event, "reasoning_id", "")))
        created_at = getattr(event, "created_at", getattr(event, "occurred_at"))
        orm_obj = BeliefLifecycleEventORM(
            event_id=str(event.event_id),
            belief_id=str(belief_id),
            created_at=created_at,
            payload=event.model_dump(mode="json"),
        )

        self.db.add(orm_obj)
        self.db.commit()

    def list_for_belief(self, belief_id: str):
        return self.db.query(BeliefLifecycleEventORM)\
            .filter_by(belief_id=belief_id)\
            .order_by(BeliefLifecycleEventORM.created_at.asc())\
            .all()

    def list_decision_events(self, since=None, decision_type=None):
        """List all lifecycle events with event_kind=decision; filter in Python for SQLite compatibility."""
        rows = self.db.query(BeliefLifecycleEventORM).order_by(
            BeliefLifecycleEventORM.created_at.desc()
        ).all()
        out = []
        for r in rows:
            p = r.payload or {}
            if p.get("event_kind") != "decision":
                continue
            if since is not None and r.created_at < since:
                continue
            if decision_type is not None:
                dt = (p.get("decision") or {}).get("type")
                if dt != decision_type:
                    continue
            out.append(r)
        return out
