"""Phase 3.3 — LLM assistive endpoints. Optional, attributable, no mutation."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.session import SessionLocal
from core.services.llm_service import (
    LLMNotConfigured,
    LLMService,
    OLLAMA_MODEL,
    TEMPERATURE,
)
from core.repositories.artifact_repository import ArtifactRepository
from core.repositories.lifecycle_repository import BeliefLifecycleRepository
from core.repositories.proposal_repository import ProposalRepository
from core.models.reasoning_artifact import ArtifactType
from core.services.belief_analysis_service import BeliefAnalysisService

router = APIRouter()


def _metadata(model: str):
    return {
        "model": model,
        "temperature": TEMPERATURE,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_llm() -> LLMService:
    return LLMService()


# --- Option 1: Drafting ---


class DraftBeliefRequest(BaseModel):
    statement: str
    snapshot_summary: str = ""
    artifact_type: str = "thesis"


class DraftQuestionRequest(BaseModel):
    question: str
    snapshot_summary: str = ""
    prompt_type: str = "refine"  # "refine" | "sub_questions"


class TextResponse(BaseModel):
    text: str
    attribution: str = "LLM Draft Suggestion (Not Saved) — Edit and apply manually."
    model: str | None = None
    temperature: float | None = None
    generated_at: str | None = None


class AnalysisResponse(BaseModel):
    delta_summary: str
    potential_tensions: list[str]
    questions_raised: list[str]
    attribution: str = "LLM Structural Analysis — For Review Only"
    model: str | None = None
    temperature: float | None = None
    generated_at: str | None = None


def _snapshot_summary(artifact_repo, snapshot_ids: list) -> str:
    """Build plain-text summary of snapshots for LLM context."""
    parts = []
    for sid in snapshot_ids[:5]:
        try:
            snap = artifact_repo.get(str(sid))
            if snap and hasattr(snap, "company") and hasattr(snap, "financials"):
                c = snap.company
                f = snap.financials
                m = getattr(snap, "metadata", None)
                as_of = str(m.as_of)[:10] if m and hasattr(m, "as_of") else "N/A"
                parts.append(
                    f"{getattr(c, 'company_name', '') or 'Unknown'} ({getattr(c, 'ticker', '') or 'N/A'}): "
                    f"revenue={f.revenue_fy}, margin={f.operating_margin_fy}, as_of={as_of}"
                )
        except Exception:
            pass
    return "\n".join(parts) if parts else ""


@router.post("/api/llm/draft-belief", response_model=TextResponse)
def draft_belief(req: DraftBeliefRequest, llm: LLMService = Depends(get_llm)):
    """Draft refined belief. User applies manually."""
    if not llm.available:
        raise HTTPException(503, "LLM not configured. Run ollama serve and ensure a model is installed (see ollama list).")
    text = llm.draft_refined_belief(
        req.statement, req.artifact_type, req.snapshot_summary
    )
    return TextResponse(text=text)


class DraftBeliefFromIdRequest(BaseModel):
    belief_id: str


@router.post("/api/llm/draft-belief-from-id", response_model=TextResponse)
def draft_belief_from_id(
    req: DraftBeliefFromIdRequest,
    llm: LLMService = Depends(get_llm),
    db: Session = Depends(get_db),
):
    """Draft refined belief from artifact. Fetches snapshots for context."""
    if not llm.available:
        raise HTTPException(503, "LLM not configured. Run ollama serve and ensure a model is installed (see ollama list).")
    artifact_repo = ArtifactRepository(db)
    belief = artifact_repo.get(req.belief_id)
    if not belief or not hasattr(belief, "claim"):
        raise HTTPException(404, "Belief not found")
    if belief.artifact_type not in {ArtifactType.thesis, ArtifactType.risk}:
        raise HTTPException(400, "Not a belief")
    snapshot_summary = _snapshot_summary(artifact_repo, belief.references.snapshot_ids)
    text = llm.draft_refined_belief(
        belief.claim.statement,
        str(belief.artifact_type),
        snapshot_summary,
    )
    meta = _metadata(OLLAMA_MODEL)
    return TextResponse(
        text=text,
        attribution="LLM Draft Suggestion (Not Saved) — Edit and apply manually.",
        model=meta["model"],
        temperature=meta["temperature"],
        generated_at=meta["generated_at"],
    )


class DraftQuestionFromIdRequest(BaseModel):
    question_id: str
    prompt_type: str = "refine"  # "refine" | "sub_questions"


@router.post("/api/llm/draft-question-from-id", response_model=TextResponse)
def draft_question_from_id(
    req: DraftQuestionFromIdRequest,
    llm: LLMService = Depends(get_llm),
    db: Session = Depends(get_db),
):
    """Draft refined question or sub-questions from artifact."""
    if not llm.available:
        raise HTTPException(503, "LLM not configured. Run ollama serve and ensure a model is installed (see ollama list).")
    artifact_repo = ArtifactRepository(db)
    question = artifact_repo.get(req.question_id)
    if not question or not hasattr(question, "claim"):
        raise HTTPException(404, "Question not found")
    if question.artifact_type != ArtifactType.question:
        raise HTTPException(400, "Not a question")
    snapshot_summary = _snapshot_summary(artifact_repo, question.references.snapshot_ids)
    if req.prompt_type == "sub_questions":
        text = llm.suggest_sub_questions(question.claim.statement)
    else:
        text = llm.draft_refined_question(question.claim.statement, snapshot_summary)
    return TextResponse(text=text)


@router.post("/api/llm/draft-question", response_model=TextResponse)
def draft_question(req: DraftQuestionRequest, llm: LLMService = Depends(get_llm)):
    """Draft refined question or suggest sub-questions."""
    if not llm.available:
        raise HTTPException(503, "LLM not configured. Run ollama serve and ensure a model is installed (see ollama list).")
    if req.prompt_type == "sub_questions":
        text = llm.suggest_sub_questions(req.question)
    else:
        text = llm.draft_refined_question(req.question, req.snapshot_summary)
    return TextResponse(text=text)


class SummarizeSnapshotsRequest(BaseModel):
    snapshot_texts: list[str] = []


@router.post("/api/llm/summarize-snapshots", response_model=TextResponse)
def summarize_snapshots(
    req: SummarizeSnapshotsRequest,
    llm: LLMService = Depends(get_llm),
):
    """Summarize snapshot metrics."""
    if not llm or not llm.available:
        raise HTTPException(503, "LLM not configured. Run ollama serve and ensure a model is installed (see ollama list).")
    text = llm.summarize_snapshots(req.snapshot_texts)
    return TextResponse(text=text)


# --- Option 2: Structural explainer ---


class ExplainProposalRequest(BaseModel):
    proposal_type: str
    belief_text: str
    condition_state: dict | None = None


def _get_stale_context_for_belief(db: Session, belief_id: str) -> dict | None:
    """If belief has newer snapshots, return context for analysis. Else None."""
    artifact_repo = ArtifactRepository(db)
    lifecycle_repo = BeliefLifecycleRepository(db)
    analysis = BeliefAnalysisService(artifact_repo, lifecycle_repo)
    grouped = analysis.get_beliefs_needing_review()
    for items in grouped.values():
        for item in items:
            if item["belief_id"] == belief_id:
                return item
    return None


@router.post("/api/llm/analyze-belief/{belief_id}", response_model=AnalysisResponse)
def analyze_belief(
    belief_id: str,
    llm: LLMService = Depends(get_llm),
    db: Session = Depends(get_db),
):
    """Option 2 — Structural Change Analysis. Only when belief has newer snapshots. Structured output."""
    if not llm.available:
        raise HTTPException(503, "LLM not configured. Run ollama serve and ensure a model is installed (see ollama list).")
    try:
        stale = _get_stale_context_for_belief(db, belief_id)
        if not stale:
            raise HTTPException(
                400,
                "Belief has no newer snapshots. Analyze is only for beliefs needing review.",
            )
        artifact_repo = ArtifactRepository(db)
        lifecycle_repo = BeliefLifecycleRepository(db)
        belief = artifact_repo.get(belief_id)
        if not belief or not hasattr(belief, "claim"):
            raise HTTPException(404, "Belief not found")
        if belief.artifact_type not in {ArtifactType.thesis, ArtifactType.risk}:
            raise HTTPException(400, "Not a belief")

        previous_summary = _snapshot_summary(
            artifact_repo, list(belief.references.snapshot_ids)
        )
        newer_summary = _snapshot_summary(
            artifact_repo, [sid for sid in stale.get("newer_snapshot_ids", [])]
        )
        orm_events = lifecycle_repo.list_for_belief(belief_id)
        last_review = (
            orm_events[-1].created_at if orm_events else belief.created_at
        )
        last_review_iso = (
            last_review.isoformat() if hasattr(last_review, "isoformat") else str(last_review)
        )
        result = llm.analyze_belief_changes(
            belief.claim.statement,
            last_review_iso,
            previous_summary,
            newer_summary,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            500,
            detail=f"Analysis failed: {e!s}",
        ) from e

    meta = _metadata(OLLAMA_MODEL)
    tensions = result.get("potential_tensions") or []
    questions = result.get("questions_raised") or []
    return AnalysisResponse(
        delta_summary=str(result.get("delta_summary", "")),
        potential_tensions=[str(t) for t in tensions],
        questions_raised=[str(q) for q in questions],
        attribution="LLM Structural Analysis — For Review Only",
        model=meta["model"],
        temperature=meta["temperature"],
        generated_at=meta["generated_at"],
    )


@router.post("/api/llm/explain-proposal", response_model=TextResponse)
def explain_proposal(req: ExplainProposalRequest, llm: LLMService = Depends(get_llm)):
    """Explain why a structural proposal was triggered. Plain language. Separate from Draft/Analyze."""
    if not llm.available:
        raise HTTPException(503, "LLM not configured. Run ollama serve and ensure a model is installed (see ollama list).")
    text = llm.explain_proposal_trigger(
        req.proposal_type,
        req.belief_text,
        req.condition_state,
    )
    return TextResponse(
        text=text,
        attribution="LLM Structural Explanation — Why this proposal was triggered.",
    )
