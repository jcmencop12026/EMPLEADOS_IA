"""Migración legacy segura: nueva BD + mapping explícito + swap atómico (CURSOR-805C)."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from app.database import Base
from app import models  # noqa: F401
from app import orchestration_models  # noqa: F401
from scripts.schema_repair import (
    HEAD_REVISION,
    SchemaRepairError,
    SchemaValidationResult,
    create_verified_backup,
    get_alembic_revision,
    sync_alembic_revision,
    validate_schema_strict,
    verify_backup_file,
)

MIGRATION_TABLE_ORDER = [
    "organizations",
    "users",
    "capabilities",
    "tools",
    "ai_employees",
    "employee_capabilities",
    "employee_templates",
    "employee_tool_grants",
    "employee_knowledge_sources",
    "employee_limits",
    "employee_model_policies",
    "employee_instructions",
    "employee_versions",
    "employee_test_cases",
    "employee_test_runs",
    "employee_certifications",
    "work_plans",
    "employee_tasks",
    "approval_requests",
    "work_events",
    "finops_records",
    "audit_logs",
]

# Defaults seguros al migrar columnas nuevas del modelo actual.
COLUMN_DEFAULTS: dict[str, dict[str, Any]] = {
    "capabilities": {
        "requires_approval": 0,
        "inputs_json": None,
        "outputs_json": None,
        "executor_types_json": None,
    },
    "tools": {
        "requires_approval": 0,
    },
    "ai_employees": {
        "code": None,  # computed
        "description": None,
        "role": None,
        "objective": None,
        "lifecycle_status": "ACTIVE",
        "maturity": "AUTONOMOUS_CONTROLLED",
        "risk_level": "LOW",
        "version": 1,
        "owner_id": None,
        "created_by_id": None,
        "shadow_mode": 0,
        "published_at": None,
        "certified_at": None,
        "updated_at": None,  # computed from created_at
    },
}


class LegacyMigrationError(SchemaRepairError):
    pass


@dataclass
class TableMigrationReport:
    table: str
    source_count: int = 0
    migrated_count: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "table": self.table,
            "source_count": self.source_count,
            "migrated_count": self.migrated_count,
            "skipped": self.skipped,
            "errors": self.errors,
        }


@dataclass
class MigrationReport:
    scenario: str
    backup: dict[str, Any] | None = None
    inventory: dict[str, int] = field(default_factory=dict)
    tables: list[TableMigrationReport] = field(default_factory=list)
    swap: dict[str, Any] = field(default_factory=dict)
    alembic_revision: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario,
            "backup": self.backup,
            "inventory": self.inventory,
            "tables": [t.to_dict() for t in self.tables],
            "swap": self.swap,
            "alembic_revision": self.alembic_revision,
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


def detect_db_scenario(db_path: Path) -> str:
    """A=no existe, B=vacía, C=compatible, D=legacy migrable, E=incompatible."""
    if not db_path.exists():
        return "A"
    if db_path.stat().st_size == 0:
        return "B"

    inv = inventory_legacy_db(db_path)
    if not inv:
        return "B"

    engine = create_engine(f"sqlite:///{db_path.as_posix()}", connect_args={"check_same_thread": False})
    validation = validate_schema_strict(engine)
    revision = get_alembic_revision(db_path)
    if validation.is_valid and revision == HEAD_REVISION:
        return "C"

    core_tables = ("organizations", "users", "capabilities")
    if any(t in inv for t in core_tables):
        return "D"

    return "E"


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
        raise LegacyMigrationError("BD nueva no pasa validación estricta", validation=validation)
    sync_alembic_revision(engine, f"sqlite:///{target_path.as_posix()}")


def _ensure_all_indexes(engine: Engine) -> None:
    with engine.begin() as conn:
        for table_name, table in Base.metadata.tables.items():
            for idx in table.indexes:
                cols = ", ".join(c.name for c in idx.columns)
                unique = "UNIQUE " if idx.unique else ""
                name = idx.name or f"ix_{table_name}_{cols.replace(', ', '_')}"
                conn.execute(text(f"CREATE {unique}INDEX IF NOT EXISTS {name} ON {table_name} ({cols})"))


def _source_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info([{table}])").fetchall()
    return {r[1] for r in rows}


def _transform_row(table: str, row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    defaults = COLUMN_DEFAULTS.get(table, {})
    for col, val in defaults.items():
        if col not in out or out[col] is None:
            out[col] = val

    if table == "ai_employees":
        if not out.get("code"):
            out["code"] = f"emp-{(out.get('id') or '')[:8]}"
        if not out.get("updated_at"):
            out["updated_at"] = out.get("created_at")
        if not out.get("role"):
            out["role"] = out.get("name")
        if not out.get("objective"):
            out["objective"] = f"Especialista {out.get('specialty', '')}"
        if not out.get("risk_level"):
            out["risk_level"] = "LOW"

    if table == "capabilities":
        if "requires_approval" not in row:
            out["requires_approval"] = 1 if str(row.get("risk_level", "")).lower() == "high" else 0
        for drop in ("status",):
            out.pop(drop, None)

    if table == "tools":
        if "requires_approval" not in row:
            out["requires_approval"] = 1 if str(row.get("risk_level", "")).lower() == "high" else 0
        out.pop("status", None)

    return out


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def _migrate_table(
    source: sqlite3.Connection,
    target: sqlite3.Connection,
    table: str,
) -> TableMigrationReport:
    report = TableMigrationReport(table=table)
    if not _table_exists(source, table):
        return report

    report.source_count = source.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
    if report.source_count == 0:
        return report

    target_cols = {c.name for c in Base.metadata.tables[table].columns}
    rows = source.execute(f"SELECT * FROM [{table}]").fetchall()
    col_names = [d[0] for d in source.execute(f"SELECT * FROM [{table}] LIMIT 0").description]

    for raw in rows:
        row = dict(zip(col_names, raw))
        try:
            transformed = _transform_row(table, row)
            insert_cols = [c for c in target_cols if c in transformed]
            values = [transformed[c] for c in insert_cols]
            placeholders = ", ".join("?" for _ in insert_cols)
            cols_sql = ", ".join(f"[{c}]" for c in insert_cols)
            target.execute(
                f"INSERT INTO [{table}] ({cols_sql}) VALUES ({placeholders})",
                values,
            )
            report.migrated_count += 1
        except Exception as exc:
            report.errors.append(f"PK={row.get('id', '?')}: {exc}")

    if report.errors:
        raise LegacyMigrationError(
            f"Migración fallida en {table}: {report.errors[0]}",
        )
    if report.migrated_count != report.source_count:
        raise LegacyMigrationError(
            f"Conteo incompleto en {table}: source={report.source_count} migrated={report.migrated_count}",
        )
    return report


def _validate_migrated_data(target_path: Path, source_inventory: dict[str, int]) -> None:
    conn = sqlite3.connect(target_path)
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise LegacyMigrationError(f"integrity_check falló: {integrity}")

        fk_errors = conn.execute("PRAGMA foreign_key_check").fetchall()
        if fk_errors:
            raise LegacyMigrationError(f"foreign_key_check falló: {fk_errors[:3]}")

        for table in MIGRATION_TABLE_ORDER:
            if table not in Base.metadata.tables:
                continue
            tgt = conn.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
            src = source_inventory.get(table, 0)
            if src > 0 and tgt != src:
                raise LegacyMigrationError(f"Conteo target inválido {table}: source={src} target={tgt}")
    finally:
        conn.close()


def atomic_swap(active_path: Path, migrating_path: Path) -> dict[str, Any]:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    legacy_archive = active_path.parent / f"{active_path.stem}_LEGACY_{ts}.db"
    backup_active = active_path.parent / f"{active_path.stem}_PRE_SWAP_{ts}.db"

    if not migrating_path.exists():
        raise LegacyMigrationError(f"BD migrating no existe: {migrating_path}")

    if active_path.exists():
        shutil.copy2(active_path, backup_active)
        verify_backup_file(backup_active, active_path)

    try:
        if active_path.exists():
            shutil.move(str(active_path), str(legacy_archive))
        shutil.move(str(migrating_path), str(active_path))
        return {
            "active": str(active_path),
            "legacy_archive": str(legacy_archive) if legacy_archive.exists() else None,
            "pre_swap_backup": str(backup_active) if backup_active.exists() else None,
        }
    except Exception as exc:
        if legacy_archive.exists() and not active_path.exists():
            shutil.move(str(legacy_archive), str(active_path))
        raise LegacyMigrationError(f"Swap atómico falló, rollback aplicado: {exc}") from exc


def migrate_legacy_database(
    database_url: str,
    *,
    skip_backup: bool = False,
    perform_swap: bool = True,
) -> dict[str, Any]:
    db_path = database_url_to_path(database_url)
    scenario = detect_db_scenario(db_path)
    report = MigrationReport(scenario=scenario)

    if scenario == "A":
        create_fresh_database(db_path)
        report.alembic_revision = HEAD_REVISION
        return report.to_dict()

    if scenario == "B":
        if db_path.exists() and db_path.stat().st_size == 0:
            db_path.unlink()
        create_fresh_database(db_path)
        report.alembic_revision = HEAD_REVISION
        return report.to_dict()

    if scenario == "C":
        report.inventory = inventory_legacy_db(db_path)
        report.alembic_revision = get_alembic_revision(db_path)
        return report.to_dict()

    if scenario == "E":
        raise LegacyMigrationError(f"BD incompatible/no migrable: {db_path}")

    # Scenario D: migración completa
    report.inventory = inventory_legacy_db(db_path)
    backup_info = None
    if not skip_backup:
        backup_path = create_verified_backup(db_path)
        backup_info = verify_backup_file(backup_path, db_path)
    report.backup = backup_info

    migrating_path = db_path.parent / f"{db_path.stem}_MIGRATING.db"
    if migrating_path.exists():
        migrating_path.unlink()

    create_fresh_database(migrating_path)

    source = sqlite3.connect(db_path)
    target = sqlite3.connect(migrating_path)
    try:
        source.execute("PRAGMA foreign_keys=ON")
        target.execute("PRAGMA foreign_keys=ON")

        for table in MIGRATION_TABLE_ORDER:
            if table not in Base.metadata.tables:
                continue
            tbl_report = _migrate_table(source, target, table)
            if tbl_report.source_count > 0:
                report.tables.append(tbl_report)
        target.commit()
    except Exception:
        target.rollback()
        raise
    finally:
        source.close()
        target.close()

    _validate_migrated_data(migrating_path, report.inventory)

    engine = create_engine(f"sqlite:///{migrating_path.as_posix()}", connect_args={"check_same_thread": False})
    validation = validate_schema_strict(engine)
    if not validation.is_valid:
        raise LegacyMigrationError("BD migrating no pasa validación estricta", validation=validation)

    report.alembic_revision = sync_alembic_revision(engine, f"sqlite:///{migrating_path.as_posix()}")

    if perform_swap:
        report.swap = atomic_swap(db_path, migrating_path)

    return report.to_dict()
