"""Tests CURSOR-805B — compatibilidad con política 805D (preservar legacy, BD nueva)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.migrations

from sqlalchemy import create_engine

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
TESTS_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from fixtures.legacy_db_fixture import build_programmatic_legacy_db  # noqa: E402
from scripts.db_startup import prepare_database  # noqa: E402
from scripts.schema_repair import HEAD_REVISION, get_alembic_revision, validate_schema_strict  # noqa: E402


def _url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def test_programmatic_legacy_preserved_and_fresh_db(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    db = data_dir / "enterprise_ai_os.db"
    build_programmatic_legacy_db(db)
    result = prepare_database(_url(db))
    assert result["scenario"] == "C"
    assert result["action"] == "legacy_preserved_and_recreated"
    assert result["alembic_revision"] == HEAD_REVISION
    engine = create_engine(_url(db), connect_args={"check_same_thread": False})
    assert validate_schema_strict(engine).is_valid
    assert list((data_dir / "LEGACY").glob("*_LEGACY_*.db"))


def test_alembic_chain_present_portable():
    backend_dir = Path(__file__).resolve().parents[1] / "backend"
    versions = list((backend_dir / "alembic" / "versions").glob("*.py"))
    assert any("4355c73adcb8" in v.name for v in versions)
    assert any("5b2eb2437398" in v.name for v in versions)
