/** Etiquetas y ayudas visibles en español — cadena comercial 1280/1310/1320/1340 */

export const TOOLTIPS = {
  roi: "Retorno sobre la inversión: beneficio neto dividido por el precio pagado.",
  payback: "Meses estimados para recuperar la inversión con el valor atribuible anual.",
  tco: "Costo total de propiedad: licencia, implementación, operación, IA, integraciones y soporte.",
  valorVerificado: "Valor con evidencia medible o documentada (HECHO).",
  valorEstimado: "Proyección sustentada con supuestos explícitos (INFERENCIA).",
  valorPotencial: "Oportunidad aún no materializada; no se suma al valor realizado ni al precio sugerido.",
  iaAdministrada: "Consumo IA gestionado por EMPLEADOS IA con costo proveedor trazable.",
  credencialesPropias: "La institución usa sus propias credenciales de proveedor IA.",
  sobreconsumo: "Uso de IA por encima del cupo incluido en el plan; puede generar cargo adicional o bloqueo.",
  precioSugerido: "Calculado solo con valor VERIFICADO + ESTIMADO atribuible; el POTENCIAL queda excluido.",
} as const;

export const VALUE_CATEGORY_LABELS: Record<string, string> = {
  AHORRO: "Ahorro",
  PERDIDA_EVITADA: "Pérdida evitada",
  INGRESO_RECUPERADO: "Ingreso recuperado",
  PRODUCTIVIDAD_LIBERADA: "Productividad liberada",
  REDUCCION_ERRORES: "Reducción de errores",
  REDUCCION_TIEMPOS: "Reducción de tiempos",
  MITIGACION_RIESGO: "Riesgo mitigado",
  NUEVO_INGRESO: "Nuevo ingreso",
  OPORTUNIDAD_CAPTURADA: "Oportunidad capturada",
};

export const TCO_CATEGORY_LABELS: Record<string, string> = {
  LICENCIAS: "Licencia",
  IMPLEMENTACION: "Implementación",
  OPERACION: "Operación",
  IA: "IA",
  CONSUMO_IA: "Consumo IA",
  INTEGRACIONES: "Integraciones",
  SOPORTE: "Soporte",
  INFRAESTRUCTURA: "Infraestructura",
  CONFIGURACION: "Configuración",
};

export const IMPL_CYCLE_STEPS = [
  { key: "diagnostico", label: "Diagnóstico" },
  { key: "configuracion", label: "Configuración" },
  { key: "implementacion", label: "Implementación" },
  { key: "adopcion", label: "Adopción" },
  { key: "medicion", label: "Medición" },
  { key: "resultado", label: "Resultado" },
  { key: "seguimiento", label: "Seguimiento" },
] as const;

export function formatMoney(value: number | null | undefined, currency = "USD"): string {
  if (value == null || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("es-CO", { style: "currency", currency, maximumFractionDigits: 0 }).format(value);
}

export function formatNumber(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("es-CO").format(value);
}

export function formatPct(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${value.toFixed(1)}%`;
}

export function credentialModeLabel(mode: string | undefined): string {
  if (mode === "CREDENCIALES_PROPIAS") return "Credenciales propias de la institución";
  return "IA administrada por nosotros";
}

export type NatureBreakdown = {
  valor_verificado_atribuible?: number;
  valor_estimado_atribuible?: number;
  valor_potencial_atribuible?: number;
  valor_atribuible_precio?: number;
  valor_atribuible_para_precio?: number;
};

export function extractNatureBreakdown(source: Record<string, unknown> | undefined): NatureBreakdown {
  const d = (source?.desglose_naturaleza ?? source) as NatureBreakdown | undefined;
  return d ?? {};
}
