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

from sqlalchemy import Boolean, DateTime, Float, Integer, LargeBinary, String, Text, create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.types import Numeric, TypeEngine

from app.database import Base
from app import automation_models  # noqa: F401
from app import models  # noqa: F401
from app import orchestration_models  # noqa: F401
from app import finops_models  # noqa: F401
from app import opportunity_models  # noqa: F401

HEAD_REVISION = "1770a1b2c3d4e"
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
    LargeBinary: "BLOB",
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


@dataclass
class SchemaDiff:
    missing_tables: list[str] = field(default_factory=list)
    missing_columns: dict[str, list[str]] = field(default_factory=dict)
    missing_indexes: dict[str, list[str]] = field(default_factory=dict)
    issues: list[SchemaIssue] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return not self.missing_tables and not self.missing_columns and not self.missing_indexes and not self.issues


def _sqlite_columns(conn: Any, table_name: str) -> dict[str, dict[str, Any]]:
    rows = conn.execute(text(f"PRAGMA table_info({table_name})")).mappings().all()
    return {str(row["name"]): dict(row) for row in rows}


def _sqlite_indexes(conn: Any, table_name: str) -> dict[str, tuple[str, ...]]:
    result: dict[str, tuple[str, ...]] = {}
    for idx in conn.execute(text(f"PRAGMA index_list({table_name})")).mappings().all():
        idx_name = str(idx["name"])
        cols = conn.execute(text(f"PRAGMA index_info({idx_name})")).mappings().all()
        result[idx_name] = tuple(str(row["name"]) for row in cols)
    return result


def _sqlite_foreign_keys(conn: Any, table_name: str) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute(text(f"PRAGMA foreign_key_list({table_name})")).mappings().all()]


def _column_sql_type(column: Any) -> str:
    for cls, sql_type in _TYPE_MAP.items():
        if isinstance(column.type, cls):
            return sql_type
    return "TEXT"


def _column_default_sql(column: Any) -> str | None:
    default = getattr(column, "server_default", None)
    if default is None:
        return None
    arg = getattr(default, "arg", None)
    if arg is None:
        return None
    return str(arg)


def _create_missing_table(conn: Any, table: Any) -> None:
    table.create(bind=conn, checkfirst=True)


def _add_missing_column(conn: Any, table_name: str, column: Any) -> None:
    sql_type = _column_sql_type(column)
    nullable = "" if column.nullable else " NOT NULL"
    default_sql = _column_default_sql(column)
    default_clause = f" DEFAULT {default_sql}" if default_sql else ""
    if not column.nullable and default_sql is None:
        nullable = ""
    conn.execute(text(f'ALTER TABLE "{table_name}" ADD COLUMN "{column.name}" {sql_type}{default_clause}{nullable}'))


def validate_schema_strict(engine: Engine) -> SchemaValidationResult:
    result = SchemaValidationResult()
    metadata = Base.metadata

    with engine.begin() as conn:
        db_tables = set(inspect(conn).get_table_names())
        for table_name, table in metadata.tables.items():
            if table_name not in db_tables:
                result.issues.append(SchemaIssue(
                    category="missing_table",
                    table=table_name,
                    name=table_name,
                    message="Tabla requerida ausente",
                    repairable=True,
                ))
                continue

            db_cols = _sqlite_columns(conn, table_name)
            model_col_names = {c.name for c in table.columns}
            for col in table.columns:
                if col.name not in db_cols:
                    result.issues.append(SchemaIssue(
                        category="missing_column",
                        table=table_name,
                        name=col.name,
                        message="Columna requerida ausente",
                        repairable=True,
                    ))

            for col in table.columns:
                if col.unique and col.name in db_cols:
                    idx_name = f"uq_{table_name}_{col.name}"
                    indexes = _sqlite_indexes(conn, table_name)
                    if not any(col.name in idx for idx in indexes) and idx_name not in indexes:
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
    result = SchemaDiff()
    metadata = Base.metadata

    with engine.begin() as conn:
        db_tables = set(inspect(conn).get_table_names())
        for table_name, table in metadata.tables.items():
            if table_name not in db_tables:
                result.missing_tables.append(table_name)
                continue

            db_cols = _sqlite_columns(conn, table_name)
            model_col_names = {c.name for c in table.columns}
            missing = [c.name for c in table.columns if c.name not in db_cols]
            if missing:
                result.missing_columns[table_name] = missing

            existing_indexes = _sqlite_indexes(conn, table_name)
            missing_indexes = [idx.name for idx in table.indexes if idx.name and idx.name not in existing_indexes]
            if missing_indexes:
                result.missing_indexes[table_name] = missing_indexes

            for extra in sorted(set(db_cols) - model_col_names):
                info = db_cols[extra]
                legacy_known = extra in LEGACY_EXTRA_COLUMNS.get(table_name, [])
                if not legacy_known:
                    result.issues.append(SchemaIssue(
                        category="extra_column",
                        table=table_name,
                        name=extra,
                        message="Columna extra presente",
                        repairable=True,
                    ))
    return result


def repair_schema(engine: Engine) -> SchemaDiff:
    diff = audit_schema(engine)
    metadata = Base.metadata

    with engine.begin() as conn:
        for table_name in diff.missing_tables:
            table = metadata.tables.get(table_name)
            if table is not None:
                _create_missing_table(conn, table)

        for table_name, columns in diff.missing_columns.items():
            table = metadata.tables[table_name]
            for col_name in columns:
                _add_missing_column(conn, table_name, table.columns[col_name])

        for table_name, indexes in diff.missing_indexes.items():
            table = metadata.tables[table_name]
            for idx in table.indexes:
                if idx.name in indexes:
                    idx.create(bind=conn, checkfirst=True)

    return audit_schema(engine)


def backup_sqlite(db_path: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest = hashlib.sha256(db_path.read_bytes()).hexdigest()[:12] if db_path.exists() else "vacia"
    destination = backup_dir / f"{db_path.stem}_{timestamp}_{digest}{db_path.suffix}"
    if db_path.exists():
        shutil.copy2(db_path, destination)
    return destination


def write_validation_report(path: Path, validation: SchemaValidationResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "is_valid": validation.is_valid,
        "issues": [issue.to_dict() for issue in validation.issues],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
