"""Reparación idempotente de SQLite legacy para EMPLEADOS_IA (CURSOR-805)."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.types import TypeEngine

from app.database import Base
from app import models  # noqa: F401
from app import orchestration_models  # noqa: F401

HEAD_REVISION = "5b2eb2437398"
REV_801 = "4355c73adcb8"

_TYPE_MAP: dict[type[TypeEngine], str] = {
    String: "VARCHAR",
    Text: "TEXT",
    Boolean: "BOOLEAN",
    Integer: "INTEGER",
    Float: "FLOAT",
    DateTime: "DATETIME",
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


def audit_schema(engine: Engine) -> SchemaDiff:
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


def _sqlite_type(col) -> str:
    for py_type, sql_type in _TYPE_MAP.items():
        if isinstance(col.type, py_type):
            if isinstance(col.type, String) and col.type.length:
                return f"VARCHAR({col.type.length})"
            return sql_type
    return "TEXT"


def _default_sql(col) -> str | None:
    if col.name == "requires_approval":
        return "0"
    if col.name == "code":
        return "'emp-temp'"
        return "0"
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
        return "CURRENT_TIMESTAMP"
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
    sql_type = _sqlite_type(col)
    default = _default_sql(col)
    nullable = col.nullable
    parts = [f"ALTER TABLE {table} ADD COLUMN {col.name} {sql_type}"]
    if not nullable:
        if default is None:
            default = "''" if isinstance(col.type, (String, Text)) else "0"
        parts.append(f"NOT NULL DEFAULT {default}")
    elif default is not None:
        parts.append(f"DEFAULT {default}")
    conn.execute(text(" ".join(parts)))


def _backfill_ai_employees(conn) -> None:
    conn.execute(text("UPDATE ai_employees SET code = 'emp-' || substr(id, 1, 8) WHERE code IS NULL OR code = ''"))
    conn.execute(text("UPDATE ai_employees SET lifecycle_status = 'ACTIVE' WHERE lifecycle_status IS NULL OR lifecycle_status = ''"))
    conn.execute(text("UPDATE ai_employees SET maturity = 'AUTONOMOUS_CONTROLLED' WHERE maturity IS NULL OR maturity = ''"))
    conn.execute(text("UPDATE ai_employees SET risk_level = 'LOW' WHERE risk_level IS NULL OR risk_level = ''"))
    conn.execute(text("UPDATE ai_employees SET version = 1 WHERE version IS NULL"))
    conn.execute(text("UPDATE ai_employees SET shadow_mode = 0 WHERE shadow_mode IS NULL"))
    conn.execute(text("UPDATE ai_employees SET updated_at = created_at WHERE updated_at IS NULL OR updated_at = 0 OR updated_at = '0'"))


def _backfill_capabilities(conn) -> None:
    conn.execute(text("UPDATE capabilities SET requires_approval = 0 WHERE requires_approval IS NULL"))
    conn.execute(text("UPDATE tools SET requires_approval = 0 WHERE requires_approval IS NULL"))


def _ensure_indexes(engine: Engine) -> None:
    """Crea índices definidos en metadata si faltan (idempotente vía IF NOT EXISTS)."""
    with engine.begin() as conn:
        for table_name, table in Base.metadata.tables.items():
            for idx in table.indexes:
                cols = ", ".join(c.name for c in idx.columns)
                unique = "UNIQUE " if idx.unique else ""
                name = idx.name or f"ix_{table_name}_{cols.replace(', ', '_')}"
                conn.execute(text(f"CREATE {unique}INDEX IF NOT EXISTS {name} ON {table_name} ({cols})"))


def repair_schema(engine: Engine) -> SchemaDiff:
    """Aplica reparación idempotente hasta satisfacer metadata actual."""
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

        _backfill_capabilities(conn)
        _backfill_ai_employees(conn)

    _ensure_indexes(engine)
    return audit_schema(engine)


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


def detect_legacy_revision(engine: Engine) -> str | None:
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    if "organizations" not in tables:
        return None
    if "work_plans" not in tables:
        return None
    if "employee_templates" not in tables:
        return REV_801
    return HEAD_REVISION


def sync_alembic_revision(engine: Engine, database_url: str) -> str:
    """Sincroniza alembic_version tras verificar esquema. Retorna revisión final."""
    diff = audit_schema(engine)
    if not diff.is_satisfied:
        missing = {
            "tables": diff.missing_tables,
            "columns": diff.missing_columns,
        }
        raise RuntimeError(f"Esquema incompleto tras reparación: {json.dumps(missing, ensure_ascii=False)}")

    from alembic.config import Config
    from alembic import command

    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", database_url)

    db_path = database_url.removeprefix("sqlite:///")
    current = get_alembic_revision(Path(db_path))
    if current == HEAD_REVISION:
        return HEAD_REVISION

    # Esquema ya reparado idempotentemente: registrar head sin re-ejecutar DDL de migraciones.
    command.stamp(cfg, HEAD_REVISION)
    return HEAD_REVISION


def repair_database(database_url: str) -> dict[str, Any]:
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    before = audit_schema(engine)
    after_repair = repair_schema(engine)
    final_revision = sync_alembic_revision(engine, database_url)
    after = audit_schema(engine)
    return {
        "before": before,
        "after_repair": after_repair,
        "after": after,
        "alembic_revision": final_revision,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
