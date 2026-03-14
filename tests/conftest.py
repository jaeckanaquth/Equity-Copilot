import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.repositories.artifact_repository import ArtifactRepository
from core.repositories.lifecycle_repository import BeliefLifecycleRepository
from db.models.proposal import ProposalORM  # noqa: F401
from db.session import Base
from tests.fixtures.snapshot_factory import snapshot_factory  # noqa: F401


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
