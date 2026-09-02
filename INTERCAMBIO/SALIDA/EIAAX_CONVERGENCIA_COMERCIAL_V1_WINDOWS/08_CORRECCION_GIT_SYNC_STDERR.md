# Corrección sincronización Git — stderr informativo ≠ fallo

**Fecha:** 2026-09-02  
**Rama:** `cursor/convergencia-comercial-v1-85e4`

---

## A. Causa exacta del falso error

`Sync-EiaaxConvergenceRepository` en `18b9be3` ejecutaba:

```powershell
& git fetch origin $branch 2>&1 | Out-Host
```

Con `$ErrorActionPreference = "Stop"` (global en `arrancar_convergencia_windows.ps1`), PowerShell trata la salida stderr de procesos nativos como **ErrorRecord** aunque `git` termine con **exit code 0**.

El mensaje `From https://github.com/jcmencop12026/EMPLEADOS_IA` es salida informativa normal de `git fetch` en stderr.

El bloque `catch` del script capturaba `$_.Exception.Message` = ese texto y lo reportaba como:

```
EIAAX — WINDOWS NO CERTIFICADO
CAUSA: From https://github.com/jcmencop12026/EMPLEADOS_IA
```

**No era un fallo real de Git.** Era un falso positivo por criterio de error incorrecto.

---

## B. Corrección aplicada

### Autoridad única: `Invoke-EiaaxGitCommand`

Delega en `Invoke-EiaaxExternalCommand`, que:

1. Fija `$ErrorActionPreference = "Continue"` durante la ejecución
2. Captura stdout+stderr con `2>&1`
3. Usa **`$LASTEXITCODE`** como única autoridad de éxito/fallo
4. Registra salida en log cuando se proporciona `LogFile`

### `Sync-EiaaxConvergenceRepository`

- `git fetch origin <branch>`
- `git checkout <branch>`
- `git pull --ff-only origin <branch>`

### Otros helpers corregidos

| Helper | Cambio |
|--------|--------|
| `Invoke-EiaaxNativeCommand` | Usa `Invoke-EiaaxExternalCommand` (pip/npm/python/alembic) |
| `Get-EiaaxGitBranchName` / `Get-EiaaxGitShortSha` | Usan `Invoke-EiaaxGitCommand` |
| `preparar_demo_eiaax.ps1` npm | Usa `Invoke-EiaaxNativeCommand` con `npm.cmd` |
| `Test-EiaaxPythonVenvCapability` | Usa `Invoke-EiaaxExternalCommand` |

### Mensajes de fallo

```
EIAAX — WINDOWS NO CERTIFICADO
ETAPA: sincronizacion_git
CAUSA: <mensaje real con exit code>
```

Log completo en `logs\demo\arrancar_convergencia.log` desde el inicio (incluye salida git).

---

## C. Conservación fix Python 18b9be3

Sin cambios en:

- `Resolve-EiaaxPython`
- `Invoke-EiaaxPythonSysProbe`
- `Build-EiaaxPythonResolutionPlan`
- bloque `PYTHON DISCOVERY`

---

## D. Pruebas

`test_git_sync.ps1`:

| Caso | Escenario | Esperado |
|------|-----------|----------|
| A | exit 0 + stderr | PASS |
| B | exit 0 + `From https://...` | PASS |
| C | exit 1 + stderr | FAIL |
| D | fake git fetch | PASS |
| E | fast-forward | PASS |
| F | non-fast-forward | FAIL seguro |

---

## E. Comando único

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\EMPLEADOS_IA_CONVERGENCIA\scripts\windows\arrancar_convergencia_windows.ps1
```

Verificar: `Codigo activo SHA: <sha>` y que la etapa `sincronizacion_git` complete sin abortar por stderr informativo.
