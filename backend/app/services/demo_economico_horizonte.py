"""Semilla idempotente — valor económico demo Clínica Horizonte."""

from __future__ import annotations

import app.diagnostic_models  # noqa: F401 — FK evaluaciones_expediente.diagnostic_id

from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.demo_comercial_constants import DEMO_CORRELATION_PREFIX
from app.economic_motor_enums import EconomicScope, EconomicValueType
from app.economic_motor_models import EconomicValueEntry
from app.evaluacion_models import EvaluacionExpediente, EvaluacionOportunidadLink
from app.models import User
from app.opportunity_models import Opportunity
from app.services import economic_motor_service as motor_svc
from app.valuation_enums import RealValueNature

DEMO_ECON_MARKER = "DEMO_HORIZONTE_ECON_V1"


def _is_demo_expediente(exp: EvaluacionExpediente) -> bool:
    if exp.correlation_id and exp.correlation_id.startswith(DEMO_CORRELATION_PREFIX):
        return True
    return exp.entidad_nombre.startswith("[DEMO]")


def _already_seeded(db: Session, organization_id: str, expediente_id: str) -> bool:
    return (
        db.query(EconomicValueEntry.id)
        .filter(
            EconomicValueEntry.organization_id == organization_id,
            EconomicValueEntry.evaluacion_id == expediente_id,
            EconomicValueEntry.notes.like(f"%{DEMO_ECON_MARKER}%"),
        )
        .first()
        is not None
    )


def ensure_horizonte_economico(
    db: Session,
    organization_id: str,
    user_id: str,
    expediente_id: str,
) -> dict[str, Any]:
    """Idempotente — valores DEMO etiquetados para CC y cabina."""
    exp = (
        db.query(EvaluacionExpediente)
        .filter(
            EvaluacionExpediente.id == expediente_id,
            EvaluacionExpediente.organization_id == organization_id,
        )
        .first()
    )
    if not exp or not _is_demo_expediente(exp):
        return {"applied": False, "reason": "not_demo_expediente"}

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"applied": False, "reason": "user_not_found"}

    if _already_seeded(db, organization_id, expediente_id):
        _refresh_oportunidades_demo(db, organization_id, expediente_id)
        return {"applied": False, "reason": "already_seeded", "reused": True}

    exp.valor_potencial = "DEMO — $185M COP/año (ESTIMADO)"

    valores = [
        (RealValueNature.VERIFICADO, EconomicValueType.AHORRO, Decimal("28500000"), "COP", "Piloto Q1 — medición validada"),
        (RealValueNature.ESTIMADO, EconomicValueType.PRODUCTIVIDAD_LIBERADA, Decimal("62000000"), "COP", "Proyección anual — reprocesos"),
        (RealValueNature.POTENCIAL, EconomicValueType.NUEVO_INGRESO, Decimal("185000000"), "COP", "Escenario completo automatización"),
    ]
    for nature, vtype, amount, currency, note in valores:
        motor_svc.register_value(
            db,
            user,
            organization_id=organization_id,
            value_type=vtype,
            value_nature=nature,
            amount=amount,
            currency=currency,
            scope_type=EconomicScope.EVALUACION,
            scope_id=expediente_id,
            evaluacion_id=expediente_id,
            methodology="DEMO — DATOS SIMULADOS",
            notes=f"{DEMO_ECON_MARKER} | {note}",
            register_finops=False,
        )

    _refresh_oportunidades_demo(db, organization_id, expediente_id)
    db.flush()
    return {
        "applied": True,
        "etiqueta": "DEMO — DATOS SIMULADOS",
        "valor_potencial_expediente": exp.valor_potencial,
        "nota": "ESTIMADO/PROYECTADO no equivalen a valor verificado",
    }


def _refresh_oportunidades_demo(db: Session, organization_id: str, expediente_id: str) -> None:
    """Variedad demo: ahorro, recuperación ingresos, riesgo/calidad."""
    links = (
        db.query(EvaluacionOportunidadLink, Opportunity)
        .join(Opportunity, Opportunity.id == EvaluacionOportunidadLink.opportunity_id)
        .filter(
            EvaluacionOportunidadLink.expediente_id == expediente_id,
            EvaluacionOportunidadLink.organization_id == organization_id,
        )
        .order_by(Opportunity.created_at.asc())
        .all()
    )
    specs = [
        {"tipo": "AHORRO", "dominio": "eficiencia", "valor": 48000000, "cert": "ESTIMADO"},
        {"tipo": "RECUPERACION", "dominio": "ingresos", "valor": 92000000, "cert": "ESTIMADO"},
        {"tipo": "RIESGO", "dominio": "calidad", "valor": 35000000, "cert": "POTENCIAL"},
    ]
    for idx, (_link, opp) in enumerate(links[:3]):
        spec = specs[idx % len(specs)]
        opp.tipo = spec["tipo"]
        opp.dominio = spec["dominio"]
        opp.valor_potencial = Decimal(str(spec["valor"]))
        opp.valor_potencial_certidumbre = spec["cert"]
        opp.descripcion = f"[DEMO] {opp.titulo} — {spec['tipo']} / {spec['dominio']}"
