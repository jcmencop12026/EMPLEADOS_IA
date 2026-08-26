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
    conocimiento = diagnostico.get("conocimiento", {})
    hipotesis = diagnostico.get("hipotesis", [])
    recomendacion = diagnostico.get("recomendacion_consolidada", {})
    priorizacion = diagnostico.get("priorizacion", {})

    if any(k in text for k in ("por qué recomiendas", "porque recomiendas", "por qué esto", "porque esto")):
        return {
            "respuesta": recomendacion.get("por_que_recomendamos") or recomendacion.get("por_que_podria", "Sin recomendación consolidada."),
            "evidencia": recomendacion.get("que_demostrado", []),
            "incertidumbre": "BAJA" if recomendacion.get("calidad_datos") == "SUFICIENTE" else "MEDIA",
            "accion_sugerida": recomendacion.get("recomendacion"),
            "clasificacion": "RECOMENDACION",
        }

    if any(k in text for k in ("qué evidencia", "que evidencia", "evidencia tienes")):
        ev = []
        for h in hipotesis[:3]:
            ev.extend(h.get("evidencia_a_favor", []))
        return {
            "respuesta": "; ".join(ev[:5]) if ev else "No hay evidencia trazable para esta pregunta.",
            "evidencia": ev,
            "incertidumbre": "BAJA" if ev else "ALTA",
            "clasificacion": "HECHO" if ev else "INFORMACION_INSUFICIENTE",
        }

    if any(k in text for k in ("qué falta", "que falta", "información falta", "informacion falta")):
        missing = diagnostico.get("suficiencia_datos", {}).get("informacion_faltante_critica", [])
        return {
            "respuesta": "; ".join(m.get("que_falta", str(m)) for m in missing) if missing else "No se identificó información crítica faltante.",
            "evidencia": missing,
            "incertidumbre": "ALTA" if missing else "BAJA",
            "clasificacion": "INFORMACION_INSUFICIENTE" if missing else "HECHO",
        }

    if any(k in text for k in ("experiencias similares", "casos similares")):
        casos = diagnostico.get("experiencia", {}).get("casos_similares", [])
        return {
            "respuesta": f"Se encontraron {len(casos)} casos similares en experiencia de la organización.",
            "evidencia": casos,
            "incertidumbre": "MEDIA",
            "clasificacion": "HECHO",
        }

    if any(k in text for k in ("cuánto podría recuperar", "cuanto podria recuperar", "cuánto vale", "cuanto vale")):
        esc = diagnostico.get("escenarios", {}).get("escenarios", {}).get("PROBABLE", {})
        val = esc.get("valor_recuperable_estimado")
        return {
            "respuesta": f"Escenario probable: valor recuperable estimado ${val:,.0f} (PROYECTADO)." if isinstance(val, (int, float)) else "No cuantificable con datos actuales.",
            "evidencia": [esc],
            "incertidumbre": "MEDIA",
            "clasificacion": "PROYECTADO",
            "advertencia": "Estimación — no es resultado real.",
        }

    if any(k in text for k in ("qué debería hacer primero", "que deberia hacer primero", "hacer primero")):
        top = (priorizacion.get("ranking") or [{}])[0]
        return {
            "respuesta": top.get("por_que_primero") or top.get("accion", "Sin priorización calculada."),
            "evidencia": [top],
            "incertidumbre": "BAJA" if top else "ALTA",
            "accion_sugerida": top.get("accion"),
            "clasificacion": "RECOMENDACION",
        }

    if any(k in text for k in ("por qué aumentó", "porque aumento", "cartera")):
        primary = diagnostico.get("hipotesis_principal")
        if primary:
            return {
                "respuesta": f"Hipótesis principal ({primary.get('estado')}): {primary.get('titulo')}. {'; '.join(primary.get('evidencia_a_favor', [])[:2])}",
                "evidencia": primary.get("evidencia_a_favor", []),
                "incertidumbre": "BAJA" if primary.get("estado") == "CONFIRMADA" else "MEDIA",
                "clasificacion": "HIPOTESIS",
            }
        return _respuesta_cartera(indicadores, hallazgos)

    if any(k in text for k in ("depende de nosotros", "nuestro proceso", "interno")):
        internal = [h for h in hipotesis if h.get("dominio") in ("radicacion", "facturacion", "proceso", "soportes")]
        external = [h for h in hipotesis if h.get("dominio") in ("pagador", "glosas", "devoluciones")]
        return {
            "respuesta": f"Factores internos probables: {', '.join(h['titulo'] for h in internal[:2]) or 'ninguno dominante'}. Externos: {', '.join(h['titulo'] for h in external[:2]) or 'ninguno dominante'}.",
            "evidencia": [{"interno": internal[:2], "externo": external[:2]}],
            "incertidumbre": "MEDIA",
            "clasificacion": "INFERENCIA",
        }

    if any(k in text for k in ("pactado", "contrato", "incumple", "cumplimiento contractual", "entidad")):
        return _respuesta_contractual(indicadores, hallazgos, conocimiento, text)

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


def _respuesta_contractual(
    indicadores: dict,
    hallazgos: list,
    conocimiento: dict,
    text: str,
) -> dict[str, Any]:
    if not conocimiento.get("utilizado"):
        return {
            "respuesta": "Información insuficiente para determinar el cumplimiento contractual.",
            "evidencia": [],
            "incertidumbre": "ALTA",
            "accion_sugerida": "Cargar y autorizar documentos contractuales en el Centro de Conocimiento.",
            "clasificacion": "INFORMACION_INSUFICIENTE",
        }

    if conocimiento.get("requiere_validacion"):
        return {
            "respuesta": (
                "Existen documentos autorizados con plazos distintos. "
                "Se requiere validación humana antes de concluir cumplimiento contractual."
            ),
            "evidencia": conocimiento.get("fuentes", []),
            "incertidumbre": "ALTA",
            "accion_sugerida": "Validar vigencia y jerarquía documental con el equipo contractual.",
            "clasificacion": "INFORMACION_INSUFICIENTE",
        }

    breach = next(
        (
            h
            for h in hallazgos
            if "incumplimiento contractual" in (h.get("titulo") or "").lower()
            or h.get("indicador") == "incumplimiento_plazo_radicacion"
        ),
        None,
    )
    if breach:
        fuentes = [
            f.get("titulo")
            for f in (breach.get("fuentes_consultadas") or breach.get("fuentes") or [])
            if isinstance(f, dict) and f.get("titulo")
        ]
        return {
            "respuesta": breach.get("descripcion", breach.get("titulo", "")),
            "evidencia": breach.get("evidencia", {}),
            "fuentes": fuentes,
            "incertidumbre": "BAJA" if breach.get("confianza") == "ALTA" else "MEDIA",
            "accion_sugerida": "Revisar proceso de radicación y tiempos operativos.",
            "clasificacion": breach.get("tipo", "HECHO"),
        }

    if "radic" in text:
        rad = indicadores.get("radicacion", {})
        if rad.get("disponible"):
            return {
                "respuesta": (
                    "Con los datos y documentos autorizados disponibles no se detectó incumplimiento contractual explícito, "
                    "pero sí demoras operativas en radicación."
                ),
                "evidencia": [{"radicacion": rad}],
                "fuentes": [f.get("titulo") for f in conocimiento.get("fuentes", []) if f.get("titulo")],
                "incertidumbre": "MEDIA",
                "accion_sugerida": None,
                "clasificacion": "INFERENCIA",
            }

    return {
        "respuesta": "Información insuficiente para determinar el cumplimiento contractual.",
        "evidencia": [],
        "incertidumbre": "ALTA",
        "accion_sugerida": None,
        "clasificacion": "INFORMACION_INSUFICIENTE",
    }
