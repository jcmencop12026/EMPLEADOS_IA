"""Servicio — Integraciones reales y conectores (1330)."""

from __future__ import annotations

import hashlib
import json
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.gateway.secrets import build_env_secret_ref, secret_configured
from app.integration_enums import (
    ConnectorStatus,
    ConnectorType,
    DestinationType,
    ErrorCategory,
    ExecutionStatus,
    TestResult,
    TriggerMode,
)
from app.integration_models import IntegrationConnector, IntegrationExecution, IntegrationWebhookEvent
from app.integration_security import redact_sensitive_headers
from app.models import Organization
from app.services import integration_executors as exec_mod
from app.services import signal_ingestion_service as signal_svc
from app.tenant_scope import ORG_STATUS_ACTIVE

CONNECTOR_CATALOG = [
    {"type": ConnectorType.API_REST, "name": "API REST", "descripcion": "Conexión HTTP configurable"},
    {"type": ConnectorType.BASE_DATOS, "name": "Base de datos", "descripcion": "Consultas parametrizadas (PostgreSQL, MySQL, SQL Server)"},
    {"type": ConnectorType.ARCHIVO, "name": "Archivo", "descripcion": "CSV, JSON, XLSX, TXT"},
    {"type": ConnectorType.SFTP, "name": "SFTP", "descripcion": "Transferencia segura de archivos"},
    {"type": ConnectorType.WEBHOOK, "name": "Webhook", "descripcion": "Entrante y saliente"},
    {"type": ConnectorType.CORREO, "name": "Correo", "descripcion": "IMAP/SMTP preparado"},
    {"type": ConnectorType.EVENTO, "name": "Evento", "descripcion": "Fuente/emisor de eventos"},
]


class IntegrationValidationError(ValueError):
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


def _ensure_org_active(db: Session, organization_id: str) -> Organization:
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    if org.status != ORG_STATUS_ACTIVE:
        raise HTTPException(status_code=403, detail="La empresa está inactiva")
    return org


def connector_to_dict(row: IntegrationConnector) -> dict[str, Any]:
    config = _parse_json(row.config_json) or {}
    return {
        "id": row.id,
        "code": row.code,
        "name": row.name,
        "descripcion": row.descripcion,
        "connector_type": row.connector_type,
        "status": row.status,
        "auth_type": row.auth_type,
        "secret_configured": secret_configured(row.secret_ref),
        "config": {k: v for k, v in config.items() if "secret" not in k.lower() and "password" not in k.lower()},
        "mapping": _parse_json(row.mapping_json),
        "schema": _parse_json(row.schema_json),
        "destination_type": row.destination_type,
        "signal_source_code": row.signal_source_code,
        "trigger_mode": row.trigger_mode,
        "retry_max": row.retry_max,
        "timeout_ms": row.timeout_ms,
        "health": {
            "last_success_at": row.last_success_at.isoformat() if row.last_success_at else None,
            "last_error_at": row.last_error_at.isoformat() if row.last_error_at else None,
            "last_error_message": row.last_error_message,
            "last_latency_ms": row.last_latency_ms,
            "consecutive_failures": row.consecutive_failures,
            "circuit_open": _is_circuit_open(row),
        },
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _ensure_aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _is_circuit_open(row: IntegrationConnector) -> bool:
    until = _ensure_aware(row.circuit_open_until)
    if until and until > _utcnow():
        return True
    return False


def _get_connector(db: Session, organization_id: str, connector_id: str) -> IntegrationConnector:
    row = db.query(IntegrationConnector).filter(
        IntegrationConnector.id == connector_id,
        IntegrationConnector.organization_id == organization_id,
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Conector no encontrado")
    return row


def list_catalog() -> list[dict[str, Any]]:
    return CONNECTOR_CATALOG


def list_connectors(db: Session, organization_id: str) -> list[IntegrationConnector]:
    return (
        db.query(IntegrationConnector)
        .filter(IntegrationConnector.organization_id == organization_id, IntegrationConnector.is_active.is_(True))
        .order_by(IntegrationConnector.name)
        .all()
    )


def create_connector(db: Session, organization_id: str, data: dict[str, Any], user_id: str | None) -> IntegrationConnector:
    _ensure_org_active(db, organization_id)
    ctype = data.get("connector_type")
    if ctype not in ConnectorType.ALL:
        raise IntegrationValidationError("Tipo de conector no válido")
    code = str(data["code"]).strip().lower()
    exists = db.query(IntegrationConnector).filter(
        IntegrationConnector.organization_id == organization_id, IntegrationConnector.code == code
    ).first()
    if exists:
        raise IntegrationValidationError("Ya existe un conector con ese código")
    secret_ref = None
    if data.get("secret_env_var"):
        secret_ref = build_env_secret_ref(data["secret_env_var"])
    row = IntegrationConnector(
        organization_id=organization_id,
        code=code,
        name=data["name"],
        descripcion=data.get("descripcion"),
        connector_type=ctype,
        status=ConnectorStatus.BORRADOR,
        auth_type=data.get("auth_type", "NINGUNA"),
        secret_ref=secret_ref,
        config_json=_json(data.get("config")) if data.get("config") else None,
        mapping_json=_json(data.get("mapping")) if data.get("mapping") else None,
        schema_json=_json(data.get("schema")) if data.get("schema") else None,
        destination_type=data.get("destination_type"),
        signal_source_code=data.get("signal_source_code"),
        trigger_mode=data.get("trigger_mode", TriggerMode.MANUAL),
        retry_max=data.get("retry_max", 3),
        timeout_ms=data.get("timeout_ms", 30000),
        allow_internal_urls=bool(data.get("allow_internal_urls", False)),
        created_by=user_id,
    )
    webhook_token_plain: str | None = None
    if ctype == ConnectorType.WEBHOOK and data.get("generate_webhook_token"):
        webhook_token_plain = secrets.token_urlsafe(32)
        row.webhook_token_hash = hashlib.sha256(webhook_token_plain.encode()).hexdigest()
    db.add(row)
    db.flush()
    row._webhook_token_once = webhook_token_plain  # type: ignore[attr-defined]
    write_audit(db, action="integraciones.conector.creado", organization_id=organization_id, user_id=user_id,
                detail=_json({"connector_id": row.id, "code": row.code, "type": ctype}), commit=False)
    return row


def update_connector(db: Session, organization_id: str, connector_id: str, data: dict[str, Any], user_id: str | None) -> IntegrationConnector:
    row = _get_connector(db, organization_id, connector_id)
    for field in ("name", "descripcion", "destination_type", "signal_source_code", "trigger_mode", "status"):
        if field in data and data[field] is not None:
            setattr(row, field, data[field])
    if "config" in data:
        row.config_json = _json(data["config"])
    if "mapping" in data:
        row.mapping_json = _json(data["mapping"])
    if "schema" in data:
        row.schema_json = _json(data["schema"])
    if data.get("secret_env_var"):
        row.secret_ref = build_env_secret_ref(data["secret_env_var"])
    db.flush()
    write_audit(db, action="integraciones.conector.editado", organization_id=organization_id, user_id=user_id,
                detail=_json({"connector_id": connector_id}), commit=False)
    return row


def _build_auth_headers(row: IntegrationConnector) -> dict[str, str]:
    from app.gateway.secrets import resolve_secret
    secret = resolve_secret(row.secret_ref)
    if not secret:
        return {}
    if row.auth_type == "API_KEY":
        return {"X-API-Key": secret}
    if row.auth_type == "BEARER":
        return {"Authorization": f"Bearer {secret}"}
    if row.auth_type == "BASIC":
        return {"Authorization": f"Basic {secret}"}
    return {}


def test_connection(db: Session, organization_id: str, connector_id: str, user_id: str | None) -> dict[str, Any]:
    row = _get_connector(db, organization_id, connector_id)
    row.status = ConnectorStatus.VALIDANDO
    config = _parse_json(row.config_json) or {}
    try:
        result = exec_mod.execute_connector(
            row.connector_type, config,
            allow_internal=row.allow_internal_urls,
            timeout_ms=row.timeout_ms,
            auth_headers=_build_auth_headers(row),
        )
        row.status = ConnectorStatus.ACTIVO
        row.last_success_at = _utcnow()
        row.last_latency_ms = result.get("latency_ms")
        row.consecutive_failures = 0
        row.circuit_open_until = None
        test_status = TestResult.EXITOSA
        message = "Conexión verificada correctamente"
        write_audit(db, action="integraciones.conector.probado", organization_id=organization_id, user_id=user_id,
                    detail=_json({"connector_id": connector_id, "result": test_status}), commit=False)
        return {"resultado": test_status, "mensaje": message, "latencia_ms": result.get("latency_ms")}
    except exec_mod.ExecutorError as exc:
        row.status = ConnectorStatus.ERROR
        row.last_error_at = _utcnow()
        row.last_error_message = str(exc)[:500]
        row.consecutive_failures += 1
        write_audit(db, action="integraciones.conector.probado", organization_id=organization_id, user_id=user_id,
                    detail=_json({"connector_id": connector_id, "result": TestResult.FALLIDA, "error": str(exc)}), commit=False)
        return {"resultado": TestResult.FALLIDA, "mensaje": str(exc), "categoria": exc.category}


def _record_execution(
    db: Session, row: IntegrationConnector, *, status: str, user_id: str | None,
    records_processed: int = 0, records_valid: int = 0, records_rejected: int = 0,
    latency_ms: int | None = None, error_category: str | None = None, error_message: str | None = None,
    idempotency_key: str | None = None, trigger_mode: str = TriggerMode.MANUAL,
) -> IntegrationExecution:
    ex = IntegrationExecution(
        connector_id=row.id,
        organization_id=row.organization_id,
        trigger_mode=trigger_mode,
        status=status,
        finished_at=_utcnow(),
        latency_ms=latency_ms,
        records_processed=records_processed,
        records_valid=records_valid,
        records_rejected=records_rejected,
        error_category=error_category,
        error_message=error_message[:500] if error_message else None,
        idempotency_key=idempotency_key,
        user_id=user_id,
    )
    db.add(ex)
    db.flush()
    return ex


def execute_connector(
    db: Session, organization_id: str, connector_id: str, user_id: str | None,
    *, idempotency_key: str | None = None, payload: dict | None = None,
) -> dict[str, Any]:
    row = _get_connector(db, organization_id, connector_id)
    if row.status not in (ConnectorStatus.ACTIVO, ConnectorStatus.DEGRADADO):
        raise IntegrationValidationError(f"Conector no activo (estado: {row.status})")
    if _is_circuit_open(row):
        raise IntegrationValidationError("Circuit breaker abierto — servicio temporalmente no disponible")
    if idempotency_key:
        prev = db.query(IntegrationExecution).filter(
            IntegrationExecution.connector_id == row.id,
            IntegrationExecution.idempotency_key == idempotency_key,
            IntegrationExecution.status == ExecutionStatus.EXITOSA,
        ).first()
        if prev:
            return {"idempotent": True, "execution_id": prev.id, "status": prev.status}

    config = _parse_json(row.config_json) or {}
    mapping = _parse_json(row.mapping_json)
    schema = _parse_json(row.schema_json)
    auth_headers = _build_auth_headers(row)
    last_error: exec_mod.ExecutorError | None = None

    for attempt in range(row.retry_max + 1):
        try:
            result = exec_mod.execute_connector(
                row.connector_type, config,
                allow_internal=row.allow_internal_urls,
                timeout_ms=row.timeout_ms,
                max_bytes=row.max_response_bytes,
                auth_headers=auth_headers,
                payload=payload,
            )
            records = exec_mod.apply_mapping(result.get("records", []), mapping)
            valid, schema_errors = exec_mod.validate_schema(records, schema)
            rejected = len(records) - len(valid)

            signals_created = 0
            if row.destination_type == DestinationType.SENALES and valid:
                signals_created = _emit_signals(db, organization_id, row, valid, user_id)

            row.last_success_at = _utcnow()
            row.last_latency_ms = result.get("latency_ms")
            row.consecutive_failures = 0
            row.circuit_open_until = None
            if row.status == ConnectorStatus.DEGRADADO:
                row.status = ConnectorStatus.ACTIVO

            ex = _record_execution(
                db, row, status=ExecutionStatus.EXITOSA if not schema_errors else ExecutionStatus.PARCIAL,
                user_id=user_id, records_processed=len(records), records_valid=len(valid),
                records_rejected=rejected, latency_ms=result.get("latency_ms"),
                idempotency_key=idempotency_key,
            )
            write_audit(db, action="integraciones.conector.ejecutado", organization_id=organization_id, user_id=user_id,
                        detail=_json({"connector_id": connector_id, "execution_id": ex.id, "valid": len(valid)}), commit=False)
            return {
                "execution_id": ex.id,
                "status": ex.status,
                "records_processed": len(records),
                "records_valid": len(valid),
                "records_rejected": rejected,
                "schema_errors": schema_errors,
                "signals_created": signals_created,
                "latency_ms": result.get("latency_ms"),
            }
        except exec_mod.ExecutorError as exc:
            last_error = exc
            if attempt < row.retry_max:
                time.sleep(row.retry_delay_ms / 1000.0 * (attempt + 1))
            continue

    row.consecutive_failures += 1
    row.last_error_at = _utcnow()
    row.last_error_message = str(last_error)[:500] if last_error else "Error desconocido"
    if row.consecutive_failures >= row.circuit_breaker_threshold:
        row.status = ConnectorStatus.DEGRADADO
        row.circuit_open_until = _utcnow() + timedelta(seconds=row.circuit_breaker_cooldown_sec)
    ex = _record_execution(
        db, row, status=ExecutionStatus.FALLIDA, user_id=user_id,
        error_category=last_error.category if last_error else ErrorCategory.DESCONOCIDO,
        error_message=str(last_error) if last_error else None,
        idempotency_key=idempotency_key,
    )
    write_audit(db, action="integraciones.conector.ejecutado", organization_id=organization_id, user_id=user_id,
                detail=_json({"connector_id": connector_id, "execution_id": ex.id, "failed": True}), commit=False)
    raise IntegrationValidationError(str(last_error) if last_error else "Ejecución fallida")


def _emit_signals(db: Session, organization_id: str, row: IntegrationConnector, records: list[dict], user_id: str | None) -> int:
    count = 0
    for rec in records:
        payload = {
            "tipo": rec.get("tipo", "integracion"),
            "dominio": rec.get("dominio", "integraciones"),
            "evento": rec.get("evento", f"conector.{row.code}"),
            "referencia": rec.get("referencia", f"{row.code}:{count}"),
            "origen": row.code,
            "modo_ingesta": "REAL",
            "source_code": row.signal_source_code,
            "metrica": rec.get("metrica"),
            "valor_metrica": str(rec.get("valor_metrica", "")) if rec.get("valor_metrica") is not None else None,
            "evidencia_resumen": rec.get("evidencia_resumen", f"Ingesta vía conector {row.name}")[:500],
            "metadata": rec,
            "idempotency_key": rec.get("idempotency_key"),
        }
        try:
            signal_svc.ingest_real_signal(db, organization_id=organization_id, user_id=user_id, data=payload, auto_process=False)
            count += 1
        except HTTPException:
            continue
    return count


def receive_webhook(
    db: Session,
    organization_id: str,
    connector_id: str,
    token: str,
    payload: dict,
) -> dict[str, Any]:
    row = _get_connector(db, organization_id, connector_id)
    if row.connector_type != ConnectorType.WEBHOOK:
        raise IntegrationValidationError("Conector no es de tipo webhook")
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    if row.webhook_token_hash and row.webhook_token_hash != token_hash:
        raise IntegrationValidationError("Token webhook inválido")
    dedupe_key = payload.get("idempotency_key") or exec_mod.hash_payload(_json(payload))
    existing = db.query(IntegrationWebhookEvent).filter(
        IntegrationWebhookEvent.organization_id == organization_id,
        IntegrationWebhookEvent.dedupe_key == dedupe_key,
    ).first()
    if existing:
        return {"status": "DUPLICADO", "event_id": existing.id}
    event = IntegrationWebhookEvent(
        connector_id=row.id,
        organization_id=organization_id,
        dedupe_key=dedupe_key,
        payload_hash=exec_mod.hash_payload(_json(payload)),
        status="RECIBIDO",
    )
    db.add(event)
    db.flush()
    result = execute_connector(db, organization_id, connector_id, None, idempotency_key=dedupe_key, payload=payload)
    event.status = "PROCESADO"
    event.processed_at = _utcnow()
    return {"status": "PROCESADO", "event_id": event.id, **result}


def list_executions(db: Session, organization_id: str, connector_id: str, limit: int = 20) -> list[dict]:
    _get_connector(db, organization_id, connector_id)
    rows = (
        db.query(IntegrationExecution)
        .filter(IntegrationExecution.connector_id == connector_id, IntegrationExecution.organization_id == organization_id)
        .order_by(IntegrationExecution.started_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id, "status": r.status, "started_at": r.started_at.isoformat(),
            "latency_ms": r.latency_ms, "records_processed": r.records_processed,
            "records_valid": r.records_valid, "records_rejected": r.records_rejected,
            "error_category": r.error_category, "error_message": r.error_message,
        }
        for r in rows
    ]


def get_health(db: Session, organization_id: str, connector_id: str) -> dict[str, Any]:
    row = _get_connector(db, organization_id, connector_id)
    total = db.query(IntegrationExecution).filter(IntegrationExecution.connector_id == row.id).count()
    success = db.query(IntegrationExecution).filter(
        IntegrationExecution.connector_id == row.id, IntegrationExecution.status == ExecutionStatus.EXITOSA
    ).count()
    return {
        "connector_id": row.id,
        "status": row.status,
        "circuit_open": _is_circuit_open(row),
        "consecutive_failures": row.consecutive_failures,
        "last_success_at": row.last_success_at.isoformat() if row.last_success_at else None,
        "last_error_at": row.last_error_at.isoformat() if row.last_error_at else None,
        "last_latency_ms": row.last_latency_ms,
        "total_executions": total,
        "success_rate": round(success / total * 100, 2) if total else None,
    }
