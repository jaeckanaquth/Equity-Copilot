from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from db.models.review_cadence import BeliefReviewCadenceORM


class CadenceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, belief_id: str) -> BeliefReviewCadenceORM | None:
        return self.db.query(BeliefReviewCadenceORM).filter_by(belief_id=belief_id).first()

    def set(self, belief_id: str, next_review_by: date, cadence_days: int | None = None) -> None:
        row = self.get(belief_id)
        now = datetime.now(UTC)
        if row:
            row.next_review_by = next_review_by
            row.cadence_days = cadence_days
            row.updated_at = now
        else:
            self.db.add(BeliefReviewCadenceORM(
                belief_id=belief_id,
                next_review_by=next_review_by,
                cadence_days=cadence_days,
                updated_at=now,
            ))
        self.db.commit()

    def delete(self, belief_id: str) -> bool:
        row = self.get(belief_id)
        if not row:
            return False
        self.db.delete(row)
        self.db.commit()
        return True

    def list_due(self, on_or_before: date):
        """Beliefs with next_review_by <= on_or_before, ordered by next_review_by asc."""
        return (
            self.db.query(BeliefReviewCadenceORM)
            .filter(BeliefReviewCadenceORM.next_review_by <= on_or_before)
            .order_by(BeliefReviewCadenceORM.next_review_by.asc())
            .all()
        )
