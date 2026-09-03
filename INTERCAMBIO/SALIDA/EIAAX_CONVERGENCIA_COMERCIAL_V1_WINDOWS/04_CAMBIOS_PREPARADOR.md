# Cambios al stack Windows para convergencia

Actualizacion minima sobre mecanismo certificado `d034566`:

| Archivo | Cambio |
|---------|--------|
| `scripts/windows/EiaaxDemo.Common.ps1` | `ExpectedAlembicHead` → `1820a1b2c3d4e`; constantes convergencia |
| `backend/scripts/seed_lote3_demo.py` | Imports modelos A+B (flujo, presentacion, espacio externo) |
| `scripts/windows/arrancar_convergencia_windows.ps1` | **Nuevo** — entrada unica convergencia |

## Sin cambios (reutilizado tal cual)

- `preparar_demo_eiaax.ps1`
- `iniciar_demo_eiaax.ps1` / `iniciar_backend_demo.ps1` / `iniciar_frontend_demo.ps1`
- `detener_demo_eiaax.ps1`
- `validar_arranque_windows.ps1`
- `Resolve-EiaaxNpmCmdExecutable`, idempotencia puertos, strictPort 5180

## Migracion BD existente (1770 → 1820)

El preparador **recrea** la BD demo (`data\eiaax_integrado_demo.db`) y ejecuta `alembic upgrade head`.  
No borra otras bases. Para conservar una BD demo previa, copiar el archivo `.db` antes de preparar.

Upgrade in-place sin recrear (avanzado):

```powershell
cd backend
$env:DATABASE_URL = "sqlite:///D:/EMPLEADOS_IA_CONVERGENCIA/data/eiaax_integrado_demo.db"
.\.venv-eiaax-demo\Scripts\python.exe -m alembic upgrade head
```

Luego ejecutar seed solo si faltan datos demo.
