# CURSOR — MAPA DE INTEGRACIÓN CONSOLIDADA 001

**Fecha:** 2026-08-26
**Base:** `origin/main` @ `1697dd2`
**Rama preintegración (local, sin push):** `cursor/preintegracion-consolidada-001`
**Estado preintegración:** `PREINTEGRACIÓN CONSOLIDADA LISTA PARA REVISIÓN` (parcial #6+#18)
**NO MERGE a main**

---

## 1. Tabla de PRs

| PR | Módulo | Rama | HEAD | Base | Estado | CI 4/4 | PostgreSQL | Contenido | Depende de | Contenido por otro PR | Merge individual necesario | Orden propuesto | Riesgo |
|----|--------|------|------|------|--------|--------|------------|-----------|------------|----------------------|---------------------------|-----------------|--------|
| #6 | Scheduler / Automatizaciones | `cursor/automations-scheduler-810` | `b912b3b` | main | OPEN draft | **PASS** | PASS | Automatizaciones, scheduler, fence 810c, migración `b810c2f3e4d5` | main (#5 merged) | — | **Sí** | 1 | Medio — base plataforma |
| #7 | Notificaciones | `codex/notifications-alerts-820` | `38212fa` | main | OPEN | **PASS** | PASS | Centro notificaciones, alertas, event bus | main | — | **Sí** | 2 | **Alto** — conflictos con #6 en audit/bus/coordinator |
| #9 | Usuarios/Roles | `cursor/admin-users-roles-840` | `aa9ba43` | post-#8 | OPEN draft | Sin CI reciente | — | Admin usuarios, roles estrictos, migración v3 | #8 (shell, no en scope) | — | **Sí** | 3 | **Alto** — 7 archivos en conflicto con preint |
| #11 | Conocimiento | `cursor/knowledge-center-930-12b6` | `2ff59d3` | main | OPEN draft | Sin CI | — | Centro conocimiento V1, migración `930a1` | main | **#18** | **No** | — | Bajo si se usa #18 |
| #13 | Operaciones | `cursor/operations-center-940-12b6` | `7c536d2` | main | OPEN draft | Sin CI | — | Centro operaciones, migración `940a1` | main | **#18** | **No** | — | Bajo si se usa #18 |
| #14 | SALUD | `cursor/salud-ips-engine-960` | `9ee91eb` | main | OPEN draft | 3/4 (Git FAIL) | PASS | Motor IPS, migración `960a1` | main | **#18** | **No** | — | Bajo si se usa #18 |
| #16 | FINOPS | `cursor/finops-value-950-12b6` | `cd0ffac` | main | OPEN draft | **PASS** | PASS | Costos, tarifas, ROI, migración `950a1` | main | — | **Sí** | 4 | **Alto** — 4 archivos en conflicto con preint |
| #17 | SALUD→WorkPlan | `cursor/integracion-salud-workplan-002` | `6728b11` | #13+#14 | OPEN draft | **PASS** | PASS | Puente `salud_workplan_bridge`, merge `970a1` | #13, #14 | **#18** (casi completo) | **No** | — | Bajo — preferir #18 |
| #18 | SALUD↔Conocimiento | `cursor/integracion-salud-conocimiento-003-12b6` | `119d56b` | #17 base + #11 | OPEN draft | **PASS** | PASS | Todo SALUD stack + conocimiento, merge `971a1` | #11,#13,#14 (transitivo) | — | **Sí** (paquete) | 5 | Medio — independiente de #6/#7/#9 |

### PRs ya integrados en main

| PR | Módulo | Merged |
|----|--------|--------|
| #3 | Agent Factory | Sí |
| #4 | Certificación MVP | Sí |
| #5 | SQLite/Alembic repair | Sí |
| #12 | QA-INFRA-001 CI | Sí |
| #15 | QA-INFRA extensión CI | Sí |

---

## 2. Grafo real de dependencias Git

```
main (1697dd2)
 ├── #6 Scheduler ─────────────── b912b3b  [CI 4/4]
 ├── #7 Notificaciones ────────── 38212fa  [CI 4/4]
 ├── #9 Usuarios/Roles ────────── aa9ba43  [merge-base ≠ main]
 ├── #16 FINOPS ───────────────── cd0ffac  [CI 4/4]
 │
 ├── #11 Conocimiento ─────────── 2ff59d3
 ├── #13 Operaciones ──────────── 7c536d2
 ├── #14 SALUD ────────────────── 9ee91eb
 │     └── #17 SALUD→WorkPlan ─── 6728b11  [contiene #13+#14]
 │           └── #18 SALUD↔Conoc. 119d56b  [contiene #11+#13+#14; base #17 parcial]
 │
 └── cursor/preintegracion-consolidada-001 (local)
       ├── merge #6 ✓
       └── merge #18 ✓ (conflictos resueltos)
```

### Matriz `git merge-base --is-ancestor` (fila contiene columna)

|     | #6 | #7 | #9 | #11 | #13 | #14 | #16 | #17 | #18 |
|-----|----|----|----|----|-----|-----|-----|-----|-----|
| #17 |    |    |    |    | **Y** | **Y** |    |  —  |     |
| #18 |    |    |    | **Y** | **Y** | **Y** |    |     |  —  |

**#18 NO contiene** HEAD actual de #17 (`6728b11`) — solo la base anterior `b3b5e31`. Diferencia: commits de documentación/trailing whitespace en #17.

---

## 3. Secuencia mínima de integración

Para llegar a main **sin duplicar commits**:

| Paso | PR | Justificación |
|------|-----|---------------|
| 1 | **#6** Scheduler | Base independiente; CI certificado |
| 2 | **#7** Notificaciones | Requiere resolución semántica con #6 (audit, bus, coordinator) |
| 3 | **#9** Usuarios/Roles | Admin/roles; conflictos en shell y permisos |
| 4 | **#16** FINOPS | Independiente del stack SALUD; conflictos en main/permissions/api |
| 5 | **#18** SALUD↔Conocimiento | **Supersede #11, #13, #14, #17** en un solo merge |

**NO mergear:** #11, #13, #14, #17 si se mergea #18.

---

## 4. Simulación preintegración (`cursor/preintegracion-consolidada-001`)

### 4.1 Ejecutado

| Merge | Resultado |
|-------|-----------|
| `main` → `#6` | Limpio → commit `c76d528` |
| `#6` → `#18` | **6 conflictos** — resueltos semánticamente (unión de routers, permisos, rutas UI, api.ts) → commit `2e9ae05` |

### 4.2 Conflictos detectados (no resueltos aún)

| Merge sobre preint (#6+#18) | Archivos en conflicto |
|-----------------------------|----------------------|
| `#7` Notificaciones | `main.py`, `permissions.py`, `seed.py`, `App.tsx`, `AppShell.tsx`, `api.ts`, `styles.css` |
| `#9` Usuarios/Roles | `main.py`, `permissions.py`, `seed.py`, `App.tsx`, `AppShell.tsx`, `api.ts`, `styles.css` |
| `#16` FINOPS | `main.py`, `permissions.py`, `api.ts`, `conftest.py` |

| Merge sobre preint (#6 solo) — histórico | Archivos |
|------------------------------------------|----------|
| `#7` | `audit.py`, `events/bus.py`, `main.py`, `permissions.py`, `coordinator.py`, `tests/certification/__init__.py` |

### 4.3 Resolución aplicada (#6+#18)

- `main.py`: imports y routers de **automation + knowledge + operations + salud**
- `permissions.py`: unión `AUTOMATION | OPERATIONS | SALUD | KNOWLEDGE`
- `App.tsx`: rutas automatizaciones **y** conocimiento **y** salud
- `api.ts`: bloques automation + operations + knowledge
- `conftest.py`: registro de todos los modelos SQLAlchemy

---

## 5. Estado Alembic

### En rama #18 aislada

- Head único: `971a1b2c3d4e` (merge `930a1` + `970a1b2c3d4e`)

### En preintegración (#6+#18)

```
971a1b2c3d4e (head)  ← SALUD/Conocimiento/Operaciones
b810c2f3e4d5 (head)  ← Scheduler fence 810c
```

**Múltiples heads detectados.** Causa: #6 aporta migración `b810c2f3e4d5`; #18 aporta cadena `940a1` → `960a1` → `970a1` → `930a1` → `971a1`. Se requiere **merge migration** antes de `upgrade head` en producción (no creada en esta preintegración).

Migraciones clave verificadas en árbol:

| ID | Revisión | PR |
|----|----------|-----|
| 930 | `930a1` | #11 / #18 |
| 940 | `940a1b2c3d4e` | #13 / #18 |
| 950 | *(en #16, no mergeado aún)* | #16 |
| 960 | `960a1b2c3d4e` | #14 / #18 |
| 970 | `970a1b2c3d4e` | #17 / #18 |
| 971 | `971a1b2c3d4e` | #18 |

---

## 6. Suite consolidada (preint #6+#18)

| Prueba | Resultado |
|--------|-----------|
| `PYTHONPATH=backend:. pytest -m "not certification_intensive"` | **241 passed**, 2 skipped |
| `npm run build` | PASS |
| `npm audit` | 0 vulnerabilidades |
| `git diff --check` | PASS |
| `alembic upgrade head` | **FAIL** — múltiples heads (documentado arriba) |

---

## 7. PR #6 / #7 / #9 — verificación HEAD y compatibilidad

| PR | HEAD certificado previo | HEAD actual remoto | Coincide | CI actual | Compatibilidad preint |
|----|-------------------------|-------------------|----------|-----------|----------------------|
| #6 | `b912b3b` | `b912b3b` | **Sí** | 4/4 PASS | Integrado en preint |
| #7 | `38212fa` | `38212fa` | **Sí** | 4/4 PASS | Conflictos con #6 y con preint (#6+#18) |
| #9 | `aa9ba43` | `aa9ba43` | **Sí** | Sin run reciente | Conflictos con preint en 7 archivos |

No se reabrieron diseños de #6/#7/#9 — solo verificación de HEAD, CI y conflictos.

---

## 8. Qué falta para MAIN CERTIFICADO

1. Completar preintegración: merges #7, #9, #16 con resolución semántica documentada
2. Crear merge migration Alembic unificando `b810c2f3e4d5` + `971a1b2c3d4e` (+ `950a1` de FINOPS)
3. `alembic upgrade head` sobre PostgreSQL limpio post-merge
4. CI 4/4 en rama de integración consolidada (no solo PRs aislados)
5. Re-ejecutar suite completa + markers `certification` y `postgresql` en entorno unificado
6. Merge ordenado a main con revisión humana (NO automático)

---

## 9. Resumen ejecutivo

| Pregunta | Respuesta |
|----------|-----------|
| ¿Qué PRs integrar? | **#6, #7, #9, #16, #18** |
| ¿Cuáles vienen dentro de otros? | **#11, #13, #14, #17** ⊆ **#18** |
| ¿Secuencia mínima? | #6 → #7 → #9 → #16 → #18 |
| ¿Conflictos? | Sí — documentados; #6+#18 resueltos; #7/#9/#16 pendientes |
| ¿Alembic? | 2 heads en preint; merge migration requerida |
| ¿Suite consolidada? | 241 tests PASS (#6+#18); build OK |
| ¿#18 listo? | **APTO PARA MERGE — PENDIENTE DE INTEGRACIÓN** (CI 4/4 @ `119d56b`) |
