# Herramientas certificación Docker Windows V1

Rama dedicada: **solo** scripts y runbook para certificar la candidata `e8cb853` en Docker Desktop Windows.

| Artefacto | Ruta |
|-----------|------|
| Script PowerShell | `scripts/CERTIFICAR_V1_DOCKER_WINDOWS_E8CB853.ps1` |
| Runbook | `INTERCAMBIO/SALIDA/CURSOR_V1_EJECUCION_LOCAL_DOCKER_WINDOWS_E8CB853.md` |

## Uso rápido (Windows)

```powershell
git clone --branch cursor/v1-certificacion-windows-tools --single-branch https://github.com/jcmencop12026/EMPLEADOS_IA.git D:\EMPLEADOS_IA_CERT_TOOLS
Set-Location D:\EMPLEADOS_IA_CERT_TOOLS
Set-ExecutionPolicy -Scope Process Bypass -Force
.\scripts\CERTIFICAR_V1_DOCKER_WINDOWS_E8CB853.ps1
```

Ver runbook completo en `INTERCAMBIO/SALIDA/CURSOR_V1_EJECUCION_LOCAL_DOCKER_WINDOWS_E8CB853.md`.

**NO MERGE** — no modifica candidata V1 ni `main`.
