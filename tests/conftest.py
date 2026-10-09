"""Shared test fixtures.

Strategy:
- A separate IN-MEMORY SQLite database (never touches app.db)
- StaticPool: all threads share the one in-memory DB (TestClient runs the
  app in a worker thread, so this is required)
- get_db dependency overridden -> test sessions
- process_job's session factory patched -> background tasks also use the
  test DB (they run outside the request cycle)
- PDFs redirected to a throwaway pytest tmp folder
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.database import Base, get_db
from app.main import app

TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=TEST_ENGINE, autoflush=False, expire_on_commit=False
)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture()
def pdf_out_dir(tmp_path, monkeypatch):
    """Redirect generated PDFs to a temp folder for the duration of a test."""
    monkeypatch.setattr(settings, "CERTIFICATE_OUTPUT_DIR", tmp_path)
    return tmp_path


@pytest.fixture()
def client(pdf_out_dir, monkeypatch):
    """API test client with a FRESH database and patched background sessions."""
    Base.metadata.drop_all(bind=TEST_ENGINE)
    Base.metadata.create_all(bind=TEST_ENGINE)

    monkeypatch.setattr(
        "app.services.job_processor.get_session_factory",
        lambda: TestingSessionLocal,
    )

    return TestClient(app)


@pytest.fixture()
def payload():
    """A fresh valid request body for every test."""
    return {
        "event_name": "AWS Cloud Practitioner Workshop",
        "event_date": "2025-01-15",
        "recipients": [
            {"name": "Harish Ravikumar", "email": "harish@example.com"},
            {"name": "Priya Sharma", "email": "priya@example.com"},
        ],
    }