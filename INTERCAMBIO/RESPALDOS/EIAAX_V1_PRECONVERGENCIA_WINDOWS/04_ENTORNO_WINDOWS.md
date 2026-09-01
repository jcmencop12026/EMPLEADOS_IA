# 04 — Entorno Windows operativo

## Plataforma validada

| Componente | Versión / valor |
|------------|-----------------|
| SO | Windows 10 |
| Shell | Windows PowerShell 5.1 |
| Worktree | `D:\EMPLEADOS_IA_INTEGRADO` |
| Python | `C:\Python314\python.exe` — 3.14.5 |
| Node | v24.16.0 |
| npm | 11.13.0 |
| BD | SQLite `data\eiaax_integrado_demo.db` |

## URLs operativas

| Servicio | URL |
|----------|-----|
| Frontend | `http://127.0.0.1:5180` |
| Backend health | `http://127.0.0.1:8000/health` |
| Login demo | `org_a_admin` |

## Scripts Windows incluidos en respaldo (`d034566`)

| Script | Función |
|--------|---------|
| `scripts/windows/validar_arranque_windows.ps1` | Entrada validación |
| `scripts/windows/preparar_demo_eiaax.ps1` | Preparador productivo |
| `scripts/windows/iniciar_demo_eiaax.ps1` | Arranque backend + frontend |
| `scripts/windows/iniciar_backend_demo.ps1` | Backend uvicorn :8000 |
| `scripts/windows/iniciar_frontend_demo.ps1` | Frontend Vite :5180 (npm.cmd) |
| `scripts/windows/detener_demo_eiaax.ps1` | Parada segura EIAAX |
| `scripts/windows/EiaaxDemo.Common.ps1` | Helpers compartidos |

## Inventario reproducible (sin copiar basura)

| Incluido en respaldo Git/tarball | Excluido deliberadamente |
|----------------------------------|--------------------------|
| Código fuente backend/frontend | `node_modules/` |
| `requirements.txt` | `.venv-eiaax-demo/` |
| `package.json` / lock | Caches npm/pip |
| Migraciones Alembic | Secretos reales |
| `seed_lote3_demo.py` | API keys / tokens |
| `credentials.example` | Logs con credenciales |
| Guía `GUIA_WINDOWS_PRUEBA_HUMANA.md` | |

## Correcciones Windows críticas en este punto

1. Preparador productivo separado de autotests dev (`fd5dc19`)
2. Alembic: exit code como autoridad, no stderr INFO (`0e05020`)
3. Frontend: `npm.cmd` explícito, no `npm.ps1` en editor (`d034566`)
4. Vite `strictPort: true` en `frontend/vite.config.ts`

## Logs útiles (sin secretos)

Ruta en worktree Windows:

```
logs\demo\preparar.log
logs\demo\backend.log
logs\demo\frontend.log
```

No se incluyen en el bundle Git (generados en ejecución). Copiar manualmente si se desea conservar evidencia de la ejecución exitosa.

## PostgreSQL

**NO APLICA** en esta prueba Windows demo SQLite.
