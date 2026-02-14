"""Proposal engine idempotency and transition logic."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from db.models.artifact import ArtifactORM
from core.repositories.proposal_repository import ProposalRepository
from core.services.proposal_engine import ProposalEngine
from tests.fixtures.artifact_factory import reasoning_artifact_factory
from tests.fixtures.snapshot_factory import make_snapshot


def test_proposal_evaluate_idempotent(artifact_repo, lifecycle_repo, db_session):
    """Refresh 10 times — proposal count stays constant."""
    snapshot_id = uuid4()
    belief_stale = reasoning_artifact_factory(
        created_at=datetime.now(timezone.utc) - timedelta(days=30),
        snapshot_ids=[snapshot_id],
        statement="Stale belief for proposal test",
    )
    snapshot = make_snapshot(
        snapshot_id=snapshot_id,
        as_of=(datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
    )
    belief_ungrounded = reasoning_artifact_factory(
        snapshot_ids=[],
        statement="Ungrounded belief for proposal test",
    )

    artifact_repo.save(belief_stale)
    artifact_repo.save(snapshot)
    artifact_repo.save(belief_ungrounded)

    proposal_repo = ProposalRepository(db_session)
    engine = ProposalEngine(artifact_repo, lifecycle_repo, proposal_repo)

    engine.evaluate()
    count_after_first = proposal_repo.count_pending()
    assert count_after_first >= 2, "Expect at least 2 proposals (review_prompt + missing_grounding)"

    for _ in range(9):
        engine.evaluate()
        assert proposal_repo.count_pending() == count_after_first


def test_accept_reject_prevents_recreation(artifact_repo, lifecycle_repo, db_session):
    """Accept/reject resolves proposal; evaluate does not recreate it."""
    snapshot_id = uuid4()
    belief_stale = reasoning_artifact_factory(
        created_at=datetime.now(timezone.utc) - timedelta(days=30),
        snapshot_ids=[snapshot_id],
        statement="Stale belief",
    )
    snapshot = make_snapshot(
        snapshot_id=snapshot_id,
        as_of=(datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
    )
    belief_ungrounded = reasoning_artifact_factory(
        snapshot_ids=[],
        statement="Ungrounded belief",
    )
    artifact_repo.save(belief_stale)
    artifact_repo.save(snapshot)
    artifact_repo.save(belief_ungrounded)

    proposal_repo = ProposalRepository(db_session)
    engine = ProposalEngine(artifact_repo, lifecycle_repo, proposal_repo)
    engine.evaluate()

    active = proposal_repo.list_active()
    assert len(active) >= 2

    # Resolve one via accept, one via reject
    review_proposal = next((r for r in active if r.proposal_type == "review_prompt"), None)
    grounding_proposal = next((r for r in active if r.proposal_type == "missing_grounding"), None)
    assert review_proposal and grounding_proposal

    proposal_repo.resolve(review_proposal.proposal_id, "accepted")
    proposal_repo.resolve(grounding_proposal.proposal_id, "rejected")

    count_before = proposal_repo.count_pending()
    engine.evaluate()
    count_after = proposal_repo.count_pending()

    # No new proposals for same beliefs — accepted/rejected block recreation
    assert count_after == count_before


def test_condition_resolution_expires_accepted_then_regenerates(
    artifact_repo, lifecycle_repo, db_session,
):
    """Accept → condition resolves (add snapshot) → expire → condition reoccurs (remove snapshot) → regenerate."""
    snapshot_id = uuid4()
    # Snapshot as_of in the past so belief does NOT get review_prompt (no "newer" snapshots)
    snapshot = make_snapshot(
        snapshot_id=snapshot_id,
        as_of=(datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
    )
    belief = reasoning_artifact_factory(
        snapshot_ids=[],
        statement="Ungrounded belief for transition test",
    )

    artifact_repo.save(belief)
    artifact_repo.save(snapshot)

    proposal_repo = ProposalRepository(db_session)
    engine = ProposalEngine(artifact_repo, lifecycle_repo, proposal_repo)
    engine.evaluate()

    active = proposal_repo.list_active()
    grounding = next((r for r in active if r.proposal_type == "missing_grounding"), None)
    assert grounding is not None
    belief_id = grounding.payload["belief_id"]

    # User accepts (only missing_grounding exists, since snapshot is older than belief)
    proposal_repo.resolve(grounding.proposal_id, "accepted")
    assert proposal_repo.count_pending() == 0

    # Condition resolves: add snapshot to belief (artifacts are immutable; simulate via direct DB update for test)
    orm = db_session.query(ArtifactORM).filter_by(artifact_id=str(belief.reasoning_id)).first()
    assert orm is not None
    payload = dict(orm.payload)
    payload["references"] = {
        "snapshot_ids": [str(snapshot_id)],
        "derived_metric_set_ids": [],
        "analysis_view_ids": [],
    }
    orm.payload = payload
    db_session.commit()

    # Engine should expire the accepted proposal (condition no longer holds)
    engine.evaluate()

    non_expired = proposal_repo.list_non_expired_by_type("missing_grounding")
    assert all(
        row.payload.get("belief_id") != belief_id for row in non_expired
    ), "Accepted proposal should be expired when condition resolves"

    # Condition reoccurs: remove snapshot from belief
    orm.payload = belief.model_dump(mode="json")
    db_session.commit()

    # Engine should create new proposal
    engine.evaluate()
    active_after = proposal_repo.list_active()
    new_proposal = next(
        (r for r in active_after if r.payload.get("belief_id") == belief_id),
        None,
    )
    assert new_proposal is not None, "Should regenerate when condition reoccurs after expiry"


def test_invariant_at_most_one_non_expired_per_belief_type(
    artifact_repo, lifecycle_repo, db_session,
):
    """Invariant: at most 1 non-expired proposal per (belief_id, proposal_type)."""
    snapshot_id = uuid4()
    belief_stale = reasoning_artifact_factory(
        created_at=datetime.now(timezone.utc) - timedelta(days=30),
        snapshot_ids=[snapshot_id],
        statement="Stale belief",
    )
    snapshot = make_snapshot(
        snapshot_id=snapshot_id,
        as_of=(datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
    )
    belief_ungrounded = reasoning_artifact_factory(
        snapshot_ids=[],
        statement="Ungrounded belief",
    )
    artifact_repo.save(belief_stale)
    artifact_repo.save(snapshot)
    artifact_repo.save(belief_ungrounded)

    proposal_repo = ProposalRepository(db_session)
    engine = ProposalEngine(artifact_repo, lifecycle_repo, proposal_repo)

    for _ in range(5):
        engine.evaluate()
        counts: dict[tuple[str, str], int] = {}
        for ptype in ("missing_grounding", "review_prompt"):
            for row in proposal_repo.list_non_expired_by_type(ptype):
                key = (row.payload.get("belief_id"), ptype)
                counts[key] = counts.get(key, 0) + 1
        for (belief_id, ptype), n in counts.items():
            assert n <= 1, f"Invariant violated: {belief_id} {ptype} has {n} non-expired"
