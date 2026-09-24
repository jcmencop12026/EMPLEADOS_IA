export const INTEGRATION_STATUS_LABELS: Record<string, string> = {
  BORRADOR: "Borrador",
  CONFIGURANDO: "Configurando",
  VALIDANDO: "Validando",
  ACTIVO: "Activo",
  DEGRADADO: "Degradado",
  ERROR: "Error",
  INACTIVO: "Inactivo",
};

export const INTEGRATION_TYPE_LABELS: Record<string, string> = {
  API_REST: "API REST",
  BASE_DATOS: "Base de datos",
  ARCHIVO: "Archivo",
  SFTP: "SFTP",
  WEBHOOK: "Webhook",
  CORREO: "Correo",
  EVENTO: "Evento",
};

export const POLICY_DECISION_LABELS: Record<string, string> = {
  PERMITIDO: "Permitido",
  DENEGADO: "Denegado",
  PERMITIDO_CON_TRANSFORMACIÓN: "Permitido con transformación",
  PROHIBIDO: "Prohibido",
};

export const EVENT_HIGHLIGHT_TYPES = [
  "INTEGRACION_SALUD_RECUPERADA",
  "RESTORE_BLOQUEADO_PRIVACIDAD",
  "SERVICIO_CAIDO",
  "SERVICIO_DEGRADADO",
];

export const WIRING_STAGE_LABELS: Record<string, string> = {
  preflight: "Validación previa",
  identidad: "Identidad",
  catalogo: "Catálogo",
  politica: "Política",
  gobierno: "Gobierno",
  ejecucion: "Ejecución",
  linaje: "Linaje",
  auditoria: "Auditoría",
  continuidad: "Continuidad",
};

export function formatTs(value: string | null | undefined): string {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString("es-CO");
  } catch {
    return value;
  }
}

export function sanitizeDetail(text: string | null | undefined): string {
  if (!text) return "—";
  return text.replace(/(password|token|api[_-]?key|secret|bearer)\s*[:=]\s*[^\s,}]+/gi, "$1=[OCULTO]");
}
