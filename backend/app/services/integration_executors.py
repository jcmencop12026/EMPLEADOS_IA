"""Ejecutores de conectores — sin llamadas externas reales en tests (1330)."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import time
from typing import Any

from app.integration_enums import ConnectorType, ErrorCategory
from app.integration_security import SSRFError, validate_external_url


class ExecutorError(Exception):
    def __init__(self, message: str, category: str = ErrorCategory.DESCONOCIDO):
        super().__init__(message)
        self.category = category


def execute_connector(
    connector_type: str,
    config: dict[str, Any],
    *,
    allow_internal: bool = False,
    timeout_ms: int = 30000,
    max_bytes: int = 5_242_880,
    auth_headers: dict[str, str] | None = None,
    payload: dict | None = None,
) -> dict[str, Any]:
    """Ejecuta conector según tipo. Modo simulación para entornos de prueba."""
    start = time.monotonic()
    if config.get("simulate_failure"):
        raise ExecutorError(config.get("failure_message", "Error simulado"), config.get("failure_category", ErrorCategory.CONEXION))
    if config.get("simulate_timeout"):
        raise ExecutorError("Tiempo de espera agotado", ErrorCategory.TIMEOUT)

    if connector_type == ConnectorType.API_REST:
        result = _execute_rest(config, allow_internal=allow_internal, auth_headers=auth_headers)
    elif connector_type == ConnectorType.ARCHIVO:
        result = _execute_file(config)
    elif connector_type == ConnectorType.BASE_DATOS:
        result = _execute_database(config)
    elif connector_type == ConnectorType.SFTP:
        result = _execute_sftp(config)
    elif connector_type == ConnectorType.WEBHOOK:
        if payload:
            result = {"records": [payload], "summary": {"direction": "entrante"}}
        else:
            result = _execute_webhook_outbound(config, payload or {}, allow_internal=allow_internal)
    elif connector_type == ConnectorType.CORREO:
        result = _execute_email(config)
    elif connector_type == ConnectorType.EVENTO:
        result = _execute_event(config, payload or {})
    else:
        raise ExecutorError(f"Tipo no soportado: {connector_type}", ErrorCategory.CONFIGURACION)

    latency = int((time.monotonic() - start) * 1000)
    records = result.get("records", [])
    return {
        "records": records,
        "records_count": len(records),
        "latency_ms": latency,
        "raw_summary": result.get("summary", {}),
    }


def _execute_rest(config: dict, *, allow_internal: bool, auth_headers: dict | None) -> dict:
    if config.get("mock_response"):
        data = config["mock_response"]
        if isinstance(data, list):
            return {"records": data, "summary": {"mock": True}}
        return {"records": [data] if isinstance(data, dict) else [], "summary": {"mock": True}}
    url = config.get("base_url", "") + config.get("endpoint", "")
    if not url:
        raise ExecutorError("URL no configurada", ErrorCategory.CONFIGURACION)
    try:
        validate_external_url(url, allow_internal=allow_internal)
    except SSRFError as exc:
        raise ExecutorError(str(exc), ErrorCategory.SSRF) from exc
    method = (config.get("method") or "GET").upper()
    if method not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
        raise ExecutorError("Método HTTP no permitido", ErrorCategory.CONFIGURACION)
    return {"records": [], "summary": {"url_validated": True, "method": method, "auth": bool(auth_headers)}}


def _execute_file(config: dict) -> dict:
    content = config.get("file_content")
    file_type = (config.get("file_type") or "JSON").upper()
    if not content:
        raise ExecutorError("Contenido de archivo no proporcionado", ErrorCategory.CONFIGURACION)
    if file_type == "JSON":
        data = json.loads(content) if isinstance(content, str) else content
        records = data if isinstance(data, list) else [data]
    elif file_type == "CSV":
        reader = csv.DictReader(io.StringIO(content))
        records = list(reader)
    elif file_type == "TXT":
        records = [{"line": ln} for ln in content.strip().splitlines() if ln.strip()]
    else:
        raise ExecutorError(f"Tipo de archivo no soportado: {file_type}", ErrorCategory.VALIDACION)
    return {"records": records, "summary": {"file_type": file_type, "rows": len(records)}}


def _execute_database(config: dict) -> dict:
    query_id = config.get("query_id")
    if not query_id:
        raise ExecutorError("Consulta parametrizada requerida (query_id)", ErrorCategory.CONFIGURACION)
    allowed = config.get("allowed_queries", {})
    if query_id not in allowed:
        raise ExecutorError("Consulta no autorizada", ErrorCategory.PERMISOS)
    mock_rows = config.get("mock_rows") or allowed.get(query_id, {}).get("mock_rows", [])
    return {"records": mock_rows, "summary": {"query_id": query_id, "engine": config.get("engine", "postgresql")}}


def _execute_sftp(config: dict) -> dict:
    action = config.get("action", "list")
    if action not in ("list", "download", "upload"):
        raise ExecutorError("Acción SFTP no permitida", ErrorCategory.PERMISOS)
    mock_files = config.get("mock_files", [{"name": "datos.csv", "size": 1024}])
    return {"records": mock_files, "summary": {"action": action, "mock": True}}


def _execute_webhook_outbound(config: dict, payload: dict, *, allow_internal: bool) -> dict:
    url = config.get("destination_url")
    if not url:
        raise ExecutorError("URL destino webhook no configurada", ErrorCategory.CONFIGURACION)
    try:
        validate_external_url(url, allow_internal=allow_internal)
    except SSRFError as exc:
        raise ExecutorError(str(exc), ErrorCategory.SSRF) from exc
    return {"records": [payload], "summary": {"destination_validated": True}}


def _execute_email(config: dict) -> dict:
    protocol = (config.get("protocol") or "IMAP").upper()
    if protocol not in ("IMAP", "SMTP"):
        raise ExecutorError("Protocolo de correo no soportado", ErrorCategory.CONFIGURACION)
    mock_messages = config.get("mock_messages", [])
    return {"records": mock_messages, "summary": {"protocol": protocol, "count": len(mock_messages)}}


def _execute_event(config: dict, payload: dict) -> dict:
    event_type = config.get("event_type", "integration.event")
    record = {"event_type": event_type, **payload}
    return {"records": [record], "summary": {"event_type": event_type}}


def apply_mapping(records: list[dict], mapping: list[dict] | None) -> list[dict]:
    if not mapping:
        return records
    out: list[dict] = []
    for rec in records:
        mapped: dict[str, Any] = {}
        for rule in mapping:
            op = rule.get("op", "rename")
            src = rule.get("source")
            dst = rule.get("target", src)
            if op == "rename" and src:
                mapped[dst] = rec.get(src)
            elif op == "fixed":
                mapped[dst] = rule.get("value")
            elif op == "concat" and rule.get("sources"):
                mapped[dst] = " ".join(str(rec.get(s, "")) for s in rule["sources"])
            elif op == "cast" and src:
                val = rec.get(src)
                cast = rule.get("cast_type", "string")
                if cast == "number":
                    mapped[dst] = float(val) if val is not None else None
                elif cast == "boolean":
                    mapped[dst] = bool(val)
                else:
                    mapped[dst] = str(val) if val is not None else None
        out.append(mapped if mapped else rec)
    return out


def validate_schema(records: list[dict], schema: dict | None) -> tuple[list[dict], list[str]]:
    if not schema:
        return records, []
    required = schema.get("required", [])
    errors: list[str] = []
    valid: list[dict] = []
    for i, rec in enumerate(records):
        missing = [f for f in required if f not in rec or rec[f] is None]
        if missing:
            errors.append(f"Registro {i}: faltan campos {missing}")
        else:
            valid.append(rec)
    return valid, errors


def hash_payload(payload: bytes | str) -> str:
    if isinstance(payload, str):
        payload = payload.encode()
    return hashlib.sha256(payload).hexdigest()
