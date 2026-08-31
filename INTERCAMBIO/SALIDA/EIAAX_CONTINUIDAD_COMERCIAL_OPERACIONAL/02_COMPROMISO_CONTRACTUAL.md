# 02 — Compromiso contractual

## Snapshot inmutable

`build_compromiso_contractual_snapshot` construye un JSON con:

- Referencias: `proposal_id`, `opportunity_id`, `evaluacion_id`, `contract_id`, `version_number`, `document_id`
- Bloque `contrato`: precio contratado, modalidad, condiciones, alcance contratado, indicadores comprometidos, supuestos
- Bloque `ia_consumo`: consumo incluido (desde `ia_consumo_json` de Centro de Negocios)
- Timestamp de captura

Se persiste en `ImplementacionProyecto.compromiso_contractual_json` al convertir.

## Separación referencia/snapshot

- **Referencias vivas:** IDs para navegación y joins (oportunidad, evaluación, contrato).
- **Snapshot:** Estado comercial en el momento de contratación/conversión; no se recalcula al cambiar la propuesta.

## Uso en vista continuidad

La vista B09 expone `compromiso_snapshot` y `contratado` para trazabilidad sin recalcular indicadores.
