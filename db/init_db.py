# db/init_db.py
from db.session import engine, Base
from db.models.artifact import ArtifactORM
from db.models.lifecycle import BeliefLifecycleEventORM
from db.models.proposal import ProposalORM


def init_db():
    Base.metadata.create_all(bind=engine)
