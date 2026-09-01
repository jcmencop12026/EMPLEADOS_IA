# EIAAX — Guia Windows para prueba humana

Procedimiento minimo para arrancar EIAAX integrado (Lote 3) en **Windows** con **SQLite demo**. No requiere PostgreSQL.

**Rama:** `cursor/windows-demo-arranque-85e4` (base: `cursor/integracion-lote-3-85e4`)  
**Worktree previsto:** `D:\EMPLEADOS_IA_INTEGRADO`  
**Alembic head:** `1770a1b2c3d4e`

---

## INCIDENTE WINDOWS 791b7a4

### Que fallo

Al ejecutar `preparar_demo_eiaax.ps1` en **Windows PowerShell 5.1**, el script no llego a ejecutarse: el parser fallo antes del runtime.

Errores observados:

- Linea ~33: `python -c "import sys; print('Python', sys.version)"` — comillas y comas ambiguas para PS 5.1.
- Linea ~107: cadena sin cerrar, disparada por `DemoA2026!` dentro de comillas dobles y por caracteres no ASCII (`preparacion` con acento, guion largo `—`).
- `iniciar_backend_demo.ps1` tenia un bloque `try` sin `catch`/`finally` (invalido en PS 5.1).

### Causa raiz

1. **Codificacion**: archivos `.ps1` en UTF-8 sin BOM + caracteres no ASCII. Windows PowerShell 5.1 interpreta el archivo con encoding del sistema y desincroniza el parser de cadenas.
2. **Quoting**: argumentos `python -c` con comillas dobles y comas dentro confunden al parser PS 5.1.
3. **`!` en cadenas dobles**: en combinacion con el desfase de encoding, agrava el error de terminador de cadena.
4. **Validacion previa insuficiente**: el validador Python aproximado no usa el parser real de PowerShell.
5. **Estados finales falsos**: instrucciones manuales posteriores al `throw` imprimian "COMPLETADO" aunque el script hubiera fallado.

### Que se corrigio

- Todos los `.ps1` reescritos en **ASCII puro** y guardados con **UTF-8 BOM**.
- Todos los `python -c` usan **comillas simples** externas: `-c 'import sys; print(sys.version)'`.
- Eliminadas contrasenas con `!` de cadenas dobles en salida de scripts.
- `try/catch` + `exit 1` en todos los scripts; mensajes de exito solo tras completar todas las etapas.
- Validador real: `validate_ps_parse.ps1` con `[System.Management.Automation.Language.Parser]::ParseFile`.
- Proteccion fail-closed de la BD demo en scripts y en `seed_lote3_demo.py`.
- Detencion limitada a PIDs/procesos gestionados por la demo.

### Como se valido

| Script | Parser PowerShell | Errores |
|--------|-------------------|---------|
| EiaaxDemo.Common.ps1 | PASS | 0 |
| preparar_demo_eiaax.ps1 | PASS | 0 |
| iniciar_backend_demo.ps1 | PASS | 0 |
| iniciar_frontend_demo.ps1 | PASS | 0 |
| iniciar_demo_eiaax.ps1 | PASS | 0 |
| detener_demo_eiaax.ps1 | PASS | 0 |
| validar_arranque_windows.ps1 | PASS | 0 |

Comando de validacion (agente y usuario):

```powershell
cd D:\EMPLEADOS_IA_INTEGRADO
powershell -ExecutionPolicy Bypass -File .\scripts\windows\validar_arranque_windows.ps1
```

### Limitaciones restantes

- **Ejecucion Windows real**: debe confirmarla el usuario en su equipo tras `git pull`.
- **Python 3.14.5**: no verificado en VM del agente; si `pip install` falla, usar `EIAAX_PYTHON`.

---

## Requisitos detectados

| Componente | Version observada | Compatibilidad |
|------------|-------------------|----------------|
| Python | 3.14.5 (`C:\Python314\python.exe`) | **No asumida** — probar; fallback `EIAAX_PYTHON` |
| Node.js | v24.16.0 | Si (requiere 20+) |
| npm | 11.13.0 | Si |
| PowerShell | 5.1+ (objetivo principal) | Si |

El procedimiento **no instala paquetes Python globalmente**. Crea un venv aislado en:

`D:\EMPLEADOS_IA_INTEGRADO\.venv-eiaax-demo`

---

## Procedimiento (4 pasos)

Abra **PowerShell** como usuario normal.

### PASO 0 — Validar scripts (recomendado tras git pull)

```powershell
cd D:\EMPLEADOS_IA_INTEGRADO
powershell -ExecutionPolicy Bypass -File .\scripts\windows\validar_arranque_windows.ps1
```

Si imprime `PARSER VALIDATION: PASS`, continuar. Si falla, no ejecutar preparacion.

### PASO A — Preparar demo (una vez, o al resetear datos)

```powershell
cd D:\EMPLEADOS_IA_INTEGRADO
powershell -ExecutionPolicy Bypass -File .\scripts\windows\preparar_demo_eiaax.ps1
```

Solo imprime exito si todas las etapas terminan bien (`exit 0`).

1. Crea/reutiliza venv Python en el worktree.
2. Instala dependencias backend.
3. Instala frontend con `npm ci` (existe `package-lock.json`).
4. Ejecuta `npm run build`.
5. Recrea **solo** `data\eiaax_integrado_demo.db` via seed.

**Importante:** el seed **no es idempotente** — borra y recrea la BD demo cada vez.

### PASO B — Iniciar EIAAX

```powershell
cd D:\EMPLEADOS_IA_INTEGRADO
powershell -ExecutionPolicy Bypass -File .\scripts\windows\iniciar_demo_eiaax.ps1
```

Valida BD demo, venv, puertos, `/health` y respuesta del frontend antes de declarar exito.

### PASO C — Abrir URL y entrar

| Campo | Valor |
|-------|-------|
| **URL** | http://127.0.0.1:5180 |
| **Usuario** | `org_a_admin` |
| **Contrasena** | ver `backend\scripts\credentials.example` |

| Usuario | Contrasena | Rol | Organizacion |
|---------|------------|-----|--------------|
| org_a_admin | DemoA2026! | admin | Empresa Demo A |
| org_a_viewer | DemoA2026! | viewer | Empresa Demo A |
| org_b_admin | DemoB2026! | admin | Empresa Demo B |

Health check backend:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/health -UseBasicParsing
```

### PASO D — Detener EIAAX

```powershell
cd D:\EMPLEADOS_IA_INTEGRADO
powershell -ExecutionPolicy Bypass -File .\scripts\windows\detener_demo_eiaax.ps1
```

Detiene solo procesos gestionados por la demo (PID files + validacion de command line).

---

## Rutas y DATABASE_URL Windows

| Concepto | Ruta / valor |
|----------|--------------|
| Worktree | `D:\EMPLEADOS_IA_INTEGRADO` |
| BD SQLite demo | `D:\EMPLEADOS_IA_INTEGRADO\data\eiaax_integrado_demo.db` |
| DATABASE_URL | `sqlite:///D:/EMPLEADOS_IA_INTEGRADO/data/eiaax_integrado_demo.db` |

Para otro directorio:

```powershell
$env:EIAAX_WORKTREE = "D:\ruta\alternativa"
```

---

## Scripts auxiliares

| Script | Proposito |
|--------|-----------|
| `scripts\windows\EiaaxDemo.Common.ps1` | Funciones compartidas |
| `scripts\windows\validate_ps_parse.ps1` | Parser real PS (uso interno/CI) |
| `scripts\windows\validar_arranque_windows.ps1` | **Comando unico de validacion** |
| `scripts\windows\preparar_demo_eiaax.ps1` | PASO A |
| `scripts\windows\iniciar_demo_eiaax.ps1` | PASO B |
| `scripts\windows\iniciar_backend_demo.ps1` | Solo backend |
| `scripts\windows\iniciar_frontend_demo.ps1` | Solo frontend |
| `scripts\windows\detener_demo_eiaax.ps1` | PASO D |

---

## Variables de entorno opcionales

| Variable | Uso |
|----------|-----|
| `EIAAX_WORKTREE` | Ruta del clon (default `D:\EMPLEADOS_IA_INTEGRADO`) |
| `EIAAX_PYTHON` | Ruta a `python.exe` si 3.14 no instala dependencias |

---

## Recuperacion ante error

| Sintoma | Accion |
|---------|--------|
| Error de parseo | `validar_arranque_windows.ps1`; asegurar `git pull` de rama corregida |
| pip falla en 3.14 | `$env:EIAAX_PYTHON = "C:\Python312\python.exe"` y repetir PASO A |
| Puerto en uso | `detener_demo_eiaax.ps1` |
| BD corrupta | Repetir PASO A (solo afecta BD demo) |

---

## Que NO toca este procedimiento

- No modifica `D:\EMPLEADOS_IA`.
- No instala PostgreSQL.
- No altera bases de otros proyectos.
- No cambia ramas V1/V2 ni hace merge.

---

## Referencias

- `COMO_PROBAR_EIAAX_INTEGRADO.md`
- `backend/scripts/seed_lote3_demo.py`
- `backend/scripts/credentials.example`
