"""Decision API: record decision, list decisions, no belief mutation."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from api.routes.artifact_detail import get_db
from api.routes.reports import get_db as reports_get_db
from db.session import Base
from core.repositories.artifact_repository import ArtifactRepository
from core.repositories.lifecycle_repository import BeliefLifecycleRepository
from tests.fixtures.artifact_factory import reasoning_artifact_factory


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)

    db = TestingSessionLocal()
    artifact_repo = ArtifactRepository(db)
    belief = reasoning_artifact_factory(statement="Original belief text.", snapshot_ids=[])
    artifact_repo.save(belief)
    db.close()
    belief_id = str(belief.reasoning_id)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[reports_get_db] = override_get_db
    try:
        yield TestClient(app), belief_id, TestingSessionLocal
    finally:
        app.dependency_overrides.clear()


def test_record_decision_201(client):
    """POST /api/beliefs/{id}/decision returns 201 and appends lifecycle event."""
    test_client, belief_id, session_factory = client
    r = test_client.post(
        f"/api/beliefs/{belief_id}/decision",
        json={"type": "reinforced", "rationale": "Data supports thesis."},
    )
    assert r.status_code == 201
    db = session_factory()
    repo = BeliefLifecycleRepository(db)
    events = repo.list_for_belief(belief_id)
    db.close()
    decision_events = [e for e in events if (e.payload or {}).get("event_kind") == "decision"]
    assert len(decision_events) == 1
    assert decision_events[0].payload.get("decision", {}).get("type") == "reinforced"
    assert decision_events[0].payload.get("decision", {}).get("rationale") == "Data supports thesis."


def test_list_decisions(client):
    """GET /api/beliefs/{id}/decisions returns only decision events."""
    test_client, belief_id, session_factory = client
    test_client.post(
        f"/api/beliefs/{belief_id}/decision",
        json={"type": "slight_tension", "rationale": "Minor friction."},
    )
    r = test_client.get(f"/api/beliefs/{belief_id}/decisions")
    assert r.status_code == 200
    data = r.json()
    assert "decisions" in data
    assert len(data["decisions"]) == 1
    assert data["decisions"][0]["payload"].get("event_kind") == "decision"
    assert data["decisions"][0]["payload"].get("decision", {}).get("type") == "slight_tension"


def test_decision_does_not_mutate_belief_text(client):
    """Recording a decision must not change belief.claim.statement."""
    test_client, belief_id, session_factory = client
    original_statement = "Original belief text."
    test_client.post(
        f"/api/beliefs/{belief_id}/decision",
        json={
            "type": "strong_tension",
            "rationale": "Would be tempting to rewrite belief here.",
        },
    )
    db = session_factory()
    artifact_repo = ArtifactRepository(db)
    belief = artifact_repo.get(belief_id)
    db.close()
    assert belief is not None
    assert belief.claim.statement == original_statement


def test_record_decision_invalid_type_400(client):
    """POST with invalid decision type returns 400."""
    test_client, belief_id, _ = client
    r = test_client.post(
        f"/api/beliefs/{belief_id}/decision",
        json={"type": "invalid_type"},
    )
    assert r.status_code == 400
    assert "decision type must be one of" in (r.json().get("detail") or "")


def test_record_decision_404(client):
    """POST for non-existent belief returns 404."""
    test_client, _, _ = client
    r = test_client.post(
        "/api/beliefs/00000000-0000-0000-0000-000000000000/decision",
        json={"type": "reinforced"},
    )
    assert r.status_code == 404


def test_reports_beliefs_by_decision(client):
    """GET /api/reports/beliefs?decision=strong_tension returns beliefs with that current decision."""
    test_client, belief_id, _ = client
    test_client.post(
        f"/api/beliefs/{belief_id}/decision",
        json={"type": "strong_tension", "rationale": "Pressure."},
    )
    r = test_client.get("/api/reports/beliefs?decision=strong_tension")
    assert r.status_code == 200
    data = r.json()
    assert data["decision_filter"] == "strong_tension"
    assert len(data["beliefs"]) == 1
    assert data["beliefs"][0]["belief_id"] == belief_id
    assert data["beliefs"][0]["current_decision"]["type"] == "strong_tension"


def test_reports_decision_summary(client):
    """GET /api/reports/decision-summary returns counts by type (derived)."""
    test_client, belief_id, _ = client
    test_client.post(
        f"/api/beliefs/{belief_id}/decision",
        json={"type": "reinforced"},
    )
    r = test_client.get("/api/reports/decision-summary")
    assert r.status_code == 200
    data = r.json()
    assert "summary" in data
    assert data["summary"].get("reinforced") == 1


def test_reports_durability(client):
    """GET /api/reports/durability returns median/mean/distribution (derived)."""
    test_client, belief_id, _ = client
    test_client.post(
        f"/api/beliefs/{belief_id}/decision",
        json={"type": "slight_tension"},
    )
    r = test_client.get("/api/reports/durability")
    assert r.status_code == 200
    data = r.json()
    assert "median_days" in data
    assert "mean_days" in data
    assert "distribution_days" in data
    assert "per_belief" in data
    assert len(data["per_belief"]) == 1
    assert data["per_belief"][0]["belief_id"] == belief_id


def test_reports_tension_density(client):
    """GET /api/reports/tension-density returns pct under tension (derived)."""
    test_client, belief_id, _ = client
    test_client.post(
        f"/api/beliefs/{belief_id}/decision",
        json={"type": "strong_tension"},
    )
    r = test_client.get("/api/reports/tension-density")
    assert r.status_code == 200
    data = r.json()
    assert data["total_beliefs"] == 1
    assert data["under_tension"] == 1
    assert data["strong_tension_count"] == 1
    assert data["tension_density_pct"] == 100.0


def test_reports_trajectories(client):
    """GET /api/reports/trajectories returns per-belief trajectory tags (derived, not stored)."""
    test_client, belief_id, _ = client
    test_client.post(
        f"/api/beliefs/{belief_id}/decision",
        json={"type": "reinforced"},
    )
    r = test_client.get("/api/reports/trajectories")
    assert r.status_code == 200
    data = r.json()
    assert "trajectories" in data
    assert "counts_by_trajectory" in data
    assert len(data["trajectories"]) == 1
    assert data["trajectories"][0]["belief_id"] == belief_id
    assert data["trajectories"][0]["trajectory"] == "stable"
    assert data["trajectories"][0]["sequence"] == ["reinforced"]
