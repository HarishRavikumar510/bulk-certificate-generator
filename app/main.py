from contextlib import asynccontextmanager

from fastapi import FastAPI

from .database import Base, engine
from . import models  # noqa: F401  -- registers models with Base.metadata
from .routers import jobs


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Bulk Certificate Generator", lifespan=lifespan)
app.include_router(jobs.router, prefix="/api/certificate-jobs", tags=["certificate-jobs"])


@app.get("/health")
def health():
    return {"status": "ok"}