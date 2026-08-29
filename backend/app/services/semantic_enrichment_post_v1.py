"""Enriquecimiento semántico post-V1 — adopción del contrato P1-ID-02 global.

Reutiliza semantic_contract.py; no define un contrato paralelo.
"""

from __future__ import annotations

from typing import Any, Callable

from app.services.semantic_contract import (
    CONTRACT_VERSION,
    SEMANTIC_HECHO,
    SEMANTIC_INFERENCIA,
    SEMANTIC_RECOMENDACION,
    SEMANTIC_SIN_CLASIFICAR,
    SUB_ACCION_PROPUESTA,
    SUB_ALERTA,
    SUB_ESTIMACION,
    SUB_PREDICCION,
    SUB_SENAL_OBSERVADA,
    SUB_VALOR_POTENCIAL,
    SUB_VALOR_VERIFICADO,
    attach_semantic,
    contract_header,
    from_llm_output,
    semantic_meta,
    valor_field_semantics,
)

# --- Subtipos post-V1 ---
SUB_EVENTO_REGISTRADO = "EVENTO_REGISTRADO"
SUB_CONFIGURACION = "CONFIGURACION"
SUB_RIESGO_ESTIMADO = "RIESGO_ESTIMADO"
SUB_POLITICA_APLICADA = "POLITICA_APLICADA"
SUB_EJECUCION_CONFIRMADA = "EJECUCION_CONFIRMADA"
SUB_APROBACION = "APROBACION"
SUB_PATRON_INFERIDO = "PATRON_INFERIDO"
SUB_TCO_PROYECTADO = "TCO_PROYECTADO"
SUB_TCO_OBSERVADO = "TCO_OBSERVADO"
SUB_PROYECCION = "PROYECCION"
SUB_CAUSA_ESTIMADA = "CAUSA_ESTIMADA"
SUB_RANKING_INFERIDO = "RANKING_INFERIDO"
SUB_HALLAZGO_AUTOMATICO = "HALLAZGO_AUTOMATICO"
SUB_CONFLICTO_DETECTADO = "CONFLICTO_DETECTADO"
SUB_REPRIORIZACION = "REPRIORIZACION"
SUB_LECCION_DERIVADA = "LECCION_DERIVADA"


def from_aprendizaje_item(item: dict[str, Any]) -> dict[str, str | None]:
    tipo = (item.get("tipo") or item.get("kind") or "").upper()
    estado = (item.get("estado") or "").upper()
    if tipo in ("RECALIBRACION", "REPRIORIZACION") and estado in ("PENDIENTE", "PROPUESTA"):
        return semantic_meta(SEMANTIC_RECOMENDACION, subtipo=SUB_REPRIORIZACION)
    if tipo in ("RECALIBRACION", "REPRIORIZACION") and estado in ("APLICADA", "EJECUTADA"):
        return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_EJECUCION_CONFIRMADA)
    if tipo in ("DESVIACION", "PATRON", "LECCION"):
        if tipo == "LECCION" and item.get("evidencia_json"):
            return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_VALOR_VERIFICADO)
        return semantic_meta(SEMANTIC_INFERENCIA, subtipo=SUB_PATRON_INFERIDO if tipo == "PATRON" else SUB_LECCION_DERIVADA)
    if tipo in ("RESULTADO", "METRICA") and item.get("evidencia_json") is not None:
        return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_VALOR_VERIFICADO)
    if tipo == "ACCION_SUGERIDA":
        return semantic_meta(SEMANTIC_RECOMENDACION, subtipo=SUB_ACCION_PROPUESTA)
    return semantic_meta(SEMANTIC_SIN_CLASIFICAR)


# --- 1270 Multiproveedor ---

def from_llm_metric_kind(kind: str | None) -> dict[str, str | None]:
    k = (kind or "").upper()
    if k in ("TOKENS", "COSTO", "LATENCIA", "ERROR", "HEALTH", "PROVEEDOR", "MODELO", "ESTADO"):
        return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_SENAL_OBSERVADA)
    if k in ("COSTO_ESTIMADO", "LATENCIA_PREDICHA", "RANKING", "RIESGO_ESTIMADO"):
        return semantic_meta(SEMANTIC_INFERENCIA, subtipo=SUB_PREDICCION if "PREDIC" in k else SUB_RANKING_INFERIDO)
    if k in ("CAMBIO_PROVEEDOR", "CAMBIO_MODELO", "ROUTING", "OPTIMIZAR_COSTO"):
        return semantic_meta(SEMANTIC_RECOMENDACION, subtipo=SUB_ACCION_PROPUESTA)
    if k == "ROUTING_EJECUTADO":
        return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_EVENTO_REGISTRADO)
    return semantic_meta(SEMANTIC_SIN_CLASIFICAR)


def from_llm_inference_log(log: dict[str, Any]) -> dict[str, str | None]:
    if log.get("text") is not None and log.get("status") == "OK":
        return from_llm_output()
    return from_llm_metric_kind("TOKENS")


def from_llm_test_result(result: dict[str, Any]) -> dict[str, str | None]:
    return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_SENAL_OBSERVADA)


# --- 1280 / 1320 Comercial y TCO ---

def from_valor_comercial_tipo(tipo_valor: str | None) -> dict[str, str | None]:
    t = (tipo_valor or "").upper()
    if t in ("VERIFICADO", "REALIZADO", "MATERIALIZADO"):
        return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_VALOR_VERIFICADO)
    if t in ("ESTIMADO", "POTENCIAL", "PROYECTADO"):
        return semantic_meta(
            SEMANTIC_INFERENCIA,
            subtipo=SUB_ESTIMACION if t == "ESTIMADO" else SUB_VALOR_POTENCIAL,
            tooltip="Valor estimado o potencial — no equivale a realizado.",
        )
    if t == "RECOMENDACION":
        return semantic_meta(SEMANTIC_RECOMENDACION, subtipo=SUB_ACCION_PROPUESTA)
    return semantic_meta(SEMANTIC_SIN_CLASIFICAR)


def from_tco_item(item: dict[str, Any]) -> dict[str, str | None]:
    modo = (item.get("modo") or item.get("tipo") or "").upper()
    if modo in ("OBSERVADO", "REGISTRADO", "VERIFICADO"):
        return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_TCO_OBSERVADO)
    if modo in ("PROYECTADO", "FORECAST", "ESTIMADO"):
        return semantic_meta(SEMANTIC_INFERENCIA, subtipo=SUB_TCO_PROYECTADO)
    if modo == "RECOMENDACION":
        return semantic_meta(SEMANTIC_RECOMENDACION, subtipo=SUB_ACCION_PROPUESTA)
    if item.get("desviacion_pct") is not None and item.get("evidencia"):
        return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_TCO_OBSERVADO)
    if item.get("desviacion_pct") is not None:
        return semantic_meta(SEMANTIC_INFERENCIA, subtipo=SUB_ESTIMACION)
    return semantic_meta(SEMANTIC_SIN_CLASIFICAR)


# --- 1290 Optimización ---

def from_optimizacion_item(item: dict[str, Any]) -> dict[str, str | None]:
    estado = (item.get("estado") or "").upper()
    tipo = (item.get("tipo") or "RECOMENDACION").upper()
    if estado in ("PENDIENTE", "PROPUESTA", "SUGERIDA"):
        return semantic_meta(SEMANTIC_RECOMENDACION, subtipo=SUB_ACCION_PROPUESTA)
    if estado in ("APROBADA",):
        return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_APROBACION)
    if estado in ("EJECUTADA", "COMPLETADA") and item.get("evidencia_json"):
        return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_EJECUCION_CONFIRMADA)
    if estado in ("FALLIDA", "ERROR"):
        return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_EVENTO_REGISTRADO)
    if estado in ("PENDIENTE_EJECUCION_HUMANA",):
        return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_EVENTO_REGISTRADO, tooltip="Estado pendiente observado — no implica resultado futuro.")
    if tipo in ("BENEFICIO_ESPERADO", "AHORRO_POTENCIAL"):
        return semantic_meta(SEMANTIC_INFERENCIA, subtipo=SUB_ESTIMACION)
    if item.get("resultado_observado"):
        return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_VALOR_VERIFICADO)
    return semantic_meta(SEMANTIC_SIN_CLASIFICAR)


# --- 1310 Planes ---

def from_plan_item(item: dict[str, Any]) -> dict[str, str | None]:
    tipo = (item.get("tipo") or "").upper()
    if tipo in ("CARACTERISTICA", "CONSUMO_INCLUIDO", "CONFIGURADO", "CONTRATADO"):
        return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_CONFIGURACION)
    if tipo in ("PROYECCION_CONSUMO", "FORECAST"):
        return semantic_meta(SEMANTIC_INFERENCIA, subtipo=SUB_PROYECCION)
    if tipo in ("RECOMENDACION_PLAN", "CAMBIO_PLAN"):
        return semantic_meta(SEMANTIC_RECOMENDACION, subtipo=SUB_ACCION_PROPUESTA)
    return semantic_meta(SEMANTIC_SIN_CLASIFICAR)


# --- 1330 Integraciones ---

def from_integracion_item(item: dict[str, Any]) -> dict[str, str | None]:
    tipo = (item.get("tipo") or item.get("kind") or "").upper()
    if tipo in ("CONFIGURADA", "PREFLIGHT", "EJECUCION", "POLITICA"):
        return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_POLITICA_APLICADA if tipo == "POLITICA" else SUB_EVENTO_REGISTRADO)
    if tipo in ("SCORE", "PRIORIZACION"):
        return semantic_meta(SEMANTIC_INFERENCIA, subtipo=SUB_RANKING_INFERIDO)
    if tipo in ("RECOMENDACION", "SYNC_SUGERIDA"):
        return semantic_meta(SEMANTIC_RECOMENDACION, subtipo=SUB_ACCION_PROPUESTA)
    if item.get("integracion_1330") or item.get("salud"):
        return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_SENAL_OBSERVADA)
    return semantic_meta(SEMANTIC_SIN_CLASIFICAR)


# --- 1340 Implementación ---

def from_implementacion_item(item: dict[str, Any]) -> dict[str, str | None]:
    tipo = (item.get("tipo") or "").upper()
    if tipo in ("HITO", "AVANCE", "READINESS_VERIFICADO"):
        return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_VALOR_VERIFICADO)
    if tipo in ("RIESGO", "READINESS", "VALOR_ESPERADO"):
        return semantic_meta(SEMANTIC_INFERENCIA, subtipo=SUB_RIESGO_ESTIMADO if tipo == "RIESGO" else SUB_ESTIMACION)
    if tipo in ("ADOPCION_SUGERIDA", "ACCION"):
        return semantic_meta(SEMANTIC_RECOMENDACION, subtipo=SUB_ACCION_PROPUESTA)
    if item.get("valor_verificado"):
        return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_VALOR_VERIFICADO)
    return semantic_meta(SEMANTIC_SIN_CLASIFICAR)


# --- 1300 Seguridad ---

def from_security_event(event: dict[str, Any]) -> dict[str, str | None]:
    et = (event.get("event_type") or event.get("tipo") or "").upper()
    if "RIESGO" in et or "ESTIMADO" in et:
        return semantic_meta(SEMANTIC_INFERENCIA, subtipo=SUB_RIESGO_ESTIMADO)
    if "RECOMENDACION" in et or "MITIGACION" in et:
        return semantic_meta(SEMANTIC_RECOMENDACION, subtipo=SUB_ACCION_PROPUESTA)
    return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_EVENTO_REGISTRADO)


# --- 1350 Gobierno ---

def from_governance_finding(finding: dict[str, Any]) -> dict[str, str | None]:
    status = (finding.get("status") or "").upper()
    if status in ("VERIFICADO", "CERRADO", "CONFIRMADO"):
        return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_VALOR_VERIFICADO)
    return semantic_meta(
        SEMANTIC_INFERENCIA,
        subtipo=SUB_HALLAZGO_AUTOMATICO,
        tooltip="Hallazgo detectado automáticamente — requiere verificación para tratarse como hecho.",
    )


def from_governance_corrective_action(action: dict[str, Any]) -> dict[str, str | None]:
    status = (action.get("status") or "").upper()
    if status == "PENDIENTE":
        return semantic_meta(SEMANTIC_RECOMENDACION, subtipo=SUB_ACCION_PROPUESTA)
    if status in ("COMPLETADA", "CERRADA", "RESUELTA"):
        return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_EJECUCION_CONFIRMADA)
    return semantic_meta(SEMANTIC_SIN_CLASIFICAR)


def from_governance_risk(risk: dict[str, Any]) -> dict[str, str | None]:
    return semantic_meta(
        SEMANTIC_INFERENCIA,
        subtipo=SUB_RIESGO_ESTIMADO,
        tooltip="Nivel de riesgo estimado — no implica incidente materializado.",
    )


def from_provider_export_decision(decision: dict[str, Any]) -> dict[str, str | None]:
    return semantic_meta(
        SEMANTIC_HECHO,
        subtipo=SUB_POLITICA_APLICADA,
        tooltip="Decisión de política registrada con trazabilidad.",
    )


# --- 1360 Continuidad ---

def from_continuidad_alerta(alerta: dict[str, Any]) -> dict[str, str | None]:
    tipo = (alerta.get("tipo") or "").upper()
    if tipo in ("RESTORE_BLOQUEADO_PRIVACIDAD",):
        return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_EVENTO_REGISTRADO)
    if tipo in ("CAUSA_ESTIMADA", "RTO_RPO_EVAL"):
        return semantic_meta(SEMANTIC_INFERENCIA, subtipo=SUB_CAUSA_ESTIMADA)
    if tipo in ("RECOMENDACION_RECUPERACION", "ACCION_SUGERIDA"):
        return semantic_meta(SEMANTIC_RECOMENDACION, subtipo=SUB_ACCION_PROPUESTA)
    if tipo in ("RECUPERACION_EJECUTADA", "BACKUP", "INCIDENTE", "EVENTO"):
        return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_EVENTO_REGISTRADO)
    return semantic_meta(SEMANTIC_INFERENCIA, subtipo=SUB_ALERTA)


def from_continuidad_backup(backup: dict[str, Any]) -> dict[str, str | None]:
    return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_SENAL_OBSERVADA)


def from_continuidad_incidente(incidente: dict[str, Any]) -> dict[str, str | None]:
    if incidente.get("causa_raiz_tipo") in ("HIPOTESIS", "ESTIMADA", None) and incidente.get("causa"):
        return semantic_meta(SEMANTIC_INFERENCIA, subtipo=SUB_CAUSA_ESTIMADA)
    return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_EVENTO_REGISTRADO)


# --- 1370 Identidad ---

def from_identity_event(event: dict[str, Any]) -> dict[str, str | None]:
    et = (event.get("event_type") or event.get("tipo") or "").upper()
    if "RIESGO" in et:
        return semantic_meta(SEMANTIC_INFERENCIA, subtipo=SUB_RIESGO_ESTIMADO)
    if "RECOMENDACION" in et or "MITIGACION" in et:
        return semantic_meta(SEMANTIC_RECOMENDACION, subtipo=SUB_ACCION_PROPUESTA)
    return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_EVENTO_REGISTRADO)


# --- 1380 SCIM ---

def from_scim_item(item: dict[str, Any]) -> dict[str, str | None]:
    tipo = (item.get("tipo") or item.get("operation") or "").upper()
    if tipo in ("CONFLICTO", "CONFLICT"):
        return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_CONFLICTO_DETECTADO)
    if tipo in ("RESOLUCION_SUGERIDA", "RECOMENDACION"):
        return semantic_meta(SEMANTIC_RECOMENDACION, subtipo=SUB_ACCION_PROPUESTA)
    if tipo:
        return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_EVENTO_REGISTRADO)
    return semantic_meta(SEMANTIC_SIN_CLASIFICAR)


# --- Enriquecimiento de payloads ---

def with_contract(payload: dict[str, Any]) -> dict[str, Any]:
    payload["contrato_semantico"] = contract_header()
    return payload


def enrich_list_semantic(
    items: list[dict[str, Any]] | None,
    classifier: Callable[[dict[str, Any]], dict[str, str | None]],
) -> list[dict[str, Any]]:
    if not items:
        return []
    out: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("tipo_semantico"):
            out.append(item)
        else:
            out.append(attach_semantic(item, classifier(item)))
    return out


def enrich_aprendizaje_payload(payload: dict[str, Any]) -> dict[str, Any]:
    with_contract(payload)
    for key in ("recalibraciones", "desviaciones", "lecciones", "items"):
        if isinstance(payload.get(key), list):
            payload[key] = enrich_list_semantic(payload[key], from_aprendizaje_item)
    return payload


def enrich_llm_payload(payload: dict[str, Any]) -> dict[str, Any]:
    with_contract(payload)
    if isinstance(payload.get("proveedores"), list):
        payload["proveedores"] = enrich_list_semantic(
            payload["proveedores"],
            lambda p: from_llm_metric_kind("PROVEEDOR") if p.get("is_enabled") is not None else from_llm_output(),
        )
    if payload.get("text") is not None:
        payload.update(from_llm_output())
    if isinstance(payload.get("items"), list):
        payload["items"] = enrich_list_semantic(payload["items"], from_llm_inference_log)
    return payload


def enrich_comercial_payload(payload: dict[str, Any]) -> dict[str, Any]:
    with_contract(payload)
    for key in ("propuestas", "items", "pipeline"):
        if isinstance(payload.get(key), list):
            payload[key] = enrich_list_semantic(
                payload[key],
                lambda i: from_valor_comercial_tipo(i.get("tipo_valor") or i.get("estado")),
            )
    for field in ("valor_verificado", "valor_potencial", "valor_estimado"):
        if field in payload:
            payload.setdefault("campos_semanticos", {})[field] = valor_field_semantics(field, payload.get(field))
    return payload


def enrich_optimizacion_payload(payload: dict[str, Any]) -> dict[str, Any]:
    with_contract(payload)
    for key in ("recomendaciones", "items", "criticas"):
        if isinstance(payload.get(key), list):
            payload[key] = enrich_list_semantic(payload[key], from_optimizacion_item)
    return payload


def enrich_planes_payload(payload: dict[str, Any]) -> dict[str, Any]:
    with_contract(payload)
    for key in ("planes", "caracteristicas", "recomendaciones"):
        if isinstance(payload.get(key), list):
            payload[key] = enrich_list_semantic(payload[key], from_plan_item)
    if payload.get("proyeccion_consumo") is not None:
        payload["proyeccion_semantica"] = semantic_meta(SEMANTIC_INFERENCIA, subtipo=SUB_PROYECCION)
    return payload


def enrich_tco_payload(payload: dict[str, Any]) -> dict[str, Any]:
    with_contract(payload)
    for key in ("items", "desviaciones", "alianzas"):
        if isinstance(payload.get(key), list):
            payload[key] = enrich_list_semantic(payload[key], from_tco_item)
    return payload


def enrich_integracion_payload(payload: dict[str, Any]) -> dict[str, Any]:
    with_contract(payload)
    for key in ("conectores", "items", "preflight"):
        if isinstance(payload.get(key), list):
            payload[key] = enrich_list_semantic(payload[key], from_integracion_item)
    return payload


def enrich_implementacion_payload(payload: dict[str, Any]) -> dict[str, Any]:
    with_contract(payload)
    for key in ("hitos", "bloqueadores", "acciones"):
        if isinstance(payload.get(key), list):
            payload[key] = enrich_list_semantic(payload[key], from_implementacion_item)
    return payload


def enrich_security_payload(payload: dict[str, Any]) -> dict[str, Any]:
    with_contract(payload)
    if isinstance(payload.get("events"), list):
        payload["events"] = enrich_list_semantic(payload["events"], from_security_event)
    if isinstance(payload.get("eventos"), list):
        payload["eventos"] = enrich_list_semantic(payload["eventos"], from_security_event)
    return payload


def enrich_governance_payload(payload: dict[str, Any]) -> dict[str, Any]:
    with_contract(payload)
    if isinstance(payload.get("hallazgos"), list):
        payload["hallazgos"] = enrich_list_semantic(payload["hallazgos"], from_governance_finding)
    if isinstance(payload.get("findings"), list):
        payload["findings"] = enrich_list_semantic(payload["findings"], from_governance_finding)
    if isinstance(payload.get("riesgos"), list):
        payload["riesgos"] = enrich_list_semantic(payload["riesgos"], from_governance_risk)
    if isinstance(payload.get("risks"), list):
        payload["risks"] = enrich_list_semantic(payload["risks"], from_governance_risk)
    if payload.get("result") and payload.get("reasons") is not None:
        payload.update(from_provider_export_decision(payload))
    if isinstance(payload.get("acciones"), list):
        payload["acciones"] = enrich_list_semantic(payload["acciones"], from_governance_corrective_action)
    if payload.get("riesgo_alto") is not None:
        payload["riesgo_alto_semantico"] = semantic_meta(SEMANTIC_INFERENCIA, subtipo=SUB_RIESGO_ESTIMADO)
    return payload


def enrich_continuidad_payload(payload: dict[str, Any]) -> dict[str, Any]:
    with_contract(payload)
    if isinstance(payload.get("alertas"), list):
        payload["alertas"] = enrich_list_semantic(payload["alertas"], from_continuidad_alerta)
    if isinstance(payload.get("backups_recientes"), list):
        payload["backups_recientes"] = enrich_list_semantic(payload["backups_recientes"], from_continuidad_backup)
    if isinstance(payload.get("servicios_criticos"), list):
        payload["servicios_criticos"] = enrich_list_semantic(
            payload["servicios_criticos"],
            lambda s: semantic_meta(SEMANTIC_HECHO, subtipo=SUB_SENAL_OBSERVADA),
        )
    if isinstance(payload.get("servicios_degradados"), list):
        payload["servicios_degradados"] = enrich_list_semantic(
            payload["servicios_degradados"],
            lambda s: semantic_meta(SEMANTIC_INFERENCIA, subtipo=SUB_ALERTA),
        )
    return payload


def enrich_identity_payload(payload: dict[str, Any]) -> dict[str, Any]:
    with_contract(payload)
    for key in ("auditoria", "eventos", "login_audit"):
        if isinstance(payload.get(key), list):
            payload[key] = enrich_list_semantic(payload[key], from_identity_event)
    return payload


def enrich_scim_payload(payload: dict[str, Any]) -> dict[str, Any]:
    with_contract(payload)
    for key in ("conflictos", "operaciones", "items"):
        if isinstance(payload.get(key), list):
            payload[key] = enrich_list_semantic(payload[key], from_scim_item)
    return payload


def enrich_model_list(items: list[Any], classifier: Callable[[dict[str, Any]], dict]) -> list[dict[str, Any]]:
    """Serializa modelos Pydantic/ORM y aplica clasificación."""
    serialized: list[dict[str, Any]] = []
    for item in items:
        if hasattr(item, "model_dump"):
            d = item.model_dump()
        elif hasattr(item, "__dict__"):
            d = {k: v for k, v in item.__dict__.items() if not k.startswith("_")}
        elif isinstance(item, dict):
            d = dict(item)
        else:
            continue
        serialized.append(attach_semantic(d, classifier(d)))
    return serialized
