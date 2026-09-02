# Entrega — Arranque atómico Windows: Git stderr + ruta autoritativa

**Fecha:** 2026-09-02  
**Rama:** `cursor/convergencia-comercial-v1-85e4`

---

## A. Causa raíz del falso fallo Git

En `18b9be3`, `Sync-EiaaxConvergenceRepository` ejecutaba `git fetch` con redirección `2>&1` bajo `$ErrorActionPreference = "Stop"`. PowerShell convierte stderr nativo de Git (p. ej. `From https://github.com/jcmencop12026/EMPLEADOS_IA`) en error terminante aunque el exit code sea 0. El `catch` del arranque reportaba ese texto como `CAUSA:`.

## B. Archivo/helper que lo provocaba

- `Sync-EiaaxConvergenceRepository` en `EiaaxDemo.Common.ps1`
- Patrón `& git ... 2>&1` sin aislar `$ErrorActionPreference`
- Bloque `catch` en `arrancar_convergencia_windows.ps1`

## C. Corrección aplicada

| Componente | Cambio |
|------------|--------|
| `Invoke-EiaaxExternalCommand` | Autoridad única: exit code, stdout/stderr, duración, etapa, log |
| `Invoke-EiaaxGitCommand` | Wrapper Git centralizado |
| `Sync-EiaaxConvergenceRepository` | fetch / checkout / pull --ff-only vía helper |
| `Invoke-EiaaxNativeCommand` | Delega en autoridad externa (pip/npm/python) |
| `Initialize-EiaaxConvergenceWorktreeFromScriptRoot` | Raíz desde ubicación física del script (`$PSScriptRoot`), no `$PWD` |
| `Assert-EiaaxConvergencePathAuthority` | Aborta si VENV/BD/logs salen de CONVERGENCIA |
| `Write-EiaaxConvergenceExecutionContext` | Imprime rutas autoritativas al inicio |

## D. SHA final

**`b01f890`**

## E. Archivos modificados

- `scripts/windows/EiaaxDemo.Common.ps1`
- `scripts/windows/arrancar_convergencia_windows.ps1`
- `scripts/windows/test_git_sync.ps1`
- `scripts/windows/test_convergence_atomic.ps1`
- `INTERCAMBIO/SALIDA/EIAAX_CONVERGENCIA_COMERCIAL_V1_WINDOWS/09_ENTREGA_ARRANQUE_ATOMICO_GIT.md`

## F. Pruebas

`ejecutar_tests_desarrollo_windows.ps1` — git stderr A–F, Python resolution, discovery, convergence atomic, PS semantics, Alembic, preparador.

## G. Fix Python 18b9be3

Conservado: `Resolve-EiaaxPython`, `Invoke-EiaaxPythonSysProbe`, `Build-EiaaxPythonResolutionPlan`, `PYTHON DISCOVERY`.

## H. Ruta autoritativa

`D:\EMPLEADOS_IA_CONVERGENCIA` — resuelta desde `scripts\windows\..\..` del script invocado.

## I. Independencia de $PWD

`Initialize-EiaaxConvergenceWorktreeFromScriptRoot` ignora el directorio actual de la consola.

## J. Comando único Windows

```powershell
Set-Location "D:\EMPLEADOS_IA_CONVERGENCIA"
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows\arrancar_convergencia_windows.ps1"
```
