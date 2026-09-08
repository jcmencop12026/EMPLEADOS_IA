#!/usr/bin/env python3
"""Seed E2E — Clínica Demo Horizonte (DEMO — DATOS SIMULADOS).

Prepara base demo con organización operadora, usuario admin y expediente
coherente para recorrido comercial: facturación, radicación y auditoría documental.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
DATA_DIR = REPO_ROOT / "data"

DEFAULT_DATABASE_URL = f"sqlite:///{(DATA_DIR / 'eiaax_horizonte_demo.db').as_posix()}"
os.environ.setdefault("DATABASE_URL", DEFAULT_DATABASE_URL)
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import automation_models  # noqa: F401, E402
from app import baseline_models  # noqa: F401, E402
from app import commercial_models  # noqa: F401, E402
from app import communications_models  # noqa: F401, E402
from app import consumption_planner_models  # noqa: F401, E402
from app import continuidad_comercial_models  # noqa: F401, E402
from app import continuidad_models  # noqa: F401, E402
from app import diagnostic_models  # noqa: F401, E402
from app import economic_motor_models  # noqa: F401, E402
from app import employee_audit_models  # noqa: F401, E402
from app import empresa_seguridad_models  # noqa: F401, E402
from app import evaluacion_models  # noqa: F401, E402
from app import experience_models  # noqa: F401, E402
from app import external_models  # noqa: F401, E402
from app import finops_models  # noqa: F401, E402
from app import flujo_comercial_models  # noqa: F401, E402
from app import gobierno_operacional_models  # noqa: F401, E402
from app import governance_models  # noqa: F401, E402
from app import identity_models  # noqa: F401, E402
from app import implementacion_models  # noqa: F401, E402
from app import integration_models  # noqa: F401, E402
from app import knowledge_models  # noqa: F401, E402
from app import learning_models  # noqa: F401, E402
from app import llm_models  # noqa: F401, E402
from app import models  # noqa: F401, E402
from app import negocio_models  # noqa: F401, E402
from app import notifications  # noqa: F401, E402
from app import opportunity_models  # noqa: F401, E402
from app import orchestration_models  # noqa: F401, E402
from app import partner_models  # noqa: F401, E402
from app import presentacion_models  # noqa: F401, E402
from app import resultados_models  # noqa: F401, E402
from app import salud_models  # noqa: F401, E402
from app import scim_models  # noqa: F401, E402
from app import security_models  # noqa: F401, E402
from app import segmentation_models  # noqa: F401, E402
from app import support_models  # noqa: F401, E402
from app import tco_models  # noqa: F401, E402
from app import transformacion_models  # noqa: F401, E402
from app import valuation_models  # noqa: F401, E402
from app import espacio_externo_models  # noqa: F401, E402

from app.database import SessionLocal  # noqa: E402
from app.demo_comercial_constants import DEMO_EMPRESA_FICTICIA  # noqa: E402
from app.models import Organization, User  # noqa: E402
from app.security import hash_password  # noqa: E402
from app.seed_orchestration import bootstrap_orchestration  # noqa: E402
from app.seed_permissions import bootstrap_permissions  # noqa: E402
from app.seed_salud import bootstrap_salud  # noqa: E402
from app.services import demo_comercial_service as demo_svc  # noqa: E402
from app.services import gobierno_operacional_service as gob_svc  # noqa: E402
from app.services import admin_service as admin_svc  # noqa: E402
from app.cert_branding import CERT_BRANDING_CONFIG  # noqa: E402
from scripts.sqlite_lifecycle import database_url_to_path, safe_unlink_sqlite  # noqa: E402

HORIZONTE_ORG = {
    "name": "EIAAX Operador Demo",
    "slug": "eiaax-operador-demo",
    "admin_username": "admin",
    "admin_password": "Admin2026!",
}


def _prepare_database(database_url: str) -> None:
    from alembic import command
    from alembic.config import Config

    db_path = database_url_to_path(database_url)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        safe_unlink_sqlite(db_path, database_url)
    alembic_cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_cfg, "head")


def main() -> int:
    database_url = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    print(f"Preparando demo Clínica Demo Horizonte: {database_url}", flush=True)
    _prepare_database(database_url)

    db = SessionLocal()
    try:
        bootstrap_permissions(db)
        org = Organization(name=HORIZONTE_ORG["name"], slug=HORIZONTE_ORG["slug"], status="ACTIVE")
        db.add(org)
        db.flush()
        bootstrap_orchestration(db, org.id, commit=False)
        bootstrap_salud(db, org.id, commit=False)
        gob_svc.ensure_default_policies(db, org.id)
        gob_svc.ensure_default_ia_policy(db, org.id)

        admin = User(
            organization_id=org.id,
            username=HORIZONTE_ORG["admin_username"],
            password_hash=hash_password(HORIZONTE_ORG["admin_password"]),
            role="admin",
            status="ACTIVE",
            is_active=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        admin_svc.update_org_config(
            db,
            org=org,
            actor_id=admin.id,
            config=CERT_BRANDING_CONFIG,
        )

        manifest = demo_svc.seed_demo_comercial(db, org.id, admin.id)

        summary: dict[str, Any] = {
            "status": "ok",
            "etiqueta": "DEMO — DATOS SIMULADOS",
            "empresa": DEMO_EMPRESA_FICTICIA,
            "database_url": database_url,
            "organization_id": org.id,
            "credentials": {
                "username": HORIZONTE_ORG["admin_username"],
                "password": HORIZONTE_ORG["admin_password"],
            },
            "expediente_id": manifest["expediente_id"],
            "expediente_codigo": manifest["expediente_codigo"],
            "enlaces": manifest["enlaces"],
            "centro_control": f"/?expediente={manifest['expediente_id']}",
            "evaluacion": manifest["enlaces"]["evaluacion"],
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        db.rollback()
        print(json.dumps({"status": "error", "detail": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
