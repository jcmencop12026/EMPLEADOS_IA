/** Identidad central EIAAX — tokens y niveles de marca */

export const EIAAX_BRAND = {
  name: "EIAAX",
  descriptor: "Ecosistema Inteligente de Procesos Empresariales",
  productLine: "EMPLEADOS IA",
  title: "EIAAX — Ecosistema Inteligente de Procesos Empresariales",
  acronym: "EIAAX",
  compactMark: "EX",
} as const;

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
