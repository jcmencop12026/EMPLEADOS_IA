"""Servicio — Modelo comercial basado en valor (1280)."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.commercial_enums import (
    CostCategory,
    CostClass,
    CredentialMode,
    DoubleCountSeverity,
    ProposalStatus,
    ScenarioType,
    ValueCategory,
    ValueNature,
    ValueScope,
)
from app.commercial_models import (
    CommercialDoubleCountAlert,
    CommercialPlan,
    CommercialProposal,
    CommercialProposalCost,
    CommercialProposalPriceHistory,
    CommercialProposalScenario,
    CommercialProposalValue,
)
from app.models import Organization
from app.opportunity_models import Opportunity
from app.tenant_scope import ORG_STATUS_ACTIVE
from app.valuation_models import OpportunityValuation, OpportunityValuationReal

INCOMPATIBLE_CATEGORIES = frozenset({
    frozenset({ValueCategory.INGRESO_RECUPERADO, ValueCategory.NUEVO_INGRESO}),
    frozenset({ValueCategory.AHORRO, ValueCategory.PERDIDA_EVITADA}),
})


class CommercialValidationError(ValueError):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, default=str)


def _parse_json(raw: str | None) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _decimal(value: float | Decimal | str | None, default: Decimal | None = None) -> Decimal | None:
    if value is None:
        return default
    return Decimal(str(value))


def _ensure_org_active(db: Session, organization_id: str) -> Organization:
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    if org.status != ORG_STATUS_ACTIVE:
        raise HTTPException(status_code=403, detail="La empresa está inactiva")
    return org


def _next_codigo(db: Session, org_id: str) -> str:
    count = db.query(func.count(CommercialProposal.id)).filter(CommercialProposal.organization_id == org_id).scalar() or 0
    return f"PROP-{count + 1:05d}"


def _infer_scope(categoria: str, explicit: str | None = None) -> str:
    if explicit and explicit in ValueScope.ALL:
        return explicit
    if categoria in ValueCategory.EXTERNO:
        return ValueScope.EXTERNO
    return ValueScope.INTERNO


def _compute_excedente_cost(plan: CommercialPlan | None, tokens_usados: int | None) -> dict[str, Any]:
    if not plan or not tokens_usados or not plan.consumo_ia_incluido_tokens:
        return {"excedente_tokens": 0, "costo_excedente": 0.0, "alerta": False, "bloqueado": False}
    incluido = plan.consumo_ia_incluido_tokens
    excedente = max(0, tokens_usados - incluido)
    costo = Decimal("0")
    if excedente > 0 and plan.excedente_ia_por_millon:
        costo = (Decimal(excedente) / Decimal("1000000") * plan.excedente_ia_por_millon).quantize(Decimal("0.0001"))
    pct_uso = (Decimal(tokens_usados) / Decimal(incluido) * 100) if incluido else Decimal("0")
    alerta = bool(plan.alerta_consumo_pct and pct_uso >= plan.alerta_consumo_pct)
    bloqueado = bool(plan.bloqueo_excedente and excedente > 0)
    return {
        "excedente_tokens": excedente,
        "costo_excedente": float(costo),
        "pct_consumo": float(pct_uso.quantize(Decimal("0.01"))),
        "alerta": alerta,
        "bloqueado": bloqueado,
        "consumo_ia_incluido_tokens": incluido,
    }


def _compute_economics(
    *,
    valor_atribuible: Decimal,
    costo_total: Decimal,
    fraccion: Decimal,
    margen_min: Decimal,
    precio_base: Decimal = Decimal("0"),
    precio_minimo: Decimal | None = None,
    precio_maximo: Decimal | None = None,
) -> dict[str, Any]:
    precio_por_valor = (valor_atribuible * fraccion).quantize(Decimal("0.0001"))
    piso_costos = (costo_total * (Decimal("1") + margen_min)).quantize(Decimal("0.0001"))
    precio_sugerido = max(precio_por_valor, piso_costos, precio_base)
    advertencias: list[str] = []
    if precio_minimo and precio_sugerido < precio_minimo:
        precio_sugerido = precio_minimo
        advertencias.append("Precio ajustado al mínimo del plan")
    if precio_maximo and precio_sugerido > precio_maximo:
        advertencias.append("Precio sugerido supera el máximo del plan — requiere revisión comercial")
    if valor_atribuible > 0 and precio_sugerido > valor_atribuible:
        advertencias.append("Precio sugerido supera el valor atribuible capturable — revisar supuestos")
    if precio_sugerido < piso_costos:
        advertencias.append("Precio sugerido por debajo del piso de costos + margen mínimo")
    beneficio_neto = (valor_atribuible - precio_sugerido).quantize(Decimal("0.0001"))
    roi = ((beneficio_neto / precio_sugerido) * 100).quantize(Decimal("0.01")) if precio_sugerido > 0 else None
    payback = (precio_sugerido / (valor_atribuible / Decimal("12"))).quantize(Decimal("0.01")) if valor_atribuible > 0 else None
    pct_conservado = ((beneficio_neto / valor_atribuible) * 100).quantize(Decimal("0.01")) if valor_atribuible > 0 else None
    pct_capturado = ((precio_sugerido / valor_atribuible) * 100).quantize(Decimal("0.01")) if valor_atribuible > 0 else None
    margen = ((precio_sugerido - costo_total) / precio_sugerido * 100).quantize(Decimal("0.01")) if precio_sugerido > 0 else None
    return {
        "valor_atribuible": float(valor_atribuible),
        "costo_total": float(costo_total),
        "precio_sugerido": float(precio_sugerido),
        "piso_costos": float(piso_costos),
        "fraccion_aplicada": float(fraccion),
        "margen_minimo_pct": float(margen_min),
        "beneficio_neto_cliente": float(beneficio_neto),
        "roi_pct": float(roi) if roi is not None else None,
        "payback_meses": float(payback) if payback is not None else None,
        "pct_valor_conservado_cliente": float(pct_conservado) if pct_conservado is not None else None,
        "pct_valor_capturado_empleados_ia": float(pct_capturado) if pct_capturado is not None else None,
        "margen_pct": float(margen) if margen is not None else None,
        "advertencias": advertencias,
    }


def _compute_attributable(gross: Decimal, pct: Decimal) -> Decimal:
    if pct <= 0:
        return Decimal("0")
    if pct > 100:
        raise CommercialValidationError("El porcentaje atribuible no puede superar 100%")
    return (gross * pct / Decimal("100")).quantize(Decimal("0.0001"))


def plan_to_dict(row: CommercialPlan) -> dict[str, Any]:
    return {
        "id": row.id,
        "organization_id": row.organization_id,
        "code": row.code,
        "name": row.name,
        "descripcion": row.descripcion,
        "credential_mode": row.credential_mode,
        "currency": row.currency,
        "precio_base_mensual": float(row.precio_base_mensual) if row.precio_base_mensual else None,
        "margen_minimo_pct": float(row.margen_minimo_pct),
        "fraccion_valor_sugerida": float(row.fraccion_valor_sugerida) if row.fraccion_valor_sugerida else None,
        "precio_minimo": float(row.precio_minimo) if row.precio_minimo else None,
        "precio_maximo": float(row.precio_maximo) if row.precio_maximo else None,
        "consumo_ia_incluido_tokens": row.consumo_ia_incluido_tokens,
        "presupuesto_ia_incluido": float(row.presupuesto_ia_incluido) if row.presupuesto_ia_incluido else None,
        "excedente_ia_por_millon": float(row.excedente_ia_por_millon) if row.excedente_ia_por_millon else None,
        "alerta_consumo_pct": float(row.alerta_consumo_pct) if row.alerta_consumo_pct else None,
        "bloqueo_excedente": row.bloqueo_excedente,
        "limits": _parse_json(row.limits_json),
        "is_active": row.is_active,
    }


def create_plan(db: Session, organization_id: str | None, data: dict[str, Any], user_id: str | None) -> CommercialPlan:
    if data.get("credential_mode") and data["credential_mode"] not in CredentialMode.ALL:
        raise CommercialValidationError("Modo de credenciales no válido")
    row = CommercialPlan(
        organization_id=organization_id,
        code=str(data["code"]).strip().lower(),
        name=data["name"],
        descripcion=data.get("descripcion"),
        credential_mode=data.get("credential_mode", CredentialMode.IA_ADMINISTRADA),
        currency=data.get("currency", "USD"),
        precio_base_mensual=_decimal(data.get("precio_base_mensual")),
        margen_minimo_pct=_decimal(data.get("margen_minimo_pct"), Decimal("0.15")) or Decimal("0.15"),
        fraccion_valor_sugerida=_decimal(data.get("fraccion_valor_sugerida")),
        precio_minimo=_decimal(data.get("precio_minimo")),
        precio_maximo=_decimal(data.get("precio_maximo")),
        consumo_ia_incluido_tokens=data.get("consumo_ia_incluido_tokens"),
        presupuesto_ia_incluido=_decimal(data.get("presupuesto_ia_incluido")),
        excedente_ia_por_millon=_decimal(data.get("excedente_ia_por_millon")),
        alerta_consumo_pct=_decimal(data.get("alerta_consumo_pct")),
        bloqueo_excedente=bool(data.get("bloqueo_excedente", False)),
        limits_json=_json(data.get("limits")) if data.get("limits") else None,
    )
    db.add(row)
    db.flush()
    write_audit(db, action="comercial.plan.creado", organization_id=organization_id, user_id=user_id,
                detail=_json({"plan_id": row.id, "code": row.code}), commit=False)
    return row


def list_plans(db: Session, organization_id: str) -> list[CommercialPlan]:
    return (
        db.query(CommercialPlan)
        .filter(
            (CommercialPlan.organization_id == organization_id) | (CommercialPlan.organization_id.is_(None)),
            CommercialPlan.is_active.is_(True),
        )
        .order_by(CommercialPlan.name)
        .all()
    )


def create_proposal(db: Session, organization_id: str, data: dict[str, Any], user_id: str | None) -> CommercialProposal:
    _ensure_org_active(db, organization_id)
    row = CommercialProposal(
        organization_id=organization_id,
        codigo=_next_codigo(db, organization_id),
        titulo=data.get("titulo") or "Propuesta comercial",
        plan_id=data.get("plan_id"),
        credential_mode=data.get("credential_mode", CredentialMode.IA_ADMINISTRADA),
        diagnostic_id=data.get("diagnostic_id"),
        currency=data.get("currency", "USD"),
        vigencia_hasta=_parse_dt(data.get("vigencia_hasta")),
        supuestos_json=_json(data.get("supuestos")) if data.get("supuestos") else None,
        riesgos_json=_json(data.get("riesgos")) if data.get("riesgos") else None,
        created_by=user_id,
    )
    db.add(row)
    db.flush()
    write_audit(db, action="comercial.propuesta.creada", organization_id=organization_id, user_id=user_id,
                detail=_json({"proposal_id": row.id, "codigo": row.codigo}), commit=False)
    return row


def _parse_dt(value: datetime | str | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def add_value_component(
    db: Session,
    organization_id: str,
    proposal_id: str,
    data: dict[str, Any],
    user_id: str | None,
) -> CommercialProposalValue:
    proposal = _get_proposal(db, organization_id, proposal_id)
    if proposal.estado not in (ProposalStatus.BORRADOR, ProposalStatus.EN_REVISION):
        raise CommercialValidationError("No se pueden modificar valores en el estado actual")
    cat = data.get("categoria")
    nat = data.get("naturaleza", ValueNature.ESTIMADO)
    if cat not in ValueCategory.ALL:
        raise CommercialValidationError("Categoría de valor no válida")
    if nat not in ValueNature.ALL:
        raise CommercialValidationError("Naturaleza de valor no válida")
    gross = _decimal(data.get("valor_bruto"))
    if gross is None or gross <= 0:
        raise CommercialValidationError("valor_bruto debe ser positivo")
    pct = _decimal(data.get("atribucion_pct"), Decimal("0")) or Decimal("0")
    if pct == 0 and not data.get("criterio_atribucion"):
        raise CommercialValidationError("Debe indicar porcentaje atribuible y criterio; no se adjudica 100% automáticamente")
    attributable = _compute_attributable(gross, pct)
    opp_id = data.get("opportunity_id")
    if opp_id:
        _validate_opportunity(db, organization_id, opp_id)
    alcance = _infer_scope(cat, data.get("alcance"))
    dedupe_key = data.get("dedupe_key") or _value_dedupe_key(organization_id, proposal_id, cat, opp_id, gross)
    row = CommercialProposalValue(
        proposal_id=proposal.id,
        organization_id=organization_id,
        opportunity_id=opp_id,
        valuation_id=data.get("valuation_id"),
        linea_base_id=data.get("linea_base_id"),
        categoria=cat,
        alcance=alcance,
        naturaleza=nat,
        external_intelligence_ref=data.get("external_intelligence_ref"),
        valor_bruto=gross,
        atribucion_pct=pct,
        valor_atribuible=attributable,
        criterio_atribucion=data.get("criterio_atribucion"),
        justificacion=data.get("justificacion"),
        evidencia=data.get("evidencia"),
        responsable_id=data.get("responsable_id") or user_id,
        dedupe_key=dedupe_key,
    )
    db.add(row)
    db.flush()
    write_audit(db, action="comercial.valor.agregado", organization_id=organization_id, user_id=user_id,
                detail=_json({"proposal_id": proposal_id, "value_id": row.id, "categoria": cat}), commit=False)
    return row


def _value_dedupe_key(org_id: str, proposal_id: str, categoria: str, opp_id: str | None, gross: Decimal) -> str:
    raw = f"{org_id}|{proposal_id}|{categoria}|{opp_id or ''}|{gross}"
    return hashlib.sha256(raw.encode()).hexdigest()[:64]


def _validate_opportunity(db: Session, organization_id: str, opportunity_id: str) -> Opportunity:
    opp = db.query(Opportunity).filter(Opportunity.id == opportunity_id, Opportunity.organization_id == organization_id).first()
    if not opp:
        raise CommercialValidationError("Oportunidad no encontrada")
    return opp


def _get_proposal(db: Session, organization_id: str, proposal_id: str) -> CommercialProposal:
    row = db.query(CommercialProposal).filter(
        CommercialProposal.id == proposal_id, CommercialProposal.organization_id == organization_id
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Propuesta no encontrada")
    return row


def add_scenario(db: Session, organization_id: str, proposal_id: str, data: dict[str, Any], user_id: str | None) -> CommercialProposalScenario:
    proposal = _get_proposal(db, organization_id, proposal_id)
    st = data.get("scenario_type")
    if st not in ScenarioType.ALL:
        raise CommercialValidationError("Tipo de escenario no válido")
    row = CommercialProposalScenario(
        proposal_id=proposal.id,
        organization_id=organization_id,
        scenario_type=st,
        valor_esperado=_decimal(data.get("valor_esperado")),
        valor_atribuible=_decimal(data.get("valor_atribuible")),
        probabilidad=_decimal(data.get("probabilidad")),
        costo=_decimal(data.get("costo")),
        periodo_meses=data.get("periodo_meses"),
        riesgo_nivel=data.get("riesgo_nivel"),
        explicacion=data.get("explicacion"),
        es_recomendado=bool(data.get("es_recomendado", st == ScenarioType.BASE)),
    )
    db.add(row)
    db.flush()
    write_audit(db, action="comercial.escenario.agregado", organization_id=organization_id, user_id=user_id,
                detail=_json({"proposal_id": proposal_id, "scenario": st}), commit=False)
    return row


def add_cost(db: Session, organization_id: str, proposal_id: str, data: dict[str, Any], user_id: str | None) -> CommercialProposalCost:
    proposal = _get_proposal(db, organization_id, proposal_id)
    cat = data.get("categoria")
    if cat not in CostCategory.ALL:
        raise CommercialValidationError("Categoría de costo no válida")
    clase = data.get("clase_costo", CostClass.COSTO_INTERNO)
    if clase not in CostClass.ALL:
        raise CommercialValidationError("Clase de costo no válida")
    monto = _decimal(data.get("monto"))
    if monto is None or monto < 0:
        raise CommercialValidationError("monto debe ser >= 0")
    row = CommercialProposalCost(
        proposal_id=proposal.id,
        organization_id=organization_id,
        categoria=cat,
        clase_costo=clase,
        monto=monto,
        currency=data.get("currency", proposal.currency),
        finops_record_id=data.get("finops_record_id"),
        descripcion=data.get("descripcion"),
        es_recurrente=bool(data.get("es_recurrente", False)),
        periodo_meses=data.get("periodo_meses"),
    )
    db.add(row)
    db.flush()
    write_audit(db, action="comercial.costo.agregado", organization_id=organization_id, user_id=user_id,
                detail=_json({"proposal_id": proposal_id, "categoria": cat, "monto": float(monto)}), commit=False)
    return row


def detect_double_count(db: Session, organization_id: str, proposal_id: str) -> list[CommercialDoubleCountAlert]:
    proposal = _get_proposal(db, organization_id, proposal_id)
    values = db.query(CommercialProposalValue).filter(CommercialProposalValue.proposal_id == proposal.id).all()
    alerts: list[CommercialDoubleCountAlert] = []
    db.query(CommercialDoubleCountAlert).filter(
        CommercialDoubleCountAlert.proposal_id == proposal.id, CommercialDoubleCountAlert.resuelto.is_(False)
    ).delete(synchronize_session=False)

    by_opp: dict[str, list[CommercialProposalValue]] = {}
    by_dedupe: dict[str, list[CommercialProposalValue]] = {}
    for v in values:
        if v.opportunity_id:
            by_opp.setdefault(v.opportunity_id, []).append(v)
        if v.dedupe_key:
            by_dedupe.setdefault(v.dedupe_key, []).append(v)

    for opp_id, group in by_opp.items():
        if len(group) > 1:
            cats = {g.categoria for g in group}
            alert = CommercialDoubleCountAlert(
                proposal_id=proposal.id,
                organization_id=organization_id,
                severidad=DoubleCountSeverity.ADVERTENCIA,
                tipo="OPORTUNIDAD_DUPLICADA",
                mensaje=f"Varios componentes de valor para la misma oportunidad ({opp_id}): {', '.join(sorted(cats))}",
                value_ids_json=_json([g.id for g in group]),
            )
            db.add(alert)
            alerts.append(alert)

    for pair in INCOMPATIBLE_CATEGORIES:
        found = [v for v in values if v.categoria in pair]
        if len(found) >= 2:
            alert = CommercialDoubleCountAlert(
                proposal_id=proposal.id,
                organization_id=organization_id,
                severidad=DoubleCountSeverity.CRITICO,
                tipo="CATEGORIAS_INCOMPATIBLES",
                mensaje=f"Posible doble conteo entre categorías: {' y '.join(sorted(pair))}",
                value_ids_json=_json([f.id for f in found]),
            )
            db.add(alert)
            alerts.append(alert)

    for key, group in by_dedupe.items():
        if len(group) > 1:
            alert = CommercialDoubleCountAlert(
                proposal_id=proposal.id,
                organization_id=organization_id,
                severidad=DoubleCountSeverity.ADVERTENCIA,
                tipo="DEDUPE_KEY",
                mensaje="Componentes con la misma clave de deduplicación",
                value_ids_json=_json([g.id for g in group]),
            )
            db.add(alert)
            alerts.append(alert)

    db.flush()
    return alerts


def get_plan(db: Session, organization_id: str, plan_id: str) -> CommercialPlan:
    row = (
        db.query(CommercialPlan)
        .filter(
            CommercialPlan.id == plan_id,
            (CommercialPlan.organization_id == organization_id) | (CommercialPlan.organization_id.is_(None)),
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    return row


def suggest_price(
    db: Session,
    organization_id: str,
    proposal_id: str,
    *,
    scenario_type: str = ScenarioType.BASE,
) -> dict[str, Any]:
    proposal = _get_proposal(db, organization_id, proposal_id)
    plan = db.query(CommercialPlan).filter(CommercialPlan.id == proposal.plan_id).first() if proposal.plan_id else None
    values = db.query(CommercialProposalValue).filter(CommercialProposalValue.proposal_id == proposal.id).all()
    costs = db.query(CommercialProposalCost).filter(CommercialProposalCost.proposal_id == proposal.id).all()
    scenario = (
        db.query(CommercialProposalScenario)
        .filter(CommercialProposalScenario.proposal_id == proposal.id, CommercialProposalScenario.scenario_type == scenario_type)
        .first()
    )

    valor_atribuible = sum((v.valor_atribuible for v in values), Decimal("0"))
    if scenario and scenario.valor_atribuible:
        valor_atribuible = scenario.valor_atribuible
    elif scenario and scenario.valor_esperado and scenario.probabilidad:
        valor_atribuible = (scenario.valor_esperado * scenario.probabilidad).quantize(Decimal("0.0001"))

    costo_total = sum((c.monto for c in costs), Decimal("0"))
    if scenario and scenario.costo:
        costo_total = max(costo_total, scenario.costo)

    fraccion = plan.fraccion_valor_sugerida if plan and plan.fraccion_valor_sugerida else Decimal("0.25")
    margen_min = plan.margen_minimo_pct if plan else Decimal("0.15")
    precio_base = plan.precio_base_mensual if plan and plan.precio_base_mensual else Decimal("0")

    result = _compute_economics(
        valor_atribuible=valor_atribuible,
        costo_total=costo_total,
        fraccion=fraccion,
        margen_min=margen_min,
        precio_base=precio_base,
        precio_minimo=plan.precio_minimo if plan else None,
        precio_maximo=plan.precio_maximo if plan else None,
    )
    precio_sugerido = Decimal(str(result["precio_sugerido"]))

    proposal.valor_total_esperado = sum((v.valor_bruto for v in values), Decimal("0")) or None
    proposal.valor_atribuible_total = valor_atribuible or None
    proposal.costo_total = costo_total or None
    proposal.precio_sugerido = precio_sugerido
    proposal.beneficio_neto_cliente = Decimal(str(result["beneficio_neto_cliente"]))
    proposal.roi_pct = Decimal(str(result["roi_pct"])) if result["roi_pct"] is not None else None
    proposal.payback_meses = Decimal(str(result["payback_meses"])) if result["payback_meses"] is not None else None
    proposal.pct_valor_conservado_cliente = Decimal(str(result["pct_valor_conservado_cliente"])) if result["pct_valor_conservado_cliente"] is not None else None
    proposal.pct_valor_capturado_empleados_ia = Decimal(str(result["pct_valor_capturado_empleados_ia"])) if result["pct_valor_capturado_empleados_ia"] is not None else None
    proposal.margen_pct = Decimal(str(result["margen_pct"])) if result["margen_pct"] is not None else None
    proposal.escenario_recomendado = scenario_type

    db.flush()
    write_audit(db, action="comercial.precio.sugerido", organization_id=organization_id, user_id=None,
                detail=_json({"proposal_id": proposal_id, "precio_sugerido": float(precio_sugerido)}), commit=False)

    result["escenario"] = scenario_type
    if plan:
        result["consumo_ia"] = _compute_excedente_cost(plan, None)
    return result


def set_final_price(
    db: Session,
    organization_id: str,
    proposal_id: str,
    precio_final: float,
    justificacion: str | None,
    user_id: str,
) -> CommercialProposal:
    proposal = _get_proposal(db, organization_id, proposal_id)
    if proposal.precio_sugerido is None:
        raise CommercialValidationError("Calcule primero el precio sugerido")
    precio = _decimal(precio_final)
    if precio is None:
        raise CommercialValidationError("precio_final inválido")
    hist = CommercialProposalPriceHistory(
        proposal_id=proposal.id,
        organization_id=organization_id,
        precio_sugerido=proposal.precio_sugerido,
        precio_modificado=precio,
        justificacion=justificacion,
        user_id=user_id,
        action="PRECIO_MODIFICADO",
    )
    db.add(hist)
    proposal.precio_final = precio
    if proposal.valor_atribuible_total:
        proposal.beneficio_neto_cliente = (proposal.valor_atribuible_total - precio).quantize(Decimal("0.0001"))
        if precio > 0:
            proposal.roi_pct = ((proposal.beneficio_neto_cliente / precio) * 100).quantize(Decimal("0.01"))
            proposal.pct_valor_capturado_empleados_ia = ((precio / proposal.valor_atribuible_total) * 100).quantize(Decimal("0.01"))
            proposal.pct_valor_conservado_cliente = (
                (proposal.beneficio_neto_cliente / proposal.valor_atribuible_total) * 100
            ).quantize(Decimal("0.01"))
    db.flush()
    write_audit(db, action="comercial.precio.modificado", organization_id=organization_id, user_id=user_id,
                detail=_json({"proposal_id": proposal_id, "precio_final": float(precio)}), commit=False)
    return proposal


def approve_proposal(db: Session, organization_id: str, proposal_id: str, user_id: str) -> CommercialProposal:
    proposal = _get_proposal(db, organization_id, proposal_id)
    if proposal.precio_final is None:
        raise CommercialValidationError("Debe establecer precio final antes de aprobar")
    proposal.estado = ProposalStatus.APROBADA
    proposal.approved_by = user_id
    proposal.approved_at = _utcnow()
    hist = CommercialProposalPriceHistory(
        proposal_id=proposal.id,
        organization_id=organization_id,
        precio_sugerido=proposal.precio_sugerido,
        precio_modificado=proposal.precio_final,
        justificacion="Aprobación comercial",
        user_id=user_id,
        action="APROBADA",
    )
    db.add(hist)
    write_audit(db, action="comercial.propuesta.aprobada", organization_id=organization_id, user_id=user_id,
                detail=_json({"proposal_id": proposal_id}), commit=False)
    return proposal


def import_from_valuation(db: Session, organization_id: str, proposal_id: str, opportunity_id: str, user_id: str | None) -> CommercialProposalValue:
    _validate_opportunity(db, organization_id, opportunity_id)
    valuation = (
        db.query(OpportunityValuation)
        .filter(OpportunityValuation.organization_id == organization_id, OpportunityValuation.opportunity_id == opportunity_id)
        .first()
    )
    if not valuation:
        raise CommercialValidationError("No existe valoración 1210 para esta oportunidad")
    real = (
        db.query(OpportunityValuationReal)
        .filter(OpportunityValuationReal.valuation_id == valuation.id, OpportunityValuationReal.is_current.is_(True))
        .order_by(OpportunityValuationReal.recorded_at.desc())
        .first()
    )
    gross = real.materialized_value if real and real.materialized_value else Decimal("0")
    pct = real.attribution_pct if real and real.attribution_pct else Decimal("0")
    if gross <= 0:
        raise CommercialValidationError("La valoración no tiene valor materializado utilizable")
    return add_value_component(
        db, organization_id, proposal_id,
        {
            "opportunity_id": opportunity_id,
            "valuation_id": valuation.id,
            "categoria": ValueCategory.OPORTUNIDAD_CAPTURADA,
            "naturaleza": real.value_nature if real else ValueNature.ESTIMADO,
            "valor_bruto": gross,
            "atribucion_pct": pct,
            "criterio_atribucion": real.justification if real else "Importado desde valoración 1210",
            "evidencia": real.evidence if real else None,
        },
        user_id,
    )


def build_traceability(db: Session, organization_id: str, proposal_id: str) -> dict[str, Any]:
    proposal = _get_proposal(db, organization_id, proposal_id)
    values = db.query(CommercialProposalValue).filter(CommercialProposalValue.proposal_id == proposal.id).all()
    costs = db.query(CommercialProposalCost).filter(CommercialProposalCost.proposal_id == proposal.id).all()
    trace = {
        "diagnostico_id": proposal.diagnostic_id,
        "oportunidades": list({v.opportunity_id for v in values if v.opportunity_id}),
        "valoraciones_1210": list({v.valuation_id for v in values if v.valuation_id}),
        "lineas_base_1200": list({v.linea_base_id for v in values if v.linea_base_id}),
        "inteligencia_externa_1240": list({v.external_intelligence_ref for v in values if v.external_intelligence_ref}),
        "finops_refs": list({c.finops_record_id for c in costs if c.finops_record_id}),
        "valor_interno_atribuible": float(sum((v.valor_atribuible for v in values if v.alcance == ValueScope.INTERNO), Decimal("0"))),
        "valor_externo_atribuible": float(sum((v.valor_atribuible for v in values if v.alcance == ValueScope.EXTERNO), Decimal("0"))),
        "supuestos": _parse_json(proposal.supuestos_json),
        "riesgos": _parse_json(proposal.riesgos_json),
        "precio_sugerido_formula": "max(valor_atribuible × fracción, costo × (1 + margen_mínimo), precio_base_plan)",
    }
    proposal.traceability_json = _json(trace)
    db.flush()
    return trace


def proposal_to_detail(db: Session, organization_id: str, proposal_id: str) -> dict[str, Any]:
    proposal = _get_proposal(db, organization_id, proposal_id)
    values = db.query(CommercialProposalValue).filter(CommercialProposalValue.proposal_id == proposal.id).all()
    scenarios = db.query(CommercialProposalScenario).filter(CommercialProposalScenario.proposal_id == proposal.id).all()
    costs = db.query(CommercialProposalCost).filter(CommercialProposalCost.proposal_id == proposal.id).all()
    alerts = db.query(CommercialDoubleCountAlert).filter(
        CommercialDoubleCountAlert.proposal_id == proposal.id, CommercialDoubleCountAlert.resuelto.is_(False)
    ).all()
    history = (
        db.query(CommercialProposalPriceHistory)
        .filter(CommercialProposalPriceHistory.proposal_id == proposal.id)
        .order_by(CommercialProposalPriceHistory.created_at.desc())
        .limit(20)
        .all()
    )
    plan = db.query(CommercialPlan).filter(CommercialPlan.id == proposal.plan_id).first() if proposal.plan_id else None
    trace = _parse_json(proposal.traceability_json) or build_traceability(db, organization_id, proposal_id)

    return {
        "id": proposal.id,
        "codigo": proposal.codigo,
        "titulo": proposal.titulo,
        "estado": proposal.estado,
        "plan": plan_to_dict(plan) if plan else None,
        "credential_mode": proposal.credential_mode,
        "escenario_recomendado": proposal.escenario_recomendado,
        "currency": proposal.currency,
        "valor_total_esperado": float(proposal.valor_total_esperado) if proposal.valor_total_esperado else None,
        "valor_atribuible_total": float(proposal.valor_atribuible_total) if proposal.valor_atribuible_total else None,
        "costo_total": float(proposal.costo_total) if proposal.costo_total else None,
        "precio_sugerido": float(proposal.precio_sugerido) if proposal.precio_sugerido else None,
        "precio_final": float(proposal.precio_final) if proposal.precio_final else None,
        "beneficio_neto_cliente": float(proposal.beneficio_neto_cliente) if proposal.beneficio_neto_cliente else None,
        "roi_pct": float(proposal.roi_pct) if proposal.roi_pct else None,
        "payback_meses": float(proposal.payback_meses) if proposal.payback_meses else None,
        "pct_valor_conservado_cliente": float(proposal.pct_valor_conservado_cliente) if proposal.pct_valor_conservado_cliente else None,
        "pct_valor_capturado_empleados_ia": float(proposal.pct_valor_capturado_empleados_ia) if proposal.pct_valor_capturado_empleados_ia else None,
        "margen_pct": float(proposal.margen_pct) if proposal.margen_pct else None,
        "vigencia_hasta": proposal.vigencia_hasta.isoformat() if proposal.vigencia_hasta else None,
        "valores": [
            {
                "id": v.id,
                "categoria": v.categoria,
                "alcance": v.alcance,
                "naturaleza": v.naturaleza,
                "external_intelligence_ref": v.external_intelligence_ref,
                "valor_bruto": float(v.valor_bruto),
                "atribucion_pct": float(v.atribucion_pct),
                "valor_atribuible": float(v.valor_atribuible),
                "criterio_atribucion": v.criterio_atribucion,
                "opportunity_id": v.opportunity_id,
                "valuation_id": v.valuation_id,
                "linea_base_id": v.linea_base_id,
            }
            for v in values
        ],
        "escenarios": [
            {
                "scenario_type": s.scenario_type,
                "valor_esperado": float(s.valor_esperado) if s.valor_esperado else None,
                "valor_atribuible": float(s.valor_atribuible) if s.valor_atribuible else None,
                "probabilidad": float(s.probabilidad) if s.probabilidad else None,
                "costo": float(s.costo) if s.costo else None,
                "es_recomendado": s.es_recomendado,
                "explicacion": s.explicacion,
            }
            for s in scenarios
        ],
        "costos": [
            {
                "id": c.id,
                "categoria": c.categoria,
                "clase_costo": c.clase_costo,
                "monto": float(c.monto),
                "finops_record_id": c.finops_record_id,
                "descripcion": c.descripcion,
            }
            for c in costs
        ],
        "alertas_doble_conteo": [
            {"id": a.id, "severidad": a.severidad, "tipo": a.tipo, "mensaje": a.mensaje}
            for a in alerts
        ],
        "historial_precios": [
            {
                "precio_sugerido": float(h.precio_sugerido) if h.precio_sugerido else None,
                "precio_modificado": float(h.precio_modificado) if h.precio_modificado else None,
                "justificacion": h.justificacion,
                "action": h.action,
                "created_at": h.created_at.isoformat() if h.created_at else None,
            }
            for h in history
        ],
        "trazabilidad": trace,
        "diagnostic_id": proposal.diagnostic_id,
        "created_at": proposal.created_at.isoformat() if proposal.created_at else None,
        "approved_at": proposal.approved_at.isoformat() if proposal.approved_at else None,
    }


def list_proposals(db: Session, organization_id: str, limit: int = 50) -> list[dict[str, Any]]:
    rows = (
        db.query(CommercialProposal)
        .filter(CommercialProposal.organization_id == organization_id)
        .order_by(CommercialProposal.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "codigo": r.codigo,
            "titulo": r.titulo,
            "estado": r.estado,
            "valor_atribuible_total": float(r.valor_atribuible_total) if r.valor_atribuible_total else None,
            "precio_sugerido": float(r.precio_sugerido) if r.precio_sugerido else None,
            "precio_final": float(r.precio_final) if r.precio_final else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


def simulate_value(db: Session, organization_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Simulación rápida sin persistir propuesta."""
    gross = _decimal(data.get("valor_bruto")) or Decimal("0")
    pct = _decimal(data.get("atribucion_pct"), Decimal("0")) or Decimal("0")
    attributable = _compute_attributable(gross, pct)
    costo = _decimal(data.get("costo_total")) or Decimal("0")
    fraccion = _decimal(data.get("fraccion_valor"), Decimal("0.25")) or Decimal("0.25")
    margen = _decimal(data.get("margen_minimo_pct"), Decimal("0.15")) or Decimal("0.15")
    result = _compute_economics(
        valor_atribuible=attributable,
        costo_total=costo,
        fraccion=fraccion,
        margen_min=margen,
    )
    if data.get("tokens_usados") and data.get("plan_id"):
        plan = get_plan(db, organization_id, data["plan_id"])
        result["consumo_ia"] = _compute_excedente_cost(plan, int(data["tokens_usados"]))
    return result


def simulate_proposal(
    db: Session,
    organization_id: str,
    proposal_id: str,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Simula sobre una propuesta existente sin modificar datos definitivos."""
    proposal = _get_proposal(db, organization_id, proposal_id)
    overrides = overrides or {}
    values = db.query(CommercialProposalValue).filter(CommercialProposalValue.proposal_id == proposal.id).all()
    costs = db.query(CommercialProposalCost).filter(CommercialProposalCost.proposal_id == proposal.id).all()
    plan = db.query(CommercialPlan).filter(CommercialPlan.id == proposal.plan_id).first() if proposal.plan_id else None
    scenario_type = overrides.get("scenario_type", proposal.escenario_recomendado or ScenarioType.BASE)
    scenario = (
        db.query(CommercialProposalScenario)
        .filter(CommercialProposalScenario.proposal_id == proposal.id, CommercialProposalScenario.scenario_type == scenario_type)
        .first()
    )

    valor_atribuible = _decimal(overrides.get("valor_atribuible"))
    if valor_atribuible is None:
        valor_atribuible = sum((v.valor_atribuible for v in values), Decimal("0"))
        if scenario and scenario.valor_atribuible:
            valor_atribuible = scenario.valor_atribuible
        elif scenario and scenario.valor_esperado and scenario.probabilidad:
            valor_atribuible = (scenario.valor_esperado * scenario.probabilidad).quantize(Decimal("0.0001"))
    if overrides.get("atribucion_pct") is not None and overrides.get("valor_bruto"):
        valor_atribuible = _compute_attributable(
            _decimal(overrides["valor_bruto"]) or Decimal("0"),
            _decimal(overrides["atribucion_pct"]) or Decimal("0"),
        )

    costo_total = _decimal(overrides.get("costo_total"))
    if costo_total is None:
        costo_total = sum((c.monto for c in costs), Decimal("0"))
        if scenario and scenario.costo:
            costo_total = max(costo_total, scenario.costo)

    fraccion = _decimal(overrides.get("fraccion_valor"))
    if fraccion is None:
        fraccion = plan.fraccion_valor_sugerida if plan and plan.fraccion_valor_sugerida else Decimal("0.25")
    margen_min = _decimal(overrides.get("margen_minimo_pct"))
    if margen_min is None:
        margen_min = plan.margen_minimo_pct if plan else Decimal("0.15")
    precio_base = plan.precio_base_mensual if plan and plan.precio_base_mensual else Decimal("0")

    result = _compute_economics(
        valor_atribuible=valor_atribuible,
        costo_total=costo_total,
        fraccion=fraccion,
        margen_min=margen_min,
        precio_base=precio_base,
        precio_minimo=plan.precio_minimo if plan else None,
        precio_maximo=plan.precio_maximo if plan else None,
    )
    result["escenario"] = scenario_type
    result["simulacion"] = True
    result["propuesta_id"] = proposal_id
    result["precio_sugerido_actual"] = float(proposal.precio_sugerido) if proposal.precio_sugerido else None
    if plan and overrides.get("tokens_usados"):
        result["consumo_ia"] = _compute_excedente_cost(plan, int(overrides["tokens_usados"]))
    return result
