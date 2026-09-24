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
from app.continuidad_models import ContinuidadAlerta, ContinuidadServicioCritico
from app.governance_models import GovAccessLog, GovLineageEvent
from app.models import AuditLog, Organization
from app.services import governance_service as gov_svc
from app.services import integration_executors as exec_mod
from app.services import integration_wiring as wiring
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
        "gov_catalog_entry_id": row.gov_catalog_entry_id,
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
    gov_catalog_entry_id = data.get("gov_catalog_entry_id")
    if gov_catalog_entry_id:
        try:
            wiring.validate_gov_catalog_entry(db, organization_id, gov_catalog_entry_id)
        except ValueError as exc:
            raise IntegrationValidationError(str(exc)) from exc
    row = IntegrationConnector(
        organization_id=organization_id,
        code=code,
        name=data["name"],
        descripcion=data.get("descripcion"),
        connector_type=ctype,
        status=ConnectorStatus.BORRADOR,
        auth_type=data.get("auth_type", "NINGUNA"),
        secret_ref=secret_ref,
        gov_catalog_entry_id=gov_catalog_entry_id,
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
    if "gov_catalog_entry_id" in data:
        gid = data.get("gov_catalog_entry_id")
        if gid:
            try:
                wiring.validate_gov_catalog_entry(db, organization_id, gid)
            except ValueError as exc:
                raise IntegrationValidationError(str(exc)) from exc
        row.gov_catalog_entry_id = gid
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
    correlation_id: str | None = None,
) -> IntegrationExecution:
    summary = {"correlation_id": correlation_id} if correlation_id else None
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
        result_summary_json=_json(summary) if summary else None,
    )
    db.add(ex)
    db.flush()
    return ex


def execute_connector(
    db: Session, organization_id: str, connector_id: str, user_id: str | None,
    *, idempotency_key: str | None = None, payload: dict | None = None,
) -> dict[str, Any]:
    row = _get_connector(db, organization_id, connector_id)
    correlation_id = wiring.new_correlation_id()
    prev_cont_estado: str | None = None
    try:
        servicio = wiring.ensure_continuidad_servicio(db, organization_id, row, user_id)
        prev_cont_estado = servicio.estado_operacional
    except Exception:
        prev_cont_estado = None

    wiring.identity_preflight_execute(db, organization_id, user_id)

    if row.status not in (ConnectorStatus.ACTIVO, ConnectorStatus.DEGRADADO):
        raise IntegrationValidationError(f"Conector no activo (estado: {row.status})")
    if _is_circuit_open(row):
        raise IntegrationValidationError("Circuit breaker abierto — servicio temporalmente no disponible")

    preflight = wiring.gov_preflight(db, organization_id, row, correlation_id)
    if not preflight.allowed:
        wiring.audit_preflight_denied(db, organization_id, user_id, connector_id, preflight)
        raise IntegrationValidationError(
            f"Preflight gobierno: {preflight.decision} — {'; '.join(preflight.reasons)}"
        )

    if idempotency_key:
        prev = db.query(IntegrationExecution).filter(
            IntegrationExecution.connector_id == row.id,
            IntegrationExecution.idempotency_key == idempotency_key,
            IntegrationExecution.status == ExecutionStatus.EXITOSA,
        ).first()
        if prev:
            return {"idempotent": True, "execution_id": prev.id, "status": prev.status, "correlation_id": correlation_id}

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
            if preflight.minimization_action:
                records = wiring.apply_gov_masking(
                    db, organization_id, records, preflight.minimization_action,
                )
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

            ex_status = ExecutionStatus.EXITOSA if not schema_errors else ExecutionStatus.PARCIAL
            ex = _record_execution(
                db, row, status=ex_status,
                user_id=user_id, records_processed=len(records), records_valid=len(valid),
                records_rejected=rejected, latency_ms=result.get("latency_ms"),
                idempotency_key=idempotency_key, correlation_id=correlation_id,
            )

            audit_detail = {
                "connector_id": connector_id,
                "execution_id": ex.id,
                "valid": len(valid),
                "correlation_id": correlation_id,
                "gov_decision": preflight.decision,
            }
            if preflight.catalog_entry_id:
                wiring.gov_register_access(
                    db, organization_id, user_id,
                    catalog_entry_id=preflight.catalog_entry_id,
                    connector_id=connector_id,
                    action="INTEGRACION_EJECUTAR",
                    result="OK",
                    correlation_id=correlation_id,
                    detail={"execution_id": ex.id, "records_valid": len(valid)},
                )
                wiring.gov_register_lineage(
                    db, organization_id, user_id,
                    catalog_entry_id=preflight.catalog_entry_id,
                    connector_id=connector_id,
                    execution_id=ex.id,
                    status=ex_status,
                    records_valid=len(valid),
                    records_rejected=rejected,
                    correlation_id=correlation_id,
                )
                wiring.gov_register_execution_result(
                    db, organization_id, user_id,
                    catalog_entry_id=preflight.catalog_entry_id,
                    connector_id=connector_id,
                    execution_id=ex.id,
                    technical_status=ex_status,
                    functional_ok=len(valid) > 0 or not schema_errors,
                    correlation_id=correlation_id,
                )

            write_audit(
                db, action="integraciones.conector.ejecutado",
                organization_id=organization_id, user_id=user_id,
                detail=_json(audit_detail), commit=False,
            )

            wiring.sync_continuidad_from_connector(
                db, organization_id, row,
                prev_estado=prev_cont_estado, user_id=user_id, correlation_id=correlation_id,
            )
            if row.gov_catalog_entry_id and config.get("register_backup_metadata"):
                wiring.register_connector_backup_metadata(
                    db, organization_id, row, user_id, correlation_id,
                )

            return {
                "execution_id": ex.id,
                "status": ex.status,
                "records_processed": len(records),
                "records_valid": len(valid),
                "records_rejected": rejected,
                "schema_errors": schema_errors,
                "signals_created": signals_created,
                "latency_ms": result.get("latency_ms"),
                "correlation_id": correlation_id,
            }
        except exec_mod.ExecutorError as exc:
            last_error = exc
            if attempt < row.retry_max:
                time.sleep(row.retry_delay_ms / 1000.0 * (attempt + 1))
            continue
        except ValueError as exc:
            raise IntegrationValidationError(str(exc)) from exc

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
        idempotency_key=idempotency_key, correlation_id=correlation_id,
    )
    if preflight.catalog_entry_id:
        wiring.gov_register_access(
            db, organization_id, user_id,
            catalog_entry_id=preflight.catalog_entry_id,
            connector_id=connector_id,
            action="INTEGRACION_EJECUTAR",
            result="ERROR",
            correlation_id=correlation_id,
            detail={"execution_id": ex.id, "failed": True},
        )
    write_audit(
        db, action="integraciones.conector.ejecutado",
        organization_id=organization_id, user_id=user_id,
        detail=_json({"connector_id": connector_id, "execution_id": ex.id, "failed": True, "correlation_id": correlation_id}),
        commit=False,
    )
    wiring.sync_continuidad_from_connector(
        db, organization_id, row,
        prev_estado=prev_cont_estado, user_id=user_id, correlation_id=correlation_id,
    )
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
            "correlation_id": (_parse_json(r.result_summary_json) or {}).get("correlation_id"),
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


def list_connectors_overview(db: Session, organization_id: str) -> list[dict[str, Any]]:
    """Vista operativa — grilla integraciones con gobierno y continuidad."""
    org = db.get(Organization, organization_id)
    org_name = org.name if org else ""
    rows = list_connectors(db, organization_id)
    conn_ids = [r.id for r in rows]
    servicio_map: dict[str, ContinuidadServicioCritico] = {}
    for svc in db.query(ContinuidadServicioCritico).filter(
        ContinuidadServicioCritico.organization_id == organization_id,
        ContinuidadServicioCritico.is_active.is_(True),
    ):
        ref = svc.proveedor_ref or ""
        if ref.startswith(wiring.PROVEEDOR_REF_PREFIX):
            servicio_map[ref[len(wiring.PROVEEDOR_REF_PREFIX):]] = svc

    last_ex: dict[str, IntegrationExecution] = {}
    if conn_ids:
        for ex in (
            db.query(IntegrationExecution)
            .filter(IntegrationExecution.connector_id.in_(conn_ids))
            .order_by(IntegrationExecution.started_at.desc())
        ):
            if ex.connector_id not in last_ex:
                last_ex[ex.connector_id] = ex

    out: list[dict[str, Any]] = []
    for row in rows:
        item = connector_to_dict(row)
        item["organization_name"] = org_name
        item["proveedor_ref"] = wiring.proveedor_ref_for_connector(row.id)
        svc = servicio_map.get(row.id)
        item["continuidad_estado"] = svc.estado_operacional if svc else None
        item["continuidad_servicio_id"] = svc.id if svc else None
        policy = None
        if row.gov_catalog_entry_id:
            policy = gov_svc.get_connector_policy_view(db, organization_id, row.gov_catalog_entry_id)
        item["politica_decision"] = policy.get("provider_decision") if policy else None
        item["politica_restricciones"] = policy.get("restrictions") if policy else []
        ex = last_ex.get(row.id)
        if ex:
            summary = _parse_json(ex.result_summary_json) or {}
            item["ultima_ejecucion"] = {
                "id": ex.id,
                "status": ex.status,
                "started_at": ex.started_at.isoformat() if ex.started_at else None,
                "correlation_id": summary.get("correlation_id"),
            }
        else:
            item["ultima_ejecucion"] = None
        out.append(item)
    return out


def get_wiring_detail(db: Session, organization_id: str, connector_id: str) -> dict[str, Any]:
    """Detalle cableado — catálogo, política, linaje, auditoría y continuidad."""
    row = _get_connector(db, organization_id, connector_id)
    catalog: dict[str, Any] | None = None
    policy: dict[str, Any] | None = None
    lineage: list[dict[str, Any]] = []
    access_logs: list[dict[str, Any]] = []
    if row.gov_catalog_entry_id:
        entry = gov_svc.get_catalog_entry(db, organization_id, row.gov_catalog_entry_id)
        if entry:
            catalog = gov_svc.catalog_to_dict(entry, db)
        policy = gov_svc.get_connector_policy_view(db, organization_id, row.gov_catalog_entry_id)
        try:
            lineage = gov_svc.list_lineage(db, organization_id, row.gov_catalog_entry_id)
        except LookupError:
            lineage = []
        access_rows = (
            db.query(GovAccessLog)
            .filter(
                GovAccessLog.organization_id == organization_id,
                GovAccessLog.catalog_entry_id == row.gov_catalog_entry_id,
            )
            .order_by(GovAccessLog.created_at.desc())
            .limit(40)
            .all()
        )
        access_logs = [gov_svc.access_log_to_dict(r) for r in access_rows]

    ref = wiring.proveedor_ref_for_connector(row.id)
    servicio = (
        db.query(ContinuidadServicioCritico)
        .filter(
            ContinuidadServicioCritico.organization_id == organization_id,
            ContinuidadServicioCritico.proveedor_ref == ref,
            ContinuidadServicioCritico.is_active.is_(True),
        )
        .first()
    )
    entidad_refs = {connector_id, row.gov_catalog_entry_id or "", servicio.id if servicio else ""}
    alertas = (
        db.query(ContinuidadAlerta)
        .filter(
            ContinuidadAlerta.organization_id == organization_id,
            ContinuidadAlerta.entidad_ref.in_([r for r in entidad_refs if r]),
        )
        .order_by(ContinuidadAlerta.created_at.desc())
        .limit(30)
        .all()
    )
    audit_rows = (
        db.query(AuditLog)
        .filter(
            AuditLog.organization_id == organization_id,
            AuditLog.detail.contains(connector_id),
        )
        .order_by(AuditLog.created_at.desc())
        .limit(40)
        .all()
    )
    preflight = None
    if row.gov_catalog_entry_id:
        pre = wiring.gov_preflight(db, organization_id, row, wiring.new_correlation_id())
        preflight = {
            "allowed": pre.allowed,
            "decision": pre.decision,
            "reasons": pre.reasons,
            "minimization_action": pre.minimization_action,
        }

    return {
        "connector": connector_to_dict(row),
        "catalog_entry": catalog,
        "policy": policy,
        "preflight": preflight,
        "executions": list_executions(db, organization_id, connector_id, limit=25),
        "health": get_health(db, organization_id, connector_id),
        "lineage": lineage,
        "access_logs": access_logs,
        "continuidad": {
            "proveedor_ref": ref,
            "servicio_id": servicio.id if servicio else None,
            "servicio_nombre": servicio.nombre if servicio else None,
            "estado_operacional": servicio.estado_operacional if servicio else None,
        },
        "eventos": [
            {
                "id": a.id,
                "tipo": a.tipo,
                "mensaje": a.mensaje,
                "severidad": a.severidad,
                "entidad_ref": a.entidad_ref,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "resuelta": a.resuelta,
            }
            for a in alertas
        ],
        "auditoria": [
            {
                "id": a.id,
                "action": a.action,
                "detail": a.detail,
                "user_id": a.user_id,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in audit_rows
        ],
    }


_TRACE_STAGE_MAP = {
    "auth.login": "IDENTIDAD",
    "auth.login.mfa": "IDENTIDAD",
    "integraciones.preflight.denegado": "PREFLIGHT",
    "integraciones.conector.ejecutado": "EJECUCIÓN",
    "integraciones.conector.probado": "EJECUCIÓN",
    "integraciones.salud.recuperada": "CONTINUIDAD",
    "integraciones.backup.metadata": "BACKUP",
    "continuidad.restore.bloqueado": "RESTORE",
}


def trace_correlation(db: Session, organization_id: str, correlation_id: str) -> dict[str, Any]:
    """Timeline compacto por correlation_id."""
    cid = correlation_id.strip()
    if not cid:
        raise IntegrationValidationError("correlation_id requerido")

    pasos: list[dict[str, Any]] = []

    for ex in db.query(IntegrationExecution).filter(
        IntegrationExecution.organization_id == organization_id,
    ):
        summary = _parse_json(ex.result_summary_json) or {}
        if summary.get("correlation_id") == cid:
            pasos.append({
                "etapa": "EJECUCIÓN",
                "origen": "integration_execution",
                "referencia": ex.id,
                "estado": ex.status,
                "detalle": f"Procesados {ex.records_processed}, válidos {ex.records_valid}",
                "timestamp": ex.started_at.isoformat() if ex.started_at else None,
            })

    for log in db.query(AuditLog).filter(
        AuditLog.organization_id == organization_id,
        AuditLog.detail.contains(cid),
    ).limit(80):
        pasos.append({
            "etapa": _TRACE_STAGE_MAP.get(log.action, "AUDITORÍA"),
            "origen": "audit",
            "referencia": log.id,
            "estado": log.action,
            "detalle": (log.detail or "")[:240],
            "timestamp": log.created_at.isoformat() if log.created_at else None,
        })

    for acc in db.query(GovAccessLog).filter(
        GovAccessLog.organization_id == organization_id,
        GovAccessLog.detail.contains(cid),
    ).limit(40):
        pasos.append({
            "etapa": "GOBIERNO",
            "origen": "gov_access",
            "referencia": acc.id,
            "estado": f"{acc.action} / {acc.result}",
            "detalle": acc.detail or "",
            "timestamp": acc.created_at.isoformat() if acc.created_at else None,
        })

    for lin in db.query(GovLineageEvent).filter(
        GovLineageEvent.organization_id == organization_id,
        GovLineageEvent.metadata_json.contains(cid),
    ).limit(40):
        pasos.append({
            "etapa": "LINAJE",
            "origen": "gov_lineage",
            "referencia": lin.id,
            "estado": lin.step_type,
            "detalle": lin.label,
            "timestamp": lin.created_at.isoformat() if lin.created_at else None,
        })

    for al in db.query(ContinuidadAlerta).filter(
        ContinuidadAlerta.organization_id == organization_id,
        ContinuidadAlerta.mensaje.contains(cid),
    ).limit(20):
        pasos.append({
            "etapa": "CONTINUIDAD",
            "origen": "continuidad_alerta",
            "referencia": al.id,
            "estado": al.tipo,
            "detalle": al.mensaje,
            "timestamp": al.created_at.isoformat() if al.created_at else None,
        })

    pasos.sort(key=lambda p: p.get("timestamp") or "")
    return {"correlation_id": cid, "pasos": pasos}
