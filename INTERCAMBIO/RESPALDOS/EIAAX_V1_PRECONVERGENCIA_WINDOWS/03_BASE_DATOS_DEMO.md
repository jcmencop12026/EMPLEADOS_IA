# 03 — Base de datos demo

## Tipo

**SQLite DEMO** — no PostgreSQL productivo.

## Ruta real (Windows — prueba visual exitosa)

```
D:\EMPLEADOS_IA_INTEGRADO\data\eiaax_integrado_demo.db
```

Definida en:

- `scripts/windows/EiaaxDemo.Common.ps1` → `$script:DemoDbFileName = "eiaax_integrado_demo.db"`
- `backend/scripts/seed_lote3_demo.py` → `DEFAULT_DATABASE_URL`

## Archivos asociados posibles

| Archivo | Tratamiento |
|---------|-------------|
| `eiaax_integrado_demo.db` | **Principal** — copiar siempre |
| `eiaax_integrado_demo.db-journal` | Copiar si existe (rollback journal) |
| `eiaax_integrado_demo.db-wal` | Copiar si existe (WAL mode) |
| `eiaax_integrado_demo.db-shm` | Copiar si existe (WAL shared memory) |

## Estado en agente cloud

La BD demo de la prueba visual Windows **no está físicamente** en el agente cloud (sin acceso a `D:\`).

### Sincronización obligatoria desde Windows

Ejecutar en el equipo Windows (sin modificar el original):

```powershell
powershell -ExecutionPolicy Bypass -File D:\EMPLEADOS_IA\INTERCAMBIO\RESPALDOS\EIAAX_V1_PRECONVERGENCIA_WINDOWS\COPIAR_BD_DEMO_DESDE_WINDOWS.ps1
```

Equivalente repo:

```
INTERCAMBIO/RESPALDOS/EIAAX_V1_PRECONVERGENCIA_WINDOWS/COPIAR_BD_DEMO_DESDE_WINDOWS.ps1
```

El script:

1. Copia `data\eiaax_integrado_demo.db` sin alterar el original.
2. Copia sidecars WAL/journal si existen.
3. Genera `SHA256_BD_DEMO.txt` con checksum.

## Alembic en BD demo

| Campo | Valor |
|-------|-------|
| Head esperado | `1770a1b2c3d4e` |
| Migración | `backend/alembic/versions/1770a1b2c3d4e_mesa_ayuda_soporte_evolucion_mb12.py` |

Verificado en código respaldado (`d034566`). La BD Windows usada en prueba visual debe estar en este head.

## Contenido demo esperado

- Empresa Demo A / Empresa Demo B
- Usuario `org_a_admin` (credenciales ejemplo en `backend/scripts/credentials.example`)
- Seed: `backend/scripts/seed_lote3_demo.py`

## SHA256 BD demo

| Estado | Valor |
|--------|-------|
| En agente cloud | **PENDIENTE SINCRONIZACIÓN WINDOWS** |
| Tras ejecutar `COPIAR_BD_DEMO_DESDE_WINDOWS.ps1` | Ver `SHA256_BD_DEMO.txt` |

## No incluido

- PostgreSQL productivo (no aplica en esta prueba)
- `enterprise_ai_os_dev.sqlite` del respaldo Lote 3 (BD distinta, respaldo anterior intacto)
