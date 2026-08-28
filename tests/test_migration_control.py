"""Tests MIGRATIONS-CONTROL-001 — preflight, ledger y gobierno Alembic."""
from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

import pytest

from scripts.db_startup import DbStartupError, run_bootstrap
from scripts.migration_control import (
    INCOMPATIBLE_DB_MESSAGE,
    MigrationControlError,
    assert_single_head,
    load_migration_ledger,
    revisions_in_repository,
    run_database_preflight,
    validate_migration_ledger,
)
from scripts.schema_repair import HEAD_REVISION, get_alembic_revision


pytestmark = pytest.mark.migrations


def test_single_alembic_head():
    assert assert_single_head() == HEAD_REVISION


def test_migration_ledger_protects_consolidated_revisions():
    report = validate_migration_ledger()
    assert report["head"] == "1030a1b2c3d4e"
    assert report["protected_count"] >= 16


def test_orphan_revision_aborts_preflight():
    db_path = Path(tempfile.mktemp(suffix=".orphan.db"))
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
        conn.execute("INSERT INTO alembic_version (version_num) VALUES ('dbf8439340e9')")
        conn.execute("CREATE TABLE organizations (id TEXT PRIMARY KEY, name TEXT)")
        conn.execute("CREATE TABLE users (id TEXT PRIMARY KEY, organization_id TEXT, username TEXT)")
        conn.commit()
    finally:
        conn.close()

    url = f"sqlite:///{db_path.as_posix()}"
    with pytest.raises(MigrationControlError) as exc:
        run_database_preflight(url)
    assert "Base de datos incompatible" in str(exc.value)
    assert "dbf8439340e9" in str(exc.value)


def test_clean_database_preflight_ok():
    db_path = Path(tempfile.mktemp(suffix=".clean.db"))
    url = f"sqlite:///{db_path.as_posix()}"
    result = run_database_preflight(url)
    assert result["status"] == "no_alembic_version"


def test_bootstrap_aborts_on_orphan_revision():
    db_path = Path(tempfile.mktemp(suffix=".orphan-boot.db"))
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
        conn.execute("INSERT INTO alembic_version (version_num) VALUES ('dbf8439340e9')")
        conn.execute("CREATE TABLE organizations (id TEXT PRIMARY KEY, name TEXT)")
        conn.execute("CREATE TABLE users (id TEXT PRIMARY KEY, organization_id TEXT, username TEXT)")
        conn.commit()
    finally:
        conn.close()

    url = f"sqlite:///{db_path.as_posix()}"
    with pytest.raises(DbStartupError) as exc:
        run_bootstrap(url)
    assert INCOMPATIBLE_DB_MESSAGE.split(".")[0] in str(exc.value)


def test_ledger_missing_revision_fails(tmp_path: Path, monkeypatch):
    ledger = load_migration_ledger()
    protected = list(ledger["protected_revisions"])
    fake_missing = "ffffffffffff"
    ledger["protected_revisions"] = protected + [fake_missing]
    ledger_path = tmp_path / "migration_ledger.json"
    ledger_path.write_text(__import__("json").dumps(ledger), encoding="utf-8")
    monkeypatch.setattr("scripts.migration_control._LEDGER_PATH", ledger_path)
    with pytest.raises(MigrationControlError, match="Revisiones protegidas ausentes"):
        validate_migration_ledger()


def test_repository_contains_all_protected_revisions():
    ledger = load_migration_ledger()
    present = revisions_in_repository()
    missing = set(ledger["protected_revisions"]) - present
    assert not missing, f"Faltan archivos de migración: {missing}"
