from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.routes.artifact_detail import router as artifact_detail_router
from api.routes.artifacts import router as artifacts_router
from api.routes.llm import router as llm_router
from api.routes.proposals import router as proposals_router
from api.routes.reports import router as reports_router
from api.routes.review import router as review_router
from api.routes.weekly_review import router as weekly_review_router
from core.exceptions import ArtifactConflictError
from core.services.llm_service import LLMNotConfigured
from db.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Equity Copilot", lifespan=lifespan)


@app.exception_handler(LLMNotConfigured)
async def llm_not_configured_handler(request: Request, exc: LLMNotConfigured):
    return JSONResponse(
        status_code=503,
        content={"detail": "LLM not configured. Run ollama serve and ensure a model is installed (see ollama list)."},
    )


@app.exception_handler(ArtifactConflictError)
async def artifact_conflict_handler(request: Request, exc: ArtifactConflictError):
    return JSONResponse(status_code=409, content={"detail": exc.message})


app.include_router(review_router, prefix="/review")
app.include_router(weekly_review_router)
app.include_router(proposals_router)
app.include_router(llm_router)
app.include_router(artifacts_router)  # before detail so /beliefs/new and /questions/new match first
app.include_router(artifact_detail_router)
app.include_router(reports_router)
