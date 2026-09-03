# Recuperación EIAAX — Windows real estable 104f785

## Identificadores

| Campo | Valor |
|-------|-------|
| SHA | `104f7850d7196d08d80fff9b4e7a8a83a5a1fa9a` |
| Tag | `eiaax-v1-windows-real-estable-104f785` |
| Rama | `cursor/convergencia-comercial-v1-85e4` |
| Alembic | `1820a1b2c3d4e` |

## Restaurar código

### Desde origin

```powershell
git fetch origin tag eiaax-v1-windows-real-estable-104f785
git checkout eiaax-v1-windows-real-estable-104f785
```

### Desde bundle offline

```powershell
git clone D:\RESPALDOS_EIAAX\EIAAX_V1_WINDOWS_ESTABLE_104f785\eiaax-v1-windows-real-estable-104f785.bundle EIAAX_RESTORE_104f785
cd EIAAX_RESTORE_104f785
git checkout eiaax-v1-windows-real-estable-104f785
git rev-parse HEAD
# debe mostrar 104f7850d7196d08d80fff9b4e7a8a83a5a1fa9a
```

## Restaurar base de datos

Usar la copia `eiaax_integrado_demo_104f785_*.db` generada por el script integral.

1. Detener EIAAX de forma controlada.
2. Conservar copia adicional de la BD operativa actual.
3. Reemplazar `data\eiaax_integrado_demo.db` con la copia respaldada.
4. Ejecutar `PRAGMA integrity_check` (debe ser `ok`).
5. Arrancar con scripts/windows existentes.

## No restaurar (regenerables)

- `node_modules/`
- `.venv/` / `venv/`
- `frontend/dist/`
- `__pycache__/`

## Verificación post-restauración

- `git rev-parse HEAD` = `104f7850...`
- Alembic current = `1820a1b2c3d4e`
- Login `org_a_admin` funcional
- http://127.0.0.1:5180 accesible
