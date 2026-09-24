# Migraciones y PostgreSQL

## Head único

- **Head:** `1770a1b2c3d4e`
- **Ledger:** `backend/alembic/migration_ledger.json` → `baseline_head: 1770a1b2c3d4e`
- **Schema repair:** `HEAD_REVISION = 1770a1b2c3d4e`

## Reconstrucción (no copia literal)

IDs históricos colisionados en ramas descendientes (1410/1420/1430/1700…) **no** se copiaron. Se crearon revisiones nuevas 1610–1770 con `down_revision` correcto sobre cadena Lote 2.

## SQLite (validado)

```bash
alembic upgrade head   # BD fresca
python3 -m pytest tests/test_migration_control.py -q
```

## PostgreSQL

La VM de integración no expone daemon PostgreSQL. Validación pendiente en entorno con Postgres aislado:

1. Restaurar esquema en `1600` desde snapshot `c536f24`
2. `alembic upgrade head`
3. Verificar `alembic heads` = 1, FK/constraints en tablas nuevas (`impl_entregables`, `negocio_contract_records`, etc.)

**Estado:** P2 operativo (no bloquea cierre de integración en SQLite/tests).
