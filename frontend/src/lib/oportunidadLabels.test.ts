import { describe, expect, it } from "vitest";
import {
  formatConfianza,
  formatPrioridad,
  labelEstadoOportunidad,
  labelPertinencia,
  labelTraceEtapa,
} from "../src/lib/oportunidadLabels";

describe("oportunidadLabels", () => {
  it("traduce estados y pertinencia", () => {
    expect(labelEstadoOportunidad("DETECTADA")).toBe("Detectada");
    expect(labelPertinencia("SOLICITAR_DATOS")).toBe("Requiere más información");
  });

  it("traduce trazas técnicas", () => {
    expect(labelTraceEtapa("OPORTUNIDAD_CREADA")).toBe("Oportunidad registrada");
    expect(labelTraceEtapa("TRANSICION_DATOS_INSUFICIENTES")).toBe("Se solicitó información adicional");
  });

  it("formatea prioridad y confianza", () => {
    expect(formatPrioridad(0.66)).toContain("Prioridad media");
    expect(formatConfianza(0.85)).toContain("Confianza alta");
  });
});
