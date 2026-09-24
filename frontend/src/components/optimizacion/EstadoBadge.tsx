import { labelEstadoEjecucion, labelEstadoRecomendacion } from "../../lib/optimizacionLabels";

type Props = { estado: string; tipo?: "recomendacion" | "ejecucion" };

const CLASS_MAP: Record<string, string> = {
  PROPUESTA: "estado-badge propuesta",
  APROBADA: "estado-badge aprobada",
  EJECUTADA: "estado-badge ejecutada",
  FALLIDA: "estado-badge fallida",
  PENDIENTE_EJECUCION_HUMANA: "estado-badge pendiente",
  RECHAZADA: "estado-badge rechazada",
  CANCELADA: "estado-badge cancelada",
  ABIERTO: "estado-badge propuesta",
  EVALUADO: "estado-badge aprobada",
  CERRADO: "estado-badge ejecutada",
};

export function EstadoBadge({ estado, tipo = "recomendacion" }: Props) {
  const label = tipo === "ejecucion" ? labelEstadoEjecucion(estado) : labelEstadoRecomendacion(estado);
  const cls = CLASS_MAP[estado] ?? "estado-badge";
  return <span className={cls}>{label}</span>;
}
