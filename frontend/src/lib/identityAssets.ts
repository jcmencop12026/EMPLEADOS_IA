/** Resolución centralizada de activos de identidad por identificador. */

const ASSET_BASE = "/assets/identity";
const EXTENSIONS = [".svg", ".png", ".webp"] as const;

export type IdentityAssetId = "eiaax-hero" | "eiaax-corporativo" | "ex-08" | "ex-micro";

const resolvedCache = new Map<IdentityAssetId, string | null>();

/**
 * Devuelve la primera ruta existente para el identificador, o null si no hay activo en repo.
 * No hardcodea rutas por pantalla: todas pasan por este resolver.
 */
export async function resolveIdentityAsset(assetId: IdentityAssetId): Promise<string | null> {
  if (resolvedCache.has(assetId)) return resolvedCache.get(assetId) ?? null;
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
  return EXTENSIONS.map((ext) => `${ASSET_BASE}/${assetId}${ext}`);
}
