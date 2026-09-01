#!/usr/bin/env python3
"""Seed de demostración EIAAX Lote 3 — puesta en marcha multiempresa."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
DATA_DIR = REPO_ROOT / "data"

# DATABASE_URL debe fijarse antes de importar la app.
DEFAULT_DATABASE_URL = f"sqlite:///{(DATA_DIR / 'eiaax_integrado_demo.db').as_posix()}"
os.environ.setdefault("DATABASE_URL", DEFAULT_DATABASE_URL)
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Registro completo de modelos (mismo orden que tests/conftest.py y app/main.py).
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
from app import resultados_models  # noqa: F401, E402
from app import salud_models  # noqa: F401, E402
from app import scim_models  # noqa: F401, E402
from app import security_models  # noqa: F401, E402
from app import segmentation_models  # noqa: F401, E402
from app import support_models  # noqa: F401, E402
from app import tco_models  # noqa: F401, E402
from app import transformacion_models  # noqa: F401, E402
from app import valuation_models  # noqa: F401, E402
from app import flujo_comercial_models  # noqa: F401, E402
from app import presentacion_models  # noqa: F401, E402
from app import espacio_externo_models  # noqa: F401, E402

from app.database import SessionLocal  # noqa: E402
from app.models import Organization, User  # noqa: E402
from app.negocio_models import NegocioProposalExtension  # noqa: E402
from app.security import hash_password  # noqa: E402
from app.seed_orchestration import bootstrap_orchestration  # noqa: E402
from app.seed_permissions import bootstrap_permissions  # noqa: E402
from app.seed_salud import bootstrap_salud  # noqa: E402
from app.services import communications_service as comm_svc  # noqa: E402
from app.services import evaluacion_service as eval_svc  # noqa: E402
from app.services import gobierno_operacional_service as gob_svc  # noqa: E402
from app.services import negocio_service as neg_svc  # noqa: E402
from app.services import resultados_service as res_svc  # noqa: E402
from app.services import support_service as support_svc  # noqa: E402
from app.services import transformacion_service as tx_svc  # noqa: E402
from scripts.sqlite_lifecycle import database_url_to_path, safe_unlink_sqlite  # noqa: E402

DEMO_ORG_A = {
    "name": "Empresa Demo A",
    "slug": "empresa-demo-a",
    "users": [
        {"username": "org_a_admin", "password": "DemoA2026!", "role": "admin"},
        {"username": "org_a_viewer", "password": "DemoA2026!", "role": "viewer"},
    ],
}

DEMO_ORG_B = {
    "name": "Empresa Demo B",
    "slug": "empresa-demo-b",
    "users": [
        {"username": "org_b_admin", "password": "DemoB2026!", "role": "admin"},
    ],
}


DEMO_DB_FILE_NAME = "eiaax_integrado_demo.db"


def _assert_demo_database_path(db_path: Path) -> None:
    resolved = db_path.resolve()
    if resolved.name != DEMO_DB_FILE_NAME:
        raise RuntimeError(f"Unsafe demo DB file name: {resolved.name}")
    if resolved.parent.name != "data":
        raise RuntimeError(f"Unsafe demo DB directory: {resolved.parent}")
    if resolved.parent.parent.name.upper() in {
        "EMPLEADOS_IA",
        "EMPLEADOS_IA_CERT",
        "EMPLEADOS_IA_V1_HOTFIX",
    }:
        raise RuntimeError(
            f"Refusing demo DB under forbidden worktree: {resolved.parent.parent.name}"
        )


def _prepare_demo_database(database_url: str) -> None:
    from alembic import command
    from alembic.config import Config

    db_path = database_url_to_path(database_url)
    _assert_demo_database_path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        safe_unlink_sqlite(db_path, database_url)

    alembic_cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_cfg, "head")


def _create_org(
    db,
    *,
    name: str,
    slug: str,
    users: list[dict[str, str]],
) -> tuple[Organization, dict[str, User]]:
    org = Organization(name=name, slug=slug, status="ACTIVE")
    db.add(org)
    db.flush()
    bootstrap_orchestration(db, org.id, commit=False)
    bootstrap_salud(db, org.id, commit=False)
    gob_svc.ensure_default_policies(db, org.id)
    gob_svc.ensure_default_ia_policy(db, org.id)

    created_users: dict[str, User] = {}
    for spec in users:
        user = User(
            organization_id=org.id,
            username=spec["username"],
            password_hash=hash_password(spec["password"]),
            role=spec["role"],
            status="ACTIVE",
            is_active=True,
        )
        db.add(user)
        created_users[spec["username"]] = user
    db.flush()
    return org, created_users


def _seed_org_a_demo_data(db, org: Organization, users: dict[str, User]) -> dict[str, Any]:
    admin = users["org_a_admin"]
    entities: dict[str, Any] = {}

    # Transformación: dossier + necesidad (crea expediente vinculado).
    tx_result = tx_svc.registrar_necesidad(
        db,
        org.id,
        admin.id,
        titulo="Optimización procesos operativos",
        necesidad="Procesos manuales con alta carga operativa y tiempos de respuesta elevados.",
        objetivo="Reducir tiempos de ciclo y mejorar trazabilidad",
        area_proceso="Operaciones",
        entidad_nombre="Unidad Operativa Demo A",
        nivel="PRELIMINAR",
    )
    expediente = tx_result["expediente"]
    dossier = tx_result["dossier"]
    expediente_id = expediente["id"]
    entities["dossier_id"] = dossier["id"]
    entities["expediente_id"] = expediente_id
    entities["expediente_codigo"] = expediente["codigo"]

    # Evaluación: hallazgo explícito + evaluación preliminar automática.
    hallazgo = eval_svc.create_hallazgo(
        db,
        expediente_id,
        org.id,
        user_id=admin.id,
        titulo="Cuello de botella en aprobaciones manuales",
        descripcion="Las aprobaciones internas requieren más de 48 horas en promedio.",
        tipo_contenido="HECHO",
        confianza="ALTA",
        explicacion_confianza="Dato reportado en la necesidad inicial del expediente demo.",
        origen="seed_lote3_demo",
        impacto_resumen="Retraso en entregas y sobrecarga del equipo operativo.",
    )
    entities["hallazgo_id"] = hallazgo.id

    eval_svc.ejecutar_evaluacion_preliminar(db, expediente_id, org.id, user_id=admin.id)

    opp_result = eval_svc.crear_oportunidad_desde_hallazgo(
        db,
        expediente_id,
        org.id,
        hallazgo_id=hallazgo.id,
        user_id=admin.id,
        dominio="operaciones",
    )
    entities["oportunidad_id"] = opp_result.get("opportunity_id")

    # Centro de negocios: propuesta con extensión.
    propuesta = neg_svc.create_proposal_from_expediente(
        db,
        admin,
        org.id,
        evaluacion_id=expediente_id,
        opportunity_id=entities["oportunidad_id"],
        titulo="Propuesta demo — automatización operativa",
    )
    entities["propuesta_id"] = propuesta["id"]
    ext = (
        db.query(NegocioProposalExtension)
        .filter(NegocioProposalExtension.proposal_id == propuesta["id"])
        .first()
    )
    entities["propuesta_extension_id"] = ext.proposal_id if ext else None

    # Resultados: indicador ANTES / PROYECTADO / REAL con evidencia.
    indicador = res_svc.create_indicador(
        db,
        org.id,
        nombre="Tiempo medio de aprobación",
        unidad="horas",
        definicion="Horas desde solicitud hasta aprobación operativa",
        valor_antes=48.0,
        valor_proyectado=24.0,
        expediente_id=expediente_id,
        hallazgo_id=hallazgo.id,
        opportunity_id=entities["oportunidad_id"],
        periodo="2026-Q1",
        tipo_analitica="COMPARATIVA",
        proceso="Operaciones / Aprobaciones",
    )
    entities["indicador_id"] = indicador["id"]

    indicador_real = res_svc.register_medicion_real(
        db,
        indicador["id"],
        org.id,
        valor_real=22.5,
        evidencia_ref="medicion-demo-2026-q1",
        calidad="VALIDADA",
    )
    entities["indicador_real"] = indicador_real["real"]

    evidencia = res_svc.add_evidencia(
        db,
        org.id,
        admin.id,
        titulo="Informe medición piloto Q1",
        indicador_id=indicador["id"],
        descripcion="Evidencia de medición real del piloto de automatización.",
        fuente="MANUAL",
        referencia="docs/demo/medicion-piloto-q1.pdf",
    )
    entities["evidencia_id"] = evidencia["id"]

    # Mesa de ayuda: caso de soporte.
    caso = support_svc.create_case_manual(
        db,
        org.id,
        admin,
        {
            "tipo": "SOLICITUD",
            "categoria": "DEMO",
            "asunto": "Consulta demo — acceso a expediente",
            "descripcion": "Solicitud de orientación sobre el expediente de evaluación demo.",
            "impacto": "BAJO",
            "urgencia": "BAJA",
            "modulo_relacionado": "evaluacion",
            "entidad_relacionada": expediente_id,
            "correlation_id": expediente.get("correlation_id"),
        },
    )
    entities["support_case_id"] = caso["id"]

    # Comunicaciones: plantillas y canal por defecto.
    comm_svc.bootstrap_default_comm_assets(db, org.id, admin)
    entities["communications_bootstrapped"] = True

    # Gobierno operacional: solicitud pendiente de aprobación.
    solicitud = gob_svc.crear_solicitud(
        db,
        org.id,
        admin.id,
        {
            "tipo_accion": "PROPUESTA",
            "recurso_tipo": "propuesta_comercial",
            "recurso_id": propuesta["id"],
            "descripcion": "Aprobación demo de propuesta comercial vinculada al expediente",
            "motivo_solicitud": "Flujo demo Lote 3 — requiere aprobación humana",
            "criticidad": "MEDIUM",
            "payload": {"propuesta_id": propuesta["id"], "expediente_id": expediente_id},
        },
    )
    entities["gobierno_solicitud_id"] = solicitud["id"]
    entities["gobierno_solicitud_estado"] = solicitud["estado"]

    db.commit()
    return entities


def main() -> int:
    database_url = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    print(f"Preparando base de datos demo: {database_url}", flush=True)
    _prepare_demo_database(database_url)

    db = SessionLocal()
    try:
        bootstrap_permissions(db)

        org_a, users_a = _create_org(
            db,
            name=DEMO_ORG_A["name"],
            slug=DEMO_ORG_A["slug"],
            users=DEMO_ORG_A["users"],
        )
        org_b, users_b = _create_org(
            db,
            name=DEMO_ORG_B["name"],
            slug=DEMO_ORG_B["slug"],
            users=DEMO_ORG_B["users"],
        )
        db.commit()

        entities_a = _seed_org_a_demo_data(db, org_a, users_a)

        summary: dict[str, Any] = {
            "database_url": database_url,
            "credentials_file": "backend/scripts/credentials.example",
            "organizations": {
                "org_a": {
                    "id": org_a.id,
                    "name": org_a.name,
                    "slug": org_a.slug,
                    "users": [
                        {
                            "username": u["username"],
                            "role": u["role"],
                            "password": u["password"],
                        }
                        for u in DEMO_ORG_A["users"]
                    ],
                    "entities": entities_a,
                },
                "org_b": {
                    "id": org_b.id,
                    "name": org_b.name,
                    "slug": org_b.slug,
                    "users": [
                        {
                            "username": u["username"],
                            "role": u["role"],
                            "password": u["password"],
                        }
                        for u in DEMO_ORG_B["users"]
                    ],
                },
            },
            "status": "ok",
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
