import os
import tempfile
import threading
import time
import uuid
from pathlib import Path
from urllib.parse import urlparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

if "DATABASE_URL" not in os.environ:
    _TEST_DB = tempfile.mktemp(suffix=".db")
    os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"
if "JWT_SECRET" not in os.environ:
    os.environ.setdefault("JWT_SECRET", "test-secret-mvp-cert803")

from app import automation_models  # noqa: F401, E402
from app import finops_models  # noqa: F401, E402
from app import knowledge_models  # noqa: F401, E402
from app import models  # noqa: F401, E402
from app import notifications  # noqa: F401, E402
from app import orchestration_models  # noqa: F401, E402
from app import salud_models  # noqa: F401, E402
from app import experience_models  # noqa: F401, E402
from app import opportunity_models  # noqa: F401, E402
from app import llm_models  # noqa: F401, E402
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import bootstrap  # noqa: E402
from app.services import automation_scheduler  # noqa: E402
from app.services import proactive_scheduler  # noqa: E402

_db_url = os.environ["DATABASE_URL"]
_connect_args = {"check_same_thread": False} if _db_url.startswith("sqlite") else {}
_pg_reset_lock = threading.Lock()


def _is_postgresql_url(url: str) -> bool:
    return url.startswith("postgresql") or url.startswith("postgres")


def _postgresql_database_name(url: str) -> str:
    parsed = urlparse(url)
    name = (parsed.path or "").lstrip("/")
    if not name:
        raise ValueError(f"No se pudo resolver nombre de BD en DATABASE_URL: {url!r}")
    return name


def _is_safe_test_database(url: str) -> bool:
    """Solo permite reset destructivo en bases claramente de prueba."""
    if not _is_postgresql_url(url):
        return False
    db_name = _postgresql_database_name(url).lower()
    blocked = {"postgres", "template0", "template1", "production", "prod"}
    if db_name in blocked:
        return False
    if "prod" in db_name and "test" not in db_name:
        return False
    return db_name.endswith("_test") or db_name.endswith("test") or "_test" in db_name


def _ensure_postgresql_schema() -> None:
    from alembic import command
    from alembic.config import Config

    from scripts.migration_control import assert_single_head

    cfg = Config(str(Path(__file__).resolve().parents[1] / "backend" / "alembic.ini"))
    command.upgrade(cfg, "head")
    head = assert_single_head()
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    if version != head:
        raise RuntimeError(
            f"PostgreSQL test DB desincronizada: alembic_version={version!r}, head esperado={head!r}"
        )


def _reset_postgresql_test_database() -> None:
    if not _is_safe_test_database(_db_url):
        raise RuntimeError(
            "Refusing PostgreSQL test reset: DATABASE_URL no apunta a una BD de prueba segura. "
            f"BD detectada: {_postgresql_database_name(_db_url)!r}"
        )
    last_error: Exception | None = None
    with _pg_reset_lock:
        for attempt in range(5):
            try:
                automation_scheduler.stop_scheduler()
                proactive_scheduler.stop_proactive_scheduler()
                engine.dispose()
                with engine.begin() as conn:
                    conn.execute(text("SELECT pg_advisory_lock(8421030)"))
                    try:
                        tables = conn.execute(
                            text(
                                "SELECT tablename FROM pg_tables "
                                "WHERE schemaname = 'public' AND tablename NOT LIKE 'alembic_%'"
                            )
                        ).scalars().all()
                        if tables:
                            quoted = ", ".join(f'"{table}"' for table in tables)
                            conn.execute(text(f"TRUNCATE {quoted} RESTART IDENTITY CASCADE"))
                    finally:
                        conn.execute(text("SELECT pg_advisory_unlock(8421030)"))
                db = TestingSessionLocal()
                try:
                    bootstrap(db)
                finally:
                    db.close()
                return
            except OperationalError as exc:
                last_error = exc
                if "deadlock" not in str(exc).lower():
                    raise
                time.sleep(0.05 * (attempt + 1))
    if last_error is not None:
        raise last_error


engine = create_engine(_db_url, connect_args=_connect_args)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

if _is_postgresql_url(_db_url):
    _ensure_postgresql_schema()
else:
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
automation_scheduler.SessionLocal = TestingSessionLocal


@pytest.fixture(autouse=True)
def _postgresql_test_isolation():
    """Resetea PostgreSQL compartido antes de cada test para evitar contaminación entre ejecuciones."""
    if _is_postgresql_url(_db_url):
        _reset_postgresql_test_database()
    yield
    if _is_postgresql_url(_db_url):
        automation_scheduler.stop_scheduler()
        proactive_scheduler.stop_proactive_scheduler()


@pytest.fixture(scope="session", autouse=True)
def _postgresql_session_cleanup():
    yield
    if _is_postgresql_url(_db_url):
        engine.dispose()


def _client_context():
    with TestClient(app) as test_client:
        automation_scheduler.stop_scheduler()
        proactive_scheduler.stop_proactive_scheduler()
        yield test_client
        proactive_scheduler.stop_proactive_scheduler()
        automation_scheduler.stop_scheduler()


if _is_postgresql_url(_db_url):

    @pytest.fixture(scope="function")
    def client(_postgresql_test_isolation) -> TestClient:
        yield from _client_context()

else:

    @pytest.fixture(scope="session")
    def client() -> TestClient:
        yield from _client_context()


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
