"""Etiquetas en español — Centro de Negocios (fuente única backend)."""

from __future__ import annotations

PROPOSAL_STATUS_LABELS: dict[str, str] = {
    "BORRADOR": "Borrador",
    "EN_REVISION": "En revisión",
    "APROBADA": "Aprobada internamente",
    "ENVIADA": "Presentada",
    "ACEPTADA": "Contratada",
    "RECHAZADA": "Descartada",
    "VENCIDA": "Suspendida",
}

APPROVAL_LEVEL_LABELS: dict[str, str] = {
    "PREPARADOR": "Preparador",
    "REVISOR": "Revisor",
    "APROBADOR_COMERCIAL": "Aprobador comercial",
    "AUTORIZADOR_FINAL": "Autorizador final",
}

APPROVAL_STATUS_LABELS: dict[str, str] = {
    "PENDIENTE": "Pendiente",
    "APROBADO": "Aprobado",
    "RECHAZADO": "Rechazado",
}

PRICE_PHASE_LABELS: dict[str, str] = {
    "RECOMENDADO": "Precio recomendado",
    "APROBADO": "Precio aprobado",
    "PRESENTADO": "Precio presentado",
    "CONTRATADO": "Precio contratado",
}

MODELo_COMERCIAL_LABELS: dict[str, str] = {
    "IMPLEMENTACION_MENSUALIDAD": "Implementación + mensualidad",
    "PROYECTO_FIJO": "Proyecto fijo",
    "SUSCRIPCION": "Suscripción",
    "VARIABLE_CONSUMO": "Variable por consumo",
    "EXITO_RESULTADOS": "Éxito / resultados",
    "HIBRIDO": "Híbrido",
}


def label_proposal_status(code: str | None) -> str:
    if not code:
        return "—"
    return PROPOSAL_STATUS_LABELS.get(code, code.replace("_", " ").title())


def label_approval_level(code: str | None) -> str:
    if not code:
        return "—"
    return APPROVAL_LEVEL_LABELS.get(code, code.replace("_", " ").title())
