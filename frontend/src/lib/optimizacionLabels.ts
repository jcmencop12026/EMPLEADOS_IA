/** Etiquetas, tooltips y semántica para aprendizaje, optimización y multiproveedor. */

export const TOOLTIPS: Record<string, string> = {
  aprendizaje:
    "Conocimiento derivado de comparar resultado esperado vs observado. No es un hecho verificado hasta tener evidencia.",
  repriorizacion: "Cambio de prioridad sugerido por aprendizaje. Si no hubo cambio, se muestra explícitamente.",
  recomendacion: "Sugerencia de portafolio óptimo bajo restricciones. Requiere aprobación humana.",
  correlation_id: "Identificador de trazabilidad transversal para auditar el flujo completo.",
  ejecucion_automatica: "La plataforma puede aplicar la recomendación aprobada sin intervención adicional.",
  ejecucion_humana: "Requiere confirmación externa antes de marcar como ejecutada.",
  routing: "Decisión de proveedor/modelo según políticas configuradas, no heurística opaca.",
  observabilidad: "Métricas reales de inferencias: éxitos, fallos, latencia, tokens y costo.",
  finops: "Costos reales de proveedor reutilizando FinOps existente.",
};

export const ESTADO_RECOMENDACION: Record<string, string> = {
  PROPUESTA: "Propuesta",
  APROBADA: "Aprobada",
  RECHAZADA: "Rechazada",
  REVISADA: "Revisada",
  EJECUTADA: "Ejecutada",
  FALLIDA: "Fallida",
  CANCELADA: "Cancelada",
};

export const ESTADO_EJECUCION: Record<string, string> = {
  PENDIENTE_EJECUCION_HUMANA: "Pendiente ejecución humana",
  EJECUTADA: "Ejecutada",
  FALLIDA: "Fallida",
};

export const ESTADO_CICLO: Record<string, string> = {
  ABIERTO: "Abierto",
  EVALUADO: "Evaluado",
  CERRADO: "Cerrado",
};

export const TIPO_EXPLICACION_SEMANTICA: Record<string, "HECHO" | "INFERENCIA"> = {
  CONFIRMADA: "HECHO",
  PROBABLE: "INFERENCIA",
  HIPOTESIS: "INFERENCIA",
};

export function labelEstadoRecomendacion(estado: string): string {
  return ESTADO_RECOMENDACION[estado] ?? estado;
}

export function labelEstadoEjecucion(estado?: string | null): string {
  if (!estado) return "—";
  return ESTADO_EJECUCION[estado] ?? estado;
}

export function sinCambioPrioridad(anterior?: number | null, nueva?: number | null): boolean {
  if (anterior == null && nueva == null) return true;
  if (anterior == null || nueva == null) return false;
  return Math.abs(anterior - nueva) < 0.0001;
}

export function extractCorrelationId(refs?: Record<string, unknown> | null): string | null {
  if (!refs) return null;
  const cid = refs.correlation_id ?? refs.correlationId;
  return typeof cid === "string" ? cid : null;
}

export function formatPct(value?: number | null, digits = 1): string {
  if (value == null) return "—";
  return `${value.toFixed(digits)}%`;
}

export function formatMs(value?: number | null): string {
  if (value == null) return "—";
  return `${Math.round(value)} ms`;
}
