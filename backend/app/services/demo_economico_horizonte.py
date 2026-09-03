"""Semilla idempotente — valor económico demo Clínica Horizonte."""

from __future__ import annotations

import app.diagnostic_models  # noqa: F401 — FK evaluaciones_expediente.diagnostic_id

from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.demo_comercial_constants import DEMO_CORRELATION_PREFIX
from app.demo_economico_semantica import DEMO_BANNER, DEMO_VALUE_SPECS, LABEL_ESTIMADO, LABEL_POTENCIAL, LABEL_SIMULACION_VERIFICADO
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


def _repair_demo_economic_semantics(db: Session, organization_id: str, expediente_id: str) -> None:
    """Corrige entradas legacy que usaban VERIFICADO para datos ficticios."""
    rows = (
        db.query(EconomicValueEntry)
        .filter(
            EconomicValueEntry.organization_id == organization_id,
            EconomicValueEntry.evaluacion_id == expediente_id,
            EconomicValueEntry.notes.like(f"%{DEMO_ECON_MARKER}%"),
        )
        .all()
    )
    specs_by_amount = {spec["amount"]: spec for spec in DEMO_VALUE_SPECS}
    for row in rows:
        amt = int(row.amount or 0)
        spec = specs_by_amount.get(amt)
        if not spec:
            continue
        row.value_nature = RealValueNature.ESTIMADO if spec["clave"] != "potencial" else RealValueNature.POTENCIAL
        row.methodology = DEMO_BANNER
        if spec["clave"] == "simulacion_verificado":
            row.notes = f"{DEMO_ECON_MARKER} | {LABEL_SIMULACION_VERIFICADO} | {spec['nota']}"
        elif spec["clave"] == "potencial":
            row.notes = f"{DEMO_ECON_MARKER} | {LABEL_POTENCIAL} | {spec['nota']}"
        else:
            row.notes = f"{DEMO_ECON_MARKER} | {LABEL_ESTIMADO} | {spec['nota']}"


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
        _repair_demo_economic_semantics(db, organization_id, expediente_id)
        _refresh_oportunidades_demo(db, organization_id, expediente_id)
        exp.valor_potencial = f"{DEMO_BANNER} — $185M COP/año ({LABEL_POTENCIAL})"
        return {"applied": False, "reason": "already_seeded", "reused": True, "semantics_repaired": True}

    exp.valor_potencial = f"{DEMO_BANNER} — $185M COP/año ({LABEL_POTENCIAL})"

    seed_rows = [
        (RealValueNature.ESTIMADO, EconomicValueType.AHORRO, Decimal("28500000"), LABEL_SIMULACION_VERIFICADO, "simulacion_verificado"),
        (RealValueNature.ESTIMADO, EconomicValueType.PRODUCTIVIDAD_LIBERADA, Decimal("62000000"), LABEL_ESTIMADO, "estimado"),
        (RealValueNature.POTENCIAL, EconomicValueType.NUEVO_INGRESO, Decimal("185000000"), LABEL_POTENCIAL, "potencial"),
    ]
    for nature, vtype, amount, etiqueta, clave in seed_rows:
        spec = next(s for s in DEMO_VALUE_SPECS if s["clave"] == clave)
        motor_svc.register_value(
            db,
            user,
            organization_id=organization_id,
            value_type=vtype,
            value_nature=nature,
            amount=amount,
            currency="COP",
            scope_type=EconomicScope.EVALUACION,
            scope_id=expediente_id,
            evaluacion_id=expediente_id,
            methodology=DEMO_BANNER,
            notes=f"{DEMO_ECON_MARKER} | {etiqueta} | {spec['nota']}",
            register_finops=False,
        )

    _refresh_oportunidades_demo(db, organization_id, expediente_id)
    db.flush()
    return {
        "applied": True,
        "etiqueta": DEMO_BANNER,
        "valor_potencial_expediente": exp.valor_potencial,
        "nota": "SIMULADO/ESTIMADO/PROYECTADO/POTENCIAL — ninguno equivale a verificación real",
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
        {"tipo": "AHORRO", "dominio": "eficiencia", "valor": 48000000, "cert": "SIMULADO — ESTIMADO"},
        {"tipo": "RECUPERACION", "dominio": "ingresos", "valor": 92000000, "cert": "SIMULADO — ESTIMADO"},
        {"tipo": "RIESGO", "dominio": "calidad", "valor": 35000000, "cert": "SIMULADO — POTENCIAL"},
    ]
    for idx, (_link, opp) in enumerate(links[:3]):
        spec = specs[idx % len(specs)]
        opp.tipo = spec["tipo"]
        opp.dominio = spec["dominio"]
        opp.valor_potencial = Decimal(str(spec["valor"]))
        opp.valor_potencial_certidumbre = spec["cert"]
        opp.descripcion = f"[DEMO] {opp.titulo} — {spec['tipo']} / {spec['dominio']} ({spec['cert']})"


def expediente_economic_resumen(
    db: Session,
    organization_id: str,
    expediente_id: str,
    *,
    vista_entidad: bool = False,
) -> dict[str, Any]:
    """Resumen económico por expediente con semántica demo explícita."""
    from app.demo_economico_semantica import build_demo_resumen

    exp = (
        db.query(EvaluacionExpediente)
        .filter(
            EvaluacionExpediente.id == expediente_id,
            EvaluacionExpediente.organization_id == organization_id,
        )
        .first()
    )
    is_demo = bool(exp and _is_demo_expediente(exp))
    rows = (
        db.query(EconomicValueEntry)
        .filter(
            EconomicValueEntry.organization_id == organization_id,
            EconomicValueEntry.evaluacion_id == expediente_id,
        )
        .all()
    )
    if is_demo and rows:
        entries = []
        for spec in DEMO_VALUE_SPECS:
            match = next((r for r in rows if int(r.amount or 0) == spec["amount"]), None)
            if match:
                entries.append({**spec, "amount": int(match.amount or 0)})
        resumen = build_demo_resumen(entries)
        if vista_entidad:
            resumen["verificado"] = None
        return resumen

    buckets = {RealValueNature.VERIFICADO: 0.0, RealValueNature.ESTIMADO: 0.0, RealValueNature.POTENCIAL: 0.0}
    for row in rows:
        key = (row.value_nature or RealValueNature.ESTIMADO).upper()
        if key in buckets:
            buckets[key] += float(row.amount or 0)
    return {
        "es_demo": False,
        "verificado": buckets[RealValueNature.VERIFICADO] or None,
        "estimado": buckets[RealValueNature.ESTIMADO] or None,
        "potencial": buckets[RealValueNature.POTENCIAL] or None,
        "realizado": (buckets[RealValueNature.VERIFICADO] + buckets[RealValueNature.ESTIMADO]) or None,
    }
