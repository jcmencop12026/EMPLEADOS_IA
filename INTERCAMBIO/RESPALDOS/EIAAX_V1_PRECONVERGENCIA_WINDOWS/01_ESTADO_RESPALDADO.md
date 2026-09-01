# 01 — Estado respaldado

## Declaración

**ESTE ES EL PUNTO OPERATIVO WINDOWS ANTERIOR A LA CONVERGENCIA COMERCIAL V1 A+B+C+D.**

## Identificación

| Campo | Valor |
|-------|-------|
| **Fecha/hora respaldo (UTC)** | 2026-09-01T18:25:00Z |
| **Proyecto** | EIAAX |
| **Repositorio** | `jcmencop12026/EMPLEADOS_IA` |
| **Rama respaldada** | `cursor/windows-demo-arranque-85e4` |
| **SHA respaldado** | `d034566` (`d0345663f0fcc286d9b68146735a05208839bd7e`) |
| **Tag de seguridad** | `eiaax-v1-preconvergencia-windows-operativo` → `d034566` |
| **Alembic head** | `1770a1b2c3d4e` (único) |

## Estado funcional documentado (Windows real)

| Componente | Estado al respaldar |
|------------|---------------------|
| Preparador productivo | COMPLETADO |
| Backend | `http://127.0.0.1:8000/health` OK |
| Frontend | `http://127.0.0.1:5180` OK |
| Login demo | OK (`org_a_admin`) |
| Empresa Demo A | OK |
| Seed / migraciones | OK |
| Revisión visual humana | INICIADA |
| Convergencia A+B+C+D | **NO integrada** |

## Distinción candidato vs correcciones Windows

### Candidato funcional integrado (Lote 3 / puesta en marcha)

| Referencia | SHA | Notas |
|------------|-----|-------|
| SHA final puesta en marcha (docs) | `75fc689` | Punto documental Lote 3 integrado |
| Base entregables puesta en marcha | `da81af7` | Entregables validación integrada |
| Rama origen integración | `cursor/integracion-lote-3-85e4` | Ancestro de la rama Windows |

**No confundir** `75fc689` con los commits posteriores del preparador/arranque Windows.

### Correcciones posteriores de arranque Windows (incluidas en este respaldo)

14 commits desde `75fc689` hasta `d034566`, incluyendo:

- `791b7a4` — scripts Windows iniciales
- `fd5dc19` — separación preparador / autotests dev
- `0e05020` — Alembic stderr INFO
- `d034566` — frontend npm.cmd (punto operativo final)

## Worktree Windows de prueba

| Campo | Valor |
|-------|-------|
| Worktree | `D:\EMPLEADOS_IA_INTEGRADO` |
| BD demo | `D:\EMPLEADOS_IA_INTEGRADO\data\eiaax_integrado_demo.db` |
| URL demo | `http://127.0.0.1:5180` |
| Backend | `http://127.0.0.1:8000` |

## A+B+C+D — NO integrados

| Bloque | SHA referencia | Estado en repo |
|--------|----------------|----------------|
| A | `f0d02bc` | NO presente en remoto local |
| B | `2bb3caa` | NO presente en remoto local |
| C | `25c79d5` | NO presente en remoto local |
| D | `40b7c9b` | NO presente en remoto local |

## Git status al respaldar (workspace agente)

- HEAD limpio en `d034566` para el respaldo Git
- Modificación local no incluida en SHA: `INTERCAMBIO/SALIDA/EIAAX_INTEGRACION_LOTE_3/17_SHA_CANDIDATO.md`
- No versionados (no eliminados): `.venv-eiaax-demo/`, logs locales, respaldos previos

## Respaldo anterior

`INTERCAMBIO/RESPALDOS/EIAAX_LOTE_3/` — **intacto**, no sobrescrito.
