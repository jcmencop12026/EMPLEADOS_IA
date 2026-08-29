"""Contrato semántico transversal — HECHO / INFERENCIA / RECOMENDACIÓN (P1-ID-02)."""

from __future__ import annotations

from typing import Any

SEMANTIC_HECHO = "HECHO"
SEMANTIC_INFERENCIA = "INFERENCIA"
SEMANTIC_RECOMENDACION = "RECOMENDACION"
SEMANTIC_SIN_CLASIFICAR = "SIN_CLASIFICAR"

SEMANTIC_TYPES = frozenset({
    SEMANTIC_HECHO,
    SEMANTIC_INFERENCIA,
    SEMANTIC_RECOMENDACION,
    SEMANTIC_SIN_CLASIFICAR,
})

CONTRACT_VERSION = "1.0"

# Subtipos opcionales (no exhaustivos)
SUB_CAUSA_DEMOSTRADA = "CAUSA_DEMOSTRADA"
SUB_CAUSA_PROBABLE = "CAUSA_PROBABLE"
SUB_HIPOTESIS = "HIPOTESIS"
SUB_CORRELACION = "CORRELACION"
SUB_PREDICCION = "PREDICCION"
SUB_ESTIMACION = "ESTIMACION"
SUB_VALOR_VERIFICADO = "RESULTADO_VERIFICADO"
SUB_VALOR_POTENCIAL = "VALOR_POTENCIAL"
SUB_ACCION_PROPUESTA = "ACCION_PROPUESTA"
SUB_SENAL_OBSERVADA = "SENAL_OBSERVADA"
SUB_DATO_EXTERNO = "DATO_EXTERNO"
SUB_ALERTA = "ALERTA"

_TOOLTIPS = {
    SEMANTIC_HECHO: "Dato u observación con evidencia o fuente trazable.",
    SEMANTIC_INFERENCIA: "Interpretación, correlación, hipótesis o estimación — no es un hecho verificado.",
    SEMANTIC_RECOMENDACION: "Acción sugerida para aprobación o ejecución — no es un resultado realizado.",
    SEMANTIC_SIN_CLASIFICAR: "Tipo semántico no determinado con seguridad.",
}


def semantic_meta(
    tipo_semantico: str,
    *,
    subtipo: str | None = None,
    etiqueta_visible: str | None = None,
    tooltip: str | None = None,
) -> dict[str, str | None]:
    tipo = tipo_semantico if tipo_semantico in SEMANTIC_TYPES else SEMANTIC_SIN_CLASIFICAR
    return {
        "tipo_semantico": tipo,
        "subtipo_semantico": subtipo,
        "etiqueta_visible": etiqueta_visible or tipo.replace("_", " "),
        "tooltip_semantico": tooltip or _TOOLTIPS.get(tipo),
    }


def from_diagnostic_cause(certeza_codigo: str | None) -> dict[str, str | None]:
    code = (certeza_codigo or "").upper()
    if code == "CONFIRMADA":
        return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_CAUSA_DEMOSTRADA)
    if code == "PROBABLE":
        return semantic_meta(SEMANTIC_INFERENCIA, subtipo=SUB_CAUSA_PROBABLE)
    if code == "HIPOTESIS":
        return semantic_meta(SEMANTIC_INFERENCIA, subtipo=SUB_HIPOTESIS)
    if code == "CORRELACION":
        return semantic_meta(
            SEMANTIC_INFERENCIA,
            subtipo=SUB_CORRELACION,
            tooltip="Correlación observada; no implica causalidad demostrada.",
        )
    return semantic_meta(SEMANTIC_SIN_CLASIFICAR)


def from_tipo_contenido(tipo_contenido: str | None) -> dict[str, str | None]:
    t = (tipo_contenido or "").upper()
    if t == "HECHO":
        return semantic_meta(SEMANTIC_HECHO)
    if t in ("INTERPRETACION", "INFERENCIA"):
        return semantic_meta(SEMANTIC_INFERENCIA)
    if t == "RECOMENDACION":
        return semantic_meta(SEMANTIC_RECOMENDACION, subtipo=SUB_ACCION_PROPUESTA)
    return semantic_meta(SEMANTIC_SIN_CLASIFICAR)


def from_tipo_entrada_explicacion(
    tipo_entrada: str | None,
    *,
    certeza_codigo: str | None = None,
    tipo_contenido: str | None = None,
) -> dict[str, str | None]:
    entrada = (tipo_entrada or "").upper()
    if entrada == "RECOMENDACION":
        return semantic_meta(SEMANTIC_RECOMENDACION, subtipo=SUB_ACCION_PROPUESTA)
    if entrada == "CORRELACION":
        return from_diagnostic_cause("CORRELACION")
    if entrada == "CAUSA" and certeza_codigo:
        return from_diagnostic_cause(certeza_codigo)
    if tipo_contenido:
        return from_tipo_contenido(tipo_contenido)
    if entrada == "SITUACION":
        return from_tipo_contenido(tipo_contenido or "HECHO")
    return semantic_meta(SEMANTIC_SIN_CLASIFICAR)


def from_atencion_item(tipo: str | None, origen: str | None = None) -> dict[str, str | None]:
    t = (tipo or "").lower()
    if t in ("aprobacion", "alerta", "senal_ingesta"):
        return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_ALERTA)
    if t in ("senal_externa_pendiente", "riesgo_externo"):
        return semantic_meta(SEMANTIC_INFERENCIA, subtipo=SUB_DATO_EXTERNO)
    if t in ("diagnostico_prioritario",):
        return semantic_meta(SEMANTIC_INFERENCIA, subtipo=SUB_PREDICCION)
    if t in ("impacto_pendiente_validacion",):
        return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_SENAL_OBSERVADA)
    if origen == "notificaciones":
        return semantic_meta(SEMANTIC_RECOMENDACION, subtipo=SUB_ACCION_PROPUESTA)
    return semantic_meta(SEMANTIC_SIN_CLASIFICAR)


def from_opportunity_estado(estado: str | None) -> dict[str, str | None]:
    e = (estado or "").upper()
    if e in ("MATERIALIZADA", "CERRADA"):
        return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_VALOR_VERIFICADO)
    if e in ("PENDIENTE_APROBACION", "EN_SEGUIMIENTO", "EN_EJECUCION"):
        return semantic_meta(SEMANTIC_INFERENCIA, subtipo=SUB_VALOR_POTENCIAL)
    return semantic_meta(SEMANTIC_SIN_CLASIFICAR)


def from_signal_item(*, modo_ingesta: str | None = None, estado_procesamiento: str | None = None) -> dict[str, str | None]:
    if estado_procesamiento in ("RECHAZADA", "DUPLICADA"):
        return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_SENAL_OBSERVADA)
    return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_SENAL_OBSERVADA)


def from_external_signal(*, classification: str | None = None, validated: bool = False) -> dict[str, str | None]:
    if validated:
        return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_DATO_EXTERNO)
    cls = (classification or "").upper()
    if cls in ("TENDENCIA", "OPORTUNIDAD", "RIESGO"):
        return semantic_meta(SEMANTIC_INFERENCIA, subtipo=SUB_PREDICCION)
    return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_DATO_EXTERNO)


def valor_field_semantics(field: str, value: Any) -> dict[str, str | None]:
    if value is None:
        return semantic_meta(SEMANTIC_SIN_CLASIFICAR)
    f = field.lower()
    if f in ("valor_esperado", "expected_value", "valor_potencial"):
        return semantic_meta(SEMANTIC_INFERENCIA, subtipo=SUB_ESTIMACION)
    if f in ("valor_materializado", "materialized_value", "valor_atribuible"):
        return semantic_meta(SEMANTIC_HECHO, subtipo=SUB_VALOR_VERIFICADO)
    if f in ("retorno_porcentaje", "beneficio_neto"):
        return semantic_meta(SEMANTIC_INFERENCIA, subtipo=SUB_ESTIMACION)
    return semantic_meta(SEMANTIC_SIN_CLASIFICAR)


def from_llm_output() -> dict[str, str | None]:
    return semantic_meta(
        SEMANTIC_INFERENCIA,
        subtipo=SUB_PREDICCION,
        tooltip="Salida de proveedor IA — interpretación, no hecho verificado.",
    )


def attach_semantic(item: dict[str, Any], meta: dict[str, str | None]) -> dict[str, Any]:
    merged = {**item, **meta}
    return merged


def enrich_explicacion_elemento(el: dict[str, Any]) -> dict[str, Any]:
    if el.get("tipo_semantico") in SEMANTIC_TYPES:
        return el
    meta = from_tipo_entrada_explicacion(
        el.get("tipo_entrada"),
        certeza_codigo=el.get("certeza_codigo"),
        tipo_contenido=el.get("tipo_contenido"),
    )
    return attach_semantic(el, meta)


def contract_header() -> dict[str, Any]:
    return {
        "version": CONTRACT_VERSION,
        "tipos": sorted(SEMANTIC_TYPES),
        "reglas": [
            "HECHO requiere evidencia o fuente trazable",
            "INFERENCIA no equivale a hecho",
            "RECOMENDACIÓN no equivale a resultado realizado",
            "Correlación no implica causalidad",
            "Estimado/potencial no equivale a verificado",
        ],
    }


def enrich_control_center_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Enriquece respuesta del Centro de Control sin alterar permisos ni datos de negocio."""
    payload["contrato_semantico"] = contract_header()

    exp = payload.get("explicacion")
    if isinstance(exp, dict) and isinstance(exp.get("elementos"), list):
        exp["elementos"] = [enrich_explicacion_elemento(el) for el in exp["elementos"]]

    if isinstance(payload.get("atencion_requerida"), list):
        payload["atencion_requerida"] = [
            attach_semantic(item, from_atencion_item(item.get("tipo"), item.get("origen")))
            for item in payload["atencion_requerida"]
        ]

    opp = payload.get("oportunidades")
    if isinstance(opp, dict) and isinstance(opp.get("criticas"), list):
        opp["criticas"] = [
            attach_semantic(c, from_opportunity_estado(c.get("estado")))
            for c in opp["criticas"]
        ]
        if opp.get("resumen"):
            opp["campos_semanticos"] = {
                "valor_potencial_total": valor_field_semantics(
                    "valor_potencial", opp["resumen"].get("valor_potencial_total")
                ),
                "valor_materializado_total": valor_field_semantics(
                    "valor_materializado", opp["resumen"].get("valor_materializado_total")
                ),
            }

    sen = payload.get("senales")
    if isinstance(sen, dict) and isinstance(sen.get("recientes"), list):
        sen["recientes"] = [
            attach_semantic(
                s,
                from_signal_item(
                    modo_ingesta=s.get("modo_ingesta"),
                    estado_procesamiento=s.get("estado_procesamiento"),
                ),
            )
            for s in sen["recientes"]
        ]

    ie = payload.get("inteligencia_externa")
    if isinstance(ie, dict) and isinstance(ie.get("recientes"), list):
        ie["recientes"] = [
            attach_semantic(
                s,
                from_external_signal(
                    classification=s.get("clasificacion"),
                    validated=s.get("validada", False),
                ),
            )
            for s in ie["recientes"]
        ]

    vr = payload.get("valor_retorno")
    if isinstance(vr, dict) and vr.get("disponible"):
        vr["campos_semanticos"] = {
            k: valor_field_semantics(k, vr.get(k))
            for k in ("valor_esperado", "valor_materializado", "valor_atribuible", "beneficio_neto", "retorno_porcentaje")
            if k in vr
        }

    llm = payload.get("llm")
    if isinstance(llm, dict) and isinstance(llm.get("proveedores"), list):
        llm["proveedores"] = [
            attach_semantic(p, from_llm_output()) for p in llm["proveedores"]
        ]

    return payload
