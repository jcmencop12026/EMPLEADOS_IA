# Cierre bloqueo post-backend health — arranque servicios Windows

**Rama:** `cursor/convergencia-comercial-v1-85e4`
**Worktree:** `D:\EMPLEADOS_IA_CONVERGENCIA`

---

## 1. Causa exacta del bloqueo

**Archivo:** `iniciar_demo_eiaax.ps1` + `Invoke-EiaaxPowerShellFile` en `EiaaxDemo.Common.ps1`
**Operación:** `Start-Process -Wait -NoNewWindow` anidado (arrancar → iniciar_demo → backend/frontend)

Tras imprimir `Backend health OK`, `iniciar_demo` lanzaba el frontend en **otro proceso PowerShell** con `-Wait` compartiendo consola. Esa cadena anidada podía quedar bloqueada indefinidamente (deadlock de consola / espera sobre proceso hijo) antes de mostrar cualquier salida del frontend.

Además, `Start-EiaaxManagedProcess` ejecutaba `npm run dev` / `uvicorn` de forma **síncrona dentro del .bat** (`call npm.cmd run dev`), manteniendo el wrapper bloqueado aunque el script PowerShell ya hubiera continuado.

## 2. Corrección

| Cambio | Efecto |
|--------|--------|
| `Invoke-EiaaxScriptInProcess` | Arranque backend/frontend en el mismo runspace (sin PowerShell anidado) |
| `arrancar` → `iniciar_demo` in-process | Elimina un nivel de `-Wait` |
| `Start-EiaaxManagedProcess` con `start /B cmd /c` | Servicios residentes desacoplados del script |
| `Invoke-EiaaxPowerShellFile` con redirect stdout/stderr | Tareas (preparar) sin deadlock de consola |
| Checkpoints `[4/7.x]` | Visibilidad de progreso |
| Rechazo explícito de `npm.ps1` en arranque servicio | Evita launcher incorrecto |
| Timeouts 45–60s en health/puertos | Sin espera infinita |

## 3. Comando único

```powershell
Set-Location "D:\EMPLEADOS_IA_CONVERGENCIA"; powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows\arrancar_convergencia_windows.ps1"
```

## 4. Limitación remota

No se puede certificar `WINDOWS REAL OPERATIVO` sin ejecución Windows real. Remoto valida lógica y regresiones estáticas/simuladas.
