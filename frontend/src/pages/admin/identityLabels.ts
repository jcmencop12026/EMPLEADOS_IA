export const USER_STATUS_LABEL: Record<string, string> = {
  ACTIVE: "Activo",
  INACTIVE: "Inactivo",
  BLOCKED: "Bloqueado",
};

export const MFA_MODE_LABEL: Record<string, string> = {
  DESACTIVADO: "Desactivado",
  OPCIONAL: "Opcional",
  OBLIGATORIO: "Obligatorio",
};

export const IDENTITY_SOURCE_LABEL: Record<string, string> = {
  LOCAL: "Local",
  SSO: "SSO / IdP",
};

export const PROVISION_STATUS_LABEL: Record<string, string> = {
  MANUAL: "Manual (sin SCIM)",
  PROVISIONADO: "Provisionado",
  ACTIVO: "Activo (SCIM)",
  SUSPENDIDO: "Suspendido",
  DESACTIVADO: "Desactivado (SCIM)",
};

export const SCIM_RATE_LIMIT_NOTE =
  "P2 conocido: límite de tasa SCIM en memoria (120 solicitudes/minuto por token). " +
  "Limitación administrativa documentada; no impide el aprovisionamiento habitual.";

export function formatTs(value: string | null | undefined): string {
  if (!value) return "—";
  return new Date(value).toLocaleString("es");
}

export function sanitizeAuditDetail(detail: string | null | undefined): string {
  if (!detail) return "—";
  return detail
    .replace(/token[=:]\s*[^\s,}]+/gi, "token=[oculto]")
    .replace(/password[=:]\s*[^\s,}]+/gi, "password=[oculto]")
    .slice(0, 240);
}
