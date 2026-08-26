"""Motor de hipótesis multidimensionales — MOTOR-ANALITICO-1000."""

from __future__ import annotations

from typing import Any

from app.services.salud_indicators import INSUFICIENTE

HYPOTHESIS_CATALOG: list[dict[str, str]] = [
    {"id": "H1", "titulo": "Facturación tardía", "dominio": "facturacion"},
    {"id": "H2", "titulo": "Radicación tardía", "dominio": "radicacion"},
    {"id": "H3", "titulo": "Devoluciones del pagador", "dominio": "devoluciones"},
    {"id": "H4", "titulo": "Glosas elevadas", "dominio": "glosas"},
    {"id": "H5", "titulo": "Soportes deficientes", "dominio": "soportes"},
    {"id": "H6", "titulo": "Condiciones contractuales", "dominio": "contratos"},
    {"id": "H7", "titulo": "Comportamiento tardío del pagador", "dominio": "pagador"},
    {"id": "H8", "titulo": "Concentración en un pagador", "dominio": "concentracion"},
    {"id": "H9", "titulo": "Proceso interno ineficiente", "dominio": "proceso"},
    {"id": "H10", "titulo": "Combinación de factores", "dominio": "combinado"},
]

STATUS_ORDER = ["CONFIRMADA", "PROBABLE", "POSIBLE", "NO DEMOSTRADA", "REFUTADA"]


def generate_hypotheses(
    indicators: dict[str, Any],
    datasets: dict[str, list[dict]],
    data_sufficiency: dict[str, Any],
    hallazgos: list[dict[str, Any]],
    knowledge_ctx: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Genera hipótesis alternativas con evidencia a favor/en contra."""
    if data_sufficiency.get("clasificacion") == "INSUFICIENTE":
        return _insufficient_hypotheses(data_sufficiency)

    scores = _score_all_hypotheses(indicators, datasets, hallazgos)
    if knowledge_ctx:
        _apply_knowledge_conflicts(scores, knowledge_ctx)
    hypotheses: list[dict[str, Any]] = []

    for item in HYPOTHESIS_CATALOG:
        hid = item["id"]
        sc = scores.get(hid, {"a_favor": [], "en_contra": [], "faltante": [], "score": 0.0})
        estado = _classify_status(sc["score"], sc["a_favor"], sc["en_contra"], data_sufficiency, knowledge_ctx)
        impacto = _estimate_impact(hid, indicators, hallazgos)
        confianza = _confidence_label(sc["score"])
        if knowledge_ctx and (knowledge_ctx.get("conflictos") or knowledge_ctx.get("requiere_validacion")):
            confianza = _downgrade_confidence(confianza)
        hypotheses.append({
            "id": hid,
            "titulo": item["titulo"],
            "dominio": item["dominio"],
            "tipo": "HIPOTESIS",
            "estado": estado,
            "confianza": confianza,
            "evidencia_a_favor": sc["a_favor"],
            "evidencia_en_contra": sc["en_contra"],
            "informacion_faltante": sc["faltante"],
            "impacto_potencial": impacto,
            "puntaje": round(sc["score"], 3),
            "relacion_causal": "hipotesis_causal" if estado in ("CONFIRMADA", "PROBABLE") else "asociacion",
        })

    hypotheses.sort(key=lambda h: (STATUS_ORDER.index(h["estado"]) if h["estado"] in STATUS_ORDER else 99, -h["puntaje"]))
    return hypotheses


def primary_hypothesis(hypotheses: list[dict[str, Any]]) -> dict[str, Any] | None:
    viable = [h for h in hypotheses if h["estado"] not in ("REFUTADA", "NO DEMOSTRADA")]
    return viable[0] if viable else (hypotheses[0] if hypotheses else None)


def _insufficient_hypotheses(sufficiency: dict[str, Any]) -> list[dict[str, Any]]:
    missing = sufficiency.get("informacion_faltante_critica", [])
    return [{
        "id": "H0",
        "titulo": "Información insuficiente para establecer causa",
        "dominio": "general",
        "tipo": "INSUFICIENTE",
        "estado": "NO DEMOSTRADA",
        "confianza": "BAJA",
        "evidencia_a_favor": [],
        "evidencia_en_contra": [],
        "informacion_faltante": missing,
        "impacto_potencial": INSUFICIENTE,
        "puntaje": 0.0,
        "relacion_causal": "no_evaluable",
        "mensaje": "Información insuficiente para establecer esta causa.",
    }]


def _score_all_hypotheses(
    indicators: dict[str, Any],
    datasets: dict[str, list[dict]],
    hallazgos: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    rad = indicators.get("radicacion", {})
    glo = indicators.get("glosas", {})
    car = indicators.get("cartera", {})
    fact = indicators.get("facturacion", {})
    devol = indicators.get("devoluciones", {})
    pagos = indicators.get("cartera", {}).get("recaudo")

    tiempo_rad = rad.get("tiempo_promedio_factura_radicacion_dias")
    no_rad = rad.get("facturas_no_radicadas", 0)
    pct_glosa = glo.get("porcentaje_glosa")
    pct_radicado = rad.get("porcentaje_radicado")
    conc = fact.get("concentracion_principal_pagador_pct")
    saldo = car.get("saldo_total", 0)
    aging_91 = (car.get("aging") or {}).get("91+", 0)

    result: dict[str, dict[str, Any]] = {h["id"]: {"a_favor": [], "en_contra": [], "faltante": [], "score": 0.0} for h in HYPOTHESIS_CATALOG}

    # H1 facturación tardía — proxy: facturas recientes sin radicar con fechas antiguas
    if fact.get("disponible") and isinstance(no_rad, int) and no_rad > 0:
        result["H1"]["a_favor"].append(f"{no_rad} facturas facturadas sin radicar")
        result["H1"]["score"] += 0.35
    if rad.get("disponible") and isinstance(pct_radicado, (int, float)) and pct_radicado > 85:
        result["H1"]["en_contra"].append(f"Radicación alta ({pct_radicado}%) reduce relevancia de facturación tardía")
        result["H1"]["score"] -= 0.2

    # H2 radicación tardía
    if isinstance(tiempo_rad, (int, float)) and tiempo_rad > 10:
        result["H2"]["a_favor"].append(f"Demora promedio factura→radicación: {tiempo_rad} días")
        result["H2"]["score"] += min(tiempo_rad / 30, 0.5)
    if isinstance(no_rad, int) and no_rad >= 2:
        result["H2"]["a_favor"].append(f"{no_rad} facturas sin radicar")
        result["H2"]["score"] += 0.25
    if isinstance(tiempo_rad, (int, float)) and tiempo_rad <= 5:
        result["H2"]["en_contra"].append(f"Radicación ágil ({tiempo_rad} días promedio)")
        result["H2"]["score"] -= 0.35

    # H3 devoluciones
    if devol.get("disponible"):
        val = devol.get("valor_devuelto_total", 0)
        if val > 0:
            result["H3"]["a_favor"].append(f"Devoluciones por ${val:,.0f}")
            result["H3"]["score"] += min(val / max(saldo or 1, 1), 0.45)
    else:
        result["H3"]["faltante"].append("Dataset de devoluciones o glosas con estado DEVUELTA")
    devueltas = _count_devueltas(datasets.get("glosas", []))
    if devueltas > 0:
        result["H3"]["a_favor"].append(f"{devueltas} registros con estado DEVUELTA en glosas")
        result["H3"]["score"] += 0.3

    # H4 glosas
    if isinstance(pct_glosa, (int, float)) and pct_glosa > 8:
        result["H4"]["a_favor"].append(f"Porcentaje de glosa: {pct_glosa}%")
        result["H4"]["score"] += min(pct_glosa / 25, 0.5)
    if isinstance(pct_glosa, (int, float)) and pct_glosa < 4:
        result["H4"]["en_contra"].append(f"Glosa baja ({pct_glosa}%)")
        result["H4"]["score"] -= 0.3

    # H5 soportes — proxy devoluciones por soporte
    soporte_signals = [d for d in datasets.get("devoluciones", []) if "soporte" in str(d.get("motivo", "")).lower()]
    if soporte_signals:
        result["H5"]["a_favor"].append(f"{len(soporte_signals)} devoluciones por soporte")
        result["H5"]["score"] += 0.35

    # H6 contractual — requiere contratos + demora vs plazo (proxy radicación)
    if indicators.get("contratos", {}).get("disponible") and isinstance(tiempo_rad, (int, float)) and tiempo_rad > 7:
        result["H6"]["a_favor"].append("Demora operativa con contratos vigentes — revisar plazos pactados")
        result["H6"]["score"] += 0.15
    if not indicators.get("contratos", {}).get("disponible"):
        result["H6"]["faltante"].append("Contratos para contrastar plazos pactados")

    # H7 comportamiento pagador — radicación buena, cartera alta, recaudo bajo
    rad_ok = isinstance(tiempo_rad, (int, float)) and tiempo_rad <= 5 and isinstance(pct_radicado, (int, float)) and pct_radicado >= 90
    glo_bajo = isinstance(pct_glosa, (int, float)) and pct_glosa < 5
    recaudo_bajo = isinstance(pagos, (int, float)) and isinstance(saldo, (int, float)) and saldo > 0 and pagos < saldo * 0.3
    if rad_ok and glo_bajo and (recaudo_bajo or aging_91 > 0):
        result["H7"]["a_favor"].append("Proceso interno ágil pero cartera/recaudo desalineados")
        result["H7"]["score"] += 0.55
        por_ent = car.get("por_entidad", {})
        if por_ent:
            top = max(por_ent.items(), key=lambda x: x[1])
            result["H7"]["a_favor"].append(f"Concentración de mora en {top[0]}")
            result["H7"]["score"] += 0.15
    if isinstance(tiempo_rad, (int, float)) and tiempo_rad > 12:
        result["H7"]["en_contra"].append("Demora interna de radicación explica parte de la mora")
        result["H7"]["score"] -= 0.25

    # H8 concentración
    if isinstance(conc, (int, float)) and conc > 70:
        result["H8"]["a_favor"].append(f"Concentración del {conc}% en un pagador")
        result["H8"]["score"] += 0.35

    # H9 proceso interno
    internal_issues = sum(1 for h in hallazgos if h.get("category") in ("radicacion", "facturacion"))
    if internal_issues >= 2 or (isinstance(tiempo_rad, (int, float)) and tiempo_rad > 10):
        result["H9"]["a_favor"].append("Múltiples hallazgos en procesos internos")
        result["H9"]["score"] += 0.3
    if rad_ok:
        result["H9"]["en_contra"].append("Indicadores de radicación dentro de umbral")
        result["H9"]["score"] -= 0.2

    # H10 combinación
    strong = sum(1 for hid in ("H2", "H3", "H4", "H7", "H8") if result[hid]["score"] >= 0.35)
    if strong >= 2:
        result["H10"]["a_favor"].append(f"{strong} hipótesis con evidencia significativa simultánea")
        result["H10"]["score"] = min(sum(result[h]["score"] for h in ("H2", "H3", "H4", "H7", "H8")) / 3, 0.85)

    return result


def _apply_knowledge_conflicts(scores: dict[str, dict[str, Any]], knowledge_ctx: dict[str, Any]) -> None:
    """Reduce confianza causal cuando hay documentos contradictorios (Caso D)."""
    if not knowledge_ctx.get("conflictos") and not knowledge_ctx.get("requiere_validacion"):
        return

    limites: list[int] = []
    for bundle in knowledge_ctx.get("conflictos", []):
        analisis = bundle.get("analisis", {})
        limites.extend(analisis.get("limites_unicos", []))

    detalle = (
        f"Plazos documentales contradictorios: {limites}"
        if limites
        else "Documentos autorizados con información contradictoria"
    )
    mensaje_faltante = "Validar vigencia y jerarquía documental antes de confirmar causa"

    for hid in ("H2", "H6", "H10"):
        scores[hid]["en_contra"].append(detalle)
        scores[hid]["faltante"].append(mensaje_faltante)
        scores[hid]["score"] = max(scores[hid]["score"] - 0.25, 0.0)

    strong = sum(1 for hid in ("H2", "H3", "H4", "H7", "H8") if scores[hid]["score"] >= 0.3)
    if strong >= 2:
        scores["H10"]["a_favor"].append(f"{strong} frentes con evidencia; conflicto documental pendiente")
        scores["H10"]["score"] = min(scores["H10"]["score"] + 0.15, 0.75)


def _downgrade_confidence(level: str) -> str:
    if level == "ALTA":
        return "MEDIA"
    if level == "MEDIA":
        return "BAJA"
    return "BAJA"


def _count_devueltas(glosas: list[dict]) -> int:
    return sum(1 for g in glosas if str(g.get("estado", "")).upper() == "DEVUELTA")


def _classify_status(
    score: float,
    a_favor: list,
    en_contra: list,
    sufficiency: dict,
    knowledge_ctx: dict[str, Any] | None = None,
) -> str:
    if sufficiency.get("clasificacion") == "INSUFICIENTE":
        return "NO DEMOSTRADA"
    has_conflict = bool(
        knowledge_ctx and (knowledge_ctx.get("conflictos") or knowledge_ctx.get("requiere_validacion"))
    )
    if score >= 0.65 and len(a_favor) >= 2 and len(en_contra) <= 1 and not has_conflict:
        return "CONFIRMADA"
    if score >= 0.45 and a_favor:
        return "PROBABLE" if not has_conflict else "POSIBLE"
    if score >= 0.25:
        return "POSIBLE"
    if en_contra and not a_favor:
        return "REFUTADA"
    return "NO DEMOSTRADA"


def _confidence_label(score: float) -> str:
    if score >= 0.6:
        return "ALTA"
    if score >= 0.35:
        return "MEDIA"
    return "BAJA"


def _estimate_impact(hid: str, indicators: dict, hallazgos: list[dict]) -> float | str:
    impacts = [h.get("economic_impact") for h in hallazgos if isinstance(h.get("economic_impact"), (int, float))]
    if impacts:
        return max(impacts)
    car = indicators.get("cartera", {})
    if hid in ("H2", "H3", "H4", "H7", "H10") and car.get("disponible"):
        return car.get("saldo_total", INSUFICIENTE)
    return INSUFICIENTE
