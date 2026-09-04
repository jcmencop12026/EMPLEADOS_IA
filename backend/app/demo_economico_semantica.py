"""Semántica inequívoca para valores económicos DEMO — evita confundir simulación con verificación real."""

from __future__ import annotations

from typing import Any

DEMO_BANNER = "DEMO — DATOS SIMULADOS"

# Etiquetas de presentación (nunca implican verificación real en demo)
LABEL_SIMULACION_VERIFICADO = "SIMULACIÓN DE RESULTADO VERIFICADO"
LABEL_ESTIMADO = "ESTIMADO"
LABEL_PROYECTADO = "PROYECTADO"
LABEL_POTENCIAL = "POTENCIAL"
LABEL_SIMULADO = "SIMULADO"

DEMO_VALUE_SPECS = [
    {
        "clave": "simulacion_verificado",
        "etiqueta": LABEL_SIMULACION_VERIFICADO,
        "amount": 28_500_000,
        "nota": "Ilustración de cómo se vería un valor verificado futuro — no es medición real",
    },
    {
        "clave": "estimado",
        "etiqueta": LABEL_ESTIMADO,
        "amount": 62_000_000,
        "nota": "Proyección anual basada en reprocesos — dato simulado",
    },
    {
        "clave": "potencial",
        "etiqueta": LABEL_POTENCIAL,
        "amount": 185_000_000,
        "nota": "Escenario completo de automatización — no realizado",
    },
]


def build_demo_resumen(entries: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Construye resumen etiquetado para UI demo."""
    by_key = {e.get("clave"): e for e in (entries or [])}
    out: dict[str, Any] = {
        "es_demo": True,
        "banner": DEMO_BANNER,
        "nota": "Ninguna cifra demo equivale a valor verificado real de la organización.",
        "simulacion_verificado": None,
        "estimado": None,
        "proyectado": None,
        "potencial": None,
        "verificado": None,
    }
    for spec in DEMO_VALUE_SPECS:
        entry = by_key.get(spec["clave"], spec)
        payload = {
            "monto": entry.get("amount"),
            "moneda": "COP",
            "etiqueta": spec["etiqueta"],
            "es_simulado": True,
            "nota": entry.get("nota", spec["nota"]),
        }
        out[spec["clave"]] = payload
        if spec["clave"] == "estimado":
            out["proyectado"] = {**payload, "etiqueta": LABEL_PROYECTADO}
    return out


def format_demo_amount(amount: float | int | None) -> str:
    if amount is None:
        return "—"
    return f"${int(amount):,} COP".replace(",", ".")
