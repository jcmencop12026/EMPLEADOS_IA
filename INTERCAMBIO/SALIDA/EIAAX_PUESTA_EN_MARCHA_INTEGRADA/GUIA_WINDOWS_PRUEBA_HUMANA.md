# EIAAX — Guía Windows para prueba humana

Procedimiento mínimo para arrancar EIAAX integrado (Lote 3) en **Windows** con **SQLite demo**. No requiere PostgreSQL.

**Rama:** `cursor/integracion-lote-3-85e4`  
**Worktree previsto:** `D:\EMPLEADOS_IA_INTEGRADO`  
**Alembic head:** `1770a1b2c3d4e`

---

## Requisitos detectados

| Componente | Versión observada en su equipo | Compatibilidad |
|------------|--------------------------------|----------------|
| Python | 3.14.5 (`C:\Python314\python.exe`) | **Probable** — si `pip install` falla, use 3.12 o 3.13 vía `EIAAX_PYTHON` |
| Node.js | v24.16.0 | **Sí** (requiere 20+) |
| npm | 11.13.0 | **Sí** |
| PowerShell | 5.1+ | **Sí** (scripts usan `${variable}` para evitar errores como `$p:`) |

El procedimiento **no instala paquetes Python globalmente**. Crea un venv aislado en:

`D:\EMPLEADOS_IA_INTEGRADO\.venv-eiaax-demo`

---

## Procedimiento (4 pasos)

Abra **PowerShell** como usuario normal (no hace falta administrador).

### PASO A — Preparar demo (una vez, o al resetear datos)

```powershell
cd D:\EMPLEADOS_IA_INTEGRADO
powershell -ExecutionPolicy Bypass -File .\scripts\windows\preparar_demo_eiaax.ps1
```

Qué hace:

1. Crea/reutiliza el venv Python en el worktree.
2. Instala dependencias backend (`requirements.txt`).
3. Instala frontend con `npm ci` (hay `package-lock.json`).
4. Ejecuta `npm run build` para validar el frontend.
5. Recrea la BD SQLite demo y ejecuta `backend/scripts/seed_lote3_demo.py`.

**Importante:** el seed **no es idempotente** — borra y recrea `data\eiaax_integrado_demo.db` cada vez.

Duración orientativa: 3–8 minutos (según red y CPU).

---

### PASO B — Iniciar EIAAX

```powershell
cd D:\EMPLEADOS_IA_INTEGRADO
powershell -ExecutionPolicy Bypass -File .\scripts\windows\iniciar_demo_eiaax.ps1
```

Se abren dos ventanas de consola (backend puerto **8000**, frontend puerto **5180**).

Scripts alternativos (mismo efecto, por separado):

- `scripts\windows\iniciar_backend_demo.ps1`
- `scripts\windows\iniciar_frontend_demo.ps1`

---

### PASO C — Abrir URL y entrar

| Campo | Valor |
|-------|-------|
| **URL** | http://127.0.0.1:5180 |
| **Usuario recomendado** | `org_a_admin` |
| **Contraseña** | `DemoA2026!` |

Otros usuarios demo:

| Usuario | Contraseña | Rol | Organización |
|---------|------------|-----|--------------|
| org_a_admin | DemoA2026! | admin | Empresa Demo A |
| org_a_viewer | DemoA2026! | viewer | Empresa Demo A |
| org_b_admin | DemoB2026! | admin | Empresa Demo B |

Detalle completo: `backend\scripts\credentials.example`

**Health check backend (opcional):**

```powershell
Invoke-WebRequest http://127.0.0.1:8000/health -UseBasicParsing
```

Respuesta esperada: HTTP 200, `status: up`.

El frontend proxifica `/api` y `/health` hacia `http://127.0.0.1:8000` (ver `frontend\vite.config.ts`).

---

### PASO D — Detener EIAAX

```powershell
cd D:\EMPLEADOS_IA_INTEGRADO
powershell -ExecutionPolicy Bypass -File .\scripts\windows\detener_demo_eiaax.ps1
```

Detiene procesos por PID guardado y libera puertos **8000** y **5180**.

También puede cerrar las ventanas de backend/frontend con `Ctrl+C`.

---

## Rutas y DATABASE_URL Windows

| Concepto | Ruta / valor |
|----------|--------------|
| Worktree | `D:\EMPLEADOS_IA_INTEGRADO` |
| BD SQLite demo | `D:\EMPLEADOS_IA_INTEGRADO\data\eiaax_integrado_demo.db` |
| DATABASE_URL | `sqlite:///D:/EMPLEADOS_IA_INTEGRADO/data/eiaax_integrado_demo.db` |

Los scripts calculan la URL automáticamente. **No use** la ruta Linux `sqlite:////workspace/data/...`.

Para otro directorio:

```powershell
$env:EIAAX_WORKTREE = "D:\ruta\alternativa"
```

---

## Scripts auxiliares versionados

| Script | Propósito |
|--------|-----------|
| `scripts\windows\EiaaxDemo.Common.ps1` | Rutas, venv, DATABASE_URL, health, puertos |
| `scripts\windows\preparar_demo_eiaax.ps1` | Preparación completa (PASO A) |
| `scripts\windows\iniciar_demo_eiaax.ps1` | Arranque backend + frontend (PASO B) |
| `scripts\windows\iniciar_backend_demo.ps1` | Solo backend |
| `scripts\windows\iniciar_frontend_demo.ps1` | Solo frontend |
| `scripts\windows\detener_demo_eiaax.ps1` | Detención limpia (PASO D) |

---

## Variables de entorno opcionales

| Variable | Uso |
|----------|-----|
| `EIAAX_WORKTREE` | Ruta del clon (default `D:\EMPLEADOS_IA_INTEGRADO`) |
| `EIAAX_PYTHON` | Ruta a `python.exe` si 3.14 no instala dependencias |

Ejemplo con Python 3.12:

```powershell
$env:EIAAX_PYTHON = "C:\Python312\python.exe"
powershell -ExecutionPolicy Bypass -File .\scripts\windows\preparar_demo_eiaax.ps1
```

---

## Problemas conocidos

1. **`"Puerto $p: ..."` falla en PowerShell** — `$p:` se interpreta como unidad de disco. Los scripts usan `${port}` o `$($port)`.
2. **Python 3.14 y wheels nativos** — `bcrypt`, `cryptography` o `psycopg2-binary` pueden no tener wheel aún. Solución: `EIAAX_PYTHON` → 3.12/3.13.
3. **Puerto en uso** — ejecute `detener_demo_eiaax.ps1` antes de reiniciar.
4. **Seed destruye la BD** — no ejecute preparar si quiere conservar datos locales de prueba.
5. **`ExecutionPolicy`** — use `-ExecutionPolicy Bypass` como en los ejemplos; no modifica la política del sistema de forma permanente.

---

## Recuperación ante error

| Síntoma | Acción |
|---------|--------|
| Backend no arranca | `detener_demo_eiaax.ps1` → volver a `iniciar_demo_eiaax.ps1` |
| Dependencias rotas | Borrar `.venv-eiaax-demo` y repetir PASO A |
| Frontend sin `node_modules` | Repetir PASO A |
| BD corrupta o datos viejos | Repetir PASO A (recrea SQLite) |
| Error pip en 3.14 | `$env:EIAAX_PYTHON = "C:\Python312\python.exe"` y PASO A |

---

## Qué NO toca este procedimiento

- **No** modifica `D:\EMPLEADOS_IA` (árbol original).
- **No** instala ni configura PostgreSQL.
- **No** altera bases de datos de otros proyectos.
- **No** borra archivos históricos del repositorio (solo recrea la BD demo en `data\`).
- **No** cambia ramas V1/V2 ni hace merge.
- **No** usa credenciales productivas ni OpenAI real.

---

## Validación realizada por el agente

| Prueba | Entorno agente | Resultado |
|--------|----------------|-----------|
| Flujo backend/seed/Alembic | Linux VM (Python 3.12) | Ver informe de commit |
| Frontend `npm ci` + `npm run build` | Linux VM (Node 22) | Ver informe de commit |
| Sintaxis PowerShell | Validación estática + parser | Ver informe de commit |
| Ejecución real Windows | No disponible en VM Linux | Usuario valida en su equipo |

---

## Referencias

- Procedimiento general (Linux/VM): `COMO_PROBAR_EIAAX_INTEGRADO.md`
- Semilla: `backend/scripts/seed_lote3_demo.py`
- Credenciales: `backend/scripts/credentials.example`
