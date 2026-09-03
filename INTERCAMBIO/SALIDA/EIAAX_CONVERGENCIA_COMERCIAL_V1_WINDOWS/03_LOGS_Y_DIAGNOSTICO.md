# Logs y diagnostico Windows

## Ubicacion

Relativo al worktree (`D:\EMPLEADOS_IA_CONVERGENCIA` por defecto):

| Archivo | Contenido |
|---------|-----------|
| `logs\demo\preparar.log` | Preparacion: Python, pip, seed, alembic |
| `logs\demo\backend.log` | uvicorn stdout/stderr |
| `logs\demo\frontend.log` | Vite / npm.cmd |
| `.runtime-eiaax-demo\backend.txt` | PID backend gestionado |
| `.runtime-eiaax-demo\frontend.txt` | PID frontend gestionado |

## Comprobaciones manuales

```powershell
# Alembic
cd D:\EMPLEADOS_IA_CONVERGENCIA\backend
$env:DATABASE_URL = "sqlite:///D:/EMPLEADOS_IA_CONVERGENCIA/data/eiaax_integrado_demo.db"
.\.venv-eiaax-demo\Scripts\python.exe -m alembic heads
.\.venv-eiaax-demo\Scripts\python.exe -m alembic current

# Health
Invoke-WebRequest http://127.0.0.1:8000/health -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:5180/ -UseBasicParsing
```

## Errores frecuentes

| Sintoma | Causa probable | Accion |
|---------|----------------|--------|
| Expected alembic head 1820 but found 1770 | Worktree antiguo | `git pull` + `preparar_demo_eiaax.ps1` |
| npm abre editor | npm.ps1 | Ya corregido en d034566: usa `npm.cmd` |
| Port 5180 in use | Instancia previa | `detener_demo_eiaax.ps1` |
| PYTHON NOT FOUND | Stub WindowsApps | `EIAAX_PYTHON=C:\Python312\python.exe` |
| Demo DB unsafe path | Worktree prohibido | No usar `D:\EMPLEADOS_IA` |

## Aborto seguro

Todos los scripts usan `$ErrorActionPreference = Stop` y `exit 1` ante fallo.  
No modifican `D:\EMPLEADOS_IA` ni borran worktrees ajenos.
