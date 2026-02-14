# db/init_db.py
from db.session import engine, Base
from db.models.artifact import ArtifactORM
from db.models.lifecycle import BeliefLifecycleEventORM

def init_db():
    Base.metadata.create_all(bind=engine)
