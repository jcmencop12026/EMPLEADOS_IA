"""Evaluación de suficiencia de datos — MOTOR-ANALITICO-1000."""

from __future__ import annotations

from typing import Any

from app.services.salud_indicators import INSUFICIENTE


def assess_data_sufficiency(
    data_profiles: dict[str, Any],
    indicators: dict[str, Any],
    request_text: str,
) -> dict[str, Any]:
    """Clasifica SUFICIENTE / PARCIAL / INSUFICIENTE con detalle por dimensión."""
    text = request_text.lower()
    dimensions: dict[str, dict[str, Any]] = {}
    scores: list[float] = []

    for source, profile in data_profiles.items():
        registros = profile.get("registros", 0)
        completitud = profile.get("completitud", 0.0)
        nivel = profile.get("nivel_calidad", "INSUFICIENTE")
        dim_score = 0.0
        if registros >= 5 and completitud >= 0.75:
            dim_score = 1.0
        elif registros >= 2 and completitud >= 0.5:
            dim_score = 0.5
        scores.append(dim_score)
        dimensions[source] = {
            "registros": registros,
            "completitud": completitud,
            "nivel_calidad": nivel,
            "duplicados": profile.get("duplicados", 0),
            "inconsistencias": profile.get("inconsistencias", []),
            "cobertura_temporal": _temporal_coverage(profile),
        }

    causal_dims = _required_dimensions(text)
    missing_critical: list[dict[str, str]] = []
    for dim in causal_dims:
        ind = indicators.get(dim, {})
        if not ind.get("disponible"):
            missing_critical.append({
                "dimension": dim,
                "que_falta": f"Datos de {dim}",
                "por_que": f"Necesario para evaluar hipótesis sobre {dim} en la solicitud.",
                "que_permitiria": f"Calcular indicadores de {dim} y contrastar causas.",
            })

    avg = sum(scores) / len(scores) if scores else 0.0
    cash_question = any(k in text for k in ("caja", "cartera", "recuper", "recaudo", "flujo"))
    if cash_question and "cartera" not in data_profiles:
        clasificacion = "INSUFICIENTE"
    elif len(data_profiles) <= 1 and missing_critical:
        clasificacion = "INSUFICIENTE"
    elif not data_profiles or avg < 0.35 or (missing_critical and len(missing_critical) >= 3):
        clasificacion = "INSUFICIENTE"
    elif missing_critical or avg < 0.7:
        clasificacion = "PARCIAL"
    else:
        clasificacion = "SUFICIENTE"

    return {
        "clasificacion": clasificacion,
        "puntaje": round(avg, 3),
        "dimensiones": dimensions,
        "informacion_faltante_critica": missing_critical,
        "limitaciones": _build_limitations(clasificacion, missing_critical),
    }


def _temporal_coverage(profile: dict[str, Any]) -> str:
    fechas = profile.get("fechas", {})
    if fechas.get("minima") and fechas.get("maxima"):
        return f"{fechas['minima']} → {fechas['maxima']}"
    return INSUFICIENTE


def _required_dimensions(text: str) -> list[str]:
    dims: list[str] = []
    mapping = {
        "cartera": ("cartera", "mora", "recaudo", "cobro", "caja"),
        "radicacion": ("radic",),
        "glosas": ("glosa", "devoluc", "objec"),
        "facturacion": ("factur",),
        "pagos": ("pago", "recaudo"),
    }
    for dim, keywords in mapping.items():
        if any(k in text for k in keywords):
            dims.append(dim)
    if "cartera" in text or "aumentó" in text or "aumento" in text:
        for extra in ("cartera", "radicacion", "glosas", "pagos"):
            if extra not in dims:
                dims.append(extra)

    if not dims:
        dims = ["facturacion", "radicacion", "glosas", "cartera"]
    return sorted(set(dims))


def _build_limitations(clasificacion: str, missing: list[dict]) -> list[str]:
    limits: list[str] = []
    if clasificacion == "INSUFICIENTE":
        limits.append("No se debe inferir causalidad con la información disponible.")
    if missing:
        limits.append(f"Faltan {len(missing)} dimensiones críticas para la solicitud.")
    return limits
