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

## INCIDENTE DETECCION PYTHON f081077

### Fallo real

Tras `PARSER VALIDATION: PASS`, la preparacion fallo con:

`ERROR: No suitable Python runtime found`

aunque `C:\Python314\python.exe` (Python 3.14.5) existe en el equipo.

### Causa raiz

Ese mensaje **no lo genera EIAAX**: lo emite `py.exe` (Python Launcher) cuando se invoca
`py -3.14` sin runtime registrado en el launcher. Con `$ErrorActionPreference = Stop`,
el error terminaba `Find-EiaaxPython` antes de validar `C:\Python314\python.exe`.

### Correccion

- Eliminado `py.exe` del descubrimiento de Python.
- Busqueda directa de `python.exe` en rutas reales (`C:\Python314`, Program Files, AppData).
- Ignorados stubs de WindowsApps.
- Mensajes diferenciados: `PYTHON NOT FOUND` vs `PYTHON X DETECTED BUT INCOMPATIBLE`.
- Log de cada candidato en `logs\demo\preparar.log`.

---

## INCIDENTE REPL INTERACTIVO (SHA 68112b0)

### Fallo real

`test_ps_semantics.ps1` ejecutaba `python.exe` sin argumentos y abrio el REPL `>>>`, bloqueando la preparacion.

### Correccion

- Autotests usan ejecutables no interactivos (`hostname.exe`, `cmd /c exit 0`, `/bin/true` en VM).
- Guard en `Invoke-EiaaxNativeCommand` rechaza python/node sin argumentos.
- Subprocesos de prueba con timeout (30s); `-NonInteractive` en todas las invocaciones PowerShell.
- `Invoke-EiaaxPowerShellFile` centraliza invocaciones sin REPL ni ventanas interactivas.

### Validacion agente (post-correccion)

- Parser: **10/10 scripts, PARSE ERRORS = 0**
- `test_ps_semantics.ps1`: **PASS** (`AUTOTESTS INTERACTIVE: 0`)
- `test_python_discovery.ps1`: **PASS** (`AUTOTESTS INTERACTIVE: 0`)
- Cadena backend (venv/pip/seed/Alembic) y frontend (npm/build): **PASS EN VM Linux**
- Ejecucion Windows real completa: **pendiente confirmacion usuario** (Python 3.14.5 ya confirmado)

---

## INCIDENTE ALEMBIC .Count (SHA 66db838)

### Fallo real

Tras seed exitoso (`"status": "ok"`), la preparacion fallo en `Verifying Alembic state...` con:

`No se encuentra la propiedad 'Count' en este objeto. Compruebe que existe.`

### Causa raiz

En `Confirm-EiaaxAlembicState`, la comprobacion de multiples heads usaba:

`($headsOutput -split ... | Where-Object { ... }).Count`

En Windows PowerShell 5.1, cuando `Where-Object` devuelve **un solo** elemento, el resultado es un **escalar** (string), no un array. Los escalares no tienen propiedad `.Count`. Con un unico head (caso normal tras seed) la verificacion fallaba.

### Correccion

- Helpers `Get-EiaaxCollectionCount`, `ConvertTo-EiaaxArray`, `Get-EiaaxAlembicHeadRevisions`, `Get-EiaaxAlembicCurrentRevisions`
- Verificacion Alembic por revision ID parseada, no por conteo fragil de pipeline
- Nuevo `test_ps_alembic.ps1` con regresion 0/1/N elementos
- Auditoria de todos los usos `.Count` en scripts Windows

### Evidencia Windows real confirmada (no revertir)

- PowerShell ejecutando scripts: OK
- Python 3.14.5 (`C:\Python314\python.exe`): OK
- venv, pip, requirements: OK
- Seed demo (`Empresa Demo A/B`, `status: ok`): OK
- Fallo unicamente en verificacion Alembic post-seed

---

## INCIDENTE AUTOTEST CASE 3 (SHA 8d00469)

### Fallo real

CASE 2 PASS (C:\Python314\python.exe detectado). CASE 3 fallo con:

`PYTHON NOT FOUND: no python.exe candidates detected on this machine.`

La suite completa aborto antes de CASE 4-7.

### Causa raiz

1. CASE 3 usaba `Get-Command python` (PATH/WindowsApps) en vez de `C:\Python314\python.exe`.
2. `Find-EiaaxPython` llama `exit 1` en el mismo proceso del autotest (no capturable por try/catch).

### Correccion (SHA 39421c5)

- CASE 3 usa `Get-EiaaxKnownWindowsPythonExe` y subproceso aislado.
- Setup/teardown de `EIAAX_PYTHON` por caso.
- CASE 4-7 revisados con el mismo patron de aislamiento.

---

### Fallo real

Tras parser PASS, la preparacion fallo con:

`No se puede enlazar el argumento con el parametro 'List' porque es una coleccion vacia.`

### Causa raiz

`Add-EiaaxPythonCandidate` tenia `[Mandatory][List[string]]$List`. En Windows PowerShell 5.1,
pasar una lista vacia al primer intento de descubrimiento provoca error de parameter binding.

Ademas `Get-ChildItem -Depth` no existe en PS 5.1.

### Correccion

- Eliminado helper con parametro `List` Mandatory.
- Descubrimiento con scriptblock local y retorno `@($array)`.
- Busqueda AppData sin `-Depth`; escaneo `C:\` solo si existe.

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
