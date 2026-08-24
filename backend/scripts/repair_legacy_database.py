#!/usr/bin/env python3
"""CLI — preservación e inventario SQLite legacy EMPLEADOS_IA (CURSOR-805D)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings  # noqa: E402
from scripts.db_startup import (  # noqa: E402
    DbStartupError,
    detect_db_scenario,
    database_url_to_path,
    prepare_database,
)
from scripts.legacy_preservation import build_full_inventory, preserve_legacy_database  # noqa: E402
from scripts.schema_repair import validate_schema_strict  # noqa: E402
from scripts.sqlite_lifecycle import release_all_sqlite_handles, sqlite_engine  # noqa: E402


def cmd_audit(database_url: str) -> int:
    db_path = database_url_to_path(database_url)
    scenario = detect_db_scenario(db_path)
    if db_path.exists():
        with sqlite_engine(db_path) as engine:
            validation = validate_schema_strict(engine)
    else:
        validation = None
    inventory = build_full_inventory(db_path) if db_path.exists() else {"tables": [], "summary": {}}
    output = {
        "scenario": scenario,
        "inventory": inventory,
        "validation": validation.to_dict() if validation else None,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 1 if scenario == "D" else 0


def cmd_preserve(database_url: str) -> int:
    db_path = database_url_to_path(database_url)
    try:
        report = preserve_legacy_database(db_path, data_dir=db_path.parent)
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
        return 0
    except DbStartupError as exc:
        print(json.dumps({"error": str(exc)}))
        return 2


def cmd_prepare(database_url: str) -> int:
    try:
        result = prepare_database(database_url)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except DbStartupError as exc:
        payload = {"error": str(exc)}
        if exc.validation:
            payload["validation"] = exc.validation.to_dict()
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 2


def cmd_scenario(database_url: str) -> int:
    scenario = detect_db_scenario(database_url_to_path(database_url))
    print(json.dumps({"scenario": scenario}))
    return 0 if scenario != "D" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Preservación SQLite legacy EMPLEADOS_IA")
    parser.add_argument("command", choices=["audit", "preserve", "prepare", "scenario", "repair"])
    parser.add_argument("--database-url", default=settings.database_url)
    args = parser.parse_args()
    if args.command == "audit":
        return cmd_audit(args.database_url)
    if args.command == "preserve":
        return cmd_preserve(args.database_url)
    if args.command == "scenario":
        return cmd_scenario(args.database_url)
    return cmd_prepare(args.database_url)


if __name__ == "__main__":
    raise SystemExit(main())
