"""MIGRATIONS-CONTROL-001 — preflight, ledger y gobierno de revisiones Alembic."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, inspect as sa_inspect, text
from sqlalchemy.engine import Engine

_LEDGER_PATH = Path(__file__).resolve().parents[1] / "alembic" / "migration_ledger.json"
_VERSIONS_DIR = Path(__file__).resolve().parents[1] / "alembic" / "versions"
_REVISION_FILE_RE = re.compile(r"^([0-9a-f]+)_.+\.py$", re.IGNORECASE)

INCOMPATIBLE_DB_MESSAGE = (
    "Base de datos incompatible con esta versión de la aplicación. "
    "La revisión Alembic persistida no pertenece a la historia actual del repositorio. "
    "Restaure un respaldo certificado o cree una base limpia con 'alembic upgrade head'."
)


class MigrationControlError(RuntimeError):
    """Error de gobierno de migraciones — fail-closed."""


def load_migration_ledger() -> dict[str, Any]:
    if not _LEDGER_PATH.exists():
        raise MigrationControlError(f"Ledger de migraciones no encontrado: {_LEDGER_PATH}")
    return json.loads(_LEDGER_PATH.read_text(encoding="utf-8"))


def revisions_in_repository() -> set[str]:
    revisions: set[str] = set()
    for path in _VERSIONS_DIR.glob("*.py"):
        match = _REVISION_FILE_RE.match(path.name)
        if match:
            revisions.add(match.group(1))
    return revisions


def validate_migration_ledger() -> dict[str, Any]:
    """Falla si una revisión protegida desaparece del repositorio."""
    ledger = load_migration_ledger()
    protected = set(ledger.get("protected_revisions") or [])
    present = revisions_in_repository()
    missing = sorted(protected - present)
    if missing:
        raise MigrationControlError(
            f"Revisiones protegidas ausentes del repositorio: {', '.join(missing)}"
        )
    heads = get_alembic_heads()
    if len(heads) != 1:
        raise MigrationControlError(f"Se esperaba un solo head Alembic, encontrados: {heads}")
    head = heads[0]
    baseline_head = ledger.get("baseline_head")
    if baseline_head and head != baseline_head:
        raise MigrationControlError(
            f"Head actual ({head}) no coincide con baseline_head del ledger ({baseline_head})"
        )
    return {
        "head": head,
        "protected_count": len(protected),
        "repository_revision_count": len(present),
        "ledger_path": str(_LEDGER_PATH),
    }


def get_alembic_heads() -> list[str]:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    script = ScriptDirectory.from_config(cfg)
    return list(script.get_heads())


def get_database_revision(engine: Engine) -> str | None:
    insp = sa_inspect(engine)
    if "alembic_version" not in insp.get_table_names():
        return None
    with engine.connect() as conn:
        row = conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).first()
    return row[0] if row and row[0] else None


def _critical_schema_present(engine: Engine) -> bool:
    insp = sa_inspect(engine)
    tables = set(insp.get_table_names())
    required = {"organizations", "users", "alembic_version"}
    return required.issubset(tables)


def run_database_preflight(database_url: str) -> dict[str, Any]:
    """
    Valida BD antes de bootstrap/seed.

    - Sin alembic_version: OK (instalación limpia / create_all dev).
    - Revisión desconocida u huérfana: ABORT fail-closed.
    - Revisión conocida: OK si schema crítico presente.
    """
    ledger = load_migration_ledger()
    known = revisions_in_repository()
    protected = set(ledger.get("protected_revisions") or [])

    engine = create_engine(database_url)
    try:
        revision = get_database_revision(engine)
        if revision is None:
            return {
                "status": "no_alembic_version",
                "message": "Sin tabla alembic_version — instalación nueva o create_all.",
            }

        if revision not in known:
            raise MigrationControlError(INCOMPATIBLE_DB_MESSAGE + f" (revisión: {revision})")

        if revision not in protected:
            raise MigrationControlError(
                INCOMPATIBLE_DB_MESSAGE + f" (revisión no certificada: {revision})"
            )

        if not _critical_schema_present(engine):
            raise MigrationControlError(
                "Base de datos incompatible con esta versión: esquema crítico incompleto "
                f"(revisión {revision})."
            )

        heads = get_alembic_heads()
        if len(heads) != 1:
            raise MigrationControlError(f"Múltiples heads Alembic en código: {heads}")

        return {
            "status": "ok",
            "revision": revision,
            "head": heads[0],
            "certified": revision in protected,
        }
    finally:
        engine.dispose()


def assert_single_head() -> str:
    heads = get_alembic_heads()
    if len(heads) != 1:
        raise MigrationControlError(f"alembic heads debe devolver uno solo; actual: {heads}")
    return heads[0]
