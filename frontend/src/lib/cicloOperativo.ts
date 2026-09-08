/** Ciclo operativo EIAAX — consola maestra (15 etapas). */

export const CICLO_ETAPAS = [
  "Conocer",
  "Evaluar",
  "Diagnosticar",
  "Detectar",
  "Valorar",
  "Decidir",
  "Presentar",
  "Contratar",
  "Implementar",
  "Operar",
  "Supervisar",
  "Medir",
  "Informar",
  "Aprender",
  "Mejorar",
] as const;

export type CicloEtapa = (typeof CICLO_ETAPAS)[number];

type CicloNavOpts = {
  expedienteId?: string;
  isDemo?: boolean;
};

/** Ruta accionable por etapa del ciclo (conserva contexto de expediente cuando aplica). */
export function cicloEtapaRuta(etapa: CicloEtapa, opts: CicloNavOpts = {}): string {
  const { expedienteId, isDemo } = opts;
  const exp = expedienteId ?? "";
  const presentacion = isDemo && exp ? `/demo/presentacion/${exp}` : exp ? `/presentacion/${exp}` : "/demo";

  if (!exp) {
    const global: Partial<Record<CicloEtapa, string>> = {
      Conocer: "/empresas",
      Evaluar: "/evaluaciones",
      Diagnosticar: "/diagnosticos",
      Detectar: "/oportunidades",
      Valorar: "/costos-valor",
      Decidir: "/comercial",
      Presentar: "/demo",
      Contratar: "/comercial",
      Implementar: "/implementacion",
      Operar: "/operaciones",
      Supervisar: "/ejecuciones",
      Medir: "/resultados",
      Informar: "/comunicaciones",
      Aprender: "/aprendizaje",
      Mejorar: "/optimizacion",
    };
    return global[etapa] ?? "/";
  }

  const porExpediente: Record<CicloEtapa, string> = {
    Conocer: `/evaluaciones/${exp}?tab=empresa`,
    Evaluar: `/evaluaciones/${exp}?tab=empresa`,
    Diagnosticar: `/evaluaciones/${exp}?tab=diagnostico`,
    Detectar: `/oportunidades?expediente=${exp}`,
    Valorar: `/evaluaciones/${exp}?tab=valor`,
    Decidir: `/evaluaciones/${exp}?tab=contrato`,
    Presentar: presentacion,
    Contratar: `/evaluaciones/${exp}?tab=contrato`,
    Implementar: `/implementacion`,
    Operar: `/operaciones?expediente=${exp}`,
    Supervisar: `/ejecuciones`,
    Medir: `/evaluaciones/${exp}?tab=resultados`,
    Informar: `/evaluaciones/${exp}?tab=informes`,
    Aprender: `/aprendizaje`,
    Mejorar: `/optimizacion`,
  };
  return porExpediente[etapa];
}

/** Regreso al Centro de Control conservando contexto de empresa. */
export function cicloRegresoCC(expedienteId?: string): string {
  return expedienteId ? `/?expediente=${expedienteId}` : "/";
}

/** Índice de etapa actual según estado del expediente (0-based). */
export function cicloEtapaIndexFromEstado(estado?: string | null): number {
  const map: Record<string, number> = {
    BORRADOR: 0,
    EN_CURSO: 1,
    PRELIMINAR: 2,
    DIAGNOSTICA: 3,
    PROFUNDA: 5,
    CERRADO: 12,
    ARCHIVADO: 14,
  };
  if (!estado) return 0;
  return map[estado] ?? 2;
}

export type CicloChipState = "done" | "current" | "next" | "pending";

export function cicloChipState(etapaIndex: number, currentIndex: number): CicloChipState {
  if (etapaIndex < currentIndex) return "done";
  if (etapaIndex === currentIndex) return "current";
  if (etapaIndex === currentIndex + 1) return "next";
  return "pending";
}
