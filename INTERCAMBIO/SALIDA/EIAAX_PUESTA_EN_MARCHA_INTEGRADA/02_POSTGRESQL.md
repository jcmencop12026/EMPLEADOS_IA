# PostgreSQL — validación real

## Resultado: NO EJECUTABLE

**Causa exacta:** la VM no dispone de `psql`, `docker` ni daemon PostgreSQL. No se instaló software ni se alteró infraestructura.

## Validación realizada (SQLite)

- BD demo: `sqlite:////workspace/data/eiaax_integrado_demo.db`
- `alembic upgrade head` → `1770a1b2c3d4e` ✓
- `test_migration_control` → PASS (suite regresión)

## Procedimiento reproducible Windows

```powershell
# 1. Instancia PostgreSQL aislada (no productiva)
createdb eiaax_lote3_upgrade_test

# 2. Restaurar esquema en head 1600 (snapshot Lote 2) o partir de vacío
$env:DATABASE_URL = "postgresql://user:pass@localhost:5432/eiaax_lote3_upgrade_test"

# 3. Upgrade
cd backend
alembic upgrade head

# 4. Verificar
alembic heads    # debe mostrar solo 1770a1b2c3d4e
alembic current  # 1770a1b2c3d4e
```

**Estado:** NO marcar PostgreSQL PASS hasta ejecutar el procedimiento anterior.
