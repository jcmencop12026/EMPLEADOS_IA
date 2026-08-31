import { describe, expect, it, vi } from "vitest";
import { identityAssetCandidates } from "./identityAssets";

describe("identityAssets", () => {
  it("genera rutas candidatas por identificador", () => {
    const paths = identityAssetCandidates("eiaax-corporativo");
    expect(paths).toEqual([
      "/assets/identity/eiaax-corporativo.svg",
      "/assets/identity/eiaax-corporativo.png",
      "/assets/identity/eiaax-corporativo.webp",
    ]);
  });

  it("resolveIdentityAsset devuelve null sin fetch real en test", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false }));
    const { resolveIdentityAsset } = await import("./identityAssets");
    const url = await resolveIdentityAsset("ex-08");
    expect(url).toBeNull();
    vi.unstubAllGlobals();
  });
});
