/** Identidad central EIAAX — tokens y niveles de marca */

export const EIAAX_BRAND = {
  name: "EIAAX",
  descriptor: "Ecosistema Inteligente de Procesos Empresariales",
  /** Línea de producto visible en shell interno (no en login). */
  productLine: "Plataforma EIAAX",
  loginTagline: "Acceso seguro a su ecosistema de procesos inteligentes",
  title: "EIAAX — Ecosistema Inteligente de Procesos Empresariales",
  acronym: "EIAAX",
  compactMark: "EX",
  platformAttribution: "Impulsado por EIAAX",
} as const;

export type EnterpriseVisualIdentity = {
  displayName: string;
  logoUrl?: string | null;
  logoCompactUrl?: string | null;
  accentColor?: string | null;
};

export const DEFAULT_ENTERPRISE_IDENTITY: EnterpriseVisualIdentity = {
  displayName: "",
  logoUrl: null,
  logoCompactUrl: null,
  accentColor: "#1d4ed8",
};

/** Niveles de marca soportados (sin fabricar activos gráficos). */
export type BrandLevel = "hero" | "corporativo" | "ex08" | "micro";

export const BRAND_LEVELS: Record<
  BrandLevel,
  { assetId: string; label: string; showDescriptor: boolean }
> = {
  hero: { assetId: "eiaax-hero", label: EIAAX_BRAND.name, showDescriptor: true },
  corporativo: { assetId: "eiaax-corporativo", label: EIAAX_BRAND.name, showDescriptor: true },
  ex08: { assetId: "ex-08", label: EIAAX_BRAND.acronym, showDescriptor: false },
  micro: { assetId: "ex-micro", label: EIAAX_BRAND.compactMark, showDescriptor: false },
};
