export function labelEstadoEvaluacion(estado: string): string {
  const map: Record<string, string> = {
    BORRADOR: "Borrador",
    EN_CURSO: "En curso",
    PRELIMINAR: "Preliminar",
    DIAGNOSTICA: "Diagnóstica",
    PROFUNDA: "Profunda",
    CERRADO: "Cerrado",
    ARCHIVADO: "Archivado",
  };
  return map[estado] ?? estado;
}

export function labelNivelEvaluacion(nivel: string): string {
  const map: Record<string, string> = {
    PRELIMINAR: "Preliminar",
    DIAGNOSTICA: "Diagnóstica",
    PROFUNDA: "Profunda",
  };
  return map[nivel] ?? nivel;
}

export function labelConfianza(c: string | undefined): string {
  const map: Record<string, string> = { ALTA: "Alta", MEDIA: "Media", BAJA: "Baja" };
  return map[c ?? ""] ?? (c || "—");
}

export function labelTipoContenido(t: string): string {
  const map: Record<string, string> = {
    HECHO: "Hecho",
    INFERENCIA: "Inferencia",
    PROYECCION: "Proyección",
    RECOMENDACION: "Recomendación",
  };
  return map[t] ?? t;
}

export function labelEstadoPublicacion(e: string): string {
  const map: Record<string, string> = {
    PRIVADO: "Privado",
    PREPARADO_PRESENTAR: "Preparado para presentar",
    PUBLICADO_EMPRESA: "Publicado a empresa",
  };
  return map[e] ?? e;
}

export function labelEstadoRelacion(e: string): string {
  const map: Record<string, string> = {
    PROSPECTO_EVALUACION: "Prospecto en evaluación",
    PROSPECTO_RESULTADOS: "Prospecto con resultados",
    CLIENTE_CONTRATADO: "Cliente contratado",
  };
  return map[e] ?? e;
}
