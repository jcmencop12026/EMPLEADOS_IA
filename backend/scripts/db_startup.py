"""Preparación de BD SQLite local: preservar legacy, crear esquema actual (CURSOR-805D)."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.database import Base
from app import models  # noqa: F401
from app import orchestration_models  # noqa: F401
from scripts.legacy_preservation import (
    LEGACY_MARKER_TABLES,
    LegacyPreservationError,
    preserve_legacy_database,
    verify_legacy_unchanged,
)
from scripts.schema_repair import (
    HEAD_REVISION,
    SchemaRepairError,
    get_alembic_revision,
    sync_alembic_revision,
    validate_schema_strict,
)

DbStartupError = SchemaRepairError


@dataclass
class StartupReport:
    scenario: str
    action: str
    alembic_revision: str | None = None
    preservation: dict[str, Any] | None = None
    inventory: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario,
            "action": self.action,
            "alembic_revision": self.alembic_revision,
            "preservation": self.preservation,
            "inventory": self.inventory,
        }


def database_url_to_path(database_url: str) -> Path:
    return Path(database_url.removeprefix("sqlite:///"))


def inventory_legacy_db(db_path: Path) -> dict[str, int]:
    if not db_path.exists() or db_path.stat().st_size == 0:
        return {}
    conn = sqlite3.connect(db_path)
    try:
        tables = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        ]
        return {
            t: conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
            for t in tables
        }
    finally:
        conn.close()


def _integrity_ok(db_path: Path) -> bool:
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally:
        conn.close()


def is_legacy_database(db_path: Path) -> bool:
    inv = inventory_legacy_db(db_path)
    if not inv:
        return False

    current_tables = set(Base.metadata.tables.keys()) | {"alembic_version"}
    db_tables = set(inv.keys())
    legacy_only = (db_tables & LEGACY_MARKER_TABLES) - current_tables
    if legacy_only:
        return True

    engine = create_engine(f"sqlite:///{db_path.as_posix()}", connect_args={"check_same_thread": False})
    validation = validate_schema_strict(engine)
    if validation.is_valid:
        return False

    if db_tables & {"organizations", "users", "capabilities", "partners", "roles", "permissions", "employees", "audit_logs", "employee_capabilities"}:
        engine = create_engine(f"sqlite:///{db_path.as_posix()}", connect_args={"check_same_thread": False})
        if not validate_schema_strict(engine).is_valid:
            return True

    return False


def detect_db_scenario(db_path: Path) -> str:
    """A=no existe, B=compatible actual, C=legacy, D=dañada/incompatible."""
    if not db_path.exists() or db_path.stat().st_size == 0:
        return "A"

    if not _integrity_ok(db_path):
        return "D"

    engine = create_engine(f"sqlite:///{db_path.as_posix()}", connect_args={"check_same_thread": False})
    validation = validate_schema_strict(engine)
    revision = get_alembic_revision(db_path)
    if validation.is_valid and revision == HEAD_REVISION:
        return "B"

    if is_legacy_database(db_path):
        return "C"

    return "D"


def create_fresh_database(target_path: Path) -> None:
    if target_path.exists():
        target_path.unlink()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{target_path.as_posix()}", connect_args={"check_same_thread": False})
    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys=ON"))
    Base.metadata.create_all(bind=engine)
    _ensure_all_indexes(engine)
    validation = validate_schema_strict(engine)
    if not validation.is_valid:
        raise DbStartupError("BD nueva no pasa validación estricta", validation=validation)
    sync_alembic_revision(engine, f"sqlite:///{target_path.as_posix()}")


def _ensure_all_indexes(engine: Engine) -> None:
    with engine.begin() as conn:
        for table_name, table in Base.metadata.tables.items():
            for idx in table.indexes:
                cols = ", ".join(c.name for c in idx.columns)
                unique = "UNIQUE " if idx.unique else ""
                name = idx.name or f"ix_{table_name}_{cols.replace(', ', '_')}"
                conn.execute(text(f"CREATE {unique}INDEX IF NOT EXISTS {name} ON {table_name} ({cols})"))


def run_bootstrap(database_url: str) -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.seed import bootstrap

    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = session_factory()
    try:
        bootstrap(db)
    finally:
        db.close()


def prepare_database(database_url: str) -> dict[str, Any]:
    db_path = database_url_to_path(database_url)
    scenario = detect_db_scenario(db_path)
    report = StartupReport(scenario=scenario, action="none")

    if scenario == "A":
        create_fresh_database(db_path)
        run_bootstrap(database_url)
        report.action = "created"
        report.alembic_revision = HEAD_REVISION
        return report.to_dict()

    if scenario == "B":
        report.inventory = inventory_legacy_db(db_path)
        report.alembic_revision = get_alembic_revision(db_path)
        report.action = "none"
        return report.to_dict()

    if scenario == "D":
        raise DbStartupError(
            f"BD actual dañada o incompatible. No se reemplaza silenciosamente: {db_path}"
        )

    # Scenario C: preservar legacy, inventariar/exportar, crear BD actual limpia
    report.inventory = inventory_legacy_db(db_path)
    preservation = preserve_legacy_database(db_path, data_dir=db_path.parent)
    legacy_path = Path(preservation.legacy_path)
    legacy_sha = preservation.sha256

    if not verify_legacy_unchanged(legacy_path, legacy_sha):
        raise LegacyPreservationError("Copia legacy alterada tras preservación")

    db_path.unlink()
    create_fresh_database(db_path)
    run_bootstrap(database_url)

    if not verify_legacy_unchanged(legacy_path, legacy_sha):
        raise LegacyPreservationError("Copia legacy modificada durante creación de BD nueva")

    report.action = "legacy_preserved_and_recreated"
    report.preservation = preservation.to_dict()
    report.alembic_revision = HEAD_REVISION
    return report.to_dict()
