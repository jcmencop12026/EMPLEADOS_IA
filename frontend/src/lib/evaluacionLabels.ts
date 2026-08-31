/** Etiquetas en español — evaluación EIAAX Bloque 2 */

export const ESTADO_EXPEDIENTE: Record<string, string> = {
  BORRADOR: "Borrador",
  EN_CURSO: "En curso",
  PRELIMINAR: "Preliminar",
  DIAGNOSTICA: "Diagnóstica",
  PROFUNDA: "Profunda",
  CERRADO: "Cerrado",
  ARCHIVADO: "Archivado",
};

export const NIVEL_EVALUACION: Record<string, string> = {
  PRELIMINAR: "Preliminar",
  DIAGNOSTICA: "Diagnóstica",
  PROFUNDA: "Profunda",
};

export const CONFIANZA: Record<string, string> = {
  ALTA: "Alta",
  MEDIA: "Media",
  BAJA: "Baja",
};

export const TIPO_CONTENIDO: Record<string, string> = {
  HECHO: "Hecho verificado",
  INFERENCIA: "Inferencia",
  PROYECCION: "Proyección",
  RECOMENDACION: "Recomendación",
};

export const ESTADO_ACCION: Record<string, string> = {
  BORRADOR: "Borrador",
  PENDIENTE_APROBACION: "Pendiente de aprobación",
  APROBADA: "Aprobada",
  RECHAZADA: "Rechazada",
  SOLICITADA: "Solicitada a PIIAX",
  EN_PROCESO: "En proceso",
  PIIAX_NO_DISPONIBLE: "PIIAX no disponible",
  COMPLETADA: "Completada",
  ERROR: "Error",
  CANCELADA: "Cancelada",
};

export const TIPO_ACCION: Record<string, string> = {
  LECTURA: "Lectura",
  ANALISIS: "Análisis",
  PROPUESTA: "Propuesta",
  EJECUCION: "Ejecución",
};

export const INTENCION_AGENTE: Record<string, string> = {
  A: "Respuesta con información existente",
  B: "Requiere información adicional",
  C: "Requiere análisis IA",
  D: "Requiere consulta externa",
  E: "Requiere acción externa",
  F: "Requiere aprobación humana",
};

export function label(map: Record<string, string>, code: string): string {
  return map[code] ?? code.replace(/_/g, " ").toLowerCase();
}
