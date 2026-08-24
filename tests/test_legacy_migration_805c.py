"""Tests CURSOR-805C — migración legacy definitiva + escenarios DB."""
from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import pytest
from sqlalchemy import create_engine

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
PROJECT_ROOT = BACKEND_DIR.parent
TESTS_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from fixtures.legacy_db_fixture import build_programmatic_legacy_db  # noqa: E402
from scripts.legacy_migration import (  # noqa: E402
    LegacyMigrationError,
    atomic_swap,
    create_fresh_database,
    detect_db_scenario,
    inventory_legacy_db,
    migrate_legacy_database,
)
from scripts.schema_repair import (  # noqa: E402
    HEAD_REVISION,
    SchemaRepairError,
    create_verified_backup,
    get_alembic_revision,
    sync_alembic_revision,
    validate_schema_strict,
    verify_backup_file,
)
from scripts.service_manager import (  # noqa: E402
    _is_empleados_ia_process,
    resolve_npm,
    save_pid_registry,
    stop_registered_services,
)


def _url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def test_scenario_a_no_db(tmp_path):
    db = tmp_path / "new.db"
    assert detect_db_scenario(db) == "A"
    result = migrate_legacy_database(_url(db), skip_backup=True)
    assert result["scenario"] == "A"
    assert db.exists()
    assert validate_schema_strict(create_engine(_url(db), connect_args={"check_same_thread": False})).is_valid


def test_scenario_b_empty_db(tmp_path):
    db = tmp_path / "empty.db"
    db.write_bytes(b"")
    assert detect_db_scenario(db) == "B"
    result = migrate_legacy_database(_url(db), skip_backup=True)
    assert result["scenario"] == "B"
    assert validate_schema_strict(create_engine(_url(db), connect_args={"check_same_thread": False})).is_valid


def test_scenario_c_compatible_db(tmp_path):
    db = tmp_path / "compatible.db"
    create_fresh_database(db)
    assert detect_db_scenario(db) == "C"
    result = migrate_legacy_database(_url(db), skip_backup=True)
    assert result["scenario"] == "C"


def test_scenario_d_legacy_migrable(tmp_path):
    db = tmp_path / "legacy.db"
    expected = build_programmatic_legacy_db(db)
    assert detect_db_scenario(db) == "D"
    result = migrate_legacy_database(_url(db), skip_backup=True, perform_swap=False)
    assert result["scenario"] == "D"
    migrating = tmp_path / "legacy_MIGRATING.db"
    assert migrating.exists()
    inv = inventory_legacy_db(migrating)
    assert inv["organizations"] == expected["organizations"]
    assert inv["users"] == expected["users"]
    assert inv["capabilities"] == expected["capabilities"]


def test_scenario_e_incompatible(tmp_path):
    db = tmp_path / "bad.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE unknown_legacy (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()
    assert detect_db_scenario(db) == "E"
    with pytest.raises(LegacyMigrationError):
        migrate_legacy_database(_url(db), skip_backup=True)


def test_missing_foreign_key_rejected_for_stamp(tmp_path):
    db = tmp_path / "no_fk.db"
    conn = sqlite3.connect(db)
    conn.executescript(
        """
        CREATE TABLE organizations (id VARCHAR(36) PRIMARY KEY, name VARCHAR(200) NOT NULL, created_at DATETIME NOT NULL);
        CREATE TABLE users (
            id VARCHAR(36) PRIMARY KEY,
            organization_id VARCHAR(36) NOT NULL,
            username VARCHAR(80) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(40) NOT NULL,
            is_active BOOLEAN NOT NULL,
            created_at DATETIME NOT NULL
        );
        """
    )
    conn.close()
    engine = create_engine(_url(db), connect_args={"check_same_thread": False})
    validation = validate_schema_strict(engine)
    assert not validation.is_valid
    assert any(i.category == "foreign_key" for i in validation.issues)
    with pytest.raises(SchemaRepairError):
        sync_alembic_revision(engine, _url(db))


def test_migration_preserves_counts_and_backend_health(tmp_path):
    db = tmp_path / "legacy.db"
    expected = build_programmatic_legacy_db(db)
    migrate_legacy_database(_url(db), skip_backup=True, perform_swap=True)
    inv = inventory_legacy_db(db)
    assert inv["organizations"] == expected["organizations"]
    assert inv["users"] == expected["users"]
    assert inv["capabilities"] == expected["capabilities"]
    assert get_alembic_revision(db) == HEAD_REVISION

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "18011"],
        cwd=str(BACKEND_DIR),
        env={**os.environ, "DATABASE_URL": _url(db)},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        ok = False
        for _ in range(30):
            try:
                with urllib.request.urlopen("http://127.0.0.1:18011/health", timeout=2) as resp:
                    ok = resp.status == 200
                    break
            except Exception:
                time.sleep(1)
        assert ok
    finally:
        proc.terminate()
        proc.wait(timeout=10)


def test_migrated_db_bootstrap_admin_login(tmp_path):
    """Tras migración, bootstrap crea admin y login funciona (no token legacy en navegador)."""
    import json

    db = tmp_path / "legacy.db"
    build_programmatic_legacy_db(db)
    migrate_legacy_database(_url(db), skip_backup=True, perform_swap=True)

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "18013"],
        cwd=str(BACKEND_DIR),
        env={**os.environ, "DATABASE_URL": _url(db)},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(30):
            try:
                with urllib.request.urlopen("http://127.0.0.1:18013/health", timeout=2):
                    break
            except Exception:
                time.sleep(1)
        else:
            pytest.fail("Backend no arrancó")

        login_req = urllib.request.Request(
            "http://127.0.0.1:18013/api/auth/login",
            data=json.dumps({"username": "admin", "password": "Admin2026*"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(login_req, timeout=5) as resp:
            token = json.loads(resp.read())["access_token"]

        me_req = urllib.request.Request(
            "http://127.0.0.1:18013/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        with urllib.request.urlopen(me_req, timeout=5) as resp:
            me = json.loads(resp.read())
        assert me["username"] == "admin"
        assert me["organization_name"]
    finally:
        proc.terminate()
        proc.wait(timeout=10)


def test_backup_empty_file_aborts(tmp_path):
    db = tmp_path / "empty.db"
    db.write_bytes(b"")
    with pytest.raises(SchemaRepairError):
        create_verified_backup(db)


def test_atomic_swap_preserves_active_on_missing_migrating(tmp_path):
    active = tmp_path / "active.db"
    create_fresh_database(active)
    missing = tmp_path / "missing.db"
    with pytest.raises(LegacyMigrationError):
        atomic_swap(active, missing)
    assert active.exists()


def test_migration_row_failure_aborts(tmp_path):
    db = tmp_path / "legacy.db"
    build_programmatic_legacy_db(db)
    conn = sqlite3.connect(db)
    conn.execute("INSERT INTO users VALUES ('bad','missing-org','x','h','admin',1,'2026-01-01')")
    conn.commit()
    conn.close()
    with pytest.raises(LegacyMigrationError):
        migrate_legacy_database(_url(db), skip_backup=True, perform_swap=False)


def test_backup_creation_verified(tmp_path):
    db = tmp_path / "sample.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()
    backup = create_verified_backup(db)
    info = verify_backup_file(backup, db)
    assert info["integrity"] == "ok"
    assert len(info["sha256"]) == 64


def test_foreign_process_not_killed(tmp_path):
    own_pid = os.getpid()
    save_pid_registry({"backend": {"role": "backend", "pid": own_pid, "cwd": "/tmp"}}, data_dir=tmp_path)
    assert not _is_empleados_ia_process(own_pid, "backend")
    result = stop_registered_services(data_dir=tmp_path)
    assert result["stopped"] == []


def test_resolve_npm_found():
    npm = resolve_npm()
    assert npm
    assert "npm" in npm.lower()


def test_idempotent_migration_scenario_c(tmp_path):
    db = tmp_path / "fresh.db"
    create_fresh_database(db)
    migrate_legacy_database(_url(db), skip_backup=True)
    migrate_legacy_database(_url(db), skip_backup=True)
    assert get_alembic_revision(db) == HEAD_REVISION
