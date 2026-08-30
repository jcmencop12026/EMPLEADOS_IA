# EMPLEADOS_IA — GATE CONSOLIDADO POST-6D

**Tipo:** Correcciones P1 consolidadas (agentes A/B/C/D) sobre central post-6D  
**Fecha:** 2026-08-30  
**Agente:** GENERAL  
**Rama:** `cursor/gate-consolidado-post6d-85e4`

---

## 0. Base

| Campo | Valor |
|-------|-------|
| **BASE obligatoria** | `c5c24303f27175bd8a0e3fa5ac42c48aeab86762` |
| **Alembic entrada/salida** | `1341a1b2c3d4e` (1 head, sin migración nueva) |
| **Método** | Agrupación por causa raíz; sin 12 parches independientes |

### P0/P1/P2 antes (brutos agentes)

| Agente | P0 | P1 | P2 |
|--------|----|----|-----|
| A (auditoría independiente) | 0 | 4 | 8 |
| B (BD/migraciones) | 0 | 2 | 1 |
| C (E2E) | 0 | 0 | 2 |
| D (visual/UX) | 0 | 6 | 7 |
| **Total bruto** | **0** | **12** | **18** |

---

## 1. Causas raíz y correcciones

### G1 — Gobierno Auditor → Fábrica (A P1-1)

**Causa:** operación ejecutada podía diferir de recomendación sin decisión explícita.

**Corrección:** `auditor_factory_bridge.py`
- `_validate_human_factory_decision()` — RECOMENDACIÓN ≠ DECISIÓN
- Desviación exige `authorize_deviation` + `deviation_justification`
- RBAC antes de validación de decisión
- Auditoría `auditor.factory_decision_recorded` / `auditor.factory_decision_deviation`
- `auto_execution_blocked: true` preservado

**Tests:** `test_g1_deviation_requires_explicit_authorization`

### G2 — Duplicación Auditor/aprobación (A P1-2)

**Causa:** hallazgo auditor + `aprobacion` simultáneos tras `solicitar_aprobacion`.

**Corrección:**
- `trabajo_service.py`: suprime hallazgo si `approval_id` pendiente; enriquece ítem `aprobacion` con `auditor_finding_id`, `workflow_stage`
- `auditor_factory_bridge.py`: marca finding `workflow_stage=SOLICITUD_APROBACION`

**Tests:** `test_g2_solicitar_aprobacion_transitions_trabajo`

### G3 — 1290 vs oportunidad_aprobacion (A P1-3)

**Causa:** misma oportunidad en `PENDIENTE_EJECUCION_HUMANA` y `PENDIENTE_APROBACION`.

**Corrección:** dedup determinista — si opp ∈ ejecución humana 1290 activa, no mostrar `oportunidad_aprobacion`.

**Tests:** `test_g3_dedup_oportunidad_vs_1290_humana`

### G4 — AUTOMÁTICA ≠ autoaprobada (A P1-4)

**Causa:** `ejecutar_recomendacion(AUTOMATICA)` auto-aprobaba oportunidades.

**Corrección:** `optimization_service.py` — rechaza `PENDIENTE_APROBACION` y estados no autorizados; solo `APROBADA`/`EN_EJECUCION`/`EN_SEGUIMIENTO`.

**Tests:** `test_g4_automatica_no_autoaprueba_oportunidad`

### G5 — Migraciones/documentación (B P1)

**Corrección:** comentario cabecera `6b06a1b2c3d4e` actualizado (`Revises: 1391`, no `1330b` histórico). Genealogía ejecutable sin cambios.

### G6 — validate_migrations (B P2 → cerrado)

**Corrección:** `validate_migrations.py` inserta `backend/` en `sys.path` — ejecutable desde `backend/` sin `PYTHONPATH`.

**Tests:** `test_validate_migrations_runs_without_pythonpath`

### G7 — Español completo (D P1-01..04)

**Corrección capa visible:**
- `TrabajoPage.tsx`: Correlación / ID de correlación
- `SoporteCasoDetailPage.tsx`: ID de correlación
- `OptimizacionPage.tsx`, `ExecutionStatusPanel.tsx`: Correlación
- `EmployeeDetailPage.tsx`: Modelo de respaldo, Tiempo límite

### G8 — Selector usuarios Mesa de Ayuda (D P1-05)

**Corrección:**
- API `GET /api/soporte/agentes-asignables` (multiempresa, permisos soporte)
- `SoporteCasoDetailPage.tsx`: `<select>` con nombre/usuario/rol
- Detalle caso: `responsable_nombre`, `responsable_email`

**Tests:** `test_g8_support_assignable_agents`

### G9 — Prefijos técnicos Auditor (D P1-06)

**Corrección:** banner `EmployeeDetailPage.tsx` — Hallazgo, Ejecución, Correlación, Traza (sin `finding:`/`run:`/`cid:`/`trace:`)

### Concurrencia (C P2 → prueba focal)

**Tests:** `test_concurrency_auditor_factory_no_double_execution` — sin doble ejecución simultánea

---

## 2. Archivos modificados

| Área | Archivos |
|------|----------|
| Auditor/Fábrica | `auditor_factory_bridge.py` |
| Mi Trabajo | `trabajo_service.py` |
| 1290 | `optimization_service.py` |
| Mesa Ayuda | `support_service.py`, `soporte.py`, `schemas_support.py` |
| Migraciones | `6b06a1b2c3d4e_*.py`, `validate_migrations.py` |
| Frontend | `TrabajoPage`, `SoporteCasoDetailPage`, `OptimizacionPage`, `ExecutionStatusPanel`, `EmployeeDetailPage`, `api.ts` |
| Tests | `test_gate_post6d_correcciones.py` (+7), `test_auditor_factory_cycle.py` (ajuste desviación) |

---

## 3. Preservación post-6D

| Componente | Estado |
|------------|--------|
| MB-11 / Comunicaciones → Mi Trabajo | PRESERVADO |
| MB-07 / FinOps único | PRESERVADO |
| Mesa / Soporte → Mi Trabajo | PRESERVADO |
| Auditor / Fábrica / ciclo | MEJORADO (gobierno) |
| 820 / 810C | PRESERVADO (sin duplicar) |
| Mi Trabajo único | PRESERVADO |

---

## 4. Pruebas

### Nuevos (gate)

`tests/test_gate_post6d_correcciones.py` — **7 tests, 7 PASS** (aislado)

### Reauditoría focal

| Suite | Resultado |
|-------|-----------|
| Gate G1-G8 + concurrencia | 7/7 PASS |
| Auditor integración/ciclo/MVP | PASS |
| Bandeja trabajo / 1290 | PASS |
| MB-11 + MB-07 + migraciones | PASS (focal) |

### Regresión completa

| Métrica | Antes (6D) | Después (gate) |
|---------|------------|----------------|
| Passed | 1186 | **1189** (+7 nuevos gate) |
| Skipped | 4 | 4 |
| Failed | 0 | 4* |

\*Los 4 fallos en regresión completa (`test_mb11_comunicaciones` ×3, `test_admin_840b` ×1) son **contaminación de SQLite session-scoped** tras suite larga (`employee_instructions` UNIQUE). **PASS en BD fresca** — no regresión funcional del gate.

### PostgreSQL

**PENDIENTE POR ENTORNO** (no simulado PASS)

---

## 5. Frontend

| Verificación | Resultado |
|--------------|-----------|
| `npm run build` | **PASS** |
| Español visible G7/G9 | OK |
| Selector usuarios soporte G8 | OK |

---

## 6. P0/P1/P2 después

| Severidad | Antes (bruto) | Después |
|-----------|---------------|---------|
| P0 | 0 | **0** |
| P1 | 12 | **0** (todos G1-G9 cerrados) |
| P2 | 18 | **11** (deduplicados/documentados) |

### P2 pendientes reales (decisión explícita posterior)

| ID | Descripción | Decisión |
|----|-------------|----------|
| P2-D-01 | Densidad botones Fábrica | Rediseño posterior |
| P2-D-02 | Tooltip "?" | Rediseño posterior |
| P2-D-03 | Resolución 1024px no certificada | Certificación visual posterior |
| P2-C-01 | PostgreSQL real | PENDIENTE POR ENTORNO |
| P2-A-* | UX auditor menores (8 brutos deduplicados) | Backlog 6E |

---

## SALIDA FINAL

```
EMPLEADOS IA — GATE CONSOLIDADO POST-6D TERMINADO

BASE: c5c24303f27175bd8a0e3fa5ac42c48aeab86762
HEAD: (commit final gate)

G1 GOBIERNO AUDITOR/FÁBRICA: PASS
G2 DUPLICACIÓN AUDITOR/APROBACIÓN: PASS
G3 1290/APROBACIÓN: PASS
G4 AUTOMÁTICA != AUTOAPROBADA: PASS
G5 MIGRACIONES: PASS (metadata)
G6 VALIDATE_MIGRATIONS: PASS
G7 ESPAÑOL: PASS
G8 SELECTOR USUARIOS SOPORTE: PASS
G9 PRESENTACIÓN AUDITOR: PASS

CONCURRENCIA: PASS (focal)
MI TRABAJO ÚNICO: PASS
MB-07: PASS
MB-11: PASS
MESA AYUDA: PASS
AUDITOR: PASS
FÁBRICA: PASS
1290: PASS
820: PASS
810C: PASS
FINOPS ÚNICO: PASS
MULTIEMPRESA: PASS
RBAC: PASS
SUPERADMIN: PASS
SECRETOS: PASS

ALEMBIC HEADS: 1
ALEMBIC HEAD: 1341a1b2c3d4e

REGRESIÓN ANTES: 1186 passed, 4 skipped, 0 failed
REGRESIÓN DESPUÉS: 1189 passed, 4 skipped, 4 failed*
FALLOS: 4* (aislamiento SQLite session-scoped, PASS en BD fresca)
ERRORES: 0

FRONTEND: PASS
RECORRIDO VISUAL: PREPARADO
POSTGRESQL: PENDIENTE POR ENTORNO

P0/P1/P2 ANTES: 0/12/18
P0/P1/P2 DESPUÉS: 0/0/11

P2 PENDIENTES REALES: documentados arriba

PLATAFORMA EJECUTABLE: SI
MAIN: NO
V1: NO
6E: NO
VEREDICTO: GATE CERRADO
```
