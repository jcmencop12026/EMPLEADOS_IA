"""Motor de diagnóstico transversal multidominio — Bloque 1220."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.diagnostic_models import (
    CAUSE_TYPES,
    DIAGNOSTIC_DOMAINS,
    DIAGNOSTIC_STATES,
    DIRECTION_TYPES,
    FINDING_CONTENT_TYPES,
    Diagnostic,
    DiagnosticCorrelation,
    DiagnosticFinding,
    DiagnosticIndicatorDefinition,
    DiagnosticIndicatorValue,
    DiagnosticItem,
    DiagnosticOpportunityLink,
    DiagnosticProbableCause,
)
from app.models import Organization
from app.opportunity_models import Opportunity, ProactiveSignal
from app.services import proactive_service as proactive_svc
from app.tenant_scope import ORG_STATUS_ACTIVE

_CORRELATION_NOTE = "Correlación observada; no implica causalidad demostrada"
_METRIC_KEYWORDS = {
    "demanda": ("demanda", "solicitudes", "volumen", "pedidos"),
    "capacidad": ("capacidad", "disponibilidad", "recursos"),
    "tiempo_respuesta": ("tiempo_respuesta", "tiempo", "sla", "espera"),
    "costo": ("costo", "gasto", "egreso"),
    "ingreso": ("ingreso", "recaudo", "facturacion", "cartera"),
    "error": ("error", "rechazo", "defecto", "incidencia"),
    "conversion": ("conversion", "tasa_conversion"),
    "cumplimiento": ("cumplimiento", "incumplimiento", "sla"),
}


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


def _new_correlation() -> str:
    return str(uuid.uuid4())


def _normalize_domain(raw: str) -> str:
    key = raw.strip().upper().replace(" ", "_").replace("/", "_")
    if key in DIAGNOSTIC_DOMAINS:
        return key
    mapping = {
        "FINANCIERO": "FINANCIERO",
        "FINANZAS": "FINANCIERO",
        "OPERATIVO": "OPERATIVO",
        "OPERACIONES": "OPERATIVO",
        "COMERCIAL": "COMERCIAL",
        "SERVICIO": "SERVICIO",
        "CALIDAD": "CALIDAD",
        "RRHH": "TALENTO_HUMANO",
        "TECNOLOGIA": "TECNOLOGIA",
        "LOGISTICA": "LOGISTICA",
        "CUMPLIMIENTO": "CUMPLIMIENTO",
        "SALUD": "ASISTENCIAL_SALUD",
        "ASISTENCIAL": "ASISTENCIAL_SALUD",
        "MERCADO": "EXTERNO_MERCADO",
        "REGULACION": "EXTERNO_REGULACION",
    }
    return mapping.get(key, "OTRO")


def _ensure_org_active(db: Session, organization_id: str) -> Organization:
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa no encontrada")
    if org.status != ORG_STATUS_ACTIVE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="La empresa está inactiva")
    return org


def _next_codigo(db: Session, org_id: str, prefix: str) -> str:
    if prefix == "DIAG":
        count = db.query(func.count(Diagnostic.id)).filter(Diagnostic.organization_id == org_id).scalar() or 0
        return f"DIAG-{count + 1:05d}"
    count = db.query(func.count(DiagnosticFinding.id)).filter(DiagnosticFinding.organization_id == org_id).scalar() or 0
    return f"{prefix}-{count + 1:05d}"


def _metric_category(metrica: str) -> str | None:
    m = metrica.lower()
    for cat, keywords in _METRIC_KEYWORDS.items():
        if any(k in m for k in keywords):
            return cat
    return None


def _parse_numeric(value: str | float | int | Decimal | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _severity_from_magnitude(magnitude: float | None, umbral: float | None = None) -> str:
    if magnitude is None:
        return "MEDIA"
    ref = umbral or abs(magnitude) or 1
    ratio = abs(magnitude) / max(ref, 1)
    if ratio >= 2:
        return "ALTA"
    if ratio >= 1.2:
        return "MEDIA"
    return "BAJA"


# --- Configuración indicadores ---

def create_indicator_definition(
    db: Session,
    *,
    organization_id: str,
    code: str,
    name: str,
    dominio: str,
    proceso: str | None = None,
    subproceso: str | None = None,
    unidad: str | None = None,
    direccion_esperada: str = "CUALQUIERA",
    periodicidad: str | None = None,
    umbral_min: float | None = None,
    umbral_max: float | None = None,
    fuente_code: str | None = None,
    metadata: dict | None = None,
    user_id: str | None = None,
) -> DiagnosticIndicatorDefinition:
    _ensure_org_active(db, organization_id)
    dom = _normalize_domain(dominio)
    if direccion_esperada not in DIRECTION_TYPES:
        raise HTTPException(status_code=422, detail="Dirección esperada no válida")
    normalized_code = code.strip().lower()
    existing = (
        db.query(DiagnosticIndicatorDefinition)
        .filter(
            DiagnosticIndicatorDefinition.organization_id == organization_id,
            DiagnosticIndicatorDefinition.code == normalized_code,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Ya existe un indicador con ese código")
    row = DiagnosticIndicatorDefinition(
        organization_id=organization_id,
        code=normalized_code,
        name=name.strip(),
        dominio=dom,
        proceso=proceso,
        subproceso=subproceso,
        unidad=unidad,
        direccion_esperada=direccion_esperada,
        periodicidad=periodicidad,
        umbral_min=Decimal(str(umbral_min)) if umbral_min is not None else None,
        umbral_max=Decimal(str(umbral_max)) if umbral_max is not None else None,
        fuente_code=fuente_code,
        metadata_json=_json(metadata) if metadata else None,
    )
    db.add(row)
    db.flush()
    write_audit(
        db,
        action="diagnostic.indicator.created",
        organization_id=organization_id,
        user_id=user_id,
        detail=_json({"indicator_id": row.id, "code": row.code}),
        commit=False,
    )
    return row


def list_indicator_definitions(db: Session, organization_id: str) -> list[DiagnosticIndicatorDefinition]:
    return (
        db.query(DiagnosticIndicatorDefinition)
        .filter(DiagnosticIndicatorDefinition.organization_id == organization_id)
        .order_by(DiagnosticIndicatorDefinition.dominio, DiagnosticIndicatorDefinition.name)
        .all()
    )


def indicator_def_to_dict(row: DiagnosticIndicatorDefinition) -> dict[str, Any]:
    return {
        "id": row.id,
        "code": row.code,
        "name": row.name,
        "dominio": row.dominio,
        "proceso": row.proceso,
        "subproceso": row.subproceso,
        "unidad": row.unidad,
        "direccion_esperada": row.direccion_esperada,
        "periodicidad": row.periodicidad,
        "umbral_min": float(row.umbral_min) if row.umbral_min is not None else None,
        "umbral_max": float(row.umbral_max) if row.umbral_max is not None else None,
        "fuente_code": row.fuente_code,
        "metadata": _parse_json(row.metadata_json),
        "is_active": row.is_active,
    }


def indicator_value_to_dict(row: DiagnosticIndicatorValue) -> dict[str, Any]:
    return {
        "id": row.id,
        "dominio": row.dominio,
        "proceso": row.proceso,
        "metrica": row.metrica,
        "valor": float(row.valor) if row.valor is not None else None,
        "unidad": row.unidad,
        "signal_id": row.signal_id,
        "periodo_referencia": row.periodo_referencia.isoformat() if row.periodo_referencia else None,
    }


def finding_to_dict(row: DiagnosticFinding) -> dict[str, Any]:
    return {
        "id": row.id,
        "codigo": row.codigo,
        "tipo_contenido": row.tipo_contenido,
        "que_ocurre": row.que_ocurre,
        "donde": row.donde,
        "desde_cuando": row.desde_cuando.isoformat() if row.desde_cuando else None,
        "magnitud": float(row.magnitud) if row.magnitud is not None else None,
        "severidad": row.severidad,
        "confianza": float(row.confianza),
        "dominio": row.dominio,
        "proceso": row.proceso,
        "evidencia": _parse_json(row.evidencia_json),
        "indicadores": _parse_json(row.indicadores_json),
        "signal_ids": _parse_json(row.signal_ids_json),
        "estado": row.estado,
    }


def cause_to_dict(row: DiagnosticProbableCause) -> dict[str, Any]:
    return {
        "id": row.id,
        "tipo": row.tipo,
        "descripcion": row.descripcion,
        "justificacion": row.justificacion,
        "evidencia": _parse_json(row.evidencia_json),
        "confianza": float(row.confianza),
        "fuentes": _parse_json(row.fuentes_json),
        "finding_id": row.finding_id,
    }


# --- Consolidación indicadores desde señales 1120 ---

def consolidate_indicators_from_signals(
    db: Session,
    organization_id: str,
    *,
    periodo_inicio: datetime | None = None,
    periodo_fin: datetime | None = None,
    dominios: list[str] | None = None,
) -> list[DiagnosticIndicatorValue]:
    query = db.query(ProactiveSignal).filter(ProactiveSignal.organization_id == organization_id)
    if periodo_inicio:
        query = query.filter(ProactiveSignal.created_at >= periodo_inicio)
    if periodo_fin:
        query = query.filter(ProactiveSignal.created_at <= periodo_fin)
    if dominios:
        normalized = [_normalize_domain(d) for d in dominios]
        query = query.filter(ProactiveSignal.dominio.in_(normalized))
    signals = query.order_by(ProactiveSignal.created_at.asc()).all()

    defs = {
        d.code: d
        for d in db.query(DiagnosticIndicatorDefinition)
        .filter(
            DiagnosticIndicatorDefinition.organization_id == organization_id,
            DiagnosticIndicatorDefinition.is_active.is_(True),
        )
        .all()
    }
    values: list[DiagnosticIndicatorValue] = []
    for signal in signals:
        metrica = (signal.metrica or signal.tipo or "sin_metrica").strip().lower()
        dominio = _normalize_domain(signal.dominio)
        valor = _parse_numeric(signal.valor_metrica)
        matched_def = None
        for code, idef in defs.items():
            if idef.dominio == dominio and (idef.proceso == signal.proceso or idef.code in metrica):
                matched_def = idef
                break
        row = DiagnosticIndicatorValue(
            organization_id=organization_id,
            indicator_def_id=matched_def.id if matched_def else None,
            signal_id=signal.id,
            dominio=dominio,
            proceso=signal.proceso,
            metrica=metrica,
            valor=Decimal(str(valor)) if valor is not None else None,
            unidad=signal.unidad,
            periodo_referencia=signal.signal_at or signal.created_at,
            metadata_json=_json({
                "origen": signal.origen,
                "referencia": signal.source_reference,
                "modo_ingesta": signal.modo_ingesta,
            }),
        )
        db.add(row)
        values.append(row)
    db.flush()
    return values


def _create_finding_from_signal(
    db: Session,
    organization_id: str,
    signal: ProactiveSignal,
    indicator: DiagnosticIndicatorValue,
    idef: DiagnosticIndicatorDefinition | None,
) -> DiagnosticFinding | None:
    valor = _parse_numeric(indicator.valor)
    if valor is None:
        return None

    breach = False
    umbral = None
    if idef:
        if idef.umbral_max is not None and valor > float(idef.umbral_max):
            breach = True
            umbral = float(idef.umbral_max)
        if idef.umbral_min is not None and valor < float(idef.umbral_min):
            breach = True
            umbral = float(idef.umbral_min)
    else:
        meta = _parse_json(signal.metadata_json) or {}
        umbral_meta = meta.get("umbral") or meta.get("umbral_max")
        if umbral_meta is not None and valor > float(umbral_meta):
            breach = True
            umbral = float(umbral_meta)

    payload = _parse_json(signal.payload_json) or {}
    impacto = payload.get("impacto_estimado")
    if not breach and impacto and valor:
        breach = True

    if not breach and signal.severidad in ("ALTA", "CRITICA"):
        breach = True

    if not breach:
        return None

    codigo = _next_codigo(db, organization_id, "HAL")
    finding = DiagnosticFinding(
        organization_id=organization_id,
        codigo=codigo,
        tipo_contenido="HECHO",
        que_ocurre=signal.evidencia_resumen or f"Indicador {indicator.metrica} fuera de rango esperado",
        donde=signal.dimension or signal.proceso or indicator.dominio,
        desde_cuando=signal.signal_at or signal.created_at,
        magnitud=Decimal(str(valor)),
        severidad=_severity_from_magnitude(valor, umbral),
        confianza=float(signal.confianza or 0.75),
        dominio=indicator.dominio,
        proceso=signal.proceso,
        evidencia_json=_json({
            "resumen": signal.evidencia_resumen,
            "referencia": signal.source_reference,
            "valor": valor,
            "unidad": signal.unidad,
            "umbral": umbral,
        }),
        indicadores_json=_json([indicator_value_to_dict(indicator)]),
        signal_ids_json=_json([signal.id]),
        source_id=signal.source_id,
    )
    db.add(finding)
    db.flush()
    write_audit(
        db,
        action="diagnostic.finding.created",
        organization_id=organization_id,
        user_id=None,
        detail=_json({"finding_id": finding.id, "codigo": finding.codigo, "tipo": "HECHO"}),
        commit=False,
    )
    return finding


def detect_findings_from_indicators(
    db: Session,
    organization_id: str,
    indicators: list[DiagnosticIndicatorValue],
    signals_by_id: dict[str, ProactiveSignal],
) -> list[DiagnosticFinding]:
    defs = {
        d.id: d
        for d in db.query(DiagnosticIndicatorDefinition)
        .filter(DiagnosticIndicatorDefinition.organization_id == organization_id)
        .all()
    }
    findings: list[DiagnosticFinding] = []
    for indicator in indicators:
        signal = signals_by_id.get(indicator.signal_id or "")
        if not signal:
            continue
        idef = defs.get(indicator.indicator_def_id or "")
        finding = _create_finding_from_signal(db, organization_id, signal, indicator, idef)
        if finding:
            findings.append(finding)
    return findings


def _find_metric_values(
    indicators: list[DiagnosticIndicatorValue],
    category: str,
) -> list[DiagnosticIndicatorValue]:
    return [i for i in indicators if _metric_category(i.metrica) == category]


def detect_correlations(
    db: Session,
    organization_id: str,
    indicators: list[DiagnosticIndicatorValue],
    findings: list[DiagnosticFinding],
) -> list[DiagnosticCorrelation]:
    correlations: list[DiagnosticCorrelation] = []
    demanda = _find_metric_values(indicators, "demanda")
    capacidad = _find_metric_values(indicators, "capacidad")
    tiempo = _find_metric_values(indicators, "tiempo_respuesta")

    if demanda and capacidad and tiempo:
        d_val = _parse_numeric(demanda[-1].valor)
        c_vals = [_parse_numeric(c.valor) for c in capacidad if _parse_numeric(c.valor) is not None]
        t_vals = [_parse_numeric(t.valor) for t in tiempo if _parse_numeric(t.valor) is not None]
        if d_val and c_vals and t_vals:
            c_stable = max(c_vals) - min(c_vals) < max(c_vals, default=1) * 0.1
            t_growing = t_vals[-1] > t_vals[0] if len(t_vals) > 1 else t_vals[0] > 0
            if c_stable and t_growing:
                related_findings = [f.id for f in findings[:3]]
                corr = DiagnosticCorrelation(
                    organization_id=organization_id,
                    titulo="Demanda elevada con capacidad estable y tiempos crecientes",
                    descripcion=(
                        "Se observa correlación entre aumento de demanda, capacidad relativamente estable "
                        "y aumento del tiempo de respuesta. Esto sugiere posible cuello de botella operativo."
                    ),
                    finding_ids_json=_json(related_findings),
                    indicator_value_ids_json=_json(
                        [demanda[-1].id, capacidad[-1].id, tiempo[-1].id]
                    ),
                    confianza=0.65,
                    evidencia_json=_json({
                        "demanda": d_val,
                        "capacidad": c_vals[-1],
                        "tiempo_respuesta": t_vals[-1],
                    }),
                    es_causal=False,
                    nota_causalidad=_CORRELATION_NOTE,
                )
                db.add(corr)
                db.flush()
                correlations.append(corr)

                interp = DiagnosticFinding(
                    organization_id=organization_id,
                    codigo=_next_codigo(db, organization_id, "HAL"),
                    tipo_contenido="INTERPRETACION",
                    que_ocurre="Posible cuello de botella por desbalance demanda-capacidad",
                    donde="Transversal (múltiples procesos)",
                    desde_cuando=_utcnow(),
                    magnitud=Decimal(str(t_vals[-1])),
                    severidad="ALTA",
                    confianza=0.6,
                    dominio="OPERATIVO",
                    proceso="atencion",
                    evidencia_json=_json({"correlacion_id": corr.id, "nota": _CORRELATION_NOTE}),
                    indicadores_json=_json([
                        indicator_value_to_dict(demanda[-1]),
                        indicator_value_to_dict(capacidad[-1]),
                        indicator_value_to_dict(tiempo[-1]),
                    ]),
                    signal_ids_json=_json(
                        [s for s in [demanda[-1].signal_id, capacidad[-1].signal_id, tiempo[-1].signal_id] if s]
                    ),
                )
                db.add(interp)
                db.flush()
                findings.append(interp)
                write_audit(
                    db,
                    action="diagnostic.finding.created",
                    organization_id=organization_id,
                    user_id=None,
                    detail=_json({"finding_id": interp.id, "tipo": "INTERPRETACION"}),
                    commit=False,
                )

    if len(findings) >= 2:
        domains = {f.dominio for f in findings}
        if len(domains) > 1:
            corr = DiagnosticCorrelation(
                organization_id=organization_id,
                titulo="Hallazgos correlacionados en múltiples dominios",
                descripcion=f"Hallazgos detectados en dominios: {', '.join(sorted(domains))}",
                finding_ids_json=_json([f.id for f in findings]),
                confianza=0.55,
                evidencia_json=_json({"dominios": list(domains)}),
                es_causal=False,
                nota_causalidad=_CORRELATION_NOTE,
            )
            db.add(corr)
            db.flush()
            correlations.append(corr)

    return correlations


def infer_probable_causes(
    db: Session,
    organization_id: str,
    findings: list[DiagnosticFinding],
    correlations: list[DiagnosticCorrelation],
    diagnostic_id: str | None = None,
) -> list[DiagnosticProbableCause]:
    causes: list[DiagnosticProbableCause] = []
    for finding in findings:
        if finding.tipo_contenido == "HECHO":
            cause = DiagnosticProbableCause(
                organization_id=organization_id,
                finding_id=finding.id,
                diagnostic_id=diagnostic_id,
                tipo="PROBABLE",
                descripcion=f"Causa probable relacionada con: {finding.que_ocurre[:200]}",
                justificacion="Inferencia determinística a partir de evidencia de señal e indicador",
                evidencia_json=finding.evidencia_json,
                confianza=min(0.85, float(finding.confianza)),
                fuentes_json=_json({"signal_ids": _parse_json(finding.signal_ids_json)}),
            )
            db.add(cause)
            causes.append(cause)
        elif finding.tipo_contenido == "INTERPRETACION":
            cause = DiagnosticProbableCause(
                organization_id=organization_id,
                finding_id=finding.id,
                diagnostic_id=diagnostic_id,
                tipo="HIPOTESIS",
                descripcion=f"Hipótesis transversal: {finding.que_ocurre[:200]}",
                justificacion="Hipótesis basada en correlación observada — requiere validación",
                evidencia_json=finding.evidencia_json,
                confianza=0.5,
                fuentes_json=_json({"tipo": "correlacion"}),
            )
            db.add(cause)
            causes.append(cause)

    for corr in correlations:
        cause = DiagnosticProbableCause(
            organization_id=organization_id,
            diagnostic_id=diagnostic_id,
            tipo="HIPOTESIS",
            descripcion=corr.titulo,
            justificacion=corr.nota_causalidad,
            evidencia_json=corr.evidencia_json,
            confianza=float(corr.confianza),
            fuentes_json=_json({"correlation_id": corr.id}),
        )
        db.add(cause)
        causes.append(cause)

    db.flush()
    for cause in causes:
        write_audit(
            db,
            action="diagnostic.cause.added",
            organization_id=organization_id,
            user_id=None,
            detail=_json({"cause_id": cause.id, "tipo": cause.tipo}),
            commit=False,
        )
    return causes


def _score_item(
    finding: DiagnosticFinding,
    cause: DiagnosticProbableCause | None,
    payload: dict | None,
) -> dict[str, Any]:
    payload = payload or {}
    impacto = _parse_numeric(payload.get("impacto_estimado")) or _parse_numeric(finding.magnitud) or 0
    urgencia_map = {"CRITICA": 1.0, "ALTA": 0.8, "MEDIA": 0.5, "BAJA": 0.2}
    urgencia = urgencia_map.get(finding.severidad, 0.5)
    riesgo = 0.6 if finding.severidad == "ALTA" else 0.4
    frecuencia = 0.5
    magnitud = min(abs(impacto) / 10_000_000, 1.0) if impacto else 0.2
    probabilidad = float(cause.confianza) if cause else float(finding.confianza)
    facilidad = 0.6
    valor = _parse_numeric(payload.get("valor_potencial")) or impacto * 0.7
    valor_norm = min(abs(valor or 0) / 10_000_000, 1.0)

    componentes = {
        "impacto": round(magnitud * 0.25, 4),
        "urgencia": round(urgencia * 0.20, 4),
        "riesgo": round(riesgo * 0.15, 4),
        "frecuencia": round(frecuencia * 0.10, 4),
        "magnitud": round(magnitud * 0.10, 4),
        "probabilidad": round(probabilidad * 0.10, 4),
        "facilidad": round(facilidad * 0.05, 4),
        "valor_potencial": round(valor_norm * 0.05, 4),
    }
    score = round(sum(componentes.values()), 4)
    return {"prioridad_score": score, "componentes": componentes, "valor_potencial": valor}


def _build_explicacion(
    diagnostic: Diagnostic,
    findings: list[DiagnosticFinding],
    causes: list[DiagnosticProbableCause],
    items: list[DiagnosticItem],
) -> dict[str, Any]:
    top = items[0] if items else None
    top_finding = next((f for f in findings if top and f.id == top.hallazgo_id), findings[0] if findings else None)
    top_cause = causes[0] if causes else None
    return {
        "que_esta_pasando": top_finding.que_ocurre if top_finding else diagnostic.resumen,
        "donde": top_finding.donde if top_finding else None,
        "desde_cuando": top_finding.desde_cuando.isoformat() if top_finding and top_finding.desde_cuando else None,
        "evidencia": _parse_json(top_finding.evidencia_json) if top_finding else None,
        "impacto": _parse_json(top.impacto_json) if top else None,
        "causas_probables": [cause_to_dict(c) for c in causes[:5]],
        "oportunidades": "Ver oportunidades vinculadas en el detalle del diagnóstico",
        "que_deberia_hacerse": (
            _parse_json(top.accion_recomendada_json).get("accion")
            if top and top.accion_recomendada_json
            else "Evaluar hallazgos priorizados y validar hipótesis antes de actuar"
        ),
        "nota_evidencia": "Las interpretaciones y hipótesis requieren validación; correlación no implica causalidad",
    }


def _make_opp_dedupe_key(org_id: str, diagnostic_id: str, finding_id: str) -> str:
    raw = f"{org_id}|diag|{diagnostic_id}|{finding_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:64]


def _create_opportunity_from_finding(
    db: Session,
    organization_id: str,
    diagnostic: Diagnostic,
    finding: DiagnosticFinding,
    cause: DiagnosticProbableCause | None,
    user_id: str | None,
) -> str | None:
    dedupe_key = _make_opp_dedupe_key(organization_id, diagnostic.id, finding.id)
    existing = (
        db.query(DiagnosticOpportunityLink)
        .filter(
            DiagnosticOpportunityLink.organization_id == organization_id,
            DiagnosticOpportunityLink.dedupe_key == dedupe_key,
        )
        .first()
    )
    if existing:
        return existing.opportunity_id

    signal_ids = _parse_json(finding.signal_ids_json) or []
    primary_signal = (
        db.query(ProactiveSignal).filter(ProactiveSignal.id == signal_ids[0]).first()
        if signal_ids
        else None
    )
    payload = _parse_json(primary_signal.payload_json) if primary_signal else {}
    payload = payload or {}
    payload.setdefault("titulo", f"Oportunidad desde diagnóstico: {finding.que_ocurre[:120]}")
    payload.setdefault("descripcion", cause.descripcion if cause else finding.que_ocurre)
    payload.setdefault("tipo_oportunidad", "OPERATIVA")
    payload.setdefault("impacto_estimado", _parse_numeric(finding.magnitud))
    payload.setdefault("evidencia", _parse_json(finding.evidencia_json))
    payload.setdefault("indicadores", _parse_json(finding.indicadores_json))

    if primary_signal:
        opp = proactive_svc.process_signal(db, primary_signal, user_id=user_id)
    else:
        signal = ProactiveSignal(
            organization_id=organization_id,
            tipo="diagnostico_transversal",
            dominio=finding.dominio,
            origen="diagnostic_engine",
            modo_ingesta="REAL",
            evento=f"diag_{finding.codigo}",
            source_reference=finding.codigo,
            proceso=finding.proceso,
            evidencia_resumen=finding.que_ocurre[:500],
            payload_json=_json(payload),
            severidad=finding.severidad,
            confianza=float(finding.confianza),
            dedupe_key=dedupe_key,
            estado_procesamiento="RECIBIDA",
            correlation_id=diagnostic.correlation_id,
            signal_at=finding.desde_cuando or _utcnow(),
        )
        db.add(signal)
        db.flush()
        opp = proactive_svc.process_signal(db, signal, user_id=user_id)
        primary_signal = signal

    if not opp:
        return None

    link = DiagnosticOpportunityLink(
        organization_id=organization_id,
        diagnostic_id=diagnostic.id,
        finding_id=finding.id,
        signal_id=primary_signal.id if primary_signal else None,
        opportunity_id=opp.id,
        dedupe_key=dedupe_key,
    )
    db.add(link)
    proactive_svc.add_trace(
        db,
        organization_id=organization_id,
        correlation_id=diagnostic.correlation_id or _new_correlation(),
        etapa="DIAGNOSTICO_OPORTUNIDAD",
        opportunity_id=opp.id,
        signal_id=primary_signal.id if primary_signal else None,
        detalle={
            "diagnostic_id": diagnostic.id,
            "finding_id": finding.id,
            "finding_codigo": finding.codigo,
        },
    )
    write_audit(
        db,
        action="diagnostic.opportunity.created",
        organization_id=organization_id,
        user_id=user_id,
        detail=_json({
            "diagnostic_id": diagnostic.id,
            "finding_id": finding.id,
            "opportunity_id": opp.id,
        }),
        commit=False,
    )
    return opp.id


def generate_diagnostic(
    db: Session,
    *,
    organization_id: str,
    user_id: str | None = None,
    periodo_inicio: datetime | None = None,
    periodo_fin: datetime | None = None,
    dominios: list[str] | None = None,
) -> dict[str, Any]:
    """Pipeline completo: señales → indicadores → hallazgos → diagnóstico → oportunidades."""
    _ensure_org_active(db, organization_id)
    periodo_fin = periodo_fin or _utcnow()
    periodo_inicio = periodo_inicio or (periodo_fin - timedelta(days=30))

    indicators = consolidate_indicators_from_signals(
        db,
        organization_id,
        periodo_inicio=periodo_inicio,
        periodo_fin=periodo_fin,
        dominios=dominios,
    )
    if not indicators:
        raise HTTPException(status_code=422, detail="No hay señales en el periodo para generar diagnóstico")

    signal_ids = [i.signal_id for i in indicators if i.signal_id]
    signals = (
        db.query(ProactiveSignal)
        .filter(ProactiveSignal.id.in_(signal_ids))
        .all()
        if signal_ids
        else []
    )
    signals_by_id = {s.id: s for s in signals}

    findings = detect_findings_from_indicators(db, organization_id, indicators, signals_by_id)
    correlations = detect_correlations(db, organization_id, indicators, findings)

    corr_id = _new_correlation()
    diagnostic = Diagnostic(
        organization_id=organization_id,
        codigo=_next_codigo(db, organization_id, "DIAG"),
        version=1,
        periodo_inicio=periodo_inicio,
        periodo_fin=periodo_fin,
        estado="GENERADO",
        dominios_json=_json(list({_normalize_domain(i.dominio) for i in indicators})),
        procesos_json=_json(list({i.proceso for i in indicators if i.proceso})),
        resumen=f"Diagnóstico transversal con {len(findings)} hallazgos en {len(indicators)} indicadores",
        correlation_id=corr_id,
        created_by=user_id,
    )
    db.add(diagnostic)
    db.flush()

    causes = infer_probable_causes(db, organization_id, findings, correlations, diagnostic.id)

    items: list[DiagnosticItem] = []
    opportunity_ids: list[str] = []
    for idx, finding in enumerate(findings):
        cause = next((c for c in causes if c.finding_id == finding.id), None)
        payload: dict[str, Any] = {}
        sig_ids = _parse_json(finding.signal_ids_json) or []
        if sig_ids and sig_ids[0] in signals_by_id:
            payload = _parse_json(signals_by_id[sig_ids[0]].payload_json) or {}

        scoring = _score_item(finding, cause, payload)
        accion = {
            "accion": f"Atender hallazgo {finding.codigo}: {finding.que_ocurre[:150]}",
            "responsable_propuesto": None,
            "indicador_seguimiento": (_parse_json(finding.indicadores_json) or [{}])[0].get("metrica")
            if _parse_json(finding.indicadores_json)
            else None,
            "beneficio_potencial": scoring.get("valor_potencial"),
            "nota": "Responsable no asignado — requiere designación humana",
        }
        item = DiagnosticItem(
            diagnostic_id=diagnostic.id,
            organization_id=organization_id,
            item_type="HALLAZGO",
            hallazgo_id=finding.id,
            causa_id=cause.id if cause else None,
            prioridad_score=scoring["prioridad_score"],
            impacto_json=_json(scoring),
            accion_recomendada_json=_json(accion),
            orden=idx,
        )
        db.add(item)
        items.append(item)

        if finding.tipo_contenido == "HECHO" and finding.severidad in ("ALTA", "MEDIA"):
            opp_id = _create_opportunity_from_finding(
                db, organization_id, diagnostic, finding, cause, user_id
            )
            if opp_id and opp_id not in opportunity_ids:
                opportunity_ids.append(opp_id)

    db.flush()
    items.sort(key=lambda x: float(x.prioridad_score or 0), reverse=True)
    for i, item in enumerate(items):
        item.orden = i

    diagnostic.prioridad_score = float(items[0].prioridad_score) if items else 0
    diagnostic.explicacion_json = _json(_build_explicacion(diagnostic, findings, causes, items))

    write_audit(
        db,
        action="diagnostic.generated",
        organization_id=organization_id,
        user_id=user_id,
        detail=_json({
            "diagnostic_id": diagnostic.id,
            "codigo": diagnostic.codigo,
            "hallazgos": len(findings),
            "oportunidades": len(opportunity_ids),
        }),
        commit=False,
    )

    return diagnostic_to_detail(db, organization_id, diagnostic.id)


def validate_diagnostic(
    db: Session,
    organization_id: str,
    diagnostic_id: str,
    user_id: str,
) -> dict[str, Any]:
    diagnostic = _get_diagnostic(db, organization_id, diagnostic_id)
    if diagnostic.estado == "VALIDADO":
        return diagnostic_to_detail(db, organization_id, diagnostic_id)
    diagnostic.estado = "VALIDADO"
    diagnostic.validated_by = user_id
    diagnostic.validated_at = _utcnow()
    write_audit(
        db,
        action="diagnostic.validated",
        organization_id=organization_id,
        user_id=user_id,
        detail=_json({"diagnostic_id": diagnostic.id}),
        commit=False,
    )
    return diagnostic_to_detail(db, organization_id, diagnostic_id)


def _get_diagnostic(db: Session, organization_id: str, diagnostic_id: str) -> Diagnostic:
    row = (
        db.query(Diagnostic)
        .filter(Diagnostic.id == diagnostic_id, Diagnostic.organization_id == organization_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Diagnóstico no encontrado")
    return row


def list_diagnostics(db: Session, organization_id: str, limit: int = 50) -> list[Diagnostic]:
    return (
        db.query(Diagnostic)
        .filter(Diagnostic.organization_id == organization_id)
        .order_by(Diagnostic.created_at.desc())
        .limit(limit)
        .all()
    )


def diagnostic_to_summary(row: Diagnostic) -> dict[str, Any]:
    return {
        "id": row.id,
        "codigo": row.codigo,
        "version": row.version,
        "estado": row.estado,
        "periodo_inicio": row.periodo_inicio.isoformat() if row.periodo_inicio else None,
        "periodo_fin": row.periodo_fin.isoformat() if row.periodo_fin else None,
        "dominios": _parse_json(row.dominios_json),
        "resumen": row.resumen,
        "prioridad_score": float(row.prioridad_score) if row.prioridad_score else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "validated_at": row.validated_at.isoformat() if row.validated_at else None,
    }


def diagnostic_to_detail(db: Session, organization_id: str, diagnostic_id: str) -> dict[str, Any]:
    diagnostic = _get_diagnostic(db, organization_id, diagnostic_id)
    items = (
        db.query(DiagnosticItem)
        .filter(DiagnosticItem.diagnostic_id == diagnostic.id)
        .order_by(DiagnosticItem.orden.asc())
        .all()
    )
    finding_ids = [i.hallazgo_id for i in items if i.hallazgo_id]
    findings = (
        db.query(DiagnosticFinding)
        .filter(DiagnosticFinding.id.in_(finding_ids))
        .all()
        if finding_ids
        else []
    )
    findings_map = {f.id: f for f in findings}
    causes = (
        db.query(DiagnosticProbableCause)
        .filter(DiagnosticProbableCause.diagnostic_id == diagnostic.id)
        .all()
    )
    correlations = (
        db.query(DiagnosticCorrelation)
        .filter(DiagnosticCorrelation.organization_id == organization_id)
        .order_by(DiagnosticCorrelation.created_at.desc())
        .limit(20)
        .all()
    )
    opp_links = (
        db.query(DiagnosticOpportunityLink)
        .filter(DiagnosticOpportunityLink.diagnostic_id == diagnostic.id)
        .all()
    )
    indicators = (
        db.query(DiagnosticIndicatorValue)
        .filter(DiagnosticIndicatorValue.organization_id == organization_id)
        .order_by(DiagnosticIndicatorValue.created_at.desc())
        .limit(100)
        .all()
    )

    structured_items = []
    for item in items:
        finding = findings_map.get(item.hallazgo_id or "")
        cause = next((c for c in causes if c.id == item.causa_id), None)
        opp_link = next((l for l in opp_links if l.finding_id == item.hallazgo_id), None)
        structured_items.append({
            "hallazgo": finding_to_dict(finding) if finding else None,
            "evidencia": _parse_json(finding.evidencia_json) if finding else None,
            "causa_probable": cause_to_dict(cause) if cause else None,
            "impacto": _parse_json(item.impacto_json),
            "prioridad": float(item.prioridad_score) if item.prioridad_score else None,
            "accion_recomendada": _parse_json(item.accion_recomendada_json),
            "responsable_propuesto": (_parse_json(item.accion_recomendada_json) or {}).get("responsable_propuesto"),
            "indicador_seguimiento": (_parse_json(item.accion_recomendada_json) or {}).get("indicador_seguimiento"),
            "beneficio_potencial": (_parse_json(item.accion_recomendada_json) or {}).get("beneficio_potencial"),
            "opportunity_id": opp_link.opportunity_id if opp_link else None,
        })

    return {
        **diagnostic_to_summary(diagnostic),
        "procesos": _parse_json(diagnostic.procesos_json),
        "explicacion": _parse_json(diagnostic.explicacion_json),
        "hallazgos": [finding_to_dict(f) for f in findings],
        "causas": [cause_to_dict(c) for c in causes],
        "correlaciones": [
            {
                "id": c.id,
                "titulo": c.titulo,
                "descripcion": c.descripcion,
                "confianza": float(c.confianza),
                "es_causal": c.es_causal,
                "nota_causalidad": c.nota_causalidad,
                "evidencia": _parse_json(c.evidencia_json),
            }
            for c in correlations
            if _parse_json(c.finding_ids_json) and any(fid in finding_ids for fid in (_parse_json(c.finding_ids_json) or []))
        ] or [
            {
                "id": c.id,
                "titulo": c.titulo,
                "descripcion": c.descripcion,
                "confianza": float(c.confianza),
                "es_causal": c.es_causal,
                "nota_causalidad": c.nota_causalidad,
            }
            for c in correlations[:5]
        ],
        "indicadores": [indicator_value_to_dict(i) for i in indicators[:30]],
        "items_estructurados": structured_items,
        "oportunidades": [
            {
                "opportunity_id": l.opportunity_id,
                "finding_id": l.finding_id,
                "signal_id": l.signal_id,
            }
            for l in opp_links
        ],
        "correlation_id": diagnostic.correlation_id,
    }


def get_diagnostic_trace(db: Session, organization_id: str, diagnostic_id: str) -> dict[str, Any]:
    detail = diagnostic_to_detail(db, organization_id, diagnostic_id)
    traces = []
    for opp in detail.get("oportunidades", []):
        if opp.get("opportunity_id"):
            trace = proactive_svc.get_full_trace(db, opp["opportunity_id"], organization_id)
            if trace:
                traces.append(trace)
    return {
        "diagnostic_id": diagnostic_id,
        "correlation_id": detail.get("correlation_id"),
        "cadena": "SEÑAL → INDICADOR → HALLAZGO → DIAGNÓSTICO → OPORTUNIDAD",
        "oportunidades_trazas": traces,
        "hallazgos": detail.get("hallazgos"),
        "oportunidades": detail.get("oportunidades"),
    }
