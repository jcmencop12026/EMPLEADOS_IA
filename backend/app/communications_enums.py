"""Enumeraciones — Centro de Información y Comunicaciones (MB-11)."""

from __future__ import annotations

CANAL_TIPOS = (
    "CORREO_ELECTRONICO",
    "INTERNO_PLATAFORMA",
    "WEBHOOK",
)

CANAL_ESTADOS = ("ACTIVO", "INACTIVO", "DEGRADADO", "ERROR")

COMUNICACION_ESTADOS = (
    "BORRADOR",
    "PROGRAMADA",
    "PENDIENTE_ENVIO",
    "ENVIANDO",
    "ENVIADA",
    "ENTREGADA",
    "FALLIDA",
    "CANCELADA",
)

TEMPLATE_ESTADOS = ("BORRADOR", "ACTIVA", "ARCHIVADA")

REGLA_ACCIONES = ("ENVIAR", "PROGRAMAR", "SOLO_REGISTRAR")

DESTINATARIO_TIPOS = (
    "USUARIO",
    "ROL",
    "GRUPO",
    "CONTACTO",
    "ORGANIZACION",
    "EXTERNO",
    "DINAMICO",
)

DESTINATARIO_DINAMICOS = (
    "RESPONSABLE_CASO",
    "ADMIN_ORGANIZACION",
    "SUPERVISOR",
    "SOLICITANTE",
    "PROPIETARIO_PROCESO",
)

TIPOS_COMUNICACION = (
    "INFORMATIVA",
    "OPERATIVA",
    "ALERTA",
    "RECORDATORIO",
    "SOLICITUD",
    "RESULTADO",
    "INFORME",
    "APROBACION",
    "INCIDENTE",
)

EVENTOS_COMUNICACION = (
    "RESULTADOS_INFORME_GENERADO",
    "RESULTADOS_MEDICION_REAL",
    "EVALUACION_INFO_FALTANTE",
    "EVALUACION_APROBACION_PENDIENTE",
    "ACCION_VENCIDA",
    "OPORTUNIDAD_RELEVANTE",
    "FALLO_IMPORTANTE",
    "SUPPORT_CASE_ASSIGNED",
    "SUPPORT_CASE_STATUS",
    "SUPPORT_CASE_RESOLVED",
    "SUPPORT_CASE_COMMENT",
    "SUPPORT_SLA_WARNING",
    "SUPPORT_CASE_ESCALATED",
)

ALLOWED_TEMPLATE_VARIABLES = frozenset({
    "nombre",
    "empresa",
    "fecha",
    "caso",
    "empleado_ia",
    "valor",
    "estado",
    "asunto",
    "organizacion",
    "evento",
    "correlation_id",
    "informe_titulo",
    "informe_version",
    "expediente",
    "expediente_codigo",
})

MAX_REINTENTOS = 3
REINTENTO_BACKOFF_SEG = (60, 120, 300)
ANTISPAM_DEFAULT_MIN = 15
