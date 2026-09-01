# EIAAX 482ff6f — Puesta en marcha Windows (convergencia comercial V1)

**Estado:** LISTO PARA PRUEBA WINDOWS  
**Agente remoto:** no ejecuto Windows real; procedimiento unico certificado abajo.

---

## Identidad del candidato

| Campo | Valor |
|-------|-------|
| SHA convergencia (integracion) | `482ff6f` |
| SHA Windows arranque | `0b48139` (incluye preparador Alembic 1820) |
| Rama | `cursor/convergencia-comercial-v1-85e4` |
| PR | #159 |
| Base protegida | `d034566` — tag `eiaax-v1-preconvergencia-windows-operativo` |
| Alembic head | `1820a1b2c3d4e` (unico) |
| Ledger | `backend/alembic/migration_ledger.json` → baseline `1820` |

---

## Estrategia segura (sin tocar historico)

| Worktree | Proposito | Alterar |
|----------|-----------|---------|
| `D:\EMPLEADOS_IA` | Historico | **NO** |
| `D:\EMPLEADOS_IA_INTEGRADO` | Candidato pre-convergencia `d034566` | **NO** (rollback inmediato) |
| `D:\EMPLEADOS_IA_CONVERGENCIA` | Candidato convergido `482ff6f` | **SI** (recomendado) |

El script `arrancar_convergencia_windows.ps1` fija por defecto `EIAAX_WORKTREE=D:\EMPLEADOS_IA_CONVERGENCIA`.

---

## Procedimiento unico (usuario Windows)

### A. Primera vez — clonar worktree convergencia

En PowerShell (como administrador no requerido):

```powershell
cd D:\
git clone https://github.com/jcmencop12026/EMPLEADOS_IA.git EMPLEADOS_IA_CONVERGENCIA
cd D:\EMPLEADOS_IA_CONVERGENCIA
git fetch origin cursor/convergencia-comercial-v1-85e4
git checkout cursor/convergencia-comercial-v1-85e4
git rev-parse --short HEAD
# Debe mostrar: 482ff6f
```

Alternativa sin clonar (git worktree):

```powershell
cd D:\EMPLEADOS_IA_INTEGRADO
git fetch origin cursor/convergencia-comercial-v1-85e4
git worktree add D:\EMPLEADOS_IA_CONVERGENCIA cursor/convergencia-comercial-v1-85e4
```

### B. Arranque (un solo comando)

```powershell
cd D:\EMPLEADOS_IA_CONVERGENCIA
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\windows\arrancar_convergencia_windows.ps1
```

Equivale a: validar parser → preparar (venv, npm, seed, alembic 1820) → iniciar backend + frontend.

Opciones:

| Parametro | Efecto |
|-----------|--------|
| `-PrepareOnly` | Solo preparacion |
| `-StartOnly` | Solo arranque (BD ya preparada) |
| `-SkipPrepare` | Igual que StartOnly |

### C. Detener

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\windows\detener_demo_eiaax.ps1
```

---

## URL y puertos

| Servicio | URL |
|----------|-----|
| Frontend (recorrido humano) | http://127.0.0.1:5180 |
| Backend health | http://127.0.0.1:8000/health |
| API docs | http://127.0.0.1:8000/docs |

Puertos: backend **8000**, frontend **5180** (`strictPort: true` en Vite).

---

## Credenciales DEMO autorizadas

Ver `backend\scripts\credentials.example`:

| Usuario | Password | Rol | Organizacion |
|---------|----------|-----|--------------|
| `org_a_admin` | `DemoA2026!` | admin | Empresa Demo A |
| `org_a_viewer` | `DemoA2026!` | viewer | Empresa Demo A |
| `org_b_admin` | `DemoB2026!` | admin | Empresa Demo B |

Login: http://127.0.0.1:5180/login

---

## Que verifica el preparador (sin cambiar mecanismo)

- Parser PowerShell 5.1 (UTF-8 BOM, sin REPL interactivo)
- Python 3.12+ real (no WindowsApps stub)
- `npm.cmd` (no `npm.ps1` en editor)
- `alembic upgrade head` → `1820a1b2c3d4e`
- `seed_lote3_demo.py` (recrea solo `data\eiaax_integrado_demo.db`)
- Frontend `npm run build`
- Idempotencia puertos / procesos EIAAX

---

## Rollback a d034566

1. Detener convergencia: `detener_demo_eiaax.ps1` en worktree convergencia.
2. Ir a `D:\EMPLEADOS_IA_INTEGRADO` (tag `eiaax-v1-preconvergencia-windows-operativo`).
3. Ejecutar alli el flujo anterior de Windows demo (sin `arrancar_convergencia_windows.ps1`).
4. Respaldo verificado: `INTERCAMBIO\RESPALDOS\EIAAX_V1_PRECONVERGENCIA_WINDOWS\`

No se altera el tag ni el respaldo Lote3.

---

## Bloqueos reales conocidos

| ID | Bloqueo | Mitigacion |
|----|---------|------------|
| B-01 | Agente Linux no ejecuta Windows | Usuario ejecuta script unico arriba |
| B-02 | Puerto 8000/5180 ocupado | Script fail-closed; detener proceso ajeno manualmente |
| B-03 | Python 3.14 incompatible con deps | `EIAAX_PYTHON=C:\Python312\python.exe` |
| B-04 | Rutas nuevas no en sidebar | Acceso directo por URL (ver `03_RUTAS_RECORRIDO.md`) |
| B-05 | Demo comercial requiere semilla | En `/demo` usar accion semilla si manifest vacio |
| B-06 | Portal `/mi-espacio` requiere usuario externo | Crear acceso desde admin espacio externo |

---

## Cierre esperado

Tras ejecutar el script en Windows real:

- **Si arranca:** reportar `EIAAX 482ff6f — WINDOWS REAL OPERATIVO`
- **Si no se probo aun:** `EIAAX 482ff6f — LISTO PARA PRUEBA WINDOWS` (estado actual agente)
