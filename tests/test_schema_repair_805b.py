"""Tests CURSOR-805B — compatibilidad con migración legacy (805C)."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
TESTS_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from fixtures.legacy_db_fixture import build_programmatic_legacy_db  # noqa: E402
from scripts.legacy_migration import migrate_legacy_database  # noqa: E402
from scripts.schema_repair import HEAD_REVISION, get_alembic_revision, validate_schema_strict  # noqa: E402


def _url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def test_programmatic_legacy_migration(tmp_path):
    db = tmp_path / "legacy.db"
    build_programmatic_legacy_db(db)
    result = migrate_legacy_database(_url(db), skip_backup=True, perform_swap=True)
    assert result["scenario"] == "D"
    assert result["alembic_revision"] == HEAD_REVISION
    engine = create_engine(_url(db), connect_args={"check_same_thread": False})
    assert validate_schema_strict(engine).is_valid


def test_alembic_chain_present_portable():
    backend_dir = Path(__file__).resolve().parents[1] / "backend"
    versions = list((backend_dir / "alembic" / "versions").glob("*.py"))
    assert any("4355c73adcb8" in v.name for v in versions)
    assert any("5b2eb2437398" in v.name for v in versions)
