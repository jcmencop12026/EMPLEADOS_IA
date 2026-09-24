"""Servicio — Inteligencia externa y oportunidades estratégicas (1240)."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.external_intelligence_enums import (
    ExternalSourceType,
    FreshnessStatus,
    IngestionChannel,
    RelevanceLevel,
    SignalClassification,
)
from app.external_models import (
    ExternalEvidence,
    ExternalSignalExtension,
    ExternalSource,
    OrganizationExternalContext,
)
from app.opportunity_models import Opportunity, ProactiveSignal
from app.services import proactive_service as proactive_svc
from app.services import signal_ingestion_service as sig_svc

EXTERNAL_ORIGIN_PREFIX = "externo:"


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


def _parse_dt(value: datetime | str | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def get_or_create_context(db: Session, organization_id: str) -> OrganizationExternalContext:
    ctx = (
        db.query(OrganizationExternalContext)
        .filter(OrganizationExternalContext.organization_id == organization_id)
        .first()
    )
    if ctx:
        return ctx
    ctx = OrganizationExternalContext(organization_id=organization_id)
    db.add(ctx)
    db.flush()
    return ctx


def update_context(db: Session, organization_id: str, data: dict[str, Any], user_id: str | None = None) -> OrganizationExternalContext:
    ctx = get_or_create_context(db, organization_id)
    for field in (
        "sector",
        "mercado",
        "productos_servicios",
        "geografias",
        "clientes_objetivo",
        "procesos_clave",
        "estrategia",
    ):
        if field in data:
            setattr(ctx, field, data[field])
    if "dominios" in data:
        ctx.dominios_json = _json(data["dominios"])
    if "freshness_recent_days" in data:
        ctx.freshness_recent_days = int(data["freshness_recent_days"])
    if "freshness_stale_days" in data:
        ctx.freshness_stale_days = int(data["freshness_stale_days"])
    ctx.updated_at = _utcnow()
    write_audit(
        db,
        action="inteligencia_externa.contexto.modificado",
        organization_id=organization_id,
        user_id=user_id,
        detail="contexto externo actualizado",
        commit=False,
    )
    return ctx


def context_to_dict(ctx: OrganizationExternalContext) -> dict[str, Any]:
    return {
        "organization_id": ctx.organization_id,
        "sector": ctx.sector,
        "mercado": ctx.mercado,
        "productos_servicios": ctx.productos_servicios,
        "geografias": ctx.geografias,
        "clientes_objetivo": ctx.clientes_objetivo,
        "procesos_clave": ctx.procesos_clave,
        "estrategia": ctx.estrategia,
        "dominios": _parse_json(ctx.dominios_json),
        "freshness_recent_days": ctx.freshness_recent_days,
        "freshness_stale_days": ctx.freshness_stale_days,
        "updated_at": ctx.updated_at.isoformat() if ctx.updated_at else None,
    }


def compute_freshness(
    published_at: datetime | None,
    captured_at: datetime | None,
    *,
    recent_days: int = 30,
    stale_days: int = 180,
) -> str:
    if not published_at and not captured_at:
        return FreshnessStatus.SIN_FECHA
    ref = published_at or captured_at
    if ref is None:
        return FreshnessStatus.SIN_FECHA
    if ref.tzinfo is None:
        ref = ref.replace(tzinfo=timezone.utc)
    age = _utcnow() - ref
    if age <= timedelta(days=recent_days):
        return FreshnessStatus.ACTUAL
    if age <= timedelta(days=stale_days):
        return FreshnessStatus.RECIENTE
    return FreshnessStatus.DESACTUALIZADA


def evaluate_relevance(
    db: Session,
    organization_id: str,
    *,
    source_type: str,
    sector: str | None,
    pais_region: str | None,
    dominio: str,
    evento: str,
) -> str:
    """Evaluación determinística de relevancia según contexto de empresa."""
    ctx = get_or_create_context(db, organization_id)
    text = f"{source_type} {sector or ''} {pais_region or ''} {dominio} {evento}".lower()
    score = 0
    if ctx.sector and ctx.sector.lower() in text:
        score += 2
    if ctx.mercado and ctx.mercado.lower() in text:
        score += 2
    if ctx.geografias and any(g.strip().lower() in text for g in ctx.geografias.split(",") if g.strip()):
        score += 1
    if ctx.productos_servicios and any(
        p.strip().lower() in text for p in ctx.productos_servicios.split(",") if p.strip()
    ):
        score += 1
    dominios = _parse_json(ctx.dominios_json) or []
    if dominio.lower() in [str(d).lower() for d in dominios]:
        score += 2
    if score >= 3:
        return RelevanceLevel.RELEVANTE
    if score >= 1:
        return RelevanceLevel.POSIBLEMENTE_RELEVANTE
    return RelevanceLevel.NO_RELEVANTE


def external_source_to_dict(src: ExternalSource) -> dict[str, Any]:
    return {
        "id": src.id,
        "code": src.code,
        "name": src.name,
        "source_type": src.source_type,
        "ingestion_channel": src.ingestion_channel,
        "url_reference": src.url_reference,
        "descripcion": src.descripcion,
        "sector": src.sector,
        "pais_region": src.pais_region,
        "frecuencia_esperada": src.frecuencia_esperada,
        "estado": src.estado,
        "confiabilidad": float(src.confiabilidad),
        "ultima_actualizacion": src.ultima_actualizacion.isoformat() if src.ultima_actualizacion else None,
        "is_active": src.is_active,
        "signal_source_id": src.signal_source_id,
    }


def list_external_sources(db: Session, organization_id: str) -> list[ExternalSource]:
    return (
        db.query(ExternalSource)
        .filter(ExternalSource.organization_id == organization_id)
        .order_by(ExternalSource.name.asc())
        .all()
    )


def get_external_source(db: Session, organization_id: str, source_id: str) -> ExternalSource | None:
    return (
        db.query(ExternalSource)
        .filter(ExternalSource.id == source_id, ExternalSource.organization_id == organization_id)
        .first()
    )


def get_external_source_by_code(db: Session, organization_id: str, code: str) -> ExternalSource | None:
    return (
        db.query(ExternalSource)
        .filter(ExternalSource.organization_id == organization_id, ExternalSource.code == code.strip().lower())
        .first()
    )


def create_external_source(
    db: Session,
    *,
    organization_id: str,
    user_id: str | None,
    code: str,
    name: str,
    source_type: str,
    ingestion_channel: str,
    **kwargs: Any,
) -> ExternalSource:
    sig_svc._ensure_org_active(db, organization_id)
    if source_type not in ExternalSourceType.ALL:
        raise HTTPException(status_code=422, detail="Tipo de fuente externa no válido")
    if ingestion_channel not in IngestionChannel.ALL:
        raise HTTPException(status_code=422, detail="Canal de ingesta no válido")
    normalized = code.strip().lower()
    if get_external_source_by_code(db, organization_id, normalized):
        raise HTTPException(status_code=409, detail="Ya existe una fuente externa con ese código")

    signal_source = sig_svc.create_source(
        db,
        organization_id=organization_id,
        code=f"ext-{normalized}",
        name=name,
        tipo_fuente="EXTERNAL_FUTURE",
        descripcion=kwargs.get("descripcion"),
        configuracion={"external": True, "source_type": source_type},
        user_id=user_id,
    )

    row = ExternalSource(
        organization_id=organization_id,
        signal_source_id=signal_source.id,
        code=normalized,
        name=name.strip(),
        source_type=source_type,
        ingestion_channel=ingestion_channel,
        url_reference=kwargs.get("url_reference"),
        descripcion=kwargs.get("descripcion"),
        sector=kwargs.get("sector"),
        pais_region=kwargs.get("pais_region"),
        frecuencia_esperada=kwargs.get("frecuencia_esperada"),
        confiabilidad=float(kwargs.get("confiabilidad") or 0.5),
        ultima_actualizacion=_utcnow(),
    )
    db.add(row)
    db.flush()
    write_audit(
        db,
        action="inteligencia_externa.fuente.creada",
        organization_id=organization_id,
        user_id=user_id,
        detail=_json({"source_id": row.id, "code": row.code}),
        commit=False,
    )
    return row


def update_external_source(
    db: Session,
    organization_id: str,
    source_id: str,
    user_id: str | None,
    data: dict[str, Any],
) -> ExternalSource:
    row = get_external_source(db, organization_id, source_id)
    if not row:
        raise HTTPException(status_code=404, detail="Fuente externa no encontrada")
    for field in (
        "name",
        "descripcion",
        "url_reference",
        "sector",
        "pais_region",
        "frecuencia_esperada",
        "estado",
    ):
        if field in data and data[field] is not None:
            setattr(row, field, data[field])
    if "confiabilidad" in data and data["confiabilidad"] is not None:
        row.confiabilidad = float(data["confiabilidad"])
    if "is_active" in data:
        row.is_active = bool(data["is_active"])
    row.ultima_actualizacion = _utcnow()
    row.updated_at = _utcnow()
    write_audit(
        db,
        action="inteligencia_externa.fuente.modificada",
        organization_id=organization_id,
        user_id=user_id,
        detail=_json({"source_id": row.id}),
        commit=False,
    )
    return row


def _evidence_dedupe_hash(org_id: str, reference: str, summary: str) -> str:
    raw = f"{org_id}|{reference}|{summary}"
    return hashlib.sha256(raw.encode()).hexdigest()[:64]


def _create_evidence(
    db: Session,
    *,
    organization_id: str,
    signal_id: str,
    external_source_id: str | None,
    data: dict[str, Any],
) -> ExternalEvidence | None:
    reference = str(data.get("reference_url") or data.get("referencia") or "")
    summary = str(data.get("summary") or data.get("resumen") or data.get("hecho_observado") or "")
    dedupe = _evidence_dedupe_hash(organization_id, reference, summary[:200])
    exists = (
        db.query(ExternalEvidence)
        .filter(ExternalEvidence.organization_id == organization_id, ExternalEvidence.dedupe_hash == dedupe)
        .first()
    )
    if exists:
        return None
    ev = ExternalEvidence(
        organization_id=organization_id,
        signal_id=signal_id,
        external_source_id=external_source_id,
        reference_url=data.get("reference_url"),
        published_at=_parse_dt(data.get("published_at") or data.get("fecha_publicacion")),
        captured_at=_parse_dt(data.get("captured_at")) or _utcnow(),
        structured_content=data.get("structured_content") or data.get("contenido"),
        observed_data=data.get("observed_data") or data.get("dato_observado"),
        summary=summary or None,
        metadata_json=_json(data.get("metadata")) if data.get("metadata") else None,
        dedupe_hash=dedupe,
    )
    db.add(ev)
    return ev


def extension_to_dict(ext: ExternalSignalExtension, evidence: list[ExternalEvidence] | None = None) -> dict[str, Any]:
    return {
        "id": ext.id,
        "signal_id": ext.signal_id,
        "external_source_id": ext.external_source_id,
        "ambito": ext.ambito,
        "captured_at": ext.captured_at.isoformat() if ext.captured_at else None,
        "published_at": ext.published_at.isoformat() if ext.published_at else None,
        "freshness_status": ext.freshness_status,
        "classification": ext.classification,
        "relevance": ext.relevance,
        "hecho_observado": ext.hecho_observado,
        "interpretacion": ext.interpretacion,
        "hipotesis": ext.hipotesis,
        "oportunidad_propuesta": ext.oportunidad_propuesta,
        "confidence_level": float(ext.confidence_level),
        "is_risk": ext.is_risk,
        "risk_type": ext.risk_type,
        "competitor": _parse_json(ext.competitor_json),
        "regulation": _parse_json(ext.regulation_json),
        "technology": _parse_json(ext.technology_json),
        "demand": _parse_json(ext.demand_json),
        "valuation_contract_ref": ext.valuation_contract_ref,
        "diagnostic_contract_ref": ext.diagnostic_contract_ref,
        "validated_at": ext.validated_at.isoformat() if ext.validated_at else None,
        "evidence": [
            {
                "id": e.id,
                "reference_url": e.reference_url,
                "published_at": e.published_at.isoformat() if e.published_at else None,
                "captured_at": e.captured_at.isoformat() if e.captured_at else None,
                "summary": e.summary,
                "observed_data": e.observed_data,
            }
            for e in (evidence or [])
        ],
    }


def ingest_external_signal(
    db: Session,
    *,
    organization_id: str,
    user_id: str | None,
    data: dict[str, Any],
    auto_process: bool = False,
) -> dict[str, Any]:
    """Ingesta señal externa: fuente → evidencia → señal 1120 → extensión 1240."""
    sig_svc._ensure_org_active(db, organization_id)

    source_code = data.get("source_code")
    if not source_code:
        raise HTTPException(status_code=422, detail="source_code es obligatorio")
    ext_source = get_external_source_by_code(db, organization_id, str(source_code))
    if not ext_source:
        raise HTTPException(status_code=404, detail="Fuente externa no encontrada")
    if not ext_source.is_active:
        raise HTTPException(status_code=422, detail="La fuente externa está inactiva")

    ctx = get_or_create_context(db, organization_id)
    published_at = _parse_dt(data.get("published_at") or data.get("fecha_publicacion"))
    captured_at = _parse_dt(data.get("captured_at")) or _utcnow()
    freshness = compute_freshness(
        published_at,
        captured_at,
        recent_days=ctx.freshness_recent_days,
        stale_days=ctx.freshness_stale_days,
    )

    classification = str(data.get("classification") or SignalClassification.INFORMACION)
    if classification not in (
        SignalClassification.OPORTUNIDAD,
        SignalClassification.RIESGO,
        SignalClassification.CAMBIO,
        SignalClassification.TENDENCIA,
        SignalClassification.EVENTO,
        SignalClassification.INFORMACION,
    ):
        classification = SignalClassification.INFORMACION

    dominio = str(data.get("dominio") or ext_source.source_type.lower())
    evento = str(data.get("evento") or "hallazgo_externo")
    relevance = data.get("relevance") or evaluate_relevance(
        db,
        organization_id,
        source_type=ext_source.source_type,
        sector=ext_source.sector,
        pais_region=ext_source.pais_region,
        dominio=dominio,
        evento=evento,
    )

    hecho = data.get("hecho_observado") or data.get("dato_observado")
    if not hecho:
        raise HTTPException(status_code=422, detail="hecho_observado es obligatorio para señales externas")

    signal_source = sig_svc.get_source(db, organization_id, ext_source.signal_source_id) if ext_source.signal_source_id else None
    ingest_payload = {
        "source_code": signal_source.code if signal_source else f"ext-{ext_source.code}",
        "tipo": str(data.get("tipo") or f"externo_{ext_source.source_type.lower().replace('/', '_')}"),
        "dominio": dominio,
        "evento": evento,
        "referencia": str(data.get("referencia") or data.get("reference_url") or f"ext-{ext_source.code}-{captured_at.date()}"),
        "origen": f"{EXTERNAL_ORIGIN_PREFIX}{ext_source.code}",
        "modo_ingesta": "REAL",
        "evidencia_resumen": str(hecho)[:500],
        "fecha": (published_at or captured_at).isoformat(),
        "idempotency_key": data.get("idempotency_key"),
        "titulo": data.get("titulo"),
        "tipo_oportunidad": "ESTRATEGICA" if classification == SignalClassification.OPORTUNIDAD else "RIESGO" if classification == SignalClassification.RIESGO else "OPERATIVA",
        "metadata": {
            "ambito": "EXTERNO",
            "source_type": ext_source.source_type,
            "freshness": freshness,
            "classification": classification,
        },
        "payload": {
            "titulo": data.get("titulo") or f"Hallazgo externo: {evento}",
            "tipo_oportunidad": "ESTRATEGICA",
            "evidencia": {"hecho": hecho, "fuente": ext_source.name},
            "contexto_externo": True,
        },
        "confianza": float(data.get("confidence_level") or ext_source.confiabilidad),
    }

    result = sig_svc.ingest_real_signal(
        db,
        organization_id=organization_id,
        user_id=user_id,
        data=ingest_payload,
        auto_process=auto_process and classification == SignalClassification.OPORTUNIDAD,
    )
    signal_id = result["signal"]["id"]
    signal = db.query(ProactiveSignal).filter(ProactiveSignal.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=500, detail="Error al registrar señal externa")

    if result.get("deduplicated"):
        existing_ext = (
            db.query(ExternalSignalExtension)
            .filter(ExternalSignalExtension.signal_id == signal.id)
            .first()
        )
        if existing_ext:
            evidence_rows = db.query(ExternalEvidence).filter(ExternalEvidence.signal_id == signal.id).all()
            result["external"] = extension_to_dict(existing_ext, evidence_rows)
            result["external_source"] = external_source_to_dict(ext_source)
            return result

    is_risk = classification == SignalClassification.RIESGO or bool(data.get("is_risk"))
    ext = ExternalSignalExtension(
        organization_id=organization_id,
        signal_id=signal.id,
        external_source_id=ext_source.id,
        captured_at=captured_at,
        published_at=published_at,
        freshness_status=freshness,
        classification=classification,
        relevance=str(relevance),
        hecho_observado=str(hecho),
        interpretacion=data.get("interpretacion"),
        hipotesis=data.get("hipotesis"),
        oportunidad_propuesta=data.get("oportunidad_propuesta"),
        confidence_level=float(data.get("confidence_level") or ext_source.confiabilidad),
        is_risk=is_risk,
        risk_type=data.get("risk_type"),
        competitor_json=_json(data["competitor"]) if data.get("competitor") else None,
        regulation_json=_json(data["regulation"]) if data.get("regulation") else None,
        technology_json=_json(data["technology"]) if data.get("technology") else None,
        demand_json=_json(data["demand"]) if data.get("demand") else None,
        valuation_contract_ref=data.get("valuation_contract_ref") or f"valoracion:opp:pending:{signal.id}",
        diagnostic_contract_ref=data.get("diagnostic_contract_ref") or f"diagnostico:signal:{signal.id}",
    )
    db.add(ext)
    db.flush()

    _create_evidence(
        db,
        organization_id=organization_id,
        signal_id=signal.id,
        external_source_id=ext_source.id,
        data=data,
    )

    ext_source.ultima_actualizacion = _utcnow()
    write_audit(
        db,
        action="inteligencia_externa.senal.incorporada",
        organization_id=organization_id,
        user_id=user_id,
        detail=_json({"signal_id": signal.id, "source": ext_source.code, "classification": classification}),
        commit=False,
    )

    evidence_rows = db.query(ExternalEvidence).filter(ExternalEvidence.signal_id == signal.id).all()
    result["external"] = extension_to_dict(ext, evidence_rows)
    result["external_source"] = external_source_to_dict(ext_source)
    return result


def list_external_signals(
    db: Session,
    organization_id: str,
    *,
    limit: int = 50,
    classification: str | None = None,
    relevance: str | None = None,
    source_type: str | None = None,
) -> list[dict[str, Any]]:
    query = (
        db.query(ExternalSignalExtension, ProactiveSignal, ExternalSource)
        .join(ProactiveSignal, ProactiveSignal.id == ExternalSignalExtension.signal_id)
        .outerjoin(ExternalSource, ExternalSource.id == ExternalSignalExtension.external_source_id)
        .filter(ExternalSignalExtension.organization_id == organization_id)
        .order_by(ExternalSignalExtension.captured_at.desc())
    )
    if classification:
        query = query.filter(ExternalSignalExtension.classification == classification)
    if relevance:
        query = query.filter(ExternalSignalExtension.relevance == relevance)
    if source_type:
        query = query.filter(ExternalSource.source_type == source_type)

    rows = query.limit(limit).all()
    items: list[dict[str, Any]] = []
    for ext, signal, source in rows:
        items.append(
            {
                "signal": sig_svc.signal_to_dict(signal),
                "external": extension_to_dict(ext),
                "source": external_source_to_dict(source) if source else None,
            }
        )
    return items


def get_external_signal_detail(db: Session, organization_id: str, signal_id: str) -> dict[str, Any]:
    ext = (
        db.query(ExternalSignalExtension)
        .filter(
            ExternalSignalExtension.signal_id == signal_id,
            ExternalSignalExtension.organization_id == organization_id,
        )
        .first()
    )
    if not ext:
        raise HTTPException(status_code=404, detail="Señal externa no encontrada")
    signal = db.query(ProactiveSignal).filter(ProactiveSignal.id == signal_id).first()
    source = get_external_source(db, organization_id, ext.external_source_id) if ext.external_source_id else None
    evidence = db.query(ExternalEvidence).filter(ExternalEvidence.signal_id == signal_id).all()
    opp = db.query(Opportunity).filter(Opportunity.signal_id == signal_id).first()
    return {
        "signal": sig_svc.signal_to_dict(signal) if signal else None,
        "external": extension_to_dict(ext, evidence),
        "source": external_source_to_dict(source) if source else None,
        "opportunity_id": opp.id if opp else None,
        "trazabilidad": sig_svc.get_signal_trace(db, organization_id, signal_id),
    }


def update_classification(
    db: Session,
    organization_id: str,
    signal_id: str,
    classification: str,
    user_id: str | None,
) -> ExternalSignalExtension:
    ext = (
        db.query(ExternalSignalExtension)
        .filter(ExternalSignalExtension.signal_id == signal_id, ExternalSignalExtension.organization_id == organization_id)
        .first()
    )
    if not ext:
        raise HTTPException(status_code=404, detail="Señal externa no encontrada")
    ext.classification = classification
    ext.is_risk = classification == SignalClassification.RIESGO
    ext.updated_at = _utcnow()
    write_audit(
        db,
        action="inteligencia_externa.clasificacion.modificada",
        organization_id=organization_id,
        user_id=user_id,
        detail=_json({"signal_id": signal_id, "classification": classification}),
        commit=False,
    )
    return ext


def update_relevance(
    db: Session,
    organization_id: str,
    signal_id: str,
    relevance: str,
    user_id: str | None,
) -> ExternalSignalExtension:
    ext = (
        db.query(ExternalSignalExtension)
        .filter(ExternalSignalExtension.signal_id == signal_id, ExternalSignalExtension.organization_id == organization_id)
        .first()
    )
    if not ext:
        raise HTTPException(status_code=404, detail="Señal externa no encontrada")
    ext.relevance = relevance
    ext.updated_at = _utcnow()
    write_audit(
        db,
        action="inteligencia_externa.relevancia.modificada",
        organization_id=organization_id,
        user_id=user_id,
        detail=_json({"signal_id": signal_id, "relevance": relevance}),
        commit=False,
    )
    return ext


def validate_external_analysis(
    db: Session,
    organization_id: str,
    signal_id: str,
    user_id: str | None,
) -> ExternalSignalExtension:
    ext = (
        db.query(ExternalSignalExtension)
        .filter(ExternalSignalExtension.signal_id == signal_id, ExternalSignalExtension.organization_id == organization_id)
        .first()
    )
    if not ext:
        raise HTTPException(status_code=404, detail="Señal externa no encontrada")
    if not ext.hecho_observado:
        raise HTTPException(status_code=422, detail="No se puede validar sin hecho observado")
    ext.validated_at = _utcnow()
    ext.validated_by = user_id
    ext.updated_at = _utcnow()
    write_audit(
        db,
        action="inteligencia_externa.senal.validada",
        organization_id=organization_id,
        user_id=user_id,
        detail=_json({"signal_id": signal_id}),
        commit=False,
    )
    return ext


def create_opportunity_from_external(
    db: Session,
    organization_id: str,
    signal_id: str,
    user_id: str | None,
) -> Opportunity:
    ext = (
        db.query(ExternalSignalExtension)
        .filter(ExternalSignalExtension.signal_id == signal_id, ExternalSignalExtension.organization_id == organization_id)
        .first()
    )
    if not ext:
        raise HTTPException(status_code=404, detail="Señal externa no encontrada")
    if ext.is_risk:
        raise HTTPException(status_code=422, detail="Use el endpoint de riesgo para señales clasificadas como riesgo")
    signal = db.query(ProactiveSignal).filter(ProactiveSignal.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Señal no encontrada")
    existing = db.query(Opportunity).filter(Opportunity.signal_id == signal_id).first()
    if existing:
        return existing
    opp = proactive_svc.process_signal(db, signal, user_id=user_id)
    if not opp:
        raise HTTPException(status_code=422, detail="No se pudo generar oportunidad desde la señal externa")
    ext.oportunidad_propuesta = opp.titulo
    ext.valuation_contract_ref = f"valoracion:opp:{opp.id}"
    write_audit(
        db,
        action="inteligencia_externa.oportunidad.generada",
        organization_id=organization_id,
        user_id=user_id,
        detail=_json({"signal_id": signal_id, "opportunity_id": opp.id}),
        commit=False,
    )
    return opp


def register_external_risk(
    db: Session,
    organization_id: str,
    signal_id: str,
    user_id: str | None,
    risk_type: str | None = None,
) -> ExternalSignalExtension:
    ext = (
        db.query(ExternalSignalExtension)
        .filter(ExternalSignalExtension.signal_id == signal_id, ExternalSignalExtension.organization_id == organization_id)
        .first()
    )
    if not ext:
        raise HTTPException(status_code=404, detail="Señal externa no encontrada")
    ext.is_risk = True
    ext.classification = SignalClassification.RIESGO
    ext.risk_type = risk_type or ext.risk_type or "RIESGO EXTERNO"
    ext.updated_at = _utcnow()
    write_audit(
        db,
        action="inteligencia_externa.riesgo.registrado",
        organization_id=organization_id,
        user_id=user_id,
        detail=_json({"signal_id": signal_id, "risk_type": ext.risk_type}),
        commit=False,
    )
    return ext
