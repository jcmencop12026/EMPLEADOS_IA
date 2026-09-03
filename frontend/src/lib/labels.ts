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
  DRAFT: "Borrador",
  LAB: "Laboratorio",
  SHADOW: "Modo sombra",
  SUPERVISED: "Supervisado",
  AUTONOMOUS_CONTROLLED: "Autónomo controlado",
};

export const AUTONOMY_LEVEL: Record<string, string> = {
  RECOMIENDA: "Recomienda",
  PREPARA: "Prepara",
  EJECUTA_CON_APROBACION: "Ejecuta con aprobación",
  EJECUTA_DENTRO_LIMITES: "Ejecuta dentro de límites",
};

export const RISK_LEVEL: Record<string, string> = {
  LOW: "Bajo",
  MEDIUM: "Medio",
  HIGH: "Alto",
  CRITICAL: "Crítico",
};

export function label(map: Record<string, string>, value: string | undefined | null): string {
  if (!value) return "—";
  return map[value] ?? value;
}
