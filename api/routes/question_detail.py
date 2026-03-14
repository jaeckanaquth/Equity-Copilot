"""Question detail and answer routes."""
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.deps import get_db
from core.models.reasoning_artifact import ArtifactType, ReasoningArtifact
from core.repositories.artifact_repository import ArtifactRepository
from core.repositories.question_answer_repository import QuestionAnswerRepository
from core.templates import templates


class QuestionAnswerBody(BaseModel):
    answer: str


router = APIRouter()


@router.get("/questions/{question_id}", response_class=HTMLResponse)
def question_detail(
    question_id: str, request: Request, db: Session = Depends(get_db)
):
    artifact_repo = ArtifactRepository(db)
    answer_repo = QuestionAnswerRepository(db)
    question = artifact_repo.get(question_id)

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if not isinstance(question, ReasoningArtifact) or question.artifact_type != ArtifactType.question:
        raise HTTPException(status_code=404, detail="Question not found")

    answer = answer_repo.get(question_id)

    return templates.TemplateResponse(
        "question_detail.html",
        {"request": request, "question": question, "answer": answer},
    )


@router.post("/api/questions/{question_id}/answer", status_code=303)
def submit_question_answer(
    question_id: str,
    answer: str = Form(""),
    db: Session = Depends(get_db),
):
    """Record or update your answer (form field: answer). Question disappears from Open Questions once answered."""
    artifact_repo = ArtifactRepository(db)
    answer_repo = QuestionAnswerRepository(db)
    question = artifact_repo.get(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if not isinstance(question, ReasoningArtifact) or question.artifact_type != ArtifactType.question:
        raise HTTPException(status_code=404, detail="Question not found")
    text = (answer or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="answer cannot be empty")
    answer_repo.set(question_id, text[:10000])
    return RedirectResponse(url=f"/questions/{question_id}", status_code=303)
