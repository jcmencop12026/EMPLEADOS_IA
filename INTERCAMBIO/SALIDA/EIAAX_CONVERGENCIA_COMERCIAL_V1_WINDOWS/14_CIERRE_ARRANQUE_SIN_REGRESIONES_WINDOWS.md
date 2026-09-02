# Cierre arranque Windows sin regresiones — backend congelado + frontend npm.cmd

**Rama:** `cursor/convergencia-comercial-v1-85e4`  
**Worktree:** `D:\EMPLEADOS_IA_CONVERGENCIA`

---

## 1. Causa exacta regresión 799d0fb

**Diff responsable:** `84d5330` → `83927dc` → `799d0fb` en `Build-EiaaxManagedProcessWrapperContent` / `Start-EiaaxManagedProcess`.

| SHA | Wrapper backend | Wrapper frontend |
|-----|-----------------|------------------|
| `84d5330` | Ejecución directa en `.bat` — **PASS Windows real** | Misma sintaxis — fallo quoting al añadir `start /B` en 83927dc |
| `83927dc` | `start /B cmd /c` + comillas externas sobre comando completo | `'"C:\Program"'` truncado |
| `799d0fb` | `start /B cmd /c` sin comillas externas — **rompe backend** | Quoting corregido pero backend roto |

**Error backend 799d0fb:** `El nombre de archivo, el nombre de directorio o la sintaxis de la etiqueta del volumen no son correctos.`

**Por qué rompió backend:** `start "EIAAX_..." /B cmd /c` reinterpreta redirecciones (`1>>`, `2>>&1`) y tokens con rutas Windows dentro de `cmd /c`, produciendo sintaxis inválida para `python.exe` aunque el frontend pareciera corregido.

## 2. Mecanismo final

### Backend (congelado desde 84d5330 — probado Windows real)

```batch
@echo off
set DATABASE_URL=...
cd /d "D:\EMPLEADOS_IA_CONVERGENCIA\backend"
"D:\EMPLEADOS_IA_CONVERGENCIA\.venv\Scripts\python.exe" "-m" "uvicorn" "app.main:app" "--host" "127.0.0.1" "--port" "8000" >> "D:\...\backend.log" 2>>&1
echo [EIAAX] EXIT_CODE=%ERRORLEVEL%>> "D:\...\backend.log"
```

- EXE: sin `call`, sin `cmd /c`, sin `start /B`
- Wrapper residente: bloquea en el servicio; `Start-Process` no usa `-Wait`

### Frontend (quoting corregido, misma familia de wrapper)

```batch
cd /d "D:\EMPLEADOS_IA_CONVERGENCIA\frontend"
call "C:\Program Files\nodejs\npm.cmd" "run" "dev" >> "D:\...\frontend.log" 2>>&1
echo [EIAAX] EXIT_CODE=%ERRORLEVEL%>> "D:\...\frontend.log"
```

- CMD/BAT: prefijo `call` + cada argumento citado por separado
- Sin comillas externas sobre el comando completo

### Orquestación (conservada desde 83927dc)

- `Invoke-EiaaxScriptInProcess` — sin deadlock PowerShell anidado
- `Invoke-EiaaxPowerShellFile` con redirect — tareas preparación sin bloqueo
- Timeouts, fail-closed, cleanup, checkpoints `[4/7.x]`–`[7/7]`

## 3. Matriz de regresión

| Caso | Remoto (Linux/pwsh) | Windows real |
|------|---------------------|--------------|
| Backend wrapper EXE directo | PASS (estructura) | Ejecuta + residente |
| Frontend npm.cmd espacios | PASS (estructura) | Ejecuta + residente |
| Sin `start /B cmd /c` | PASS | — |
| Sin deadlock orquestación | PASS | — |
| Suite completa | PASS exit 0 | Validación local |

## 4. Comando único validación local

```powershell
Set-Location "D:\EMPLEADOS_IA_CONVERGENCIA"; powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows\arrancar_convergencia_windows.ps1"
```

## 5. Limitación remota

No sustituye Windows real. Remoto valida generación de wrappers, matriz estática y suite; puertos 8000/5180 requieren validación local.
