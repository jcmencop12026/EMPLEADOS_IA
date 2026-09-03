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

/** Estados de capacidad externa (contrato UX español) */
export const ESTADO_CAPACIDAD_ES: Record<string, string> = {
  "NO DISPONIBLE": "No disponible",
  DISPONIBLE: "Disponible",
  PENDIENTE: "Pendiente",
  "EN COLA": "En cola",
  EJECUTANDO: "Ejecutando",
  "ESPERANDO APROBACION": "Esperando aprobación",
  COMPLETADO: "Completado",
  FALLIDO: "Fallido",
  CANCELADO: "Cancelado",
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
  G: "Puede convertirse en oportunidad",
  H: "Puede convertirse en tarea/seguimiento",
};

export function label(map: Record<string, string>, code: string): string {
  return map[code] ?? code.replace(/_/g, " ").toLowerCase();
}

export function labelEstadoCapacidad(estadoEs?: string, estadoInterno?: string): string {
  if (estadoEs) return ESTADO_CAPACIDAD_ES[estadoEs] ?? estadoEs;
  return label(ESTADO_ACCION, estadoInterno ?? "");
}

export function labelEstadoEvaluacion(estado: string): string {
  return label(ESTADO_EXPEDIENTE, estado);
}

export function labelNivelEvaluacion(nivel: string): string {
  return label(NIVEL_EVALUACION, nivel);
}

export function labelConfianza(c: string | undefined): string {
  return label(CONFIANZA, c ?? "");
}

export function labelTipoContenido(t: string): string {
  return label(TIPO_CONTENIDO, t);
}

export function labelEstadoPublicacion(e: string): string {
  const map: Record<string, string> = {
    PRIVADO: "Privado",
    PREPARADO_PRESENTAR: "Preparado para presentar",
    PUBLICADO_EMPRESA: "Publicado a empresa",
  };
  return map[e] ?? e;
}

export function labelEstadoRelacion(estado: string): string {
  const map: Record<string, string> = {
    PROSPECTO_EVALUACION: "Prospecto en evaluación",
    PROSPECTO: "Prospecto",
    CLIENTE: "Cliente",
    CLIENTE_ACTIVO: "Cliente activo",
  };
  return map[estado] ?? estado.replace(/_/g, " ").toLowerCase();
}
