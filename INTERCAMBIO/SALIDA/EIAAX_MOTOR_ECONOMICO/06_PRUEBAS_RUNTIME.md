# 06 — Pruebas y runtime representativo

## Suite focal

**Archivo:** `tests/test_economic_motor_1600.py`

| Prueba | Cobertura |
|---|---|
| `test_register_cost_real_creates_finops_and_motor_entry` | Costo REAL → FinOps + motor |
| `test_register_estimated_cost_no_finops` | ESTIMADO sin duplicar FinOps |
| `test_potencial_not_in_realizado` | POTENCIAL excluido de realizado |
| `test_entity_view_excludes_private_economy` | Vista Entidad sin privados |
| `test_private_economy_requires_permission` | RBAC viewer → 403 |
| `test_private_economy_superadmin` | CRUD economía privada |
| `test_price_recommendation_is_draft` | Precio BORRADOR, no auto-publicado |
| `test_indicators_phases` | ANTES/PROYECTADO/REAL API |
| `test_backfill_finops_idempotent` | Sync FinOps idempotente |

## Resultado runtime (2026-08-31)

```
9 passed
```

## Validación migraciones

```
alembic upgrade head → 1600a1b2c3d4e
scripts/validate_migrations.py → PASS
```

## Runtime API (smoke)

- `GET /api/motor-economico/vista-entidad` → 200
- `GET /api/motor-economico/indicadores` → fases ANTES/PROYECTADO/REAL
- `POST /api/motor-economico/precio-recomendado` → BORRADOR
- `GET /api/centro-control/resumen-ejecutivo` → incluye módulo `motor_economico`
