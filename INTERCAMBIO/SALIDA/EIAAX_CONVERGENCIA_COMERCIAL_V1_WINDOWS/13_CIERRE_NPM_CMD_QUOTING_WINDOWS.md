# Cierre regresión frontend — quoting npm.cmd con espacios (Windows)

**Rama:** `cursor/convergencia-comercial-v1-85e4`
**Worktree:** `D:\EMPLEADOS_IA_CONVERGENCIA`

---

## 1. Causa exacta

**Archivo:** `scripts/windows/EiaaxDemo.Common.ps1`
**Función:** `Start-EiaaxManagedProcess` (ahora delega en `Build-EiaaxManagedProcessWrapperContent`)
**Línea afectada (patrón anterior):** construcción de `$serviceCommand` + `Get-EiaaxBatchQuotedArgument` sobre el comando completo

### Comando incorrecto anterior

El wrapper `.bat` generaba una línea equivalente a:

```batch
start "EIAAX_run_frontend" /B cmd /c "call \"C:\Program Files\nodejs\npm.cmd\" \"run\" \"dev\" >> \"D:\...\frontend.log\" 2>>&1"
```

Windows interpretaba el primer token entre comillas como ejecutable `"C:\Program"` (truncado en el espacio), produciendo:

```
'"C:\Program"' no se reconoce como un comando interno o externo
```

### Mecanismo corregido

Cada segmento se cita por separado; **no** se envuelve el argumento completo de `cmd /c` en comillas externas:

```batch
start "EIAAX_run_frontend" /B cmd /c call "C:\Program Files\nodejs\npm.cmd" "run" "dev" 1>>"D:\...\frontend.log" 2>>&1
```

`Build-EiaaxManagedProcessWrapperContent` expone la generación del wrapper para pruebas de regresión.

## 2. Conservación de correcciones previas

Sin cambios en:

- servicios desacoplados (`start /B`, sin `-Wait` residente);
- checkpoints `[4/7.1]`–`[4/7.6]`;
- timeouts, fail-closed, cleanup, PID ownership;
- rechazo de `npm.ps1`;
- UTF-8 BOM, parser aggregate, Git stderr, bootstrap, Python discovery, Alembic, backend health.

## 3. Pruebas de regresión

`test_service_startup.ps1` valida:

| Caso | Resultado esperado |
|------|-------------------|
| A. Ruta sin espacios | PASS |
| B. Ruta con espacios (`C:\Program Files\...`) | PASS |
| C. Argumentos con espacios | PASS |
| D. Servicio residente | wrapper `start /B` + `exit /b 0` (no bloquea) |
| E/F. Fallo / log tail | `New-EiaaxStartupFailureMessage` incluye salida reciente |
| Windows real (opcional) | `tool.cmd` en ruta con espacios ejecuta y escribe log |

## 4. Comando único (validación local)

```powershell
Set-Location "D:\EMPLEADOS_IA_CONVERGENCIA"; powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows\arrancar_convergencia_windows.ps1"
```

## 5. Criterio de cierre remoto

**EIAAX — REGRESIÓN FRONTEND WINDOWS CORREGIDA Y CANDIDATO LISTO PARA VALIDACIÓN LOCAL FINAL**

No se declara `WINDOWS REAL OPERATIVO` sin ejecución Windows real del operador.
