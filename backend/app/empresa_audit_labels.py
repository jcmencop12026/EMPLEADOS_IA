"""Etiquetas en español para acciones de auditoría y gobierno."""

from __future__ import annotations

AUDIT_ACTION_LABELS_ES: dict[str, str] = {
  # Autenticación y plataforma
  "auth.login": "Inicio de sesión",
  "auth.login.failed": "Intento de inicio fallido",
  "auth.logout": "Cierre de sesión",
  "platform.organization.created": "Empresa creada",
  "platform.organization.status_changed": "Estado de empresa cambiado",
  # Empleados IA
  "employee.created": "Empleado IA creado",
  "employee.updated": "Empleado IA actualizado",
  "employee.activated": "Empleado IA activado",
  "employee.certified": "Empleado IA certificado",
  "employee.published": "Empleado IA publicado",
  # Operaciones y automatización
  "automation.created": "Automatización creada",
  "automation.scheduler_run": "Ejecución programada",
  "operations.cancelled": "Operación cancelada",
  # IA y FinOps
  "llm.inference": "Inferencia de IA",
  "llm.model.create": "Modelo IA registrado",
  "llm.routing.create": "Ruta IA creada",
  "llm.routing.update": "Ruta IA actualizada",
  "finops.registration.failed": "Error al registrar consumo",
  # Seguridad
  "security.mfa.enabled": "MFA activado",
  "security.mfa.disabled": "MFA desactivado",
  "security.mfa.verified": "MFA verificado",
  "security.session.revoked": "Sesión revocada",
  "security.policy.updated": "Política de seguridad actualizada",
  # Identidad
  "identidad.politica.actualizada": "Política de identidad actualizada",
  "identidad.proveedor.creado": "Proveedor de identidad creado",
  "identidad.proveedor.activado": "Proveedor de identidad activado",
  # Gobierno de datos 1350
  "gov.catalog.create": "Entrada de catálogo creada",
  "gov.catalog.update": "Entrada de catálogo actualizada",
  "gov.classification.create": "Nivel de clasificación creado",
  "gov.access.logged": "Acceso a datos registrado",
  "gov.export.recorded": "Exportación registrada",
  "gov.finding.created": "Hallazgo de gobierno creado",
  # Evaluación BP1
  "evaluacion.visibility": "Visibilidad de evaluación cambiada",
  "evaluacion.created": "Expediente de evaluación creado",
  # Gobierno operacional
  "gobierno.accion.solicitada": "Acción solicitada",
  "gobierno.accion.aprobada": "Acción aprobada",
  "gobierno.accion.rechazada": "Acción rechazada",
  "gobierno.accion.ejecutada": "Acción ejecutada",
  "gobierno.accion.cancelada": "Acción cancelada",
  "gobierno.visibilidad.cambiada": "Visibilidad cambiada",
  "gobierno.ia.politica.creada": "Política IA creada",
  # Empresa seguridad transversal
  "empresa.clasificacion.asignada": "Clasificación asignada",
  "empresa.evidencia.vinculada": "Evidencia vinculada",
  "empresa.visibilidad.cambiada": "Visibilidad empresarial cambiada",
}

RESULTADO_LABELS_ES: dict[str, str] = {
  "EJECUTADA": "Ejecutada",
  "RECHAZADA": "Rechazada",
  "CANCELADA": "Cancelada",
  "APROBADA": "Aprobada",
  "PENDIENTE": "Pendiente",
  "EXITOSO": "Exitoso",
  "FALLIDO": "Fallido",
}

GRUPO_CONTROLES_ES: dict[str, str] = {
  "acceso": "Acceso",
  "datos": "Datos",
  "ia": "IA",
  "aprobaciones": "Aprobaciones",
  "auditoria": "Auditoría",
  "trazabilidad": "Trazabilidad",
  "privacidad": "Privacidad",
  "continuidad": "Continuidad",
}

ESTADO_CONTROL_ES: dict[str, str] = {
  "IMPLEMENTADO": "Implementado",
  "CONFIGURADO": "Configurado",
  "PENDIENTE": "Pendiente",
  "NO_DISPONIBLE": "No disponible",
}


def etiqueta_accion(action: str | None) -> str:
    if not action:
        return "—"
    if action in AUDIT_ACTION_LABELS_ES:
        return AUDIT_ACTION_LABELS_ES[action]
    if action.startswith("gobierno."):
        suffix = action.split(".", 1)[1].replace(".", " · ").replace("_", " ")
        return f"Gobierno · {suffix}"
    if action.startswith("gov."):
        suffix = action.split(".", 1)[1].replace(".", " · ").replace("_", " ")
        return f"Gobierno de datos · {suffix}"
    if action.startswith("security."):
        suffix = action.split(".", 1)[1].replace(".", " · ").replace("_", " ")
        return f"Seguridad · {suffix}"
    return action.replace(".", " · ").replace("_", " ")


def sanitizar_detalle(detail: str | None, max_len: int = 300) -> str | None:
    """Evita exponer payloads sensibles innecesarios en consulta."""
    if not detail:
        return None
    lowered = detail.lower()
    sensibles = ("password", "token", "secret", "credential", "api_key", "hash")
    if any(s in lowered for s in sensibles):
        return "[Detalle omitido — contiene información sensible]"
    if len(detail) > max_len:
        return detail[:max_len] + "…"
    return detail
