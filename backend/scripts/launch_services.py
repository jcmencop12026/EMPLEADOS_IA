#!/usr/bin/env python3
"""Orquestador de arranque/parada multiplataforma para BAT (CURSOR-805C)."""
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
    HEAD_REVISION,
    detect_db_scenario,
    migrate_legacy_database,
    database_url_to_path,
)
from scripts.schema_repair import validate_schema_strict  # noqa: E402
from scripts.service_manager import (  # noqa: E402
    load_pid_registry,
    save_pid_registry,
    start_backend,
    start_frontend,
    stop_registered_services,
    wait_for_health,
)
from sqlalchemy import create_engine  # noqa: E402


def cmd_prepare(database_url: str) -> int:
    """Identificar escenario DB y migrar sólo si corresponde."""
    db_path = database_url_to_path(database_url)
    scenario = detect_db_scenario(db_path)
    print(json.dumps({"scenario": scenario}))

    if scenario in ("A", "B", "D"):
        try:
            result = migrate_legacy_database(database_url, skip_backup=(scenario == "A"))
            print(json.dumps({"status": "ok", "action": "migrated", "result": result}))
            return 0
        except Exception as exc:
            print(json.dumps({"error": str(exc)}))
            return 2

    if scenario == "C":
        print(json.dumps({"status": "ok", "action": "none"}))
        return 0

    print(json.dumps({"error": "BD incompatible/no migrable"}))
    return 3


def cmd_start(database_url: str, backend_port: int, frontend_port: int) -> int:
    prep = cmd_prepare(database_url)
    if prep != 0:
        return prep

    stop_registered_services()
    registry: dict = {"database_url": database_url}

    try:
        backend = start_backend(port=backend_port, database_url=database_url)
        registry["backend"] = backend
        save_pid_registry(registry)

        if not wait_for_health(f"http://127.0.0.1:{backend_port}/health"):
            stop_registered_services()
            print(json.dumps({"error": "Backend /health no respondió HTTP 200"}))
            return 4

        frontend = start_frontend(port=frontend_port)
        registry["frontend"] = frontend
        save_pid_registry(registry)

        if not wait_for_health(f"http://127.0.0.1:{frontend_port}/", timeout_sec=45):
            stop_registered_services()
            print(json.dumps({"error": "Frontend no respondió HTTP 200"}))
            return 5

        pid_path = save_pid_registry(registry)
        print(json.dumps({
            "status": "ok",
            "backend_url": f"http://127.0.0.1:{backend_port}",
            "frontend_url": f"http://127.0.0.1:{frontend_port}",
            "pid_file": str(pid_path),
        }))
        return 0
    except Exception as exc:
        stop_registered_services()
        print(json.dumps({"error": str(exc)}))
        return 6


def cmd_stop() -> int:
    result = stop_registered_services()
    print(json.dumps(result, indent=2))
    return 0


def cmd_scenario(database_url: str) -> int:
    scenario = detect_db_scenario(database_url_to_path(database_url))
    print(json.dumps({"scenario": scenario}))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare", "start", "stop", "status", "scenario"])
    parser.add_argument("--database-url", default=settings.database_url)
    parser.add_argument("--backend-port", type=int, default=8010)
    parser.add_argument("--frontend-port", type=int, default=5180)
    args = parser.parse_args()

    if args.command == "prepare":
        return cmd_prepare(args.database_url)
    if args.command == "start":
        return cmd_start(args.database_url, args.backend_port, args.frontend_port)
    if args.command == "stop":
        return cmd_stop()
    if args.command == "scenario":
        return cmd_scenario(args.database_url)
    print(json.dumps(load_pid_registry(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
