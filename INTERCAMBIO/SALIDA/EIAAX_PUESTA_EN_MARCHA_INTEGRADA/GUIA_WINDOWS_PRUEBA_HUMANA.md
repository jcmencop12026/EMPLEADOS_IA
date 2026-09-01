# EIAAX — Guia Windows para prueba humana

Procedimiento minimo para arrancar EIAAX integrado (Lote 3) en Windows con SQLite demo.

**Rama:** `cursor/windows-demo-arranque-85e4`  
**Worktree:** `D:\EMPLEADOS_IA_INTEGRADO`  
**Alembic head:** `1770a1b2c3d4e`

---

## INCIDENTE WINDOWS 791b7a4

### Fallo real

`preparar_demo_eiaax.ps1` fallo con errores de **parseo** en Windows PowerShell 5.1 antes de ejecutar cualquier logica.

### Causa raiz

1. Archivos `.ps1` en UTF-8 sin BOM con caracteres no ASCII (`preparacion` acentuada, guion largo).
2. `python -c "import sys; print('Python', sys.version)"` con comillas dobles ambiguas en PS 5.1.
3. `DemoA2026!` dentro de comillas dobles agravo el error de terminador de cadena.
4. `try` sin `catch`/`finally` en `iniciar_backend_demo.ps1`.
5. Validador Python previo no usaba el parser real de PowerShell.

### Correccion (SHA posterior a 791b7a4)

- Reescritura ASCII + UTF-8 BOM de todos los scripts.
- Version Python via `python -V` (sin `-c` fragil).
- Parser real obligatorio al inicio de preparacion.
- Estado en `.runtime-eiaax-demo`, logs en `logs\demo\`.
- Procesos en segundo plano sin ventanas extra; solo PIDs gestionados por la demo.
- Puertos ocupados: fail closed, no matar procesos ajenos.
- BD demo protegida fail-closed en scripts y seed.

### Validacion agente

Parser PowerShell real (`ParseFile`): **7/7 scripts, 0 errores**.  
Ejecucion Windows real: **pendiente confirmacion usuario**.

---

## Procedimiento (4 pasos)

### PASO A — Preparar demo

```powershell
cd D:\EMPLEADOS_IA_INTEGRADO
powershell -ExecutionPolicy Bypass -File .\scripts\windows\preparar_demo_eiaax.ps1
```

Incluye validacion del parser antes de preparar. Solo imprime exito si todo termina bien.

### PASO B — Iniciar EIAAX

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\iniciar_demo_eiaax.ps1
```

### PASO C — Abrir

| Campo | Valor |
|-------|-------|
| URL | http://127.0.0.1:5180 |
| Usuario | `org_a_admin` |
| Contrasena | ver `backend\scripts\credentials.example` |

### PASO D — Detener

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\detener_demo_eiaax.ps1
```

---

## Comando unico inicial (tras git pull)

```powershell
cd D:\EMPLEADOS_IA_INTEGRADO
powershell -ExecutionPolicy Bypass -File .\scripts\windows\validar_arranque_windows.ps1
```

Equivale a validar parser + preparar demo. Si falla, copie la salida completa.

---

## Rutas clave

| Concepto | Valor |
|----------|-------|
| BD demo | `D:\EMPLEADOS_IA_INTEGRADO\data\eiaax_integrado_demo.db` |
| Venv | `D:\EMPLEADOS_IA_INTEGRADO\.venv-eiaax-demo` |
| Estado | `D:\EMPLEADOS_IA_INTEGRADO\.runtime-eiaax-demo` |
| Logs | `D:\EMPLEADOS_IA_INTEGRADO\logs\demo\` |

---

## Si Python 3.14 falla

```powershell
$env:EIAAX_PYTHON = "C:\ruta\real\python.exe"
powershell -ExecutionPolicy Bypass -File .\scripts\windows\preparar_demo_eiaax.ps1
```

Solo use rutas que existan en su equipo.

---

## Que NO toca

- `D:\EMPLEADOS_IA`, `D:\EMPLEADOS_IA_CERT`, `D:\EMPLEADOS_IA_V1_HOTFIX`
- PostgreSQL y otras bases de datos
- Paquetes Python globales

---

## Scripts

| Script | Proposito |
|--------|-----------|
| `validar_arranque_windows.ps1` | Punto de entrada unico (parser + preparar) |
| `preparar_demo_eiaax.ps1` | Preparacion demo |
| `iniciar_demo_eiaax.ps1` | Arranque completo |
| `detener_demo_eiaax.ps1` | Detencion selectiva |
| `validate_ps_parse.ps1` | Parser real (interno/CI) |
