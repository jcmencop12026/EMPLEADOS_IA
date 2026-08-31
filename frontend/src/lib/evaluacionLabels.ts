/** Etiquetas en español para dominio evaluación EIAAX (BP1). */

export const EVALUACION_ESTADO_LABELS: Record<string, string> = {
  BORRADOR: "Borrador",
  EN_CURSO: "En curso",
  PRELIMINAR: "Preliminar",
  DIAGNOSTICA: "Diagnóstica",
  PROFUNDA: "Profunda",
  CERRADO: "Cerrado",
};

export const EVALUACION_NIVEL_LABELS: Record<string, string> = {
  PRELIMINAR: "Preliminar",
  DIAGNOSTICA: "Diagnóstica",
  PROFUNDA: "Profunda",
};

export const TIPO_CONTENIDO_LABELS: Record<string, string> = {
  HECHO: "Hecho",
  INFERENCIA: "Inferencia",
  RECOMENDACION: "Recomendación",
  PROBLEMA_ORIGINAL: "Problema original",
  OPORTUNIDAD: "Oportunidad",
};

export const CONFIANZA_LABELS: Record<string, string> = {
  ALTA: "Alta",
  MEDIA: "Media",
  BAJA: "Baja",
};

export function labelEstadoEvaluacion(code: string): string {
  return EVALUACION_ESTADO_LABELS[code] ?? code;
}

export function labelNivelEvaluacion(code: string): string {
  return EVALUACION_NIVEL_LABELS[code] ?? code;
}

export function labelTipoContenido(code: string): string {
  return TIPO_CONTENIDO_LABELS[code] ?? code.replace(/_/g, " ").toLowerCase();
}

export function labelConfianza(code: string): string {
  return CONFIANZA_LABELS[code] ?? code;
}

export function formatPorcentaje(value: number | null | undefined): string {
  if (value == null) return "—";
  return `${value}%`;
}

export function formatConfianza(value: string | number | null | undefined): string {
  if (value == null || value === "") return "—";
  const s = String(value);
  return labelConfianza(s.toUpperCase()) !== s.toUpperCase() ? labelConfianza(s.toUpperCase()) : s;
}
