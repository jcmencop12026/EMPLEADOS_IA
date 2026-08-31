import { describe, expect, it } from "vitest";
import {
  labelEstadoEvaluacion,
  labelNivelEvaluacion,
  labelTipoContenido,
  formatConfianza,
} from "./evaluacionLabels";

describe("evaluacionLabels", () => {
  it("traduce estados de expediente", () => {
    expect(labelEstadoEvaluacion("BORRADOR")).toBe("Borrador");
    expect(labelEstadoEvaluacion("EN_CURSO")).toBe("En curso");
  });

  it("traduce niveles", () => {
    expect(labelNivelEvaluacion("PRELIMINAR")).toBe("Preliminar");
  });

  it("traduce tipo contenido", () => {
    expect(labelTipoContenido("RECOMENDACION")).toBe("Recomendación");
  });

  it("formatea confianza conocida", () => {
    expect(formatConfianza("ALTA")).toBe("Alta");
  });
});
