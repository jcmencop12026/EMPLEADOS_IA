import os
import tempfile
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_TEST_DB = tempfile.mktemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"
os.environ["JWT_SECRET"] = "test-secret-mvp-cert803"

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import bootstrap  # noqa: E402

engine = create_engine(os.environ["DATABASE_URL"], connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)
_bootstrap_db = TestingSessionLocal()
bootstrap(_bootstrap_db)
_bootstrap_db.close()


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def token(client: TestClient) -> str:
    res = client.post("/api/auth/login", json={"username": "admin", "password": "Admin2026*"})
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.fixture
def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def unique_username() -> str:
    return f"user-{uuid.uuid4().hex[:8]}"
