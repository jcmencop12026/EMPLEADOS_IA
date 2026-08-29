# EMPLEADOS_IA — CONVERGENCIA 1250B
## Inteligencia externa + Diagnóstico transversal

**Rama:** `cursor/1250b-inteligencia-externa-diagnostico-85e4`  
**Base:** `166a04fa228433073936ea5d7dc2702f1a8324ae` (1220)  
**HEAD:** `3c0206ee48d34255b2ffa6ba79ba977c2d7b1a24`  
**Fecha:** 2026-08-29

---

## Objetivo

Integrar de forma controlada las evoluciones 1220 (diagnóstico transversal) y 1240 (inteligencia externa), ambas sobre 1120 (señales reales), en una cadena funcional única:

```
FUENTES INTERNAS + FUENTES EXTERNAS
  → SEÑALES
  → INDICADORES / HALLAZGOS
  → DIAGNÓSTICO
  → RIESGOS / OPORTUNIDADES
```

---

## Estrategia de integración Git

| Elemento | Valor |
|----------|-------|
| Rama origen 1220 | `cursor/1220-diagnostico-transversal` @ `166a04f` |
| Commits 1240 integrados | `0947480`, `b8798e0` (cherry-pick) |
| Ancestro común 1120 | `5eaad7e` — no reintegrado |
| Rama 1250B | `cursor/1250b-inteligencia-externa-diagnostico-85e4` |

Conflictos resueltos semánticamente (no ours/theirs indiscriminado) en:
- `backend/app/main.py`
- `backend/app/permissions.py`
- `frontend/src/App.tsx`, `AppShell.tsx`, `api.ts`, `auth/permissions.ts`
- `tests/conftest.py`

---

## Migraciones Alembic

| Revisión | Descripción |
|----------|-------------|
| `1120a1b2c3d4e` | Señales reales (ancestro común) |
| `1220a1b2c3d4e` | Diagnóstico transversal |
| `1240c3d4e5f6a` | Inteligencia externa |
| **`1250b1c2d3e4f`** | **MERGE** 1220 + 1240 |

**HEAD Alembic final:** `1250b1c2d3e4f` (una sola cabeza)

Ledger actualizado en `backend/alembic/migration_ledger.json` y `backend/scripts/schema_repair.py`.

---

## Integración funcional

### Backend (`diagnostic_service.py`)

- `detect_findings_from_external_signals()` — hallazgos desde `ExternalSignalExtension`
- Diferenciación **HECHO** / **INTERPRETACIÓN** / **HIPÓTESIS** (hipótesis en causas, no promovidas a hecho)
- Trazabilidad externa en evidencia: fuente, frescura, clasificación, relevancia, confianza
- Riesgos externos (`is_risk`) **no** generan oportunidad automática en diagnóstico
- Diagnóstico mixto interno + externo en un solo pipeline `generate_diagnostic()`
- `get_diagnostic_trace()` ampliado con `cadenas_externas`

### RBAC consolidado

- `diagnosticos.*` + `inteligencia_externa.*` + `oportunidades.*` sin pérdida
- Roles admin/superadmin/operator/viewer actualizados

### Frontend

Rutas y menú consolidados:
- `/senales`
- `/diagnosticos`
- `/inteligencia-externa`

Texto visible en español. Sin rutas huérfanas.

### No integrado (por diseño)

- Bloque 1210 (valoración económica / ROI)
- `valuation_contract_ref` conservado en extensiones externas

---

## Pruebas ejecutadas

| Suite | Resultado |
|-------|-----------|
| 1120 `test_senales_reales_1120.py` | **PASS** (11) |
| 1220 `test_diagnostico_transversal_1220.py` | **PASS** (15) |
| 1240 `test_inteligencia_externa_1240.py` | **PASS** (14) |
| 1250B `test_convergencia_1250b.py` | **PASS** (11) |
| Suite SQLite completa | **654 passed**, 1 failed (preexistente 1120), 2 skipped |
| `npm run build` | **PASS** |
| Migraciones control | **PASS** |

### Cobertura convergencia 1250B

- fuente externa → señal
- señal externa → hallazgo
- hallazgo externo → diagnóstico
- diagnóstico con señal interna + externa
- señal externa → oportunidad (sin duplicar)
- riesgo externo (sin oportunidad automática)
- deduplicación
- hecho vs interpretación vs hipótesis
- frescura
- tenant A/B transversal
- RBAC transversal
- empresa inactiva bloquea ingesta externa

---

## Salida final

```
EMPLEADOS_IA — CONVERGENCIA 1250B TERMINADA

RAMA:
cursor/1250b-inteligencia-externa-diagnostico-85e4

BASE:
166a04fa228433073936ea5d7dc2702f1a8324ae

HEAD:
3c0206e

1120: PASS
1220: PASS
1240: PASS
MIGRACIONES: PASS
HEAD ALEMBIC: 1250b1c2d3e4f
FUENTES INTERNAS: PASS
FUENTES EXTERNAS: PASS
DIAGNÓSTICO INTERNO+EXTERNO: PASS
TRAZABILIDAD: PASS
RIESGOS: PASS
OPORTUNIDADES: PASS
DEDUPLICACIÓN: PASS
RBAC: PASS
MULTIEMPRESA: PASS
UI: PASS
TESTS FOCALES: 51/51 PASS
TESTS CONVERGENCIA: 11/11 PASS
SUITE GENERAL: 654 passed, 1 failed (preexistente roundtrip 1120), 2 skipped
FRONTEND: PASS
P0: 0
P1: 1 (roundtrip Alembic 1120 preexistente — FK sin nombre en batch_alter_table)
P2: 0
VEREDICTO: APTO
NO MERGE.
```

---

## Nota P1

`test_migration_roundtrip_upgrade_downgrade_upgrade` falla al aplicar migración `1120a1b2c3d4e` (`ValueError: Constraint must have a name`). Este fallo ya existía en la rama 1220 antes de 1250B; no es regresión introducida por la convergencia.

---

EMPLEADOS IA. Convergencia inteligencia externa terminada.
