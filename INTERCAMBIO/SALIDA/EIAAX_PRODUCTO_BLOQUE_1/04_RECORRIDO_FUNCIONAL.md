# 04 — Recorrido funcional

## Flujo E2E implementado

1. **Crear entidad/evaluación** — `/evaluaciones` → Nueva evaluación (entidad, problema, objetivo, nivel).
2. **Información adaptativa** — Pestaña Información: campos según nivel con explicación, por qué, impacto en precisión.
3. **Completar parcialmente** — Guardar respuestas; % información y confianza se recalculan.
4. **Evaluación preliminar** — Resumen → Ejecutar evaluación; genera hallazgos (problema original, gaps, proyección).
5. **Hallazgo** — Pestaña Análisis EIAAX: tipo, confianza, evidencia, origen.
6. **Impacto** — Pestaña Impacto: ANTES / PROYECTADO (etiquetado) / REAL.
7. **Oportunidad** — Crear oportunidad desde hallazgo → motor 1030.
8. **Visibilidad** — Checkbox «Visible para entidad» (persistido en backend + log).
9. **Vista Entidad** — Previsualización filtrada sin notas internas ni costos.
10. **Trazabilidad** — Correlation ID, log visibilidad, historial hallazgos.

## Panel EIAAX

Acciones rápidas: información faltante, profundizar, causas, impacto, oportunidades, siguiente análisis. Sin proveedor LLM → mensaje en español, sin respuestas simuladas.
