"""Clasificación de intención del agente EIAAX — Bloque Producto 2 (A–H)."""

from __future__ import annotations

import re
from typing import Any

INTENCION_DESCRIPCIONES: dict[str, str] = {
    "A": "Puede responderse con información existente en el expediente.",
    "B": "Necesita información adicional del usuario o de la entidad.",
    "C": "Requiere análisis asistido por IA.",
    "D": "Requiere consultar una fuente externa (capacidad de lectura).",
    "E": "Requiere ejecutar una acción externa (capacidad técnica).",
    "F": "Requiere aprobación humana antes de continuar.",
    "G": "Puede convertirse en oportunidad de mejora o valor.",
    "H": "Puede convertirse en tarea o seguimiento operativo.",
}

_EXTERNAL_KEYWORDS = re.compile(
    r"\b(fuente|externo|sistema|api|base de datos|sincroniz|integraci[oó]n|erp|consultar datos|validar)\b",
    re.I,
)
_EXECUTE_KEYWORDS = re.compile(
    r"\b(ejecut|enviar|sincroniz|transformar|notificar|proceso|automatiz)\b",
    re.I,
)
_APPROVAL_KEYWORDS = re.compile(
    r"\b(aprob|autoriz|confirmar ejecuci[oó]n|modificar sistema)\b",
    re.I,
)
_INFO_MISSING_KEYWORDS = re.compile(
    r"\b(falta|pendiente|qué información|información adicional|incompleto)\b",
    re.I,
)
_OPPORTUNITY_KEYWORDS = re.compile(
    r"\b(oportunidad|mejora|valor|beneficio|optimiz|ahorro|ingreso)\b",
    re.I,
)
_TASK_KEYWORDS = re.compile(
    r"\b(tarea|seguimiento|asignar|escalar|recordatorio|plazo|responsable)\b",
    re.I,
)


def classify_intent(
    mensaje: str,
    *,
    accion_sugerida: str | None,
    porcentaje_informacion: int,
    tiene_proveedor_llm: bool,
    piiax_disponible: bool,
    info_pendiente_count: int,
) -> dict[str, Any]:
    texto = (mensaje or "").strip()
    accion = (accion_sugerida or "").strip()

    if accion in ("informacion_faltante",) or _INFO_MISSING_KEYWORDS.search(texto) or (
        info_pendiente_count > 0 and porcentaje_informacion < 60
    ):
        return _result("B", capacidad_sugerida=None, requiere_aprobacion=False)

    if accion in ("identificar_oportunidades", "crear_oportunidad") or _OPPORTUNITY_KEYWORDS.search(texto):
        return _result("G", capacidad_sugerida=None, requiere_aprobacion=False)

    if accion in ("asignar_tarea", "seguimiento") or _TASK_KEYWORDS.search(texto):
        return _result("H", capacidad_sugerida=None, requiere_aprobacion=False)

    if _APPROVAL_KEYWORDS.search(texto) or accion in ("ejecutar_externo",):
        return _result("F", capacidad_sugerida="ejecutar_proceso", requiere_aprobacion=True)

    if _EXECUTE_KEYWORDS.search(texto):
        return _result("E", capacidad_sugerida="ejecutar_proceso", requiere_aprobacion=True)

    if _EXTERNAL_KEYWORDS.search(texto) or accion in ("buscar_fuentes", "analizar_fuentes"):
        cap = "consultar_datos"
        return _result("D", capacidad_sugerida=cap, requiere_aprobacion=False)

    if accion in (
        "profundizar_hallazgo", "buscar_causas", "cuantificar_impacto",
        "siguiente_analisis", "explicar_indicador",
    ):
        if tiene_proveedor_llm:
            return _result("C", capacidad_sugerida=None, requiere_aprobacion=False)
        return _result("A", capacidad_sugerida=None, requiere_aprobacion=False)

    if porcentaje_informacion >= 50 and not _EXTERNAL_KEYWORDS.search(texto):
        return _result("A", capacidad_sugerida=None, requiere_aprobacion=False)

    if tiene_proveedor_llm:
        return _result("C", capacidad_sugerida=None, requiere_aprobacion=False)

    return _result("B", capacidad_sugerida=None, requiere_aprobacion=False)


def _result(
    codigo: str,
    *,
    capacidad_sugerida: str | None,
    requiere_aprobacion: bool,
) -> dict[str, Any]:
    return {
        "intencion": codigo,
        "descripcion": INTENCION_DESCRIPCIONES[codigo],
        "capacidad_sugerida": capacidad_sugerida,
        "requiere_aprobacion": requiere_aprobacion,
        "ejecutar_externo_automatico": False,
    }
