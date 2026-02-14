import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from api.routes.review import get_db
from db.session import Base
from db.models.artifact import ArtifactORM
from db.models.lifecycle import BeliefLifecycleEventORM
from core.repositories.artifact_repository import ArtifactRepository
from tests.fixtures.artifact_factory import reasoning_artifact_factory


@pytest.fixture
def client():
    # StaticPool + check_same_thread: single in-memory DB shared across threads
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)

    # Seed one belief so coverage endpoint can be tested
    db = TestingSessionLocal()
    artifact_repo = ArtifactRepository(db)
    belief = reasoning_artifact_factory(snapshot_ids=[])
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
    try:
        yield TestClient(app), engine, belief_id
    finally:
        app.dependency_overrides.clear()


def test_review_endpoints_are_read_only(client):
    client, engine, belief_id = client
    writes_detected = []

    @event.listens_for(engine, "before_cursor_execute")
    def detect_writes(conn, cursor, statement, parameters, context, executemany):
        normalized = statement.strip().upper()
        if normalized.startswith(("INSERT", "UPDATE", "DELETE")):
            writes_detected.append(statement)

    # Call all review endpoints
    client.get("/review/questions")
    client.get("/review/beliefs/stale")
    client.get("/review/orphans")
    client.get(f"/review/beliefs/{belief_id}/coverage")

    assert len(writes_detected) == 0, f"Writes detected: {writes_detected}"
