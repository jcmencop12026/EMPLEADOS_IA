# Arranque Windows atómico — pyvenv.cfg y Python base

**Fecha:** 2026-09-01  
**Rama:** `cursor/convergencia-comercial-v1-85e4`  
**Worktree destino:** `D:\EMPLEADOS_IA_CONVERGENCIA`  
**Referencia funcional:** `D:\EMPLEADOS_IA_INTEGRADO\.venv-eiaax-demo`

---

## Causa raíz definitiva

El entorno **INTEGRADO sí tenía Python operativo** vía:

```
D:\EMPLEADOS_IA_INTEGRADO\.venv-eiaax-demo\Scripts\python.exe
```

El worktree **CONVERGENCIA** es nuevo y no tenía `.venv-eiaax-demo`. El preparador necesita el **Python base** que originó el venv anterior para crear un venv independiente.

El fallo `PYTHON NOT FOUND` no significaba ausencia de Python en la máquina, sino que el descubrimiento no leía `pyvenv.cfg` del venv funcional ni priorizaba correctamente la cadena autoritativa.

Además, procesos previos de INTEGRADO en 8000/5180 producían **falsos positivos** HTTP sin validar PID/comando del worktree convergido.

---

## Estrategia aplicada

### 1. Descubrimiento Python (orden autoritativo)

| Prioridad | Fuente |
|-----------|--------|
| A | `EIAAX_PYTHON` (si válido con `python -V` exit 0) |
| B | Python base desde `D:\EMPLEADOS_IA_INTEGRADO\.venv-eiaax-demo\pyvenv.cfg` (`home`, `executable`, `command`) |
| C | `py` launcher (`-0p`, `-3.x -c`) |
| D | `where.exe` + barrido `PATH` |
| E | Registro `PythonCore` HKLM/HKCU |
| F | Instalaciones estándar (`C:\Python3xx`, Program Files, AppData) |

Cada candidato se valida ejecutando `python.exe -V` (exit 0). Se excluyen stubs WindowsApps y el intérprete del venv (no se usa el `python.exe` del venv anterior como base).

### 2. Venv convergencia autónomo

Destino: `D:\EMPLEADOS_IA_CONVERGENCIA\.venv-eiaax-demo`

- Si no existe: crear con Python base validado.
- Si existe pero dañado (`Scripts\python.exe`, `pyvenv.cfg` o `-V` fallan): reconstruir **solo** en CONVERGENCIA.
- **No tocar** `D:\EMPLEADOS_IA_INTEGRADO\.venv-eiaax-demo`.

### 3. Cambio controlado de instancia

`Clear-EiaaxPortsForConvergence`:

1. Detecta ocupación 8000/5180 (PID + CMD).
2. Si pertenece a INTEGRADO → `detener_demo_eiaax.ps1` oficial con `EIAAX_WORKTREE` temporal.
3. Si pertenece a CONVERGENCIA → detiene el propio candidato.
4. Si proceso ajeno/no EIAAX → **ABORTA**.
5. Verifica puertos libres antes de continuar.

### 4. Script único atómico

`arrancar_convergencia_windows.ps1` incluye:

- `git fetch/checkout/pull` de la rama del manifest
- preparación completa
- arranque
- validación PID/comando → worktree CONVERGENCIA
- `/health` con `git_sha`, `alembic_current`, `demo_profile`, `demo_db_name`

Salida éxito: `EIAAX <sha> — WINDOWS REAL OPERATIVO`  
Salida fallo: `EIAAX — WINDOWS NO CERTIFICADO` + `CAUSA: ...` + exit 1

---

## Comando ÚNICO para el usuario

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\EMPLEADOS_IA_CONVERGENCIA\scripts\windows\arrancar_convergencia_windows.ps1
```

Opcional si el autodescubrimiento falla:

```powershell
$env:EIAAX_PYTHON = "C:\Python312\python.exe"
powershell -NoProfile -ExecutionPolicy Bypass -File D:\EMPLEADOS_IA_CONVERGENCIA\scripts\windows\arrancar_convergencia_windows.ps1
```

---

## Criterios WINDOWS REAL OPERATIVO

Todos deben ser PASS:

| Check | Criterio |
|-------|----------|
| Repositorio | rama `cursor/convergencia-comercial-v1-85e4` |
| Python base | resuelto y ejecutable (`-V` exit 0) |
| Venv convergencia | `D:\EMPLEADOS_IA_CONVERGENCIA\.venv-eiaax-demo` |
| Dependencias | pip/requirements + npm build |
| BD convergencia | `data\eiaax_integrado_demo.db` |
| Seed | ejecutado |
| Alembic | head/current `1820a1b2c3d4e` |
| Backend propio | PID/CMD contiene `D:\EMPLEADOS_IA_CONVERGENCIA` |
| Frontend propio | PID/CMD contiene `D:\EMPLEADOS_IA_CONVERGENCIA` |
| Runtime identity | `/health` runtime block coincide con manifest |
| Puertos | 8000 backend, 5180 frontend del candidato |

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `scripts/windows/EiaaxDemo.Common.ps1` | `Read-EiaaxPyvenvCfg`, discovery reordenado, venv integrity, stop INTEGRADO, PID ownership |
| `scripts/windows/arrancar_convergencia_windows.ps1` | Flujo atómico 7 pasos, git sync, certificación fail-closed |
| `scripts/windows/preparar_demo_eiaax.ps1` | Detección/reconstrucción venv dañado |
| `scripts/windows/test_python_discovery.ps1` | Casos pyvenv.cfg y Store alias |
| `scripts/windows/test_convergence_atomic.ps1` | **nuevo** — pruebas atómicas convergencia |

---

## Pruebas

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\windows\test_python_discovery.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\windows\test_convergence_atomic.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\windows\test_ps_semantics.ps1
```

---

## pyvenv.cfg (sin datos sensibles)

Ejemplo de campos leídos (valores reales dependen de la máquina):

```
home = <ruta instalación Python>
executable = <ruta python.exe base>
version = 3.12.x
command = <python base> -m venv D:\EMPLEADOS_IA_INTEGRADO\.venv-eiaax-demo
```

El script registra `version` y `home` en `logs\demo\arrancar_convergencia.log` cuando el archivo existe.
