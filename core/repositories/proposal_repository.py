from sqlalchemy.orm import Session

from db.models.proposal import ProposalORM

# Status states: pending | accepted | rejected | expired
# No deletion. Ever.


class ProposalRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, proposal: dict):
        orm = ProposalORM(**proposal)
        self.db.add(orm)
        self.db.commit()

    def count_pending(self) -> int:
        return self.db.query(ProposalORM).filter_by(status="pending").count()

    def list_active(self):
        """Return pending proposals only (display)."""
        return (
            self.db.query(ProposalORM)
            .filter(ProposalORM.status == "pending")
            .order_by(ProposalORM.created_at.desc())
            .all()
        )

    def exists_pending(self, belief_id: str, proposal_type: str) -> bool:
        """True if pending proposal exists for same belief_id and proposal_type."""
        for row in self.db.query(ProposalORM).filter_by(
            status="pending", proposal_type=proposal_type
        ).all():
            if row.payload.get("belief_id") == belief_id:
                return True
        return False

    def exists_for_belief(self, belief_id: str, proposal_type: str) -> bool:
        """True if any non-expired proposal exists (pending, accepted, or rejected).
        Engine must not regenerate when accepted/rejected — only when expired."""
        for row in self.db.query(ProposalORM).filter(
            ProposalORM.status.in_(("pending", "accepted", "rejected")),
            ProposalORM.proposal_type == proposal_type,
        ).all():
            if row.payload.get("belief_id") == belief_id:
                return True
        return False

    def update_status(self, proposal_id: str, new_status: str):
        """Update proposal status.
        Allowed: pending → accepted/rejected/expired; accepted/rejected → expired (when condition resolves)."""
        valid = ("accepted", "rejected", "expired")
        if new_status not in valid:
            raise ValueError(f"new_status must be one of {valid}")
        obj = self.db.query(ProposalORM).filter_by(proposal_id=proposal_id).first()
        if not obj:
            return
        if obj.status == "pending":
            obj.status = new_status
            self.db.commit()
        elif obj.status in ("accepted", "rejected") and new_status == "expired":
            obj.status = "expired"
            self.db.commit()

    def list_pending_by_type(self, proposal_type: str):
        """Return pending proposals of given type for resolved-condition checks."""
        return (
            self.db.query(ProposalORM)
            .filter_by(status="pending", proposal_type=proposal_type)
            .all()
        )

    def list_all(self):
        """All proposals, newest first. For audit view."""
        return (
            self.db.query(ProposalORM)
            .order_by(ProposalORM.created_at.desc())
            .all()
        )

    def list_non_expired_by_type(self, proposal_type: str):
        """Return all non-expired proposals of given type (pending, accepted, rejected).
        Used to expire when condition resolves — including user-acknowledged proposals."""
        return (
            self.db.query(ProposalORM)
            .filter(
                ProposalORM.proposal_type == proposal_type,
                ProposalORM.status.in_(("pending", "accepted", "rejected")),
            )
            .all()
        )

    def expire(self, proposal_id: str):
        """Mark proposal expired (automatic when condition resolves)."""
        self.update_status(proposal_id, "expired")

    def resolve(self, proposal_id: str, resolution: str):
        """Resolve via user action (accept or reject). Delegates to update_status."""
        if resolution not in ("accepted", "rejected"):
            raise ValueError("resolution must be 'accepted' or 'rejected'")
        self.update_status(proposal_id, resolution)

    def expire_older_than_days(self, days: int):
        from datetime import datetime, timedelta

        cutoff = datetime.utcnow() - timedelta(days=days)
        (
            self.db.query(ProposalORM)
            .filter(ProposalORM.status == "pending", ProposalORM.created_at < cutoff)
            .update({"status": "expired"}, synchronize_session=False)
        )
        self.db.commit()
