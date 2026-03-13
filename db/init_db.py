# db/init_db.py
from db.session import engine, Base
from db.models.artifact import ArtifactORM
from db.models.lifecycle import BeliefLifecycleEventORM
from db.models.proposal import ProposalORM
from db.models.question_answer import QuestionAnswerORM
from db.models.review_cadence import BeliefReviewCadenceORM
from db.models.observed_returns import ObservedReturnPeriodORM, BeliefReturnObservationORM


def init_db():
    Base.metadata.create_all(bind=engine)
