# 03 — Propuesta inteligente

## Un solo expediente, un solo objeto

`create_proposal_from_expediente` reutiliza:

- Organización y evaluación (`evaluacion_id`)
- Oportunidad vinculada (`opportunity_id` desde link o parámetro)
- Necesidad/objetivo del expediente en perspectiva GERENCIA
- Valoración vía `import_from_valuation` cuando existe
- Trazabilidad en `traceability_json`

## Tres perspectivas — un documento

Almacenadas en `perspectivas_json` (`NegocioProposalExtension`):

| Perspectiva | Contenido |
|-------------|-----------|
| **GERENCIA** | situación, oportunidad, impacto, ROI, inversión, resultados |
| **OPERACIONES** | procesos, solución, automatización, indicadores, implementación |
| **SISTEMAS** | arquitectura, integraciones, seguridad/gobierno, continuidad |

API: `PUT /api/centro-negocios/propuestas/{id}/perspectivas`

## Documento para cliente

`documento_cliente_json` — solo campos autorizados:

- Resumen, situación, oportunidad, solución, alcance
- Inversión (precio final, no sugerido interno)
- Modalidad comercial, consumo IA, supuestos
- `economia_privada_incluida: false` siempre en vista cliente

## Documento interno

`documento_interno_json` — margen, costos, recomendación económica, riesgos.

Solo visible con permiso `negocio.economy.private` o `finops.economy.private`.
