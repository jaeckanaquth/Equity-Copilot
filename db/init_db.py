# db/init_db.py
from db.session import Base, engine


def init_db():
    Base.metadata.create_all(bind=engine)
