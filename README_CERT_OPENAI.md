# Herramientas certificacion OpenAI real V1

Rama dedicada: certificar GATE-02 / UAT-015 / UAT-020 con **una sola** llamada OpenAI via gateway.

| Artefacto | Ruta |
|-----------|------|
| Script PowerShell | `scripts/CERTIFICAR_V1_OPENAI_REAL_E8CB853.ps1` |
| Runbook | `INTERCAMBIO/SALIDA/CURSOR_V1_CERTIFICACION_OPENAI_REAL_E8CB853.md` |
| Pruebas sin costo | `scripts/TEST_CERTIFICAR_OPENAI_REAL_FLOW.ps1` |

## Pre-requisitos (Windows local)

1. Candidata `D:\EMPLEADOS_IA_CERT` @ `e8cb853`
2. Stack Docker certificado (`cursor/v1-certificacion-windows-tools`)
3. `OPENAI_API_KEY` en entorno Windows (no en archivos versionados)
4. Backend accesible en `http://127.0.0.1:15180` (nginx) con `OPENAI_API_KEY` en el contenedor backend

## Uso rapido

```powershell
git clone --branch cursor/v1-certificacion-openai-tools --single-branch `
  https://github.com/jcmencop12026/EMPLEADOS_IA.git D:\EMPLEADOS_IA_CERT_TOOLS

Set-Location D:\EMPLEADOS_IA_CERT_TOOLS
Set-ExecutionPolicy -Scope Process Bypass -Force

# OPENAI_API_KEY debe existir en el entorno de Windows (no pegar en el script)
.\scripts\CERTIFICAR_V1_OPENAI_REAL_E8CB853.ps1
```

Si la clave no esta presente:

```
OPENAI REAL: PENDIENTE POR CREDENCIAL LOCAL AUSENTE
```

**NO MERGE** — no modifica candidata V1 ni `main`.
