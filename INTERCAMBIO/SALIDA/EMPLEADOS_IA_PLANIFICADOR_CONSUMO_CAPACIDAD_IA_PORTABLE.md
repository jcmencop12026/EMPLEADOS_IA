# EMPLEADOS IA — Planificador MB-07 Portable (desacoplado)

## Origen y base

| Campo | Valor |
|-------|--------|
| **Fuente implementada** | `37ab2bb54da2e7f1a4ea8a9c793b2f3247dee208` (`cursor/mb-07-planificador-consumo-capacidad`) |
| **Base portable** | `cda96774909576e589ee1fddcbabf08aeec65540` (`cursor/fase2-central-integracion` Tramo 4) |
| **Rama portable** | `cursor/mb07-planificador-portable-central` |
| **Alembic base** | `1340a1b2c3d4e` |
| **Alembic MB-07** | `1507a1b2c3d4e` (`down_revision`: `1340a1b2c3d4e`) |

## Dependencias eliminadas

| Dependencia | Estado |
|-------------|--------|
| **Auditor** (`1400a1b2c3d4e`, `employee_audit_*`, `empleados_auditor`) | **ELIMINADA** |
| **Mi Trabajo** (`trabajo_*`, bandeja) | **ELIMINADA** |
| SHAs `be761f6`, `3d066ae` | **NO referenciados** |

La lógica determinística (costo LLM = 0) se modela por `is_deterministic` en transversal y `execution_ref` con `deterministic` / categoría no-LLM, sin importar módulos Auditor.

## Inventario diferencial (cda9677 → 37ab2bb)

### Portados (solo MB-07)

| Archivo | Acción |
|---------|--------|
| `backend/app/consumption_planner_models.py` | Nuevo |
| `backend/app/services/consumption_planner_service.py` | Nuevo (adaptado: sin ref Auditor) |
| `backend/app/schemas_consumption_planner.py` | Nuevo |
| `backend/alembic/versions/1507a1b2c3d4e_consumption_planner_mb07.py` | Nuevo (`down_revision` → `1340`) |
| `backend/app/routers/finops.py` | + rutas `/planner/*` |
| `backend/app/permissions.py` | + `finops.planner.*`, `finops.margin.view` |
| `backend/app/main.py` | + import `consumption_planner_models` |
| `backend/alembic/migration_ledger.json` | HEAD → `1507a1b2c3d4e` |
| `backend/scripts/schema_repair.py` | HEAD → `1507a1b2c3d4e` |
| `tests/conftest.py` | + import modelos MB-07 |
| `tests/test_consumption_planner_mb07.py` | Nuevo |
| `frontend/src/api.ts` | + APIs planner |
| `frontend/src/pages/CostosValorPage.tsx` | + pestañas planificador |

### Excluidos explícitamente

- Migración `1400a1b2c3d4e` (Auditor)
- `employee_audit_*`, `empleados_auditor`, `trabajo_*`
- Tests auditor / bandeja / integración Mi Trabajo
- Cualquier eliminación de módulos Tramo 4 (1280–1340, 1270, comercial, TCO, etc.)

## APIs preservadas

`/api/finops/planner/resumen`, `config`, `simular`, `capacidad`, `presupuesto`, `comparar`, `empleado`, `transversal`, `margen`, `contrato-centro-control`, `alertas`.

Centro de Control: **NO modificado** (solo contrato portable).

## PLANES (nota AVIONES)

En el reporte externo previo, **"AVIONES: PASS"** fue error de presentación/traducción automática del área **PLANES**. El código y tests usan **PLANES** (consumo incluido, saldo, sobreconsumo). No existe etiqueta "AVIONES" en UI ni entregables de código.

## Receta para General

1. Partir de `cursor/fase2-central-integracion` @ `cda9677` (o HEAD central certificado con `1340a1b2c3d4e`).
2. Merge/cherry-pick rama `cursor/mb07-planificador-portable-central`.
3. `alembic upgrade head` → `1507a1b2c3d4e`.
4. `pytest tests/test_consumption_planner_mb07.py` + suite central.
5. `npm run build` frontend.

## Veredicto

APTO PARA PORTAR — MB-07 lineal sobre Tramo 4, sin cadena Auditor.

## Certificación ejecutada (entorno portable)

| Prueba | Resultado |
|--------|-----------|
| MB-07 (`test_consumption_planner_mb07.py`) | 22 passed |
| Migration control | 7 passed |
| FinOps 1110 + 1280 + 1310 + 1320 + 1340 | passed (focal fresh DB) |
| Alembic upgrade → downgrade 1340 → upgrade | PASS |
| Frontend build | PASS |
| Suite completa local (fresh SQLite) | 880 passed — entorno VM; baseline Docker Tramo 4 certificó 1061 |
| 1270 errors (6) | Preexistentes en cda9677 (mismo entorno, no regresión MB-07) |

PostgreSQL roundtrip: PENDIENTE POR ENTORNO.
