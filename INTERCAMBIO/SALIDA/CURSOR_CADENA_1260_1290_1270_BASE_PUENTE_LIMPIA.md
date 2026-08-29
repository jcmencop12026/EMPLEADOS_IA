# EMPLEADOS IA — Cadena 1260/1290/1270 base puente limpia

**Agente:** D — Verificación SHA Fase 1 + cadena portátil  
**Fecha:** 2026-08-29  
**Rama portátil:** `cursor/aprendizaje-optimizacion-multiproveedor-base-puente`  
**Base ancla:** `4b67183af1d527684e41cad0b02d7a997d3b2499` (`cursor/base-puente-v1-post-v1`)

---

## 0. Verificación SHA real Fase 1 (solo documental)

| Campo | Valor |
|-------|-------|
| Rama Fase 1 | `cursor/convergencia-final-post-v1-integracion` |
| **SHA REAL REMOTO** | `041209f4acabd595b5249c979a7e61031f598048` |
| Último commit | `041209f docs(convergencia): entregable fase 1 post-V1 integracion 1360/1350/1300/1370/1380` |
| merge-base con base-puente | `4b67183af1d527684e41cad0b02d7a997d3b2499` ✓ |
| Rama Fase 1 modificada | **NO** |

> Nota: el SHA `041209f4a8c8e8f3b0e2c8e5f3a7b2d1e9c4a6f` citado en instrucciones previas **no** coincide con el remoto verificado.

---

## 1. Genealogía Alembic portátil (temporal)

Cadena lineal sobre base puente:

```
1250f1a2b3c4d  (merge convergencia 1250A+1250B — base puente)
    ↓
1260a1b2c3d4e  (aprendizaje / repriorización) — reanclado desde 1250a1b2c3d4e
    ↓
1290a1b2c3d4e  (optimización / recomendaciones)
    ↓
1270a1b2c3d4e  (multiproveedor / observabilidad) — reanclado desde 1210b2c3d4e5f
```

**ALEMBIC HEADS:** 1  
**ALEMBIC HEAD:** `1270a1b2c3d4e`

### Re-parent futuro sobre Fase 1 certificada

Cuando Fase 1 esté auditada, la primera migración portada deberá re-parentarse al head real de Fase 1:

```
1380a1b2c3d4e  (head Fase 1 certificada)
    ↓
1260a1b2c3d4e
    ↓
1290a1b2c3d4e
    ↓
1270a1b2c3d4e
```

---

## 2. Commits funcionales portables

| Bloque | SHA completo | Origen funcional |
|--------|--------------|------------------|
| BASE | `4b67183af1d527684e41cad0b02d7a997d3b2499` | `cursor/base-puente-v1-post-v1` |
| PORT-1260 | `5769b45c7edc13d7ba335240a7948f8a25f245a7` | cherry-pick `6a6cfbcfaf64fde501e0586700d8e6639498f644` |
| PORT-1290 | `03427289c06ee0f7a992d63def699844c18e7534` | cherry-pick `fa6db17` (feat, no tip docs `7141b43`) |
| PORT-1270 | `2e8dcb236702027d00e5aeb716527fc76284682e` | cherry-pick `cd13421` (feat, no tip docs `f89639a`) |
| AJUSTE+PRUEBAS | `aad23271d18e9589de037c877a3cfcb662150675` | reanclaje Alembic, fixes observabilidad/CC, prueba focal |
| DOC | `3a64d98` | entregable `CURSOR_CADENA_1260_1290_1270_BASE_PUENTE_LIMPIA.md` |

**HEAD rama portátil:** `3a64d98` (incluye entregable documental)

---

## 3. Conflictos resueltos manualmente

Archivos fusionados preservando **1230 Centro de Control**, **1240 Inteligencia Externa**, **1250** y añadiendo 1260/1290/1270:

- `backend/app/main.py` — routers `inteligencia_externa`, `control_center`, `aprendizaje`, `optimizacion`
- `backend/app/permissions.py` — permisos IE + CC + aprendizaje + optimización
- `backend/scripts/schema_repair.py` — HEAD → `1270a1b2c3d4e`
- `backend/alembic/migration_ledger.json` — baseline_head + revisiones protegidas
- `frontend/src/App.tsx`, `AppShell.tsx`, `api.ts`, `auth/permissions.ts`
- `tests/conftest.py`

---

## 4. Resultados de pruebas

| Área | Resultado |
|------|-----------|
| 1260 aprendizaje | **PASS** (8 tests) |
| 1290 optimización | **PASS** (12 tests) |
| 1270 multiproveedor | **PASS** (14 tests) |
| Ciclo RESULTADO→APRENDIZAJE→RECOMENDACIÓN | **PASS** (`test_cadena_1260_1290_1270_integracion.py`) |
| Multiproveedor | **PASS** |
| Observabilidad | **PASS** (fix claves nulas en `por_proveedor`) |
| FinOps preservado | **PASS** (sin duplicar 1110; trazabilidad en logs inferencia) |
| Multiempresa | **PASS** (tests 1260/1290/1270 cross-tenant) |
| RBAC | **PASS** |
| SUPERADMIN | **PASS** (tests plataforma existentes) |
| SQLite Alembic | **PASS** (upgrade → downgrade 1250f → upgrade; 1 head) |
| PostgreSQL | **PENDIENTE POR ENTORNO** (sin credenciales reales) |
| Regresión backend | **809 passed, 4 skipped, 0 failed, 0 errors** |
| Frontend build | **PASS** (`npm run build`) |

### Preservación bloques previos

| Bloque | Preservado |
|--------|------------|
| V1 | **SÍ** |
| 1230 Centro de Control | **SÍ** |
| 1240 Inteligencia Externa | **SÍ** |
| 1250 convergencia | **SÍ** |

---

## 5. Hallazgos y ajustes menores

| ID | Severidad | Descripción | Estado |
|----|-----------|-------------|--------|
| — | P0 | 0 fugas multiempresa detectadas | — |
| — | P1 | 0 bloqueantes | — |
| OBS-1270 | P2 | Claves `None` en agregación `por_proveedor` rompían validación API | Corregido |
| CC-DT | P2 | Comparación naive/aware en vencimientos Centro de Control | Corregido |

---

## 6. Restricciones respetadas

- **NO** se modificó `cursor/convergencia-final-post-v1-integracion`
- **NO** Fase 2, main, V1, PR #32, merge, tags
- **NO** OpenAI real, Ollama, 1280/1310/1320/1330/1340/1350/1360/1300/1370/1380
- **NO** cableado 1260/1290/1270 → Centro de Control (1230)
- **NO** `git add .`

---

## 7. Veredicto

**APTO PARA PORTAR DESPUÉS DE CERTIFICAR FASE 1**

La cadena `1260 → 1290 → 1270` está construida de forma lineal sobre la base puente, con commits funcionales separados y pruebas PASS. Al converger sobre Fase 1 certificada, re-parentar `1260a1b2c3d4e` a `1380a1b2c3d4e`.

---

## SALIDA FINAL

```
EMPLEADOS IA — CADENA 1260/1290/1270 LIMPIA TERMINADA

SHA REAL FASE 1:
041209f4acabd595b5249c979a7e61031f598048

BASE PIEZA:
4b67183af1d527684e41cad0b02d7a997d3b2499

RAMA:
cursor/aprendizaje-optimizacion-multiproveedor-base-puente

HEAD:
3a64d98

PORT 1260:
5769b45c7edc13d7ba335240a7948f8a25f245a7

PORT 1290:
03427289c06ee0f7a992d63def699844c18e7534

PORT 1270:
2e8dcb236702027d00e5aeb716527fc76284682e

ALEMBIC HEADS:
1

ALEMBIC HEAD:
1270a1b2c3d4e

1260:
PASS

1290:
PASS

1270:
PASS

CICLO RESULTADO→APRENDIZAJE→RECOMENDACIÓN:
PASS

MULTIPROVEEDOR:
PASS

OBSERVABILIDAD:
PASS

FINOPS PRESERVADO:
PASS

MULTIEMPRESA:
PASS

RBAC:
PASS

SUPERADMIN:
PASS

SQLITE:
PASS (upgrade/downgrade/upgrade, 1 head)

POSTGRESQL:
PENDIENTE POR ENTORNO

REGRESIÓN:
809 passed, 4 skipped, 0 failed, 0 errors

FRONTEND:
PASS

1230 PRESERVADO:
SI

1240 PRESERVADO:
SI

1250 PRESERVADO:
SI

V1 PRESERVADA:
SI

P0:
0

P1:
0

P2:
2

RAMA CENTRAL FASE 1 MODIFICADA:
NO

MAIN:
NO MODIFICADO

V1:
NO MODIFICADA

MERGE:
NO

VEREDICTO:
APTO PARA PORTAR DESPUÉS DE CERTIFICAR FASE 1
```
