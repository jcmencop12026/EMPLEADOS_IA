"""Fixtures PostgreSQL para certificación (usa DATABASE_URL de QA-INFRA)."""
from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.seed import bootstrap


def _is_postgresql_url(url: str) -> bool:
    return url.startswith("postgresql") or url.startswith("postgres")


@pytest.fixture(scope="session")
def pg_engine():
    url = os.environ.get("DATABASE_URL", "")
    if not _is_postgresql_url(url):
        pytest.skip("DATABASE_URL no es PostgreSQL")
    connect_args = {}
    engine = create_engine(url, connect_args=connect_args)
    Base.metadata.create_all(bind=engine)
    db = sessionmaker(bind=engine)()
    try:
        bootstrap(db)
    finally:
        db.close()
    yield engine
    engine.dispose()


@pytest.fixture
def pg_session(pg_engine):
    Session = sessionmaker(bind=pg_engine)
    db = Session()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def pg_health(pg_engine):
    with pg_engine.connect() as conn:
        assert conn.execute(text("SELECT 1")).scalar_one() == 1
