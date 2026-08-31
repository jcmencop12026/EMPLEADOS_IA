# EMPLEADOS_IA — BLOQUE 1250A — CONVERGENCIA POST-V1 FASE 1

**Agente:** C  
**Rama:** `cursor/1250a-convergencia-post-v1`  
**Base:** `4c03cbe`  
**Fecha:** 2026-08-29  

---

## 1. Matriz de ramas integradas

| Bloque | Rama origen | HEAD verificado | Base | Depende de | Migración | Riesgo conflicto |
|--------|-------------|-----------------|------|------------|-----------|------------------|
| 1100 | `cursor/1100-cierre-operativo-oportunidades` | `3bc3979` | `4c03cbe` | — | — | Medio (`OportunidadDetailPage`) |
| 1110 | `cursor/1110-finops-trazabilidad-economica` | `6234638` | `4c03cbe` | — | `1110a1b2c3d4e` | Alto (`OportunidadDetailPage`, `permissions`) |
| 1120 | `cursor/1120-senales-reales-deteccion` | `5eaad7e` | `4c03cbe` | — | `1120a1b2c3d4e` | Medio (`main.py`) |
| 1200 | `cursor/1200-linea-base-impacto` | `0278177` | `4c03cbe` | — | `1200a1b2c3d4e` | Medio (`main.py`, `styles.css`) |
| 1210 | `cursor/1210-valoracion-economica-roi-85e4` | `076bca6` (PR #35) | rama 1110 | 1110 | `1210b2c3d4e5f` | Alto (`main.py`, `permissions`, `OportunidadDetailPage`) |
| 1220 | `cursor/1220-diagnostico-transversal` | `166a04f` (PR #36) | `5eaad7e` | 1120 | `1220a1b2c3d4e` | Alto (`main.py`, `permissions`, frontend rutas) |

**No integrados:** 1230, 1240, V1 candidata `831d0c2`, PR #32.

---

## 2. Orden de integración utilizado

Cherry-pick de commits funcionales (sin docs-only duplicados), respetando ancestry:

1. `e6e74d2` → 1100 (`a976a43`)
2. `bc7e53c` → 1110 (`ba5ea72`) — conflicto `OportunidadDetailPage`
3. `38f7b7d` → 1120 (`9469373`)
4. `0278177` → 1200 (`443819e`) — conflictos `main.py`, `styles.css`
5. Fix convergencia 1100+1110 (`1bb231f`)
6. `8f8e57f` → 1210 (`d17a3c7`) — conflictos `main.py`, `permissions`, `OportunidadDetailPage`
7. `ac1668f` → 1220 (`bbf3f22`) — conflictos `main.py`, `permissions`, `conftest.py`
8. Migración merge Alembic `1250a1b2c3d4e` (convergencia)

---

## 3. Conflictos y resolución

| # | Archivo | Resolución |
|---|---------|------------|
| 1 | `backend/app/main.py` | Registro de todos los modelos y routers: `senales`, `linea_base`, `valoracion`, `diagnosticos` |
| 2 | `backend/app/permissions.py` | Unión de `LINEA_BASE`, `VALORACION`, `DIAGNOSTICOS` en catálogo, roles admin/superadmin/operator/viewer |
| 3 | `frontend/src/pages/OportunidadDetailPage.tsx` | Cadena operativa 1100 + pestaña FinOps 1110 + pestaña Valoración 1210 |
| 4 | `frontend/src/styles.css` | Fusión estilos 1100 + 1200 |
| 5 | `tests/conftest.py` | Imports `baseline_models`, `valuation_models`, `diagnostic_models` |

**Total conflictos resueltos:** 5 archivos (múltiples regiones por archivo).

---

## 4. Alembic

**Heads encontrados antes del merge:**

- `1200a1b2c3d4e` (desde `d1e2f3a4b5c6`)
- `1210b2c3d4e5f` (cadena `1110` → `1210`)
- `1220a1b2c3d4e` (cadena `1120` → `1220`)

**Migración merge creada:**

- `1250a1b2c3d4e_merge_convergencia_post_v1_1250a.py`
- `down_revision`: `["1200a1b2c3d4e", "1210b2c3d4e5f", "1220a1b2c3d4e"]`

**Head final:** `1250a1b2c3d4e`

**Ledger actualizado:** `backend/alembic/migration_ledger.json`  
**HEAD_REVISION:** `backend/scripts/schema_repair.py` → `1250a1b2c3d4e`

---

## 5. Modelos registrados

| Módulo | Bloque | Tablas principales |
|--------|--------|-------------------|
| `finops_models` | 1110 | consumos, presupuestos |
| `opportunity_models` | 1030/1100/1120 | opportunities, signals, tracking |
| `baseline_models` | 1200 | líneas base, mediciones, impacto |
| `valuation_models` | 1210 | valoraciones, escenarios, costos |
| `diagnostic_models` | 1220 | diagnósticos, hallazgos, indicadores |

Sin tablas duplicadas ni entidades Opportunity paralelas.

---

## 6. RBAC consolidado

Permisos activos en convergencia:

- `oportunidades.*` (1030/1100)
- `finops.*` (1110)
- `linea_base.*` (1200)
- `valoracion.*` (1210)
- `diagnosticos.*` (1220)
- Señales reutilizan `oportunidades.view` en rutas frontend

---

## 7. Multiempresa

Verificado en pruebas focales y convergencia:

- Aislamiento oportunidades, líneas base, valoraciones, diagnósticos entre tenants
- Org inactiva bloquea operaciones (con restauración en test 1200 para no contaminar suite)

---

## 8. Frontend

- Rutas: `/oportunidades`, `/senales`, `/lineas-base`, `/diagnosticos`
- Menú `AppShell.tsx` consolidado
- `OportunidadDetailPage`: resumen, seguimiento, resultado, ejecución, trazabilidad, FinOps, valoración
- `npm run build`: **PASS**

---

## 9. Pruebas

### Focales por bloque (SQLite fresco)

| Bloque | Resultado | Tests |
|--------|-----------|-------|
| 1100 | PASS | 7 |
| 1110 | PASS | 11 |
| 1120 | PASS | 11 |
| 1200 | PASS | 14 |
| 1210 | PASS | 19 |
| 1220 | PASS | 15 |
| **Total focal** | **PASS** | **74/74** |

### Convergencia (`tests/test_convergencia_1250a.py`)

| Caso | Resultado |
|------|-----------|
| señal → oportunidad | PASS |
| diagnóstico → oportunidad | PASS |
| oportunidad → seguimiento/resultado | PASS |
| oportunidad → FinOps | PASS |
| oportunidad → línea base | PASS |
| oportunidad → valoración | PASS |
| aislamiento multiempresa | PASS |
| RBAC transversal | PASS |
| **Total convergencia** | **8/8 PASS** |

### Suite general SQLite

- **681 passed**, 2 skipped, **5 failed**
- Fallos en suite larga por contaminación de estado (org inactiva sin restaurar en tests legacy P0/prerelease/1120) — reproducibles solo en orden de suite completa; focales y convergencia pasan en DB fresca.

---

## 10. P0 / P1 / P2

| ID | Severidad | Descripción |
|----|-----------|-------------|
| P0 | 0 | Sin bloqueantes funcionales en módulos integrados |
| P1 | 1 | `test_admin_840b_v3::test_migration_roundtrip` falla en downgrade SQLite (constraint sin nombre) con historial extendido |
| P2 | 4 | Tests de suite larga con contaminación por org inactiva (P0/prerelease/1120) — no afectan focales ni convergencia |

---

## 11. Veredicto

**APTO** para convergencia post-V1 fase 1.

- Rama integrada operativa con los 6 bloques
- Un solo head Alembic
- Oportunidad como eje transversal verificado
- Trazabilidad señal→diagnóstico→oportunidad→FinOps→línea base→valoración compatible
- **NO MERGE** a main

---

## 12. Commits de integración

```
a976a43 feat(1100): cierre operativo UI oportunidades y cadena de ejecución
ba5ea72 feat(finops): trazabilidad costo-oportunidad y FinOps operativo (bloque 1110)
9469373 feat(1120): señales reales, ingesta y detección proactiva B1.5
443819e feat(1200): línea base, medición posterior e impacto B2.1
1bb231f fix(1250a): fusionar FinOps 1110 con cierre operativo 1100 en OportunidadDetailPage
d17a3c7 feat(valoracion): motor económico, escenarios y ROI por oportunidad (bloque 1210)
bbf3f22 feat(1220): diagnóstico transversal multidominio sobre señales 1120
```

Commit adicional: `8572a4f` — merge Alembic, pruebas convergencia, entregable.

**HEAD final rama:** `8572a4f520fabd4b9d251ccfb0dddeb6600dc44d`
