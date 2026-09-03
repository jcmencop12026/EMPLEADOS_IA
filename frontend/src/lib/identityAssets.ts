/** Resolución centralizada de activos de identidad por identificador. */

const ASSET_BASE = "/assets/identity";
const EXTENSIONS = [".svg", ".png", ".webp"] as const;

export type IdentityAssetId = "eiaax-hero" | "eiaax-corporativo" | "ex-08" | "ex-micro";

/** Activos versionados en repo — ruta directa sin HEAD async (evita fallback en Windows). */
const BUNDLED_ASSETS: Partial<Record<IdentityAssetId, string>> = {
  "eiaax-hero": `${ASSET_BASE}/eiaax-hero.svg`,
  "eiaax-corporativo": `${ASSET_BASE}/eiaax-corporativo.svg`,
  "ex-08": `${ASSET_BASE}/ex-08.svg`,
};

export function getBundledIdentityAsset(assetId: IdentityAssetId): string | null {
  return BUNDLED_ASSETS[assetId] ?? null;
}

const resolvedCache = new Map<IdentityAssetId, string | null>();

/**
 * Devuelve la primera ruta existente para el identificador, o null si no hay activo en repo.
 */
export async function resolveIdentityAsset(assetId: IdentityAssetId): Promise<string | null> {
  if (resolvedCache.has(assetId)) return resolvedCache.get(assetId) ?? null;
  const bundled = BUNDLED_ASSETS[assetId];
  if (bundled) {
    resolvedCache.set(assetId, bundled);
    return bundled;
  }
  for (const ext of EXTENSIONS) {
    const url = `${ASSET_BASE}/${assetId}${ext}`;
    try {
      const res = await fetch(url, { method: "HEAD" });
      if (res.ok) {
        resolvedCache.set(assetId, url);
        return url;
      }
    } catch {
      /* sin activo */
    }
  }
  resolvedCache.set(assetId, null);
  return null;
}

/** Rutas candidatas sincrónicas (para precarga o SSR futuro). */
export function identityAssetCandidates(assetId: IdentityAssetId): string[] {
  const bundled = BUNDLED_ASSETS[assetId];
  if (bundled) return [bundled];
  return EXTENSIONS.map((ext) => `${ASSET_BASE}/${assetId}${ext}`);
}
