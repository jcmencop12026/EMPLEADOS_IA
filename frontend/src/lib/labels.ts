/** Etiquetas visuales en español — valores API permanecen en inglés. */
export const LIFECYCLE_STATUS: Record<string, string> = {
  DRAFT: "Borrador",
  CONFIGURING: "Configurando",
  READY_FOR_TEST: "Listo para prueba",
  TESTING: "En prueba",
  FAILED_TEST: "Prueba fallida",
  READY_FOR_CERTIFICATION: "Listo para certificar",
  CERTIFIED: "Certificado",
  PUBLISHED: "Publicado",
  ACTIVE: "Activo",
  PAUSED: "Pausado",
  RETIRED: "Retirado",
};

/** Fases funcionales MB-06 (mapeo API). */
export const LIFECYCLE_PHASE: Record<string, string> = {
  BORRADOR: "Borrador",
  CONFIGURADO: "Configurado",
  EN_PRUEBAS: "En pruebas",
  APROBADO: "Aprobado",
  PUBLICADO: "Publicado",
  ACTIVO: "Activo",
  PAUSADO: "Pausado",
  RETIRADO: "Retirado",
};

export const EXECUTION_STATUS: Record<string, string> = {
  COMPLETED: "Completado",
  WAITING_APPROVAL: "Esperando aprobación",
  RUNNING: "En ejecución",
  FAILED: "Fallido",
  READY: "Listo",
  PLANNING: "Planificando",
};

export const APPROVAL_STATUS: Record<string, string> = {
  PENDING: "Pendiente",
  APPROVED: "Aprobado",
  REJECTED: "Rechazado",
  NOT_REQUIRED: "No requerida",
};

export const MATURITY: Record<string, string> = {
  EXPERIMENTAL: "Experimental",
  STABLE: "Estable",
  PRODUCTION: "Producción",
  AUTONOMOUS_CONTROLLED: "Autónomo controlado",
  SHADOW: "Modo sombra",
  SUPERVISED: "Supervisado",
};

export const RISK_LEVEL: Record<string, string> = {
  LOW: "Bajo",
  MEDIUM: "Medio",
  HIGH: "Alto",
  CRITICAL: "Crítico",
};

export const EVENT_TYPE: Record<string, string> = {
  WORK_REQUESTED: "Solicitud de trabajo",
  WORK_PLANNED: "Plan de trabajo creado",
  TASK_CREATED: "Tarea creada",
  TASK_STARTED: "Tarea iniciada",
  TASK_COMPLETED: "Tarea completada",
  TASK_FAILED: "Tarea fallida",
  WORK_COMPLETED: "Trabajo completado",
  WORK_FAILED: "Trabajo fallido",
  APPROVAL_REQUIRED: "Aprobación requerida",
  APPROVAL_COMPLETED: "Aprobación completada",
  FINOPS_LIMIT_REACHED: "Límite de costos alcanzado",
  TOOL_DENIED: "Herramienta denegada",
  SYSTEM_ERROR: "Error del sistema",
  TENANT_SECURITY_EVENT: "Evento de seguridad",
  "work.cancelled": "Trabajo cancelado",
};

export const AUDIT_ACTION: Record<string, string> = {
  "platform.organization.created": "Empresa creada",
  "platform.organization.status_changed": "Estado de empresa cambiado",
  "auth.login": "Inicio de sesión",
  "auth.login.failed": "Intento de inicio fallido",
  "employee.created": "Empleado IA creado",
  "employee.updated": "Empleado IA actualizado",
  "employee.activated": "Empleado IA activado",
  "automation.created": "Automatización creada",
  "automation.scheduler_run": "Ejecución programada",
  "llm.inference": "Inferencia de IA",
  "finops.registration.failed": "Error al registrar consumo",
};

export function label(map: Record<string, string>, value: string | undefined | null): string {
  if (!value) return "—";
  return map[value] ?? value;
}

export function formatAuditAction(action: string | undefined | null): string {
  if (!action) return "—";
  return AUDIT_ACTION[action] ?? action.replace(/\./g, " · ").replace(/_/g, " ");
}

/** Estados técnicos de salud de plataforma (valores API permanecen en inglés). */
export const HEALTH_STATUS: Record<string, string> = {
  up: "Operativa",
  down: "No disponible",
  degraded: "Degradada",
  unknown: "Desconocido",
};

export function formatHealthStatus(status: string | undefined | null): string {
  if (!status) return "—";
  return HEALTH_STATUS[status.toLowerCase()] ?? status;
}
