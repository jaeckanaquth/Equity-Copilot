from sqlalchemy.orm import Session
from pydantic import BaseModel

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
            payload=event.model_dump(),
        )

        self.db.add(orm_obj)
        self.db.commit()

    def list_for_belief(self, belief_id: str):
        return self.db.query(BeliefLifecycleEventORM)\
            .filter_by(belief_id=belief_id)\
            .order_by(BeliefLifecycleEventORM.created_at.asc())\
            .all()
