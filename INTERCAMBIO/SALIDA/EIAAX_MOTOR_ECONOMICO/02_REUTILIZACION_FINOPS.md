# 02 — Reutilización FinOps y módulos existentes

## FinOps core (950/1110) — sin duplicar

| Operación motor | Delegación FinOps |
|---|---|
| Costo REAL con consumo IA | `finops_service.registrar_consumo()` → `finops_records` |
| Valor VERIFICADO/ESTIMADO | `finops_service.registrar_valor()` → `finops_values` |
| Valor POTENCIAL | Solo `economic_value_entries` (no FinOps — no confundir con realizado) |
| Dashboard ROI entidad | `finops_service.dashboard_summary()` |
| Clasificación DIRECTO/TRANSVERSAL/PLATAFORMA | `consumption_planner_service.classify_finops_record()` |
| Agregación REAL periodo | `aggregate_real_consumption()` |
| Simulación PROYECTADO | `consumption_planner_service.simulate()` |
| Presupuesto/consumo incluido | `ConsumptionPlannerOrgConfig` + `FinOpsBudget` |

## Valoración 1210

- Naturalezas `VERIFICADO` / `ESTIMADO` / `POTENCIAL` alineadas con `RealValueNature`
- Mapeo certeza FinOps: `Real`→VERIFICADO, `Estimado`→ESTIMADO

## Sincronización idempotente

`POST /api/motor-economico/sincronizar-finops` + `backfill_costs_from_finops()` enlaza `finops_records` existentes a `economic_cost_entries` sin duplicar filas.

## Lo que NO se hizo (mandato)

- No segundo módulo FinOps paralelo
- No propuesta comercial completa (1280 intacto como módulo)
- No PIIAX
- No rediseño UX global
- No tocar BP2 de GENERAL
