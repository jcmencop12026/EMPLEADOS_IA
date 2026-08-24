"""Tests CURSOR-805B — reparación SQLite/Alembic y gestión de servicios."""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
PROJECT_ROOT = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from scripts.schema_repair import (  # noqa: E402
    HEAD_REVISION,
    SchemaRepairError,
    create_verified_backup,
    get_alembic_revision,
    repair_database,
    repair_schema,
    sync_alembic_revision,
    validate_schema_strict,
    verify_backup_file,
)
from scripts.service_manager import (  # noqa: E402
    _is_empleados_ia_process,
    save_pid_registry,
    stop_registered_services,
)


LEGACY_SOURCE = PROJECT_ROOT / "data" / "enterprise_ai_os_PRE_REPAIR_20260823_163607.db"


def _db_url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def _make_codex_legacy_db(tmp_path: Path) -> Path:
    """Simula BD legacy real: sin requires_approval + columna status NOT NULL."""
    if not LEGACY_SOURCE.exists():
        pytest.skip("BD legacy de referencia no disponible")
    dst = tmp_path / "codex_legacy.db"
    shutil.copy2(LEGACY_SOURCE, dst)
    conn = sqlite3.connect(dst)
    conn.execute("DELETE FROM alembic_version")
    conn.execute("DROP TABLE IF EXISTS employee_templates")
    # Recrear capabilities sin requires_approval pero con status NOT NULL (escenario Codex)
    conn.executescript(
        """
        CREATE TABLE capabilities_legacy AS SELECT
            id, organization_id, code, name, description, risk_level, is_active, created_at
        FROM capabilities;
        DROP TABLE capabilities;
        CREATE TABLE capabilities (
            id VARCHAR(36) NOT NULL PRIMARY KEY,
            organization_id VARCHAR(36) NOT NULL,
            code VARCHAR(80) NOT NULL,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            risk_level VARCHAR(20) NOT NULL,
            status VARCHAR(40) NOT NULL,
            is_active BOOLEAN NOT NULL,
            created_at DATETIME NOT NULL
        );
        INSERT INTO capabilities
        SELECT id, organization_id, code, name, description, risk_level, 'ACTIVE', is_active, created_at
        FROM capabilities_legacy;
        DROP TABLE capabilities_legacy;
        """
    )
    conn.commit()
    conn.close()
    return dst


def test_backup_creation_and_verification(tmp_path):
    src = tmp_path / "sample.db"
    conn = sqlite3.connect(src)
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

    backup = create_verified_backup(src)
    info = verify_backup_file(backup, src)
    assert info["size"] > 0
    assert info["integrity"] == "ok"
    assert len(info["sha256"]) == 64


def test_incompatible_schema_rejected_for_stamp(tmp_path):
    db = tmp_path / "incompatible.db"
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE capabilities ("
        "organization_id VARCHAR(36) NOT NULL, "
        "code VARCHAR(80) NOT NULL, "
        "PRIMARY KEY (organization_id, code)"
        ")"
    )
    conn.commit()
    conn.close()

    engine = create_engine(_db_url(db), connect_args={"check_same_thread": False})
    validation = validate_schema_strict(engine)
    assert not validation.is_valid
    assert any(i.category == "primary_key" and not i.repairable for i in validation.issues)

    with pytest.raises(SchemaRepairError):
        sync_alembic_revision(engine, _db_url(db))


def test_legacy_codex_db_repair_and_backend_health(tmp_path):
    legacy = _make_codex_legacy_db(tmp_path)
    url = _db_url(legacy)

    before = validate_schema_strict(create_engine(url, connect_args={"check_same_thread": False}))
    assert not before.is_valid

    result = repair_database(url, skip_backup=True)
    assert result["after"]["valid"] is True
    assert result["alembic_revision"] == HEAD_REVISION

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "18010"],
        cwd=str(BACKEND_DIR),
        env={**os.environ, "DATABASE_URL": url},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        ok = False
        for _ in range(30):
            try:
                with urllib.request.urlopen("http://127.0.0.1:18010/health", timeout=2) as resp:
                    ok = resp.status == 200
                    break
            except Exception:
                time.sleep(1)
        assert ok, "Backend no arrancó sobre copia legacy reparada"
    finally:
        proc.terminate()
        proc.wait(timeout=10)


def test_repair_idempotent_and_preserves_data(tmp_path):
    legacy = _make_codex_legacy_db(tmp_path)
    url = _db_url(legacy)

    conn = sqlite3.connect(legacy)
    before_counts = {
        "organizations": conn.execute("SELECT COUNT(*) FROM organizations").fetchone()[0],
        "users": conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        "ai_employees": conn.execute("SELECT COUNT(*) FROM ai_employees").fetchone()[0],
        "capabilities": conn.execute("SELECT COUNT(*) FROM capabilities").fetchone()[0],
    }
    conn.close()

    repair_database(url, skip_backup=True)
    repair_database(url, skip_backup=True)

    conn = sqlite3.connect(legacy)
    after_counts = {
        "organizations": conn.execute("SELECT COUNT(*) FROM organizations").fetchone()[0],
        "users": conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        "ai_employees": conn.execute("SELECT COUNT(*) FROM ai_employees").fetchone()[0],
        "capabilities": conn.execute("SELECT COUNT(*) FROM capabilities").fetchone()[0],
    }
    assert before_counts == after_counts
    assert get_alembic_revision(legacy) == HEAD_REVISION


def test_foreign_process_not_killed(tmp_path):
  # Simula PID ajeno registrado erróneamente: no debe matarse si no es EMPLEADOS_IA
    own_pid = os.getpid()
    save_pid_registry({"backend": {"role": "backend", "pid": own_pid}}, data_dir=tmp_path)
    # El proceso actual no es uvicorn EMPLEADOS_IA
    assert not _is_empleados_ia_process(own_pid, "backend")
    result = stop_registered_services(data_dir=tmp_path)
    assert result["stopped"] == []
    assert any(s["reason"] == "no pertenece a EMPLEADOS_IA" for s in result["skipped"])


def test_alembic_chain_present_portable():
    versions_dir = BACKEND_DIR / "alembic" / "versions"
    versions = list(versions_dir.glob("*.py"))
    assert any("4355c73adcb8" in v.name for v in versions)
    assert any("5b2eb2437398" in v.name for v in versions)


def test_partial_repair_recovery(tmp_path):
    db = tmp_path / "partial.db"
    shutil.copy2(_make_codex_legacy_db(tmp_path), db)
    url = _db_url(db)
    engine = create_engine(url, connect_args={"check_same_thread": False})
    repair_schema(engine)
    validation = validate_schema_strict(engine)
    assert validation.is_valid
