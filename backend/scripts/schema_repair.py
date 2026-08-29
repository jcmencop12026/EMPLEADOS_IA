"""Reparación idempotente y validación estricta de SQLite legacy (CURSOR-805/805B)."""
from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.types import Numeric, TypeEngine

from app.database import Base
from app import automation_models  # noqa: F401
from app import models  # noqa: F401
from app import orchestration_models  # noqa: F401
from app import finops_models  # noqa: F401

HEAD_REVISION = "1391a1b2c3d4e"
REV_801 = "4355c73adcb8"

# Columnas legacy conocidas que no existen en el modelo actual y rompen INSERT ORM.
LEGACY_EXTRA_COLUMNS: dict[str, list[str]] = {
    "capabilities": ["status"],
    "tools": ["status"],
}

_TYPE_MAP: dict[type[TypeEngine], str] = {
    String: "TEXT",
    Text: "TEXT",
    Boolean: "INTEGER",
    Integer: "INTEGER",
    Float: "REAL",
    Numeric: "NUMERIC",
    DateTime: "TEXT",
}


class SchemaRepairError(RuntimeError):
    def __init__(self, message: str, validation: SchemaValidationResult | None = None):
        super().__init__(message)
        self.validation = validation


@dataclass
class SchemaIssue:
    category: str
    table: str
    name: str
    message: str
    repairable: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "table": self.table,
            "name": self.name,
            "message": self.message,
            "repairable": self.repairable,
        }


@dataclass
class SchemaValidationResult:
    issues: list[SchemaIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[SchemaIssue]:
        return [i for i in self.issues if not i.repairable or i.category.endswith("_error")]

    @property
    def is_valid(self) -> bool:
        return len(self.issues) == 0

    @property
    def is_repairable(self) -> bool:
        if self.is_valid:
            return True
        return all(i.repairable for i in self.issues)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.is_valid,
            "repairable": self.is_repairable,
            "issues": [i.to_dict() for i in self.issues],
        }


@dataclass
class SchemaDiff:
    missing_tables: list[str] = field(default_factory=list)
    extra_tables: list[str] = field(default_factory=list)
    missing_columns: dict[str, list[str]] = field(default_factory=dict)
    extra_columns: dict[str, list[str]] = field(default_factory=dict)

    @property
    def is_satisfied(self) -> bool:
        return not self.missing_tables and not self.missing_columns


def _types_compatible(expected: str, actual: str) -> bool:
    if expected == actual:
        return True
    datetime_types = {"TEXT", "DATETIME", "TIMESTAMP"}
    if expected in datetime_types and actual in datetime_types:
        return True
    if expected == "INTEGER" and actual == "BOOLEAN":
        return True
    if expected == "TEXT" and actual in {"VARCHAR", "CHAR", "CLOB"}:
        return True
    numeric_types = {"REAL", "NUMERIC", "DECIMAL"}
    if expected in numeric_types and actual in numeric_types:
        return True
    return False


def _normalize_sqlite_type(declared: str) -> str:
    upper = (declared or "TEXT").upper()
    if "INT" in upper or upper == "BOOLEAN":
        return "INTEGER"
    if "CHAR" in upper or "CLOB" in upper or "TEXT" in upper:
        return "TEXT"
    if "BLOB" in upper:
        return "BLOB"
    if "REAL" in upper or "FLOA" in upper or "DOUB" in upper or "NUM" in upper or "DEC" in upper:
        return "REAL"
    if "DATE" in upper or "TIME" in upper:
        return "DATETIME"
    return upper


def _expected_type(col) -> str:
    for py_type, sql_type in _TYPE_MAP.items():
        if isinstance(col.type, py_type):
            return sql_type
    return "TEXT"


def _sqlite_columns(conn, table: str) -> dict[str, dict[str, Any]]:
    rows = conn.execute(text(f"PRAGMA table_info({table})")).mappings().all()
    return {r["name"]: dict(r) for r in rows}


def _sqlite_indexes(conn, table: str) -> set[str]:
    rows = conn.execute(text(f"PRAGMA index_list({table})")).mappings().all()
    return {r["name"] for r in rows if r["name"]}


def _sqlite_foreign_keys(conn, table: str) -> list[dict[str, Any]]:
    rows = conn.execute(text(f"PRAGMA foreign_key_list({table})")).mappings().all()
    return [dict(r) for r in rows]


def validate_schema_strict(engine: Engine) -> SchemaValidationResult:
    """Validación estricta contra metadata SQLAlchemy actual."""
    result = SchemaValidationResult()
    insp = inspect(engine)

    with engine.connect() as conn:
        db_tables = set(insp.get_table_names()) - {"alembic_version"}
        meta_tables = set(Base.metadata.tables.keys())

        for table in sorted(meta_tables - db_tables):
            result.issues.append(SchemaIssue(
                category="table",
                table=table,
                name=table,
                message="Tabla requerida ausente",
                repairable=True,
            ))

        for table_name in sorted(meta_tables & db_tables):
            table = Base.metadata.tables[table_name]
            db_cols = _sqlite_columns(conn, table_name)
            model_col_names = {c.name for c in table.columns}

            for col in table.columns:
                if col.name not in db_cols:
                    result.issues.append(SchemaIssue(
                        category="column",
                        table=table_name,
                        name=col.name,
                        message="Columna requerida ausente",
                        repairable=True,
                    ))
                    continue

                db_col = db_cols[col.name]
                expected = _expected_type(col)
                actual = _normalize_sqlite_type(db_col["type"])
                if not _types_compatible(expected, actual):
                    # Tipos incompatibles (p.ej. INTEGER vs TEXT en PK) no son reparables automáticamente.
                    incompatible = not (
                        (expected == "INTEGER" and actual == "TEXT")
                        or (expected == "TEXT" and actual == "INTEGER")
                    )
                    result.issues.append(SchemaIssue(
                        category="type",
                        table=table_name,
                        name=col.name,
                        message=f"Tipo incompatible: esperado {expected}, actual {actual}",
                        repairable=not incompatible,
                    ))

                if not col.nullable and db_col["notnull"] == 0 and col.default is None and col.server_default is None:
                    result.issues.append(SchemaIssue(
                        category="nullable",
                        table=table_name,
                        name=col.name,
                        message="Columna NOT NULL en modelo pero nullable en BD",
                        repairable=True,
                    ))

            pk_cols = {c.name for c in table.primary_key.columns}
            db_pk = {name for name, info in db_cols.items() if info["pk"] == 1}
            if pk_cols != db_pk:
                result.issues.append(SchemaIssue(
                    category="primary_key",
                    table=table_name,
                    name=",".join(sorted(pk_cols)),
                    message=f"PK incompatible: modelo={sorted(pk_cols)} bd={sorted(db_pk)}",
                    repairable=False,
                ))

            for col in table.columns:
                if col.unique and col.name in db_cols:
                    idx_name = f"uq_{table_name}_{col.name}"
                    indexes = _sqlite_indexes(conn, table_name)
                    if not any(col.name in idx for idx in indexes) and idx_name not in indexes:
                        # unique=True sin índice explícito en metadata.indexes
                        unique_indexes = conn.execute(text(f"PRAGMA index_list({table_name})")).mappings().all()
                        has_unique = False
                        for idx in unique_indexes:
                            if idx["unique"]:
                                idx_cols = conn.execute(text(f"PRAGMA index_info({idx['name']})")).mappings().all()
                                if [r["name"] for r in idx_cols] == [col.name]:
                                    has_unique = True
                        if not has_unique:
                            result.issues.append(SchemaIssue(
                                category="unique",
                                table=table_name,
                                name=col.name,
                                message="Restricción UNIQUE ausente",
                                repairable=True,
                            ))

            for idx in table.indexes:
                if idx.name and idx.name not in _sqlite_indexes(conn, table_name):
                    result.issues.append(SchemaIssue(
                        category="index",
                        table=table_name,
                        name=idx.name,
                        message="Índice requerido ausente",
                        repairable=True,
                    ))

            db_fks = _sqlite_foreign_keys(conn, table_name)
            db_fk_pairs = {(fk["from"], fk["table"]) for fk in db_fks}
            for fk in table.foreign_keys:
                local_cols = tuple(sorted(c.name for c in fk.constraint.columns))
                ref_table = fk.column.table.name
                for local_col in local_cols:
                    if (local_col, ref_table) not in db_fk_pairs:
                        result.issues.append(SchemaIssue(
                            category="foreign_key",
                            table=table_name,
                            name=f"{local_col}->{ref_table}.{fk.column.name}",
                            message="Foreign key requerida ausente",
                            repairable=False,
                        ))

            for extra in sorted(set(db_cols) - model_col_names):
                info = db_cols[extra]
                legacy_known = extra in LEGACY_EXTRA_COLUMNS.get(table_name, [])
                if info["notnull"] == 1 and info["dflt_value"] is None and not legacy_known:
                    result.issues.append(SchemaIssue(
                        category="extra_column",
                        table=table_name,
                        name=extra,
                        message="Columna extra NOT NULL sin default bloquea INSERT ORM",
                        repairable=True,
                    ))
                elif not legacy_known:
                    result.issues.append(SchemaIssue(
                        category="extra_column",
                        table=table_name,
                        name=extra,
                        message="Columna extra presente (no bloqueante si nullable/con default)",
                        repairable=True,
                    ))

    return result


def audit_schema(engine: Engine) -> SchemaDiff:
    """Auditoría resumida de tablas/columnas."""
    insp = inspect(engine)
    db_tables = set(insp.get_table_names()) - {"alembic_version"}
    meta_tables = set(Base.metadata.tables.keys())
    diff = SchemaDiff(
        missing_tables=sorted(meta_tables - db_tables),
        extra_tables=sorted(db_tables - meta_tables),
    )
    for table in sorted(meta_tables & db_tables):
        db_cols = {c["name"] for c in insp.get_columns(table)}
        model_cols = {c.name for c in Base.metadata.tables[table].columns}
        missing = sorted(model_cols - db_cols)
        extra = sorted(db_cols - model_cols)
        if missing:
            diff.missing_columns[table] = missing
        if extra:
            diff.extra_columns[table] = extra
    return diff


def _default_sql(col) -> str | None:
    if col.name == "requires_approval":
        return "0"
    if col.name == "code":
        return "'emp-temp'"
    if col.name == "is_active":
        return "1"
    if col.name == "shadow_mode":
        return "0"
    if col.name == "version" and col.table.name == "ai_employees":
        return "1"
    if col.name == "lifecycle_status":
        return "'ACTIVE'"
    if col.name == "maturity":
        return "'AUTONOMOUS_CONTROLLED'"
    if col.name == "updated_at":
        return "'1970-01-01 00:00:00'"
    if col.name == "risk_level":
        return "'LOW'"
    if col.name == "max_concurrent_tasks":
        return "3"
    if col.name == "timeout_seconds":
        return "120"
    if col.name == "max_retries":
        return "2"
    if col.name == "permission":
        return "'ALLOW'"
    if col.name == "severity":
        return "'medium'"
    if col.name == "test_type":
        return "'SMOKE'"
    if col.name == "status" and col.table.name == "employee_versions":
        return "'DRAFT'"
    if isinstance(col.type, Boolean):
        return "0"
    if isinstance(col.type, Integer):
        return "0"
    return None


def _add_column(conn, table: str, col) -> None:
    sql_type = _expected_type(col)
    default = _default_sql(col)
    parts = [f"ALTER TABLE {table} ADD COLUMN {col.name} {sql_type}"]
    if not col.nullable:
        if default is None:
            default = "''" if isinstance(col.type, (String, Text)) else "0"
        parts.append(f"NOT NULL DEFAULT {default}")
    elif default is not None:
        parts.append(f"DEFAULT {default}")
    conn.execute(text(" ".join(parts)))


def _drop_legacy_extra_columns(conn, table: str, columns: list[str]) -> None:
    for col in columns:
        cols = _sqlite_columns(conn, table)
        if col not in cols:
            continue
        conn.execute(text(f"ALTER TABLE {table} DROP COLUMN {col}"))


def _rebuild_table_without_extras(conn, table_name: str) -> None:
    """Copia solo columnas del modelo y reemplaza tabla (fallback si DROP COLUMN falla)."""
    model_cols = [c.name for c in Base.metadata.tables[table_name].columns]
    col_list = ", ".join(model_cols)
    tmp = f"_repair_{table_name}"
    conn.execute(text(f"CREATE TABLE {tmp} AS SELECT {col_list} FROM {table_name}"))
    conn.execute(text(f"DROP TABLE {table_name}"))
    conn.execute(text(f"ALTER TABLE {tmp} RENAME TO {table_name}"))


def _backfill_ai_employees(conn) -> None:
    conn.execute(text("UPDATE ai_employees SET code = 'emp-' || substr(id, 1, 8) WHERE code IS NULL OR code = '' OR code = 'emp-temp'"))
    conn.execute(text("UPDATE ai_employees SET lifecycle_status = 'ACTIVE' WHERE lifecycle_status IS NULL OR lifecycle_status = ''"))
    conn.execute(text("UPDATE ai_employees SET maturity = 'AUTONOMOUS_CONTROLLED' WHERE maturity IS NULL OR maturity = ''"))
    conn.execute(text("UPDATE ai_employees SET risk_level = 'LOW' WHERE risk_level IS NULL OR risk_level = ''"))
    conn.execute(text("UPDATE ai_employees SET version = 1 WHERE version IS NULL"))
    conn.execute(text("UPDATE ai_employees SET shadow_mode = 0 WHERE shadow_mode IS NULL"))
    conn.execute(text(
        "UPDATE ai_employees SET updated_at = created_at "
        "WHERE updated_at IS NULL OR updated_at = 0 OR updated_at = '0'"
    ))


def _backfill_capabilities(conn) -> None:
    conn.execute(text("UPDATE capabilities SET requires_approval = 0 WHERE requires_approval IS NULL"))
    conn.execute(text("UPDATE tools SET requires_approval = 0 WHERE requires_approval IS NULL"))


def _ensure_indexes(engine: Engine) -> None:
    with engine.begin() as conn:
        for table_name, table in Base.metadata.tables.items():
            for idx in table.indexes:
                cols = ", ".join(c.name for c in idx.columns)
                unique = "UNIQUE " if idx.unique else ""
                name = idx.name or f"ix_{table_name}_{cols.replace(', ', '_')}"
                conn.execute(text(f"CREATE {unique}INDEX IF NOT EXISTS {name} ON {table_name} ({cols})"))


def repair_schema(engine: Engine) -> SchemaValidationResult:
    """Aplica reparación idempotente hasta satisfacer validación estricta."""
    Base.metadata.create_all(bind=engine, checkfirst=True)

    with engine.begin() as conn:
        insp = inspect(conn)
        for table_name, table in Base.metadata.tables.items():
            if table_name not in insp.get_table_names():
                continue
            existing = {c["name"] for c in insp.get_columns(table_name)}
            for col in table.columns:
                if col.name not in existing:
                    _add_column(conn, table_name, col)

        for table_name, extras in LEGACY_EXTRA_COLUMNS.items():
            if table_name in insp.get_table_names():
                try:
                    _drop_legacy_extra_columns(conn, table_name, extras)
                except Exception:
                    _rebuild_table_without_extras(conn, table_name)

        _backfill_capabilities(conn)
        _backfill_ai_employees(conn)

    _ensure_indexes(engine)
    return validate_schema_strict(engine)


def verify_backup_file(backup_path: Path, source_path: Path | None = None) -> dict[str, Any]:
    if not backup_path.exists():
        raise SchemaRepairError(f"Backup no existe: {backup_path}")
    size = backup_path.stat().st_size
    if size <= 0:
        raise SchemaRepairError(f"Backup vacío: {backup_path}")

    conn = sqlite3.connect(backup_path)
    try:
        conn.execute("SELECT 1")
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise SchemaRepairError(f"PRAGMA integrity_check falló: {integrity}")
    finally:
        conn.close()

    digest = hashlib.sha256(backup_path.read_bytes()).hexdigest()
    info: dict[str, Any] = {
        "path": str(backup_path),
        "size": size,
        "sha256": digest,
        "integrity": "ok",
    }
    if source_path and source_path.exists():
        info["source_size"] = source_path.stat().st_size
    return info


def create_verified_backup(db_path: Path) -> Path:
    if not db_path.exists():
        raise SchemaRepairError(f"Base de datos no encontrada: {db_path}")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent / f"{db_path.stem}_PRE_REPAIR_{ts}.db"
    shutil.copy2(db_path, backup_path)
    verify_backup_file(backup_path, db_path)
    return backup_path


def get_alembic_revision(db_path: Path) -> str | None:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'")
        if not cur.fetchone():
            return None
        cur.execute("SELECT version_num FROM alembic_version LIMIT 1")
        row = cur.fetchone()
        return row[0] if row and row[0] else None
    finally:
        conn.close()


def sync_alembic_revision(engine: Engine, database_url: str) -> str:
    validation = validate_schema_strict(engine)
    if not validation.is_valid:
        raise SchemaRepairError(
            "No se puede hacer stamp: esquema no válido",
            validation=validation,
        )

    import os
    from alembic.config import Config
    from alembic import command

    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", database_url)

    db_path = Path(database_url.removeprefix("sqlite:///"))
    current = get_alembic_revision(db_path)
    if current == HEAD_REVISION:
        return HEAD_REVISION

    prev_env = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = database_url
    try:
        command.stamp(cfg, HEAD_REVISION)
    finally:
        if prev_env is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = prev_env

    stamped = get_alembic_revision(db_path)
    if stamped != HEAD_REVISION:
        raise SchemaRepairError(f"Stamp falló: esperado {HEAD_REVISION}, actual {stamped}")
    return HEAD_REVISION


def repair_database(database_url: str, *, skip_backup: bool = False) -> dict[str, Any]:
    """Delega en preparación de BD (CURSOR-805D): preservar legacy o crear actual."""
    from scripts.db_startup import prepare_database

    _ = skip_backup
    return prepare_database(database_url)


def database_url_to_path(database_url: str) -> Path:
    return Path(database_url.removeprefix("sqlite:///"))
