# Incidente PYTHON NOT FOUND — causa raiz y correccion

**Fecha:** 2026-09-01  
**Worktree afectado:** `D:\EMPLEADOS_IA_CONVERGENCIA`  
**SHA candidato:** `f13c58d` (y posteriores)

---

## Sintoma observado

```
ERROR: PYTHON NOT FOUND: no python.exe candidates detected on this machine.
```

Tras exit code 1 del preparador, un bloque externo reporto Backend/Frontend True — **falso positivo** por procesos previos en puertos 8000/5180.

---

## Causa raiz (Python)

El detector en `d034566` y `f13c58d` era **identico** en logica base (`Get-Command`, rutas estaticas, AppData).  
No hubo regresion de codigo entre esos commits para Python.

La falla en el worktree nuevo se explica por:

1. **Worktree fresco** sin `.venv-eiaax-demo` — obliga a descubrir Python de sistema.
2. **PATH limitado** en la sesion PowerShell — `Get-Command python` puede no resolver aunque Python exista.
3. **Instalacion via py launcher** — el stack anterior pudo usar `py` o ruta no cubierta solo por `Get-Command`.
4. **Stubs WindowsApps** filtrados correctamente — si la unica entrada era stub, la lista quedaba vacia.

**Conclusion:** el mensaje "no instalado" era enganoso; faltaban **mecanismos de descubrimiento** ya usados implicitamente en el entorno integrado anterior.

---

## Correccion aplicada

`Get-EiaaxPythonDiscoveryCandidates` ahora agrega, en orden seguro:

| Mecanismo | Funcion |
|-----------|---------|
| `EIAAX_PYTHON` | override explicito |
| `.venv` existente | via `Find-EiaaxPython` |
| Rutas estaticas / Program Files / AppData | ya existian |
| `where.exe python.exe` | **nuevo** |
| `py -0p` y `py -3.x -c` | **nuevo** (launcher, no REPL) |
| Registro `PythonCore` HKLM/HKCU | **nuevo** |
| Barrido PATH `python.exe` | **nuevo** |

Sin instalar Python automaticamente. Sin hardcodear una ruta fija.

---

## Causa raiz (falso positivo Backend/Frontend)

El script anterior:

- Mostraba exito aunque el preparador fallara (flujo 1/2 sin certificacion final).
- No verificaba identidad de instancia.
- No detenia procesos ajenos antes de preparar.
- `iniciar_*` podia reutilizar servicios en puerto sin confirmar candidato.

---

## Correccion (certificacion fail-closed)

`arrancar_convergencia_windows.ps1` ahora:

1. Valida rama via `eiaax_convergence_manifest.json` (no SHA hardcodeado obsoleto).
2. `Clear-EiaaxPortsForConvergence` — aborta si puerto ocupado por proceso no gestionado o de otro worktree.
3. Preparacion — **aborta** si falla (no continua a start).
4. Escribe identidad runtime en `.runtime-eiaax-demo/`.
5. Arranca backend con env `EIAAX_GIT_SHA`, `EIAAX_DEMO_PROFILE`, `EIAAX_RUNTIME_MARKER`.
6. Verifica Alembic `1820` en BD y codigo.
7. Verifica `/health` backend + proxy frontend con bloque `runtime`:
   - `git_sha`
   - `demo_profile`
   - `runtime_marker`
   - `alembic_current`
   - `demo_db_name`

Solo entonces imprime: `EIAAX <sha> - WINDOWS REAL OPERATIVO`

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `scripts/windows/EiaaxDemo.Common.ps1` | Python discovery, puertos, manifest, identidad |
| `scripts/windows/arrancar_convergencia_windows.ps1` | Script unico certificado |
| `scripts/windows/eiaax_convergence_manifest.json` | Autoridad rama/Alembic (no SHA fijo) |
| `scripts/windows/iniciar_backend_demo.ps1` | Pasa env runtime al backend |
| `backend/app/config.py` | Campos identidad runtime |
| `backend/app/health.py` | Bloque `runtime` en `/health` |

---

## Comando unico para el usuario

```powershell
cd D:\EMPLEADOS_IA_CONVERGENCIA
git pull
git checkout cursor/convergencia-comercial-v1-85e4
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\windows\arrancar_convergencia_windows.ps1
```

Si falla: **no** declarar operativo. Revisar `logs\demo\arrancar_convergencia.log`.

Opcional si Python no se autodetecta:

```powershell
$env:EIAAX_PYTHON = "C:\Python312\python.exe"
```
