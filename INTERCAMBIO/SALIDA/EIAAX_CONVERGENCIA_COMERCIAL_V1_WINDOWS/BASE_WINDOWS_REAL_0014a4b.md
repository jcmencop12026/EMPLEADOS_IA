# BASE WINDOWS REAL OPERATIVA — REFERENCIA CONGELADA

**SHA:** `0014a4b`
**Rama:** `cursor/convergencia-comercial-v1-85e4`
**Worktree:** `D:\EMPLEADOS_IA_CONVERGENCIA`
**Estado:** Validado en Windows real — WINDOWS REAL OPERATIVO

## Pipeline congelado (NO modificar en misión de producto)

- `scripts/windows/**`
- Bootstrap, Git sync, Python discovery, venv, wrappers, npm launcher
- Puertos 8000/5180, health checks, runtime identity, Alembic startup
- Fail-closed, cleanup, timeouts

## Comando único autoritativo

```powershell
Set-Location "D:\EMPLEADOS_IA_CONVERGENCIA"; powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows\arrancar_convergencia_windows.ps1"
```

## Verificación de preservación

Al cierre de cada misión de producto:

```bash
git diff 0014a4b -- scripts/windows/
```

Debe estar vacío.
