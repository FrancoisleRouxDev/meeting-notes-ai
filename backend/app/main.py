from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401  (registers the tables with SQLAlchemy)
from app.core.config import settings
from app.db import Base, engine
from app.routers import auth

# Temporary shortcut to create tables. Alembic migrations replace this before submission.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Meeting Notes AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,  # the browser needs this to send the session cookie
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)


@app.get("/health")
def health():
    return {"status": "ok"}
