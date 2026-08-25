"""Servicio de preguntas naturales sobre resultados calculados."""

from __future__ import annotations

from typing import Any

from app.services.salud_indicators import INSUFICIENTE


def responder_pregunta(pregunta: str, diagnostico: dict[str, Any]) -> dict[str, Any]:
    """Responde preguntas usando indicadores ya calculados — sin inventar datos."""
    text = pregunta.lower()
    indicadores = diagnostico.get("indicadores", {})
    trazabilidad = diagnostico.get("trazabilidad", {})
    hallazgos = diagnostico.get("hallazgos", [])

    if "caja" in text or "recaudo" in text or "menos caja" in text:
        return _respuesta_caja(indicadores, trazabilidad, hallazgos)

    if "radic" in text:
        return _respuesta_radicacion(indicadores, hallazgos)

    if "glosa" in text:
        return _respuesta_glosas(indicadores, hallazgos)

    if "cartera" in text or "mora" in text:
        return _respuesta_cartera(indicadores, hallazgos)

    # Respuesta genérica basada en hallazgos
    if not hallazgos:
        return {
            "respuesta": "No hay hallazgos calculados para responder esta pregunta.",
            "evidencia": [],
            "incertidumbre": "ALTA",
            "accion_sugerida": None,
        }

    top = hallazgos[0]
    return {
        "respuesta": f"Según el análisis: {top.get('descripcion', top.get('titulo', ''))}",
        "evidencia": [top.get("evidencia", {})],
        "incertidumbre": "BAJA" if top.get("confianza") == "ALTA" else "MEDIA",
        "accion_sugerida": None,
    }


def _respuesta_caja(indicadores: dict, trazabilidad: dict, hallazgos: list) -> dict[str, Any]:
    fact = indicadores.get("facturacion", {})
    cartera = indicadores.get("cartera", {})
    glosas = indicadores.get("glosas", {})

    if not fact.get("disponible"):
        return _insuficiente("facturación")

    partes = []
    evidencia = []

    facturado = fact.get("valor_facturado")
    partes.append(f"Facturó ${facturado:,.0f}")

    if glosas.get("disponible"):
        glosado = glosas.get("valor_glosado", 0)
        partes.append(f"tiene ${glosado:,.0f} en glosas")
        evidencia.append({"indicador": "valor_glosado", "valor": glosado})

    if cartera.get("disponible"):
        saldo = cartera.get("saldo_total", 0)
        recaudo = cartera.get("recaudo", INSUFICIENTE)
        partes.append(f"cartera por cobrar de ${saldo:,.0f}")
        if recaudo != INSUFICIENTE:
            partes.append(f"recaudo de ${recaudo:,.0f}")
        evidencia.append({"indicador": "saldo_cartera", "valor": saldo})

    pagado = trazabilidad.get("pagado", INSUFICIENTE)
    if pagado != INSUFICIENTE:
        partes.append(f"pagos recibidos de ${pagado:,.0f}")
        evidencia.append({"indicador": "pagado", "valor": pagado})

    respuesta = (
        "Aunque facturó más, la caja puede verse afectada porque: "
        + "; ".join(partes[1:]) + "."
        if len(partes) > 1
        else f"Facturó ${facturado:,.0f} pero no hay datos suficientes de cartera, glosas o pagos para explicar la variación de caja."
    )

    incertidumbre = "BAJA" if cartera.get("disponible") and glosas.get("disponible") else "MEDIA"

    accion = None
    for h in hallazgos:
        if h.get("categoria") in ("cartera", "glosas"):
            accion = f"Revisar: {h.get('titulo')}"
            break

    return {"respuesta": respuesta, "evidencia": evidencia, "incertidumbre": incertidumbre, "accion_sugerida": accion}


def _respuesta_radicacion(indicadores: dict, hallazgos: list) -> dict[str, Any]:
    rad = indicadores.get("radicacion", {})
    if not rad.get("disponible"):
        return _insuficiente("radicación")

    tiempo = rad.get("tiempo_promedio_factura_radicacion_dias", INSUFICIENTE)
    pct = rad.get("porcentaje_radicado", INSUFICIENTE)
    no_rad = rad.get("facturas_no_radicadas", 0)

    return {
        "respuesta": (
            f"El {pct}% del valor facturado está radicado. "
            f"Tiempo promedio factura→radicación: {tiempo} días. "
            f"Facturas sin radicar: {no_rad}."
        ),
        "evidencia": [{"porcentaje_radicado": pct, "tiempo_dias": tiempo, "no_radicadas": no_rad}],
        "incertidumbre": "BAJA",
        "accion_sugerida": next((h["titulo"] for h in hallazgos if h.get("categoria") == "radicacion"), None),
    }


def _respuesta_glosas(indicadores: dict, hallazgos: list) -> dict[str, Any]:
    glosas = indicadores.get("glosas", {})
    if not glosas.get("disponible"):
        return _insuficiente("glosas")

    return {
        "respuesta": (
            f"Valor glosado: ${glosas.get('valor_glosado', 0):,.0f}. "
            f"Porcentaje de glosa: {glosas.get('porcentaje_glosa', INSUFICIENTE)}%."
        ),
        "evidencia": [{"por_causal": glosas.get("por_causal", {})}],
        "incertidumbre": "BAJA",
        "accion_sugerida": next((h["titulo"] for h in hallazgos if h.get("categoria") == "glosas"), None),
    }


def _respuesta_cartera(indicadores: dict, hallazgos: list) -> dict[str, Any]:
    cartera = indicadores.get("cartera", {})
    if not cartera.get("disponible"):
        return _insuficiente("cartera")

    aging = cartera.get("aging", {})
    return {
        "respuesta": (
            f"Saldo total de cartera: ${cartera.get('saldo_total', 0):,.0f}. "
            f"Aging: 0-30 días ${aging.get('0-30', 0):,.0f}, "
            f"91+ días ${aging.get('91+', 0):,.0f}."
        ),
        "evidencia": [{"aging": aging}],
        "incertidumbre": "BAJA",
        "accion_sugerida": next((h["titulo"] for h in hallazgos if h.get("categoria") == "cartera"), None),
    }


def _insuficiente(dominio: str) -> dict[str, Any]:
    return {
        "respuesta": f"Información insuficiente para responder sobre {dominio}.",
        "evidencia": [],
        "incertidumbre": "ALTA",
        "accion_sugerida": f"Cargar datos de {dominio} para habilitar este análisis.",
    }
