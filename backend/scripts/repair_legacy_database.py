#!/usr/bin/env python3
"""CLI — migración SQLite legacy EMPLEADOS_IA (CURSOR-805C)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings  # noqa: E402
from scripts.legacy_migration import (  # noqa: E402
    LegacyMigrationError,
    detect_db_scenario,
    database_url_to_path,
    inventory_legacy_db,
    migrate_legacy_database,
)
from scripts.schema_repair import validate_schema_strict  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402


def cmd_audit(database_url: str) -> int:
    db_path = database_url_to_path(database_url)
    scenario = detect_db_scenario(db_path)
    engine = create_engine(database_url, connect_args={"check_same_thread": False}) if db_path.exists() else None
    validation = validate_schema_strict(engine) if engine else None
    output = {
        "scenario": scenario,
        "inventory": inventory_legacy_db(db_path) if db_path.exists() else {},
        "validation": validation.to_dict() if validation else None,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))
    if scenario == "E":
        return 1
    if validation and not validation.is_valid and scenario == "C":
        return 1
    return 0


def cmd_migrate(database_url: str, skip_backup: bool, no_swap: bool) -> int:
    try:
        result = migrate_legacy_database(
            database_url,
            skip_backup=skip_backup,
            perform_swap=not no_swap,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except LegacyMigrationError as exc:
        payload = {"error": str(exc)}
        if exc.validation:
            payload["validation"] = exc.validation.to_dict()
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 2


def cmd_scenario(database_url: str) -> int:
    scenario = detect_db_scenario(database_url_to_path(database_url))
    print(json.dumps({"scenario": scenario}))
    return 0 if scenario != "E" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Migración SQLite legacy EMPLEADOS_IA")
    parser.add_argument("command", choices=["audit", "migrate", "scenario", "repair"], help="comando")
    parser.add_argument("--database-url", default=settings.database_url)
    parser.add_argument("--skip-backup", action="store_true")
    parser.add_argument("--no-swap", action="store_true", help="No hacer swap atómico (tests)")
    args = parser.parse_args()
    if args.command == "audit":
        return cmd_audit(args.database_url)
    if args.command == "scenario":
        return cmd_scenario(args.database_url)
    return cmd_migrate(args.database_url, args.skip_backup, args.no_swap)


if __name__ == "__main__":
    raise SystemExit(main())
