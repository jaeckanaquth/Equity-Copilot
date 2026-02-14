from tests.fixtures.snapshot_factory import snapshot_factory  # noqa: F401
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.session import Base
from db.models.artifact import ArtifactORM
from db.models.lifecycle import BeliefLifecycleEventORM
from core.repositories.artifact_repository import ArtifactRepository
from core.repositories.lifecycle_repository import BeliefLifecycleRepository


@pytest.fixture(scope="function")
def db_session():

    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine)

    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()

    yield session

    session.close()


@pytest.fixture
def artifact_repo(db_session):
    return ArtifactRepository(db_session)


@pytest.fixture
def lifecycle_repo(db_session):
    return BeliefLifecycleRepository(db_session)
