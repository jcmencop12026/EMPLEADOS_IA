"""Enumeraciones — Mesa de Ayuda y Soporte (MB-12)."""

from __future__ import annotations

# Tipos de caso configurables
TIPOS_CASO = (
    "INCIDENTE",
    "SOLICITUD",
    "PROBLEMA",
    "CONSULTA",
    "MEJORA",
    "ACCESO",
    "INTEGRACION",
    "AUTOMATIZACION",
    "EMPLEADO_IA",
    "FACTURACION_COSTOS",
    "SEGURIDAD",
    "OTRO",
)

ESTADOS_CASO = (
    "NUEVO",
    "CLASIFICADO",
    "ASIGNADO",
    "EN_ANALISIS",
    "EN_PROCESO",
    "PENDIENTE_USUARIO",
    "PENDIENTE_TERCERO",
    "RESUELTO",
    "VALIDACION_PENDIENTE",
    "CERRADO",
    "CANCELADO",
)

ESTADOS_ABIERTOS = frozenset({
    "NUEVO",
    "CLASIFICADO",
    "ASIGNADO",
    "EN_ANALISIS",
    "EN_PROCESO",
    "PENDIENTE_USUARIO",
    "PENDIENTE_TERCERO",
    "VALIDACION_PENDIENTE",
})

ESTADO_ETIQUETAS: dict[str, str] = {
    "NUEVO": "Nuevo",
    "CLASIFICADO": "Clasificado",
    "ASIGNADO": "Asignado",
    "EN_ANALISIS": "En análisis",
    "EN_PROCESO": "En progreso",
    "PENDIENTE_USUARIO": "Esperando información",
    "PENDIENTE_TERCERO": "Esperando tercero",
    "RESUELTO": "Resuelto",
    "VALIDACION_PENDIENTE": "Validación pendiente",
    "CERRADO": "Cerrado",
    "CANCELADO": "Cancelado",
}

PRIORIDADES = ("CRITICA", "ALTA", "MEDIA", "BAJA")
IMPACTOS = ("CRITICO", "ALTO", "MEDIO", "BAJO")
URGENCIAS = ("CRITICA", "ALTA", "MEDIA", "BAJA")

ORIGENES = ("MANUAL", "AUTOMATICO")

ACCIONES_HISTORIAL = (
    "CREACION",
    "CLASIFICACION",
    "CAMBIO_ESTADO",
    "ASIGNACION",
    "COMENTARIO",
    "ESCALAMIENTO",
    "RESOLUCION",
    "CIERRE",
    "ACTUALIZACION",
    "DIAGNOSTICO",
    "PRIORIDAD",
    "EVIDENCIA",
    "VALIDACION",
)

SLA_ESTADOS = ("DENTRO", "PROXIMO", "VENCIDO", "NO_APLICA")

SLA_ETIQUETAS: dict[str, str] = {
    "DENTRO": "En tiempo",
    "PROXIMO": "Próximo a vencer",
    "VENCIDO": "Vencido",
    "NO_APLICA": "Sin SLA",
}

ESCALAMIENTO_MOTIVOS = (
    "CRITICIDAD",
    "VENCIMIENTO",
    "SIN_RESPUESTA",
    "COMPLEJIDAD",
    "DEPENDENCIA_EXTERNA",
    "RECURRENCIA",
)

EVIDENCIA_TIPOS = (
    "LOG",
    "CAPTURA",
    "DOCUMENTO",
    "ERROR",
    "EVENTO",
    "EJECUCION",
    "OBJETO_EIAAX",
    "OTRO",
)

VALIDACION_SOLICITANTE = ("PENDIENTE", "ACEPTADA", "RECHAZADA")

PROBLEMA_ESTADOS = ("ABIERTO", "EN_ANALISIS", "MITIGADO", "CERRADO")

TIPOS_ARTICULO_KB = ("ARTICULO", "PROCEDIMIENTO", "SOLUCION", "FAQ")

EVENTOS_SOPORTE_MB11 = (
    "SUPPORT_CASE_ASSIGNED",
    "SUPPORT_CASE_STATUS",
    "SUPPORT_CASE_RESOLVED",
    "SUPPORT_CASE_COMMENT",
    "SUPPORT_SLA_WARNING",
    "SUPPORT_CASE_ESCALATED",
)

# Matriz impacto × urgencia → prioridad sugerida
_PRIORIDAD_SCORE = {"CRITICO": 4, "ALTO": 3, "MEDIO": 2, "BAJO": 1}
_URGENCIA_SCORE = {"CRITICA": 4, "ALTA": 3, "MEDIA": 2, "BAJA": 1}


def suggest_priority(impacto: str, urgencia: str) -> str:
    """Calcula prioridad sugerida a partir de impacto y urgencia."""
    i = _PRIORIDAD_SCORE.get(impacto.upper(), 2)
    u = _URGENCIA_SCORE.get(urgencia.upper(), 2)
    score = i + u
    if score >= 7:
        return "CRITICA"
    if score >= 5:
        return "ALTA"
    if score >= 3:
        return "MEDIA"
    return "BAJA"
