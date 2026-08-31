# 05 — FinOps desde contrato (B06)

## Bridge

`backend/app/services/continuidad_finops_bridge.py`

- `ensure_budget_from_ia_consumo` — crea/vincula presupuesto FinOps operacional
- `contract_finops_summary` — resumen para vista continuidad

## Separación comercial vs operacional

| Concepto | Fuente | Destino |
|----------|--------|---------|
| Precio comercial (ingreso) | `precio_final` / contrato | Snapshot compromiso, NO FinOps cost |
| Presupuesto operacional IA | `ia_consumo_json` (`consumo_incluido_usd`, `presupuesto_operacional`) | `finops_budgets` |

Al contratar (`contract_proposal`) y al convertir, se vincula `finops_budget_id` en contrato y proyecto.

## Endpoint relacionado

`PUT /api/centro-negocios/propuestas/{id}/ia-consumo` acepta `presupuesto_operacional` y `periodicidad`.

## Brecha cerrada

**B06** — Contrato alimenta planificación económica sin segundo FinOps.
