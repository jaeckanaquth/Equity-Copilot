from sqlalchemy import Column, String, DateTime, Text
from db.session import Base
from datetime import datetime, timezone


def _utc_now():
    return datetime.now(timezone.utc)


class QuestionAnswerORM(Base):
    """One answer per question. question_id references artifacts.artifact_id."""
    __tablename__ = "question_answers"

    question_id = Column(String, primary_key=True, index=True)
    answer_text = Column(Text, nullable=False)
    answered_at = Column(DateTime, nullable=False, default=_utc_now)
