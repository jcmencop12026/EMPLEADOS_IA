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
