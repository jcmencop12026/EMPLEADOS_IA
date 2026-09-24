/** Etiquetas Centro de Negocios — fuente única frontend */

export const PROPOSAL_STATUS_LABELS: Record<string, string> = {
  BORRADOR: "Borrador",
  EN_REVISION: "En revisión",
  APROBADA: "Aprobada internamente",
  ENVIADA: "Presentada",
  ACEPTADA: "Contratada",
  RECHAZADA: "Descartada",
  VENCIDA: "Suspendida",
};

export const APPROVAL_LEVEL_LABELS: Record<string, string> = {
  PREPARADOR: "Preparador",
  REVISOR: "Revisor",
  APROBADOR_COMERCIAL: "Aprobador comercial",
  AUTORIZADOR_FINAL: "Autorizador final",
};

export const PRICE_PHASE_LABELS: Record<string, string> = {
  RECOMENDADO: "Precio recomendado",
  APROBADO: "Precio aprobado",
  PRESENTADO: "Precio presentado",
  CONTRATADO: "Precio contratado",
};

export function labelProposalStatus(code: string | undefined | null): string {
  if (!code) return "—";
  return PROPOSAL_STATUS_LABELS[code] ?? code.replace(/_/g, " ");
}

export function labelApprovalLevel(code: string | undefined | null): string {
  if (!code) return "—";
  return APPROVAL_LEVEL_LABELS[code] ?? code.replace(/_/g, " ");
}
