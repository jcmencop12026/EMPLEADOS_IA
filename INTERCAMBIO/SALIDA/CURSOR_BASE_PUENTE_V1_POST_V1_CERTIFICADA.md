# EMPLEADOS_IA — BASE PUENTE V1 + POST-V1 CERTIFICADA

**Rama:** `cursor/base-puente-v1-post-v1`  
**Fecha:** 2026-08-29  
**Tipo:** Ejecución controlada — puente de bases

---

## Objetivo cumplido

Base puente que contiene **simultáneamente**:

- **A.** Post-V1 convergido 1100–1250 (`eb229806`)
- **B.** Delta funcional V1 final (4 commits cherry-pick)

Sin integración de 1260–1380.

---

## Referencias inmutables verificadas

| Ref | SHA | Estado |
|-----|-----|--------|
| V1 candidata | `e8cb853a2c447fd5e136a0907e44d68ce2c8cf81` | OK (`origin`) |
| POST-V1 | `eb229806136e29acddc0f592b5f017f5c3cb2958` | OK (`origin`) |
| Merge-base | `4c03cbe0ba0ff8537452ec58f7aaca7ce18bede4` | OK |

---

## Commits V1 aplicados (orden)

| Orden | SHA | Mensaje | Conflicto |
|-------|-----|---------|-----------|
| 1 | `36a7af6` | fix(docker): DATABASE_URL seguro | Auto-merge |
| 2 | `eb7476d` | fix(config): precedencia DATABASE_URL | Auto-merge |
| 3 | `72e6b0e` | fix(security): bootstrap + prod validation | Auto-merge `main.py` |
| 4 | `460405f` | fix(ui): Knowledge auth + español | Resuelto: `CostosValorPage`, `OportunidadDetailPage` |

**HEAD puente:** `d57b831e41b8e017da612c3c442f9f29c981f674`

### Resolución de conflictos (460405f)

- **POST-V1 preservado:** cadena operativa, toolbar completo, pestaña valoración, FinOps extendido
- **V1 incorporado:** descarga Knowledge autenticada, labels español, subtítulo «Costos y consumo»

---

## Diff control vs `eb229806`

32 archivos, +1209 / −67 líneas — **exclusivamente delta V1** + docs INTERCAMBIO de los commits.

### Preservación POST-V1 verificada

| Componente | Estado |
|------------|--------|
| 1100–1220 (FinOps, Señales, Línea base, Valoración, Diagnóstico) | OK |
| 1230 Centro de Control | OK (`control_center.py`, `CentroControlPage.tsx`) |
| 1240 Inteligencia Externa | OK |
| Migraciones 1250a / 1250b / 1250f | OK |
| Routers en `main.py` | OK (control_center, inteligencia_externa, senales, etc.) |

### Preservación V1 verificada

| Componente | Estado | Diff vs `e8cb853` |
|------------|--------|-------------------|
| `security_config.py` | OK | 0 líneas |
| `db_url.py` | OK | 0 líneas |
| `config.py` | OK | 0 líneas |
| `docker-compose.yml` / entrypoint / `alembic/env.py` | OK | incorporado |
| Knowledge descarga autenticada | OK | 0 líneas vs V1 |
| `test_docker_database_url.py` | OK | 0 líneas |
| `test_security_rbac_v1.py` | OK | 0 líneas |

---

## Alembic

| Verificación | Resultado |
|--------------|-----------|
| `alembic heads` | **1 cabeza:** `1250f1a2b3c4d` |
| `1110.down_revision` | `d1e2f3a4b5c6` (ancestro V1 confirmado) |
| Nueva merge revision | **NO creada** (no necesaria) |
| `schema_repair.HEAD_REVISION` | `1250f1a2b3c4d` (sin cambio) |

---

## Pruebas

### V1 focal

| Suite | Resultado |
|-------|-----------|
| `test_docker_database_url.py` | PASS |
| `test_security_rbac_v1.py` | PASS |
| `test_knowledge_930.py` | PASS |
| `test_migration_control.py` | PASS |

### POST-V1 focal

| Suite | Resultado |
|-------|-----------|
| `test_senales_reales_1120.py` | PASS |
| `test_valoracion_1210.py` | PASS |
| `test_bloque_1230_centro_control.py` | PASS |
| `test_inteligencia_externa_1240.py` | PASS |
| `test_convergencia_final_1250.py` | PASS |

### Suite general SQLite

**774 passed, 4 skipped, 0 failed, 0 errors**

### PostgreSQL

**NO EJECUTADO** — sin instancia PostgreSQL ni Docker en entorno de certificación.  
Clasificado **P2** (validación pendiente en entorno con PG real).

### Frontend

`npm run build` — **PASS**

---

## Seguridad

| Control | Resultado |
|---------|-----------|
| Bootstrap inseguro en prod | **NO** (validación endurecida) |
| JWT producción inseguro | **NO** (mín. 32 chars) |
| CORS inseguro en prod | **NO** (sin `*`) |
| DATABASE_URL especial | **PASS** (tests) |
| Knowledge sin autenticación | **NO** |
| SUPERADMIN | **PASS** (RBAC tests) |
| Multiempresa | **PASS** (suite general) |
| RBAC | **PASS** |
| Secretos versionados | **0** |

---

## P0 / P1 / P2

| Nivel | Cantidad | Detalle |
|-------|----------|---------|
| **P0** | 0 | — |
| **P1** | 0 | — |
| **P2** | 1 | PostgreSQL upgrade/downgrade no ejecutado en este entorno |

---

## Restricciones respetadas

- NO integrado 1260–1380
- NO modificado `main`, V1, PR #32
- NO merge a main
- NO `git add .` (staging explícito en commits cherry-pick)

---

## Uso como base de convergencia

Esta rama sustituye a `eb229806` como **raíz recomendada** para incorporar 1260–1380.

Actualizar `CURSOR_PLAN_UNICO_CONVERGENCIA_FINAL_POST_V1.md` (cuando proceda):

- Base: `d57b831e41b8e017da612c3c442f9f29c981f674`
- Gate puente V1: **COMPLETADO**

---

## Veredicto

**BASE PUENTE CERTIFICADA**
