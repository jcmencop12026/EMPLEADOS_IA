/** Mensajes neutrales cuando no hay interpretación backend suficiente. */

export const INFORMACION_INSUFICIENTE =
  "Información insuficiente para determinar esta conclusión.";

export function narrativaCampo(value: unknown): string {
  if (value === null || value === undefined) return INFORMACION_INSUFICIENTE;
  const text = String(value).trim();
  return text.length > 0 ? text : INFORMACION_INSUFICIENTE;
}

export function buildNarrativaFromInterpretacion(
  interpretacion: Record<string, unknown> | null | undefined,
  resumen: Record<string, unknown> | null | undefined,
  esDemo: boolean,
): {
  que: string;
  porQue: string;
  significa: string;
  atencion: string;
  oportunidad: string;
  valor: string;
  recomendacion: string;
} {
  const fmtVal = (v: unknown): string => {
    if (v === null || v === undefined) return INFORMACION_INSUFICIENTE;
    if (typeof v === "number") return v.toLocaleString("es-CO");
    const s = String(v).trim();
    return s || INFORMACION_INSUFICIENTE;
  };

  const demoMonto = (block: unknown): string => {
    if (!block || typeof block !== "object") return INFORMACION_INSUFICIENTE;
    const b = block as { monto?: number; etiqueta?: string };
    if (!b.monto) return INFORMACION_INSUFICIENTE;
    return `${b.etiqueta ?? ""}: $${Number(b.monto).toLocaleString("es-CO")} COP`.trim();
  };

  return {
    que: narrativaCampo(interpretacion?.que_ocurrio),
    porQue: narrativaCampo(interpretacion?.por_que),
    significa: narrativaCampo(interpretacion?.que_significa),
    atencion: narrativaCampo(interpretacion?.requiere_atencion),
    oportunidad: narrativaCampo(interpretacion?.oportunidad),
    valor: esDemo
      ? [demoMonto(resumen?.estimado), demoMonto(resumen?.potencial)]
          .filter((x) => x !== INFORMACION_INSUFICIENTE)
          .join(" · ") || INFORMACION_INSUFICIENTE
      : fmtVal(resumen?.estimado ?? resumen?.potencial),
    recomendacion: narrativaCampo(interpretacion?.recomendacion),
  };
}
