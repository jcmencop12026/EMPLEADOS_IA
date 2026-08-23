#!/usr/bin/env python3
"""CLI — reparación SQLite legacy EMPLEADOS_IA (CURSOR-805)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings  # noqa: E402
from scripts.schema_repair import audit_schema, repair_database  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402


def _diff_to_dict(diff) -> dict:
    return {
        "missing_tables": diff.missing_tables,
        "extra_tables": diff.extra_tables,
        "missing_columns": diff.missing_columns,
        "extra_columns": diff.extra_columns,
        "satisfied": diff.is_satisfied,
    }


def cmd_audit(database_url: str) -> int:
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    diff = audit_schema(engine)
    print(json.dumps(_diff_to_dict(diff), indent=2, ensure_ascii=False))
    return 0 if diff.is_satisfied else 1


def cmd_repair(database_url: str) -> int:
    result = repair_database(database_url)
    output = {
        "before": _diff_to_dict(result["before"]),
        "after_repair": _diff_to_dict(result["after_repair"]),
        "after": _diff_to_dict(result["after"]),
        "alembic_revision": result["alembic_revision"],
        "timestamp": result["timestamp"],
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0 if result["after"].is_satisfied else 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Reparación SQLite legacy EMPLEADOS_IA")
    parser.add_argument("command", choices=["audit", "repair"], help="audit o repair")
    parser.add_argument("--database-url", default=settings.database_url, help="URL SQLAlchemy")
    args = parser.parse_args()
    if args.command == "audit":
        return cmd_audit(args.database_url)
    return cmd_repair(args.database_url)


if __name__ == "__main__":
    raise SystemExit(main())
