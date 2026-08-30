/** Terminología visible en español — valores API pueden permanecer en inglés. */

export const CONTINUITY_EVENT_LABELS: Record<string, string> = {
  INTEGRACION_SALUD_RECUPERADA: "Integración recuperada",
  RESTORE_BLOQUEADO_PRIVACIDAD: "Restauración bloqueada por privacidad",
  SERVICIO_CAIDO: "Servicio caído",
  SERVICIO_DEGRADADO: "Servicio degradado",
};

export const BACKUP_STATE_LABELS: Record<string, string> = {
  PROGRAMADO: "Programado",
  EJECUTADO: "Ejecutado",
  VERIFICADO: "Verificado",
  RESTAURADO_EN_PRUEBA: "Restaurado en prueba",
};

export function formatCalcLabel(value: string | null | undefined): string {
  if (!value) return "No calculable";
  if (value === "NO CALCULABLE") return "No calculable";
  return value;
}

export function formatContinuityEvent(type: string | null | undefined): string {
  if (!type) return "—";
  return CONTINUITY_EVENT_LABELS[type] ?? type.replace(/_/g, " ");
}

export function formatBackupState(state: string | null | undefined): string {
  if (!state) return "—";
  return BACKUP_STATE_LABELS[state] ?? state.replace(/_/g, " ");
}
