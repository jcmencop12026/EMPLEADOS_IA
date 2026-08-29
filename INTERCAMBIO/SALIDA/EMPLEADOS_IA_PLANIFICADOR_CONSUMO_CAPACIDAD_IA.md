# EMPLEADOS IA — Planificador de Consumo y Capacidad IA (MB-07)

**Rama:** `cursor/mb-07-planificador-consumo-capacidad`  
**MB:** MB-07  
**Base portable:** `cursor/auditor-integracion-mi-trabajo` → Alembic `1400a1b2c3d4e`  
**HEAD Alembic:** `1507a1b2c3d4e`

## Objetivo

Extender FinOps existente (sin segundo FinOps) con planificación de consumo, capacidad, presupuesto, simulación y comparación multiproveedor, distinguiendo siempre ESTIMADO / REAL / PROYECTADO y clasificación DIRECTO / TRANSVERSAL_ATRIBUIBLE / PLATAFORMA.

## Arquitectura

```
FinOps (existente)          Planificador MB-07 (extensión)
├── FinOpsRecord            ├── ConsumptionPlannerOrgConfig
├── FinOpsRate (catálogo)   ├── ConsumptionPlannerTransversal
├── FinOpsBudget            ├── ConsumptionPlannerSimulation
├── FinOpsValueRecord       └── consumption_planner_service
└── LlmInferenceLog              ├── classify / aggregate REAL
                                 ├── estimate DIRECTO / TRANSVERSAL
                                 ├── simulate (PROYECTADO)
                                 ├── compare_providers
                                 ├── presupuesto / capacidad / margen
                                 └── centro_control_contract (solo contrato)
```

**API:** rutas bajo `/api/finops/planner/*` en router FinOps existente.  
**Frontend:** pestañas en `/costos-valor` (`CostosValorPage`) — Resumen, Consumos, Capacidad, Simulador, Presupuesto, Comparación.  
**Centro de Control:** NO modificado; contrato resumido vía `GET /api/finops/planner/contrato-centro-control`.

## Modelo económico

| Clasificación | Descripción |
|---------------|-------------|
| DIRECTO | Consumo de Empleados IA de la organización |
| TRANSVERSAL_ATRIBUIBLE | Capacidades transversales atribuidas (Auditor, Oportunidades, etc.) |
| PLATAFORMA | Consumo no atribuible exclusivamente (`platform:*`, ops globales) |

**Determinístico:** `is_deterministic` o ref `transversal:auditor*` → costo LLM = 0; solo infra/CPU/almacenamiento.  
**POTENCIAL:** excluido de `realized_value_sum` (no ROI/payback realizado).  
**Credenciales:** `IA_ADMINISTRADA` vs `CREDENCIALES_PROPIAS` (costo API puede ser COSTO_DEL_CLIENTE).

## Fórmulas (estimación)

- Ejecuciones mensuales directas: `activos × ejec/día × días`
- Tokens: `ejecuciones × tokens_in/out_avg`
- Costo IA ponderado: suma sobre distribución de modelos (pct debe sumar 100%) × tarifas `FinOpsRate`
- Transversal mensual: `executions_per_period × 30 / period_days`; LLM=0 si determinístico
- Proyectado total: directo + transversal + plataforma (param)
- Sobreconsumo: `max(0, proyectado - consumo_incluido)`
- Margen bruto: `precio_cliente - costo_total` (permiso `finops.margin.view`)

Precios **no hardcodeados** — catálogo `FinOpsRate` versionado por org.

## Persistencia

| Tabla | revision |
|-------|----------|
| `consumption_planner_org_configs` | `1507a1b2c3d4e` |
| `consumption_planner_transversal` | |
| `consumption_planner_simulations` | |

`down_revision`: `1400a1b2c3d4e` (Auditor MVP portable).

## APIs

| Método | Ruta | Permiso |
|--------|------|---------|
| GET | `/api/finops/planner/resumen` | finops.view |
| GET/PATCH | `/api/finops/planner/config` | view / finops.planner.configure |
| POST | `/api/finops/planner/simular` | finops.planner.simulate |
| GET | `/api/finops/planner/capacidad` | finops.view |
| GET | `/api/finops/planner/presupuesto` | finops.view |
| POST | `/api/finops/planner/comparar` | finops.view |
| GET | `/api/finops/planner/empleado/{id}` | finops.view |
| GET/PATCH | `/api/finops/planner/transversal` | view / configure |
| GET | `/api/finops/planner/margen` | finops.margin.view |
| GET | `/api/finops/planner/contrato-centro-control` | finops.view |
| GET | `/api/finops/planner/alertas` | finops.view |

Multiempresa: `organization_id` solo vía `resolve_organization_id` (superadmin + `platform.organization.view`).

## Seguridad

- RBAC: `finops.planner.simulate`, `finops.planner.configure`, `finops.margin.view`
- Viewer: ve consumo, no simula ni margen
- Sin exposición de secretos/API keys
- Auditoría: `consumption_planner.config.updated`, `consumption_planner.transversal.updated`

## Tests

`tests/test_consumption_planner_mb07.py` — 22 casos: clasificación, determinístico LLM=0, estimado/real/proyectado, distribución 100%, simulador 25×20×30=15000, presupuesto, capacidad, comparación, empleado, transversal, margen, POTENCIAL, credenciales, multiempresa, RBAC, contrato CC.

Regresión focal: auditor MVP + integración Mi Trabajo + migration_control.

## Commits portables (receta)

1. Rama desde `cursor/auditor-integracion-mi-trabajo` (o HEAD con `1400a1b2c3d4e`).
2. Aplicar archivos:
   - `backend/app/consumption_planner_models.py`
   - `backend/app/services/consumption_planner_service.py`
   - `backend/app/schemas_consumption_planner.py`
   - `backend/app/routers/finops.py` (extensión planner)
   - `backend/app/permissions.py`
   - `backend/app/main.py`
   - `backend/alembic/versions/1507a1b2c3d4e_consumption_planner_mb07.py`
   - `backend/alembic/migration_ledger.json`
   - `backend/scripts/schema_repair.py`
   - `tests/conftest.py`
   - `tests/test_consumption_planner_mb07.py`
   - `frontend/src/api.ts`
   - `frontend/src/pages/CostosValorPage.tsx`
3. `alembic upgrade head` → `1507a1b2c3d4e`
4. `pytest tests/test_consumption_planner_mb07.py`
5. `npm run build` en frontend

**NO tocar:** `main`, V1, `cursor/fase2-central-integracion`, Centro de Control UI.

## Veredicto

APTO PARA PORTAR — extensión FinOps coherente, tests PASS, frontend build PASS, una cabeza Alembic.
