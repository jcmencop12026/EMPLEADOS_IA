"""Tests CURSOR-805E — WinError 32, idempotencia preservación, lifecycle SQLite."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
TESTS_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from fixtures.legacy_db_fixture import build_programmatic_legacy_db  # noqa: E402
from scripts.db_startup import create_fresh_database, prepare_database  # noqa: E402
from scripts.legacy_preservation import find_preserved_legacy_by_sha256, preserve_legacy_database  # noqa: E402
from scripts.schema_repair import HEAD_REVISION, get_alembic_revision, validate_schema_strict  # noqa: E402
from scripts.sqlite_lifecycle import (  # noqa: E402
    release_all_sqlite_handles,
    safe_unlink_sqlite,
    sqlite_engine,
    verify_sqlite_closed,
)


def _url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def test_sqlite_replace_after_engine_dispose(tmp_path):
    """Demuestra replace seguro: crear → validar → dispose → reemplazar → reabrir."""
    active = tmp_path / "active.db"
    create_fresh_database(active)
    url = _url(active)

    with sqlite_engine(active) as engine:
        assert validate_schema_strict(engine).is_valid
        assert get_alembic_revision(active) == HEAD_REVISION

    release_all_sqlite_handles(url)
    safe_unlink_sqlite(active, url)
    create_fresh_database(active)

    verify_sqlite_closed(active)
    with sqlite_engine(active) as engine:
        assert validate_schema_strict(engine).is_valid
        assert get_alembic_revision(active) == HEAD_REVISION


def test_prepare_with_app_database_engine_open(tmp_path):
    """Simula WinError 32: engine global abierto sobre legacy antes del replace."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    db = data_dir / "enterprise_ai_os.db"
    build_programmatic_legacy_db(db, extended=True)
    url = _url(db)

    from app import database as app_database

    _ = app_database.engine.connect().close()

    result = prepare_database(url)
    assert result["action"] == "legacy_preserved_and_recreated"
    assert db.exists()
    assert get_alembic_revision(db) == HEAD_REVISION


def test_preservation_idempotent_same_sha256(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    db = data_dir / "legacy.db"
    build_programmatic_legacy_db(db, extended=True)

    first = preserve_legacy_database(db, data_dir=data_dir)
    second = preserve_legacy_database(db, data_dir=data_dir)

    assert first.sha256 == second.sha256
    assert first.legacy_path == second.legacy_path
    legacy_files = list((data_dir / "LEGACY").glob("*_LEGACY_*.db"))
    assert len(legacy_files) == 1
    assert find_preserved_legacy_by_sha256(data_dir, first.sha256) is not None


def test_scenario_c_idempotent_preservation_on_retry(tmp_path):
    """Si LEGACY ya tiene el SHA256, no duplica copia al reintentar prepare."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    db = data_dir / "enterprise_ai_os.db"
    build_programmatic_legacy_db(db, extended=True)

    first = prepare_database(_url(db))
    assert first["action"] == "legacy_preserved_and_recreated"
    legacy_files = list((data_dir / "LEGACY").glob("*_LEGACY_*.db"))
    legacy_count_1 = len(legacy_files)
    legacy_copy = legacy_files[0]

    shutil.copy2(legacy_copy, db)

    second = prepare_database(_url(db))
    assert second["action"] == "legacy_preserved_and_recreated"
    legacy_count_2 = len(list((data_dir / "LEGACY").glob("*_LEGACY_*.db")))
    assert legacy_count_2 == legacy_count_1
