export type SemanticType = "HECHO" | "INFERENCIA" | "RECOMENDACION" | "SIN_CLASIFICAR";

export type SemanticMeta = {
  tipo_semantico?: SemanticType | string | null;
  subtipo_semantico?: string | null;
  etiqueta_visible?: string | null;
  tooltip_semantico?: string | null;
};

const LABELS: Record<string, string> = {
  HECHO: "HECHO",
  INFERENCIA: "INFERENCIA",
  RECOMENDACION: "RECOMENDACIÓN",
  SIN_CLASIFICAR: "SIN CLASIFICAR",
};

const TOOLTIPS: Record<string, string> = {
  HECHO: "Dato u observación con evidencia o fuente trazable.",
  INFERENCIA: "Interpretación o estimación — no es un hecho verificado.",
  RECOMENDACION: "Acción sugerida — no es un resultado realizado.",
  SIN_CLASIFICAR: "Tipo semántico no determinado con seguridad.",
};

type Props = {
  tipo?: string | null;
  subtipo?: string | null;
  tooltip?: string | null;
  className?: string;
};

export function SemanticBadge({ tipo, subtipo, tooltip, className = "" }: Props) {
  const key = (tipo || "SIN_CLASIFICAR").toUpperCase();
  const label = LABELS[key] ?? LABELS.SIN_CLASIFICAR;
  const title = tooltip ?? TOOLTIPS[key] ?? TOOLTIPS.SIN_CLASIFICAR;
  const cssKey = key === "RECOMENDACION" ? "recomendacion" : key.toLowerCase();
  return (
    <span
      className={`cc-tag cc-tag-${cssKey} ${className}`.trim()}
      title={subtipo ? `${title} (${subtipo})` : title}
      aria-label={`${label}: ${title}`}
    >
      {label}
    </span>
  );
}

export function resolveSemanticTipo(
  item: SemanticMeta & { tipo_contenido?: string | null; certeza_codigo?: string | null }
): string {
  if (item.tipo_semantico) return item.tipo_semantico;
  const tc = (item.tipo_contenido || "").toUpperCase();
  if (tc === "HECHO") return "HECHO";
  if (tc === "INFERENCIA" || tc === "INTERPRETACION") return "INFERENCIA";
  if (tc === "RECOMENDACION") return "RECOMENDACION";
  return "SIN_CLASIFICAR";
}
