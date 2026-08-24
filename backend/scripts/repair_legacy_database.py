#!/usr/bin/env python3
"""CLI — reparación SQLite legacy EMPLEADOS_IA (CURSOR-805/805B)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings  # noqa: E402
from scripts.schema_repair import (  # noqa: E402
    SchemaRepairError,
    audit_schema,
    create_verified_backup,
    repair_database,
    validate_schema_strict,
    verify_backup_file,
)
from sqlalchemy import create_engine  # noqa: E402


def cmd_audit(database_url: str) -> int:
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    validation = validate_schema_strict(engine)
    diff = audit_schema(engine)
    output = {
        "validation": validation.to_dict(),
        "summary": {
            "missing_tables": diff.missing_tables,
            "missing_columns": diff.missing_columns,
            "extra_columns": diff.extra_columns,
        },
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0 if validation.is_valid else 1


def cmd_repair(database_url: str, skip_backup: bool) -> int:
    try:
        result = repair_database(database_url, skip_backup=skip_backup)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except SchemaRepairError as exc:
        payload = {"error": str(exc)}
        if exc.validation:
            payload["validation"] = exc.validation.to_dict()
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 2


def cmd_backup(database_url: str) -> int:
    db_path = Path(database_url.removeprefix("sqlite:///"))
    backup_path = create_verified_backup(db_path)
    info = verify_backup_file(backup_path, db_path)
    print(json.dumps(info, indent=2, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Reparación SQLite legacy EMPLEADOS_IA")
    parser.add_argument("command", choices=["audit", "repair", "backup"], help="audit, repair o backup")
    parser.add_argument("--database-url", default=settings.database_url, help="URL SQLAlchemy")
    parser.add_argument("--skip-backup", action="store_true", help="Omitir backup (solo tests)")
    args = parser.parse_args()
    if args.command == "audit":
        return cmd_audit(args.database_url)
    if args.command == "backup":
        return cmd_backup(args.database_url)
    return cmd_repair(args.database_url, skip_backup=args.skip_backup)


if __name__ == "__main__":
    raise SystemExit(main())
