"""Aggregates belief and question detail routes. get_db is re-exported for dependency injection and tests."""
from fastapi import APIRouter

from api.deps import get_db
from api.routes.belief_detail import router as belief_router
from api.routes.question_detail import router as question_router

router = APIRouter()
router.include_router(belief_router)
router.include_router(question_router)

__all__ = ["router", "get_db"]
