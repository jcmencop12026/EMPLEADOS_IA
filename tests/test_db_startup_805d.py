"""Tests CURSOR-805D — preservación legacy + BD actual limpia."""
from __future__ import annotations

import json
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
from scripts.db_startup import (  # noqa: E402
    DbStartupError,
    create_fresh_database,
    detect_db_scenario,
    inventory_legacy_db,
    prepare_database,
)
from scripts.legacy_preservation import (  # noqa: E402
    build_full_inventory,
    preserve_legacy_database,
    verify_legacy_unchanged,
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
    _collect_descendant_pids,
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
    result = prepare_database(_url(db))
    assert result["scenario"] == "A"
    assert result["action"] == "created"
    assert db.exists()
    assert get_alembic_revision(db) == HEAD_REVISION
    assert validate_schema_strict(create_engine(_url(db), connect_args={"check_same_thread": False})).is_valid


def test_scenario_b_compatible_db(tmp_path):
    db = tmp_path / "compatible.db"
    create_fresh_database(db)
    assert detect_db_scenario(db) == "B"
    result = prepare_database(_url(db))
    assert result["scenario"] == "B"
    assert result["action"] == "none"


def test_scenario_c_legacy_preserved_and_new_db(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    db = data_dir / "enterprise_ai_os.db"
    expected = build_programmatic_legacy_db(db, extended=True)
    assert detect_db_scenario(db) == "C"

    result = prepare_database(_url(db))
    assert result["scenario"] == "C"
    assert result["action"] == "legacy_preserved_and_recreated"
    assert result["preservation"]["sha256"]
    assert (data_dir / "LEGACY" / "LEGACY_INVENTORY.json").exists()
    assert (data_dir / "LEGACY" / "LEGACY_INVENTORY.csv").exists()

    legacy_files = list((data_dir / "LEGACY").glob("*_LEGACY_*.db"))
    assert len(legacy_files) == 1
    legacy_sha = result["preservation"]["sha256"]
    assert verify_legacy_unchanged(legacy_files[0], legacy_sha)

    inv = inventory_legacy_db(db)
    assert inv["organizations"] == 1
    assert inv["users"] == 1
    assert get_alembic_revision(db) == HEAD_REVISION

    legacy_inv = inventory_legacy_db(legacy_files[0])
    assert legacy_inv["organizations"] == expected["organizations"]
    assert legacy_inv["partners"] == expected["partners"]


def test_scenario_d_damaged_db_rejected(tmp_path):
    db = tmp_path / "bad.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE unknown_only (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()
    assert detect_db_scenario(db) == "D"
    with pytest.raises(DbStartupError):
        prepare_database(_url(db))


def test_legacy_inventory_complete(tmp_path):
    db = tmp_path / "legacy.db"
    build_programmatic_legacy_db(db, extended=True)
    inventory = build_full_inventory(db)
    table_names = {t["table"] for t in inventory["tables"]}
    assert "organizations" in table_names
    assert "partners" in table_names
    assert "role_permissions" in table_names
    assert inventory["summary"]["tables_with_data"]


def test_legacy_export_exists(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    db = data_dir / "legacy.db"
    build_programmatic_legacy_db(db)
    report = preserve_legacy_database(db, data_dir=data_dir)
    export_dir = Path(report.export_dir)
    assert (export_dir / "organizations.json").exists()
    assert (export_dir / "organizations.csv").exists()
    assert (export_dir / "users.json").exists()


def test_legacy_not_modified_during_prepare(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    db = data_dir / "enterprise_ai_os.db"
    build_programmatic_legacy_db(db)
    report = preserve_legacy_database(db, data_dir=data_dir)
    legacy_path = Path(report.legacy_path)
    sha_before = report.sha256
    prepare_database(_url(db))
    assert verify_legacy_unchanged(legacy_path, sha_before)


def test_backup_hash_verified(tmp_path):
    db = tmp_path / "sample.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()
    backup = create_verified_backup(db)
    info = verify_backup_file(backup, db)
    assert info["integrity"] == "ok"
    assert len(info["sha256"]) == 64


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
    with pytest.raises(SchemaRepairError):
        sync_alembic_revision(engine, _url(db))


def test_backend_health_and_login_after_legacy_prepare(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    db = data_dir / "enterprise_ai_os.db"
    build_programmatic_legacy_db(db)
    prepare_database(_url(db))

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "18014"],
        cwd=str(BACKEND_DIR),
        env={**os.environ, "DATABASE_URL": _url(db)},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(30):
            try:
                with urllib.request.urlopen("http://127.0.0.1:18014/health", timeout=2):
                    break
            except Exception:
                time.sleep(1)
        else:
            pytest.fail("Backend no arrancó")

        login_req = urllib.request.Request(
            "http://127.0.0.1:18014/api/auth/login",
            data=json.dumps({"username": "admin", "password": "Admin2026*"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(login_req, timeout=5) as resp:
            token = json.loads(resp.read())["access_token"]
        me_req = urllib.request.Request(
            "http://127.0.0.1:18014/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        with urllib.request.urlopen(me_req, timeout=5) as resp:
            me = json.loads(resp.read())
        assert me["username"] == "admin"
    finally:
        proc.terminate()
        proc.wait(timeout=10)


def test_compatible_db_not_recreated(tmp_path):
    db = tmp_path / "fresh.db"
    create_fresh_database(db)
    mtime_before = db.stat().st_mtime
    prepare_database(_url(db))
    assert db.stat().st_mtime == mtime_before


def test_resolve_npm_found():
    npm = resolve_npm()
    assert npm
    assert "npm" in npm.lower()


def test_foreign_process_not_killed(tmp_path):
    own_pid = os.getpid()
    save_pid_registry({"backend": {"role": "backend", "pid": own_pid, "cwd": "/tmp"}}, data_dir=tmp_path)
    assert not _is_empleados_ia_process(own_pid, "backend")
    result = stop_registered_services(data_dir=tmp_path)
    assert result["stopped"] == []


def test_process_tree_collects_children():
    children = _collect_descendant_pids(os.getpid())
    assert isinstance(children, list)


def test_idempotent_prepare_scenario_b(tmp_path):
    db = tmp_path / "fresh.db"
    create_fresh_database(db)
    prepare_database(_url(db))
    prepare_database(_url(db))
    assert get_alembic_revision(db) == HEAD_REVISION
