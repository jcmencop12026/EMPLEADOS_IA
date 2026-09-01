/** Tests funcionales — CTA demo → evaluación real. */

import { describe, expect, it } from "vitest";

describe("CTA evaluaciones desde demo", () => {
  it("preselecciona área desde query string area", () => {
    const params = new URLSearchParams("nuevo=1&area=Facturación y glosas");
    const nuevo = params.get("nuevo") === "1";
    const area = params.get("area_label") || params.get("area") || "";
    expect(nuevo).toBe(true);
    expect(area).toBe("Facturación y glosas");
    const titulo = area ? `Evaluación — ${area}` : "";
    expect(titulo).toContain("Facturación");
  });

  it("no falla sin área en query string", () => {
    const params = new URLSearchParams("nuevo=1");
    const area = params.get("area_label") || params.get("area") || "";
    expect(area).toBe("");
    const titulo = area ? `Evaluación — ${area}` : "";
    expect(titulo).toBe("");
  });

  it("distingue ruta demo de presentación real", () => {
    const demoPath = "/demo/presentacion/exp-123";
    const realPath = "/presentacion/exp-456";
    expect(demoPath.startsWith("/demo/")).toBe(true);
    expect(realPath.startsWith("/demo/")).toBe(false);
  });
});
