"""Diagnóstico de salud V1 — API, PostgreSQL y schedulers."""
from __future__ import annotations

from typing import Any, Literal

from pathlib import Path

from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.services.automation_scheduler import is_scheduler_running as automation_scheduler_running
from app.services.proactive_scheduler import is_scheduler_running as proactive_scheduler_running

HealthStatus = Literal["up", "degraded", "down"]


def _db_dialect() -> str:
    url = settings.database_url.lower()
    if url.startswith("postgresql"):
        return "postgresql"
    if url.startswith("sqlite"):
        return "sqlite"
    return "other"


def check_database() -> dict[str, Any]:
    dialect = _db_dialect()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "status": "up",
            "dialect": dialect,
            "message": "Base de datos accesible",
        }
    except Exception:
        return {
            "status": "down",
            "dialect": dialect,
            "message": "Base de datos no disponible",
        }


def check_schedulers() -> dict[str, Any]:
    automation = automation_scheduler_running()
    proactive = proactive_scheduler_running()
    if automation and proactive:
        status: HealthStatus = "up"
        message = "Schedulers activos"
    elif automation or proactive:
        status = "degraded"
        message = "Uno o más schedulers inactivos"
    else:
        status = "down"
        message = "Schedulers no activos"
    return {
        "status": status,
        "automation_scheduler": "up" if automation else "down",
        "proactive_scheduler": "up" if proactive else "down",
        "message": message,
    }


def aggregate_status(components: dict[str, dict[str, Any]]) -> HealthStatus:
    statuses = [c.get("status", "down") for c in components.values()]
    if all(s == "up" for s in statuses):
        return "up"
    if any(s == "down" for s in statuses):
        if components.get("database", {}).get("status") == "down":
            return "degraded"
        return "degraded"
    return "degraded"


def build_runtime_identity() -> dict[str, Any]:
    """Identidad tecnica de instancia demo — sin secretos."""
    identity: dict[str, Any] = {
        "demo_profile": settings.eiaax_demo_profile,
        "git_sha": settings.eiaax_git_sha,
        "runtime_marker": settings.eiaax_runtime_marker,
    }
    db = check_database()
    identity["database_dialect"] = db.get("dialect")
    if db.get("dialect") == "sqlite":
        try:
            db_path = settings.database_url.split("///", 1)[-1]
            identity["demo_db_name"] = Path(db_path).name
        except Exception:
            pass
    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).first()
        if row and row[0]:
            identity["alembic_current"] = row[0]
    except Exception:
        identity["alembic_current"] = None
    return identity


def build_health_report(*, include_schedulers: bool = True) -> dict[str, Any]:
    components: dict[str, dict[str, Any]] = {
        "api": {"status": "up", "message": "Proceso API en ejecución"},
        "database": check_database(),
    }
    if include_schedulers:
        components["schedulers"] = check_schedulers()

    status = aggregate_status(components)
    report: dict[str, Any] = {
        "status": status,
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "components": components,
    }
    runtime = build_runtime_identity()
    if any(runtime.get(k) for k in ("demo_profile", "git_sha", "runtime_marker", "alembic_current")):
        report["runtime"] = runtime
    return report


def health_http_status(report: dict[str, Any]) -> int:
    status = report.get("status", "down")
    if status == "up":
        return 200
    if status == "degraded":
        return 503
    return 503
