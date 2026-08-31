# 09 — Empleados IA y capacidades externas

## Empleado IA (`empleado_ia_requerimientos`)

Requerimiento estructurado para Fábrica futura:

- objetivo, responsabilidad
- entradas/salidas (JSON)
- herramientas, frecuencia, riesgo, supervisión, indicadores
- confianza

Generado solo para alternativas `EMPLEADO_IA` / `APLICAR_IA`.

## Capacidad externa (`capacidad_externa_necesidades`)

Expresa **necesidad empresarial** — no selecciona conector PIIAX.

`contrato_json` preparado para abstracción GENERAL:

```json
{
  "tipo_necesidad": "INTEGRAR",
  "integracion_futura": "capacidad_externa_abstraccion_GENERAL",
  "piiax": false
}
```

## Dimensionamiento personal (P1)

Análisis de carga/horas liberables requiere métricas — no afirmaciones sin evidencia en P0.
