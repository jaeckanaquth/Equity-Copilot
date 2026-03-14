from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from db.models.question_answer import QuestionAnswerORM


class QuestionAnswerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, question_id: str) -> dict | None:
        row = self.db.query(QuestionAnswerORM).filter_by(question_id=question_id).first()
        if not row:
            return None
        return {
            "answer_text": row.answer_text,
            "answered_at": row.answered_at,
        }

    def set(self, question_id: str, answer_text: str) -> None:
        now = datetime.now(UTC)
        row = self.db.query(QuestionAnswerORM).filter_by(question_id=question_id).first()
        if row:
            row.answer_text = answer_text
            row.answered_at = now
        else:
            self.db.add(QuestionAnswerORM(
                question_id=question_id,
                answer_text=answer_text,
                answered_at=now,
            ))
        self.db.commit()

    def has_answer(self, question_id: str) -> bool:
        return self.db.query(QuestionAnswerORM).filter_by(question_id=question_id).first() is not None

    def answered_question_ids(self) -> set[str]:
        rows = self.db.query(QuestionAnswerORM.question_id).all()
        return {r[0] for r in rows}
