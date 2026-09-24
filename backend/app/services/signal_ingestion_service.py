"""Ingesta de señales reales — Bloque 1120."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.models import Organization
from app.opportunity_models import Opportunity, ProactiveSignal, SignalSource
from app.services import proactive_service as proactive_svc
from app.tenant_scope import ORG_STATUS_ACTIVE

SOURCE_TYPES = frozenset({"API", "DATABASE", "FILE", "EVENT", "AUTOMATION", "EXTERNAL_FUTURE"})
INGEST_MODES = frozenset({"REAL", "SINTETICO", "PRUEBA"})
PROCESSING_STATES = frozenset({"RECIBIDA", "PROCESADA", "RECHAZADA", "DUPLICADA"})
_DEDUPE_WINDOW_HOURS = 24
_SECRET_KEY_PATTERN = re.compile(r"(password|secret|token|api[_-]?key|authorization)", re.I)


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


def _sanitize_metadata(data: dict | None) -> dict:
    if not data:
        return {}
    safe: dict[str, Any] = {}
    for key, value in data.items():
        if _SECRET_KEY_PATTERN.search(str(key)):
            safe[key] = "[REDACTED]"
        elif isinstance(value, str) and len(value) > 500:
            safe[key] = value[:500] + "…"
        else:
            safe[key] = value
    return safe


def _make_dedupe_key(
    org_id: str,
    *,
    idempotency_key: str | None,
    tipo: str,
    origen: str,
    source_ref: str | None,
    evento: str,
) -> str:
    if idempotency_key:
        raw = f"{org_id}|idem|{idempotency_key}"
    else:
        raw = f"{org_id}|{tipo}|{origen}|{source_ref or ''}|{evento}"
    return hashlib.sha256(raw.encode()).hexdigest()[:64]


def _ensure_org_active(db: Session, organization_id: str) -> Organization:
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa no encontrada")
    if org.status != ORG_STATUS_ACTIVE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="La empresa está inactiva")
    return org


def source_to_dict(source: SignalSource) -> dict[str, Any]:
    return {
        "id": source.id,
        "code": source.code,
        "name": source.name,
        "tipo_fuente": source.tipo_fuente,
        "descripcion": source.descripcion,
        "is_active": source.is_active,
        "configuracion": _parse_json(source.configuracion_json),
        "created_at": source.created_at.isoformat() if source.created_at else None,
        "updated_at": source.updated_at.isoformat() if source.updated_at else None,
    }


def list_sources(db: Session, organization_id: str) -> list[SignalSource]:
    return (
        db.query(SignalSource)
        .filter(SignalSource.organization_id == organization_id)
        .order_by(SignalSource.name.asc())
        .all()
    )


def get_source(db: Session, organization_id: str, source_id: str) -> SignalSource | None:
    return (
        db.query(SignalSource)
        .filter(SignalSource.id == source_id, SignalSource.organization_id == organization_id)
        .first()
    )


def get_source_by_code(db: Session, organization_id: str, code: str) -> SignalSource | None:
    return (
        db.query(SignalSource)
        .filter(SignalSource.organization_id == organization_id, SignalSource.code == code.strip().lower())
        .first()
    )


def create_source(
    db: Session,
    *,
    organization_id: str,
    code: str,
    name: str,
    tipo_fuente: str,
    descripcion: str | None = None,
    configuracion: dict | None = None,
    user_id: str | None = None,
) -> SignalSource:
    _ensure_org_active(db, organization_id)
    normalized_code = code.strip().lower()
    if tipo_fuente not in SOURCE_TYPES:
        raise HTTPException(status_code=422, detail="Tipo de fuente no válido")
    if get_source_by_code(db, organization_id, normalized_code):
        raise HTTPException(status_code=409, detail="Ya existe una fuente con ese código")
    row = SignalSource(
        organization_id=organization_id,
        code=normalized_code,
        name=name.strip(),
        tipo_fuente=tipo_fuente,
        descripcion=descripcion,
        configuracion_json=_json(_sanitize_metadata(configuracion)) if configuracion else None,
    )
    db.add(row)
    db.flush()
    write_audit(
        db,
        action="signal.source.created",
        organization_id=organization_id,
        user_id=user_id,
        detail=_json({"source_id": row.id, "code": row.code, "tipo": row.tipo_fuente}),
        commit=False,
    )
    return row


def list_recent_signals(
    db: Session,
    organization_id: str,
    *,
    limit: int = 50,
    modo_ingesta: str | None = None,
) -> list[ProactiveSignal]:
    query = db.query(ProactiveSignal).filter(ProactiveSignal.organization_id == organization_id)
    if modo_ingesta:
        query = query.filter(ProactiveSignal.modo_ingesta == modo_ingesta)
    return query.order_by(ProactiveSignal.created_at.desc()).limit(limit).all()


def signal_to_dict(signal: ProactiveSignal) -> dict[str, Any]:
    opp = None
    return {
        "id": signal.id,
        "organization_id": signal.organization_id,
        "source_id": signal.source_id,
        "tipo": signal.tipo,
        "dominio": signal.dominio,
        "origen": signal.origen,
        "modo_ingesta": signal.modo_ingesta,
        "proceso": signal.proceso,
        "metrica": signal.metrica,
        "valor_metrica": signal.valor_metrica,
        "unidad": signal.unidad,
        "dimension": signal.dimension,
        "referencia": signal.source_reference,
        "evidencia_resumen": signal.evidencia_resumen,
        "estado_procesamiento": signal.estado_procesamiento,
        "rejection_reason": signal.rejection_reason,
        "procesada": signal.procesada,
        "correlation_id": signal.correlation_id,
        "signal_at": signal.signal_at.isoformat() if signal.signal_at else None,
        "created_at": signal.created_at.isoformat() if signal.created_at else None,
        "processed_at": signal.processed_at.isoformat() if signal.processed_at else None,
        "metadata": _parse_json(signal.metadata_json),
    }


def _validate_signal_input(data: dict[str, Any]) -> None:
    required = ("tipo", "dominio", "evento", "referencia")
    missing = [field for field in required if not str(data.get(field) or "").strip()]
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Campos obligatorios faltantes: {', '.join(missing)}",
        )
    if data.get("modo_ingesta", "REAL") not in INGEST_MODES:
        raise HTTPException(status_code=422, detail="Modo de ingesta no válido")


def ingest_real_signal(
    db: Session,
    *,
    organization_id: str,
    user_id: str | None,
    data: dict[str, Any],
    auto_process: bool = True,
) -> dict[str, Any]:
    """Registra y opcionalmente procesa una señal real normalizada."""
    _ensure_org_active(db, organization_id)
    _validate_signal_input(data)

    source: SignalSource | None = None
    source_code = data.get("source_code")
    if source_code:
        source = get_source_by_code(db, organization_id, str(source_code))
        if not source:
            raise HTTPException(status_code=404, detail="Fuente de señal no encontrada")
        if not source.is_active:
            raise HTTPException(status_code=422, detail="La fuente de señal está inactiva")

    modo = str(data.get("modo_ingesta") or "REAL").upper()
    origen = str(data.get("origen") or (source.code if source else "api_ingesta"))
    referencia = str(data["referencia"]).strip()
    idempotency_key = data.get("idempotency_key")
    dedupe_key = _make_dedupe_key(
        organization_id,
        idempotency_key=str(idempotency_key).strip() if idempotency_key else None,
        tipo=str(data["tipo"]),
        origen=origen,
        source_ref=referencia,
        evento=str(data["evento"]),
    )

    window_start = _utcnow() - timedelta(hours=_DEDUPE_WINDOW_HOURS)
    existing = (
        db.query(ProactiveSignal)
        .filter(
            ProactiveSignal.organization_id == organization_id,
            ProactiveSignal.dedupe_key == dedupe_key,
            ProactiveSignal.created_at >= window_start,
        )
        .first()
    )
    if existing:
        existing.estado_procesamiento = "DUPLICADA"
        opp = db.query(Opportunity).filter(Opportunity.signal_id == existing.id).first()
        write_audit(
            db,
            action="signal.duplicate",
            organization_id=organization_id,
            user_id=user_id,
            detail=_json({"signal_id": existing.id, "referencia": referencia}),
            commit=False,
        )
        return {
            "signal": signal_to_dict(existing),
            "is_new": False,
            "deduplicated": True,
            "opportunity_id": opp.id if opp else None,
        }

    evidencia = _sanitize_metadata(data.get("evidencia") if isinstance(data.get("evidencia"), dict) else {})
    metadata = _sanitize_metadata(data.get("metadata") if isinstance(data.get("metadata"), dict) else {})
    evidencia_resumen = data.get("evidencia_resumen") or evidencia.get("resumen")
    if isinstance(evidencia_resumen, str) and len(evidencia_resumen) > 500:
        evidencia_resumen = evidencia_resumen[:500]

    motor_payload = dict(data.get("payload") or {})
    motor_payload.setdefault("source_reference", referencia)
    motor_payload.setdefault("titulo", data.get("titulo") or f"Señal: {data['evento']}")
    motor_payload.setdefault("tipo_oportunidad", data.get("tipo_oportunidad") or "OPERATIVA")
    if evidencia:
        motor_payload.setdefault("evidencia", evidencia)
    if data.get("indicadores"):
        motor_payload.setdefault("indicadores", data["indicadores"])
    if data.get("impacto_estimado") is not None:
        motor_payload.setdefault("impacto_estimado", data["impacto_estimado"])
    if data.get("valor_potencial") is not None:
        motor_payload.setdefault("valor_potencial", data["valor_potencial"])

    signal_at = data.get("fecha")
    parsed_signal_at = None
    if isinstance(signal_at, datetime):
        parsed_signal_at = signal_at
    elif isinstance(signal_at, str) and signal_at.strip():
        try:
            parsed_signal_at = datetime.fromisoformat(signal_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Fecha de señal no válida") from exc

    correlation_id = proactive_svc._new_correlation()
    signal = ProactiveSignal(
        organization_id=organization_id,
        source_id=source.id if source else None,
        tipo=str(data["tipo"]),
        dominio=str(data["dominio"]),
        origen=origen,
        modo_ingesta=modo,
        source_reference=referencia,
        evento=str(data["evento"]),
        proceso=data.get("proceso"),
        metrica=data.get("metrica"),
        valor_metrica=str(data["valor"]) if data.get("valor") is not None else None,
        unidad=data.get("unidad"),
        dimension=data.get("dimension"),
        evidencia_resumen=str(evidencia_resumen) if evidencia_resumen else None,
        payload_json=_json(motor_payload),
        metadata_json=_json(metadata) if metadata else None,
        severidad=str(data.get("severidad") or "MEDIA"),
        confianza=float(data.get("confianza") or 0.7),
        dedupe_key=dedupe_key,
        estado_procesamiento="RECIBIDA",
        correlation_id=correlation_id,
        signal_at=parsed_signal_at or _utcnow(),
    )
    db.add(signal)
    db.flush()

    proactive_svc.add_trace(
        db,
        organization_id=organization_id,
        correlation_id=correlation_id,
        etapa="SENAL_CREADA",
        signal_id=signal.id,
        detalle={
            "modo_ingesta": modo,
            "fuente": source.code if source else origen,
            "referencia": referencia,
            "metrica": signal.metrica,
            "regla": data.get("regla_analisis"),
        },
    )
    write_audit(
        db,
        action="signal.received",
        organization_id=organization_id,
        user_id=user_id,
        detail=_json(
            {
                "signal_id": signal.id,
                "source_id": signal.source_id,
                "referencia": referencia,
                "modo": modo,
            }
        ),
        commit=False,
    )

    opportunity_id = None
    if auto_process and modo == "REAL":
        opp = proactive_svc.process_signal(db, signal, user_id=user_id)
        if opp:
            signal.estado_procesamiento = "PROCESADA"
            opportunity_id = opp.id
            write_audit(
                db,
                action="opportunity.detected",
                organization_id=organization_id,
                user_id=user_id,
                detail=_json(
                    {
                        "signal_id": signal.id,
                        "opportunity_id": opp.id,
                        "codigo": opp.codigo,
                        "regla": data.get("regla_analisis"),
                    }
                ),
                commit=False,
            )
        elif signal.estado_procesamiento != "DUPLICADA":
            signal.estado_procesamiento = "PROCESADA" if signal.procesada else "RECHAZADA"
            if signal.estado_procesamiento == "RECHAZADA":
                signal.rejection_reason = "Señal observada sin oportunidad accionable"
                proactive_svc.add_trace(
                    db,
                    organization_id=organization_id,
                    correlation_id=correlation_id,
                    etapa="SENAL_RECHAZADA",
                    signal_id=signal.id,
                    detalle={"razon": signal.rejection_reason},
                )
                write_audit(
                    db,
                    action="signal.rejected",
                    organization_id=organization_id,
                    user_id=user_id,
                    detail=_json({"signal_id": signal.id, "razon": signal.rejection_reason}),
                    commit=False,
                )
        write_audit(
            db,
            action="signal.processed",
            organization_id=organization_id,
            user_id=user_id,
            detail=_json({"signal_id": signal.id, "opportunity_id": opportunity_id}),
            commit=False,
        )

    return {
        "signal": signal_to_dict(signal),
        "is_new": True,
        "deduplicated": False,
        "opportunity_id": opportunity_id,
        "trace_correlation_id": correlation_id,
    }


def get_signal_trace(db: Session, organization_id: str, signal_id: str) -> dict[str, Any]:
    signal = (
        db.query(ProactiveSignal)
        .filter(ProactiveSignal.id == signal_id, ProactiveSignal.organization_id == organization_id)
        .first()
    )
    if not signal:
        raise HTTPException(status_code=404, detail="Señal no encontrada")
    opp = db.query(Opportunity).filter(Opportunity.signal_id == signal.id).first()
    traces = proactive_svc.get_full_trace(db, opp.id, organization_id) if opp else {
        "trazas": [],
        "correlation_id": signal.correlation_id,
    }
    source = get_source(db, organization_id, signal.source_id) if signal.source_id else None
    return {
        "signal": signal_to_dict(signal),
        "fuente": {
            "id": source.id,
            "code": source.code,
            "name": source.name,
            "tipo_fuente": source.tipo_fuente,
        }
        if source
        else None,
        "opportunity_id": opp.id if opp else None,
        "trazabilidad": traces,
    }
