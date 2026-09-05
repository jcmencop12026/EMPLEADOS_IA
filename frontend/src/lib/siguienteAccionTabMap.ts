/** Mapa único pestaña «siguiente acción» → tab cabina (CC + EvaluacionConsolePage). */

export const SIGUIENTE_ACCION_TAB_MAP: Record<string, string> = {
  resumen: "empresa",
  empresa: "empresa",
  informacion: "diagnostico",
  diagnostico: "diagnostico",
  analisis: "diagnostico",
  impacto: "valor",
  valor: "valor",
  oportunidades: "resultados",
  resultados: "resultados",
  solucion: "solucion",
  informes: "informes",
  contrato: "contrato",
  operacion: "operacion",
  consumo: "consumo",
  "vista-empresa": "vista-empresa",
};

export const CABINA_TAB_LABELS_ES: Record<string, string> = {
  empresa: "Empresa",
  diagnostico: "Diagnóstico",
  solucion: "Solución IA",
  operacion: "Operación",
  consumo: "Consumo",
  valor: "Valor",
  resultados: "Resultados",
  informes: "Informes",
  contrato: "Contrato",
  "vista-empresa": "Vista Empresa",
};

export function mapSiguienteAccionToCabinaTab(pestaña: string): string | undefined {
  const key = pestaña.trim().toLowerCase();
  return SIGUIENTE_ACCION_TAB_MAP[key];
}

export function cabinaTabPath(expedienteId: string, tab: string): string {
  return `/evaluaciones/${expedienteId}?tab=${encodeURIComponent(tab)}`;
}

export function labelCabinaTab(pestaña: string): string {
  const mapped = mapSiguienteAccionToCabinaTab(pestaña);
  if (mapped && CABINA_TAB_LABELS_ES[mapped]) return CABINA_TAB_LABELS_ES[mapped];
  return pestaña.replace(/_/g, " ");
}
