#!/usr/bin/env python3
"""Orquestador de arranque/parada multiplataforma para BAT (CURSOR-805B)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings  # noqa: E402
from scripts.repair_legacy_database import cmd_audit, cmd_repair  # noqa: E402
from scripts.schema_repair import HEAD_REVISION, get_alembic_revision, database_url_to_path  # noqa: E402
from scripts.service_manager import (  # noqa: E402
    load_pid_registry,
    save_pid_registry,
    start_backend,
    start_frontend,
    stop_registered_services,
    wait_for_health,
)


def cmd_prepare(database_url: str) -> int:
    """Auditar BD; reparar si es reparable; verificar Alembic."""
    audit_code = cmd_audit(database_url)
    if audit_code == 0:
        db_path = database_url_to_path(database_url)
        if db_path.exists() and get_alembic_revision(db_path) == HEAD_REVISION:
            print(json.dumps({"status": "ok", "action": "none"}))
            return 0

    repair_code = cmd_repair(database_url, skip_backup=False)
    if repair_code != 0:
        return repair_code

    audit_after = cmd_audit(database_url)
    if audit_after != 0:
        return audit_after

    db_path = database_url_to_path(database_url)
    if get_alembic_revision(db_path) != HEAD_REVISION:
        print(json.dumps({"error": "Alembic no en head tras reparación"}))
        return 3
    print(json.dumps({"status": "ok", "action": "repaired"}))
    return 0


def cmd_start(database_url: str, backend_port: int, frontend_port: int) -> int:
    prep = cmd_prepare(database_url)
    if prep != 0:
        return prep

    stop_registered_services()

    backend = start_backend(port=backend_port, database_url=database_url)
    if not wait_for_health(f"http://127.0.0.1:{backend_port}/health"):
        print(json.dumps({"error": "Backend /health no respondió HTTP 200"}))
        return 4

    frontend = start_frontend(port=frontend_port)
    if not wait_for_health(f"http://127.0.0.1:{frontend_port}/", timeout_sec=45):
        print(json.dumps({"error": "Frontend no respondió HTTP 200"}))
        return 5

    registry = {
        "backend": backend,
        "frontend": frontend,
        "database_url": database_url,
    }
    pid_path = save_pid_registry(registry)
    print(json.dumps({
        "status": "ok",
        "backend_url": f"http://127.0.0.1:{backend_port}",
        "frontend_url": f"http://127.0.0.1:{frontend_port}",
        "pid_file": str(pid_path),
    }))
    return 0


def cmd_stop() -> int:
    result = stop_registered_services()
    print(json.dumps(result, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare", "start", "stop", "status"])
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
    print(json.dumps(load_pid_registry(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
