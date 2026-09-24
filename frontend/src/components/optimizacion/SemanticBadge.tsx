type Kind = "HECHO" | "INFERENCIA" | "RECOMENDACION";

const CLASS: Record<Kind, string> = {
  HECHO: "semantic-badge hecho",
  INFERENCIA: "semantic-badge inferencia",
  RECOMENDACION: "semantic-badge recomendacion",
};

const LABEL: Record<Kind, string> = {
  HECHO: "Hecho",
  INFERENCIA: "Inferencia",
  RECOMENDACION: "Recomendación",
};

export function SemanticBadge({ kind }: { kind: Kind }) {
  return <span className={CLASS[kind]}>{LABEL[kind]}</span>;
}
