from contextlib import asynccontextmanager

from fastapi import FastAPI
from api.routes.review import router as review_router
from api.routes.weekly_review import router as weekly_review_router
from db.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Equity Copilot", lifespan=lifespan)

app.include_router(review_router, prefix="/review")
app.include_router(weekly_review_router)
