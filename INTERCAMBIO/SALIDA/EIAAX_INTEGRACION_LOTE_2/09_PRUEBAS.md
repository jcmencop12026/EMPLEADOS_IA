# 09 — Pruebas

## Suites focales (obligatorias)

Ejecutadas desde raíz del repo (`python3 -m pytest tests/...`):

| Suite | Archivo | Resultado |
|-------|---------|-----------|
| BP1 evaluación | `test_bloque_producto_1_evaluacion.py` | PASS (8) |
| BP2 PIIAX prep | `test_bloque_producto_2_piiax_prep.py` | PASS (16) |
| Gobierno operacional | `test_gobierno_operacional.py` | PASS |
| Partners MB-03 | `test_mb03_partners.py` | PASS |
| Motor económico 1600 | `test_economic_motor_1600.py` | PASS |
| Migraciones | `test_migration_control.py` | PASS |

**Total focal: 59 passed**

## Migraciones

| Verificación | Resultado |
|--------------|-----------|
| Un solo head Alembic | PASS (`1600a1b2c3d4e`) |
| Ledger protegido | PASS |
| Upgrade SQLite dev | PASS |

## Frontend

| Verificación | Resultado |
|--------------|-----------|
| `npm run build` | PASS |
| `brand.test.ts`, `evaluacionLabels.test.ts` | PASS (vitest) |

## Ámbitos cubiertos

- Multiempresa / aislamiento
- RBAC (incl. corrección viewer sin `evaluacion.view` indebido)
- Partners grant/revoke
- Gobierno políticas/aprobaciones
- Motor económico / economía privada
- BP2 siguiente acción / intents A–H
- Visibilidad evaluación

## Regresión BP1

- Expediente, hallazgos, vista entidad, preguntar sin proveedor, e2e recorrido — PASS

## Nota ejecución

Ejecutar pytest desde `/workspace` (no desde `backend/`) para resolver imports `conftest`.
