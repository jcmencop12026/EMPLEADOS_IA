import { describe, expect, it } from "vitest";
import { BRAND_LEVELS, EIAAX_BRAND } from "./brand";

describe("brand", () => {
  it("define identidad central EIAAX", () => {
    expect(EIAAX_BRAND.name).toBe("EIAAX");
    expect(EIAAX_BRAND.descriptor).toContain("Procesos Empresariales");
  });

  it("soporta niveles de marca sin activos hardcodeados", () => {
    expect(BRAND_LEVELS.hero.assetId).toBe("eiaax-hero");
    expect(BRAND_LEVELS.corporativo.assetId).toBe("eiaax-corporativo");
    expect(BRAND_LEVELS.ex08.assetId).toBe("ex-08");
    expect(BRAND_LEVELS.micro.assetId).toBe("ex-micro");
  });
});
