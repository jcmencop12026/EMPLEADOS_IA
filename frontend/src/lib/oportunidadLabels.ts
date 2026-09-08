/** Etiquetas empresariales para oportunidades — códigos API permanecen internos. */

export const ESTADO_OPORTUNIDAD: Record<string, string> = {
  DETECTADA: "Detectada",
  EN_EVALUACION: "En evaluación",
  PRIORIZADA: "Priorizada",
  PROPUESTA: "Propuesta",
  PENDIENTE_APROBACION: "Pendiente de aprobación",
  APROBADA: "Aprobada",
  EN_EJECUCION: "En ejecución",
  EN_SEGUIMIENTO: "En seguimiento",
  MATERIALIZADA: "Materializada",
  CERRADA: "Cerrada",
  DESCARTADA: "Descartada",
  CANCELADA: "Cancelada",
  FALLIDA: "Fallida",
  DATOS_INSUFICIENTES: "Datos insuficientes",
  NO_PERTINENTE: "No pertinente",
  SIN_CAPACIDAD: "Sin capacidad",
  POSPUESTA: "Pospuesta",
};

export const PERTINENCIA_OPORTUNIDAD: Record<string, string> = {
  ALTA: "Alta pertinencia",
  MEDIA: "Pertinencia media",
  BAJA: "Baja pertinencia",
  SOLICITAR_DATOS: "Requiere más información",
  NO_PERTINENTE: "No pertinente",
};

export const TIPO_OPORTUNIDAD: Record<string, string> = {
  RIESGO: "Riesgo operativo",
  AHORRO: "Ahorro",
  INGRESO: "Ingreso",
  PRODUCTIVIDAD: "Productividad",
  CUMPLIMIENTO: "Cumplimiento",
  CALIDAD: "Calidad",
  OPORTUNIDAD_COMERCIAL: "Oportunidad comercial",
};

export const MOMENTO_OPORTUNIDAD: Record<string, string> = {
  INMEDIATO: "Inmediato",
  CORTO_PLAZO: "Corto plazo",
  MEDIO_PLAZO: "Medio plazo",
  LARGO_PLAZO: "Largo plazo",
};

export const RESULTADO_OPORTUNIDAD: Record<string, string> = {
  EXITO: "Éxito",
  PARCIAL: "Parcial",
  FALLO: "Fallo",
};

export const VALOR_CERTIDUMBRE: Record<string, string> = {
  VERIFICADO: "Verificado",
  ESTIMADO: "Estimado",
  POTENCIAL: "Potencial",
  SIMULADO: "Simulado (demo)",
};

export const VALUATION_STATUS: Record<string, string> = {
  BORRADOR: "Borrador",
  VALIDADA: "Validada",
  CERRADA: "Cerrada",
};

export const VALUE_NATURE: Record<string, string> = {
  VERIFICADO: "Verificado",
  ESTIMADA: "Estimado",
  POTENCIAL: "Potencial",
};

export const SCENARIO_TYPE: Record<string, string> = {
  CONSERVADOR: "Conservador",
  BASE: "Base",
  OPTIMISTA: "Optimista",
};

export const TRACE_ETAPA: Record<string, string> = {
  SENAL_CREADA: "Señal detectada",
  OPORTUNIDAD_CREADA: "Oportunidad registrada",
  TRANSICION_DATOS_INSUFICIENTES: "Se solicitó información adicional",
  EVALUACION: "Evaluación",
  PRIORIZACION: "Priorización",
  APROBACION: "Aprobación",
  ACTIVACION: "Activación",
  EJECUCION: "Ejecución",
  MATERIALIZACION: "Materialización",
};

export function labelOportunidad(map: Record<string, string>, value: string | undefined | null): string {
  if (!value) return "—";
  return map[value] ?? value.replace(/_/g, " ").toLowerCase().replace(/^\w/, (c) => c.toUpperCase());
}

export function labelEstadoOportunidad(estado: string | undefined | null): string {
  return labelOportunidad(ESTADO_OPORTUNIDAD, estado);
}

export function labelPertinencia(v: string | undefined | null): string {
  return labelOportunidad(PERTINENCIA_OPORTUNIDAD, v);
}

export function labelTipoOportunidad(v: string | undefined | null): string {
  return labelOportunidad(TIPO_OPORTUNIDAD, v);
}

export function labelMomento(v: string | undefined | null): string {
  return labelOportunidad(MOMENTO_OPORTUNIDAD, v);
}

export function labelTraceEtapa(v: string | undefined | null): string {
  return labelOportunidad(TRACE_ETAPA, v);
}

export function formatPrioridad(score: number | null | undefined): string {
  if (score == null || Number.isNaN(score)) return "—";
  const n = Number(score);
  if (n >= 0.75) return `${n.toFixed(2)} — Prioridad alta`;
  if (n >= 0.5) return `${n.toFixed(2)} — Prioridad media`;
  if (n >= 0.25) return `${n.toFixed(2)} — Prioridad moderada`;
  return `${n.toFixed(2)} — Prioridad baja`;
}

export function formatConfianza(score: number | null | undefined): string {
  if (score == null || Number.isNaN(score)) return "—";
  const n = Number(score);
  const pct = Math.round(n * 100);
  if (pct >= 85) return `${pct}% — Confianza alta`;
  if (pct >= 65) return `${pct}% — Confianza media`;
  if (pct >= 40) return `${pct}% — Confianza limitada`;
  return `${pct}% — Confianza baja`;
}

export function formatTraceDetalle(detalle: unknown): string {
  if (detalle == null) return "—";
  if (typeof detalle === "string") return detalle;
  if (typeof detalle !== "object") return String(detalle);
  const labels: Record<string, string> = {
    motivo: "Motivo",
    estado: "Estado",
    pertinencia: "Pertinencia",
    tipo_oportunidad: "Tipo",
    confianza: "Confianza",
    valor_potencial: "Valor potencial",
    expediente_id: "Expediente",
    hallazgo_id: "Hallazgo",
  };
  return Object.entries(detalle as Record<string, unknown>)
    .filter(([, v]) => v != null && v !== "")
    .map(([k, v]) => {
      const lbl = labels[k] ?? k.replace(/_/g, " ");
      const val = typeof v === "string" && PERTINENCIA_OPORTUNIDAD[v]
        ? labelPertinencia(v)
        : typeof v === "string" && ESTADO_OPORTUNIDAD[v]
          ? labelEstadoOportunidad(v)
          : typeof v === "string" && TIPO_OPORTUNIDAD[v]
            ? labelTipoOportunidad(v)
            : String(v);
      return `${lbl}: ${val}`;
    })
    .join(" · ") || "—";
}

export function formatValorConCertidumbre(
  monto: number | null | undefined,
  certidumbre: string | undefined | null,
  formatMoney: (v: number | null | undefined) => string,
): string {
  const base = formatMoney(monto);
  if (!certidumbre) return base;
  const cert = labelOportunidad(VALOR_CERTIDUMBRE, certidumbre);
  return `${base} (${cert})`;
}
