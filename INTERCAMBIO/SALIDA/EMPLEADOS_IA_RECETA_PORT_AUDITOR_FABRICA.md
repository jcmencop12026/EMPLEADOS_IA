# EMPLEADOS IA — RECETA DE PORTABILIDAD
## Ciclo Auditor → Mi Trabajo → Fábrica

**Agente:** C (certificación final)
**Fecha:** 2026-08-29
**Rama origen certificada:** `cursor/ciclo-auditor-fabrica-dec7`
**HEAD:** `0de93ec5abf03670fc2e6d27635b3bc9314e8b39`
**Base destino esperada:** rama de integración vigente (NO `cursor/fase2-central-integracion`, NO `main`, NO `V1`)

---

## A. Prerrequisitos centrales

General debe verificar que la rama destino ya tiene (o portará antes del ciclo):

| Prerrequisito | Revisión / módulo | Motivo |
|---------------|-------------------|--------|
| Agent Factory base | `5b2eb2437398` | Empleados IA, versionado base |
| Knowledge Center | `930a1` (reutilizado, no duplicar) | Contexto empleado |
| Cadena multitenant / org | `c1a2b3c4d5e6` o equivalente central | `organization_id` en todas las tablas |
| Head Alembic central conocido | anotar SHA + `revision` | Punto de reparent obligatorio |
| Wiring 1330 (si aplica en central) | `1330a` + `1330b` | Padre actual de `6b06` y `1400` en origen |

**NO portar desde origen:** commits de Centro de Control (1220/1240 P1), vistas 1300/1370/1380, ensayo comercial, ni wiring histórico salvo que central los requiera explícitamente.

---

## B. Commits funcionales exactos a portar

Portar **contenido funcional**, no el historial completo `041209f..0de93ec` (97 archivos mezclan CC/wiring).

| Etapa | Commits | HEAD certificado | Tipo |
|-------|---------|------------------|------|
| 1. Mi Trabajo núcleo | `40e76bc` | `40e76bc` | feat |
| 2. Auditor MVP | `9fbe416`, `1033fcd` | `3d066ae` | feat + fix Alembic |
| 3. Auditor → Mi Trabajo | `599d69b` | `be761f6` | feat |
| 4. Fábrica MB-06 | `6430da8`, `dccc40f`, `8759bb9` | `a5c518b` | feat + P1 UI |
| 5. Puente (merge + fix) | `d575d06`, `817f501` | `817f501` | merge selectivo + fix |
| 6. Documentación | `0de93ec` | `0de93ec` | docs (opcional) |

**Commits de solo documentación** (`3d066ae`, `be761f6`, `a5c518b`, `0de93ec`): opcionales para código; útiles como evidencia.

---

## C. Orden REAL de integración

Orden verificado por dependencias de código y Alembic (no asumir el orden conceptual sin validar):

```text
[Prerrequisitos infra central: head conocido]
    ↓
1. Mi Trabajo núcleo (40e76bc)
    ↓
2. Auditor MVP (9fbe416 + 1033fcd)     ─┐
    ↓                                    │ paralelos desde mismo padre Alembic
3. Auditor → Mi Trabajo (599d69b)        │ (requiere pasos 1 y 2)
    ↓                                    │
4. Fábrica MB-06 (6430da8→8759bb9)     ─┘
    ↓
5. Alembic merge 14b0 (requiere 6b06 + 1400 aplicados)
    ↓
6. Puente 14b1 + código bridge (d575d06 selectivo + 817f501)
```

**Nota:** En origen, `6b06` y `1400` comparten `down_revision = 1330b1b2c3d4f`. En central, **reparentar** ambos sobre el head real equivalente, no copiar `1330b` ciegamente.

---

## D. Archivos conflictivos esperados

| Archivo | Capas que lo tocan | Estrategia |
|---------|-------------------|------------|
| `backend/app/main.py` | Mi Trabajo, Auditor | Merge manual de routers |
| `backend/app/permissions.py` | Auditor, Fábrica, Puente | Unión de permisos sin duplicar |
| `frontend/src/api.ts` | Todas | Añadir endpoints, no reemplazar |
| `frontend/src/App.tsx` / `AppShell.tsx` | Mi Trabajo, Auditor | Rutas `/trabajo`, `/empleados-auditor` |
| `backend/app/services/trabajo_service.py` | Mi Trabajo, Auditor→Trabajo, Puente | Conservar bandeja + `revisar_fabrica` |
| `backend/app/routers/empleados_auditor.py` | Auditor + Puente | MVP + endpoints puente |
| `backend/app/employee_audit_models.py` | Auditor + Puente | Modelos auditor + `EmployeeImprovementTrace` |
| `frontend/src/pages/EmployeeDetailPage.tsx` | Fábrica P1 + Puente | Pestaña Aprobación + banner auditor |
| `backend/alembic/migration_ledger.json` | Todas las migraciones | Añadir revisiones sin borrar protegidas |
| `backend/scripts/schema_repair.py` | Auditor, Fábrica | Merge conservador |

**Del merge `d575d06` NO portar** (arrastre histórico):
- `control_center_service.py`, `control_center_adapters.py`, `diagnostic_service.py`
- `CentroControlPage.tsx`
- `test_centro_control_*`, `test_diagnostico_transversal_1220.py`
- Docs `CURSOR_FASE2_CENTRAL_TRAMO*.md`

---

## E. Migraciones — inventario y reglas

### Revisiones del ciclo (rama certificada)

| revision_id | down_revision (origen) | Rol | Portar |
|-------------|------------------------|-----|--------|
| `6b06a1b2c3d4e` | `1330b1b2c3d4f` | Fábrica MB-06 tablas | SÍ — reparentar |
| `1400a1b2c3d4e` | `1330b1b2c3d4f` | Auditor MVP tablas | SÍ — reparentar |
| `14b0c1d2e3f4` | (`6b06`, `1400`) | Merge Alembic | SÍ — tras ambas ramas |
| `14b1c2d3e4f5` | `14b0c1d2e3f4` | Puente `employee_improvement_traces` | SÍ |

### Verificación explícita solicitada

| revision_id | Estado en rama | Colisión repo |
|-------------|----------------|---------------|
| `6b06a1b2c3d4e` | 1 archivo, head parcial | SIN COLISIÓN |
| `1400a1b2c3d4e` | 1 archivo, head parcial | SIN COLISIÓN |
| `14b1c2d3e4f5` | 1 archivo, **HEAD único** | SIN COLISIÓN |
| `1390a1b2c3d4e` | NO presente (renombrado → `1400`) | NO_APLICA |
| `1391a1b2c3d4e` | NO presente | NO_APLICA |
| `1507a1b2c3d4e` | NO presente | NO_APLICA |

**Cabecera Alembic:** 1 head = `14b1c2d3e4f5`

### Migración puente `14b1c2d3e4f5` — especificación exacta

| Atributo | Valor |
|----------|-------|
| `revision` | `14b1c2d3e4f5` |
| `down_revision` | `14b0c1d2e3f4` |
| Tabla creada | `employee_improvement_traces` |
| FK | `organizations`, `ai_employees`, `employee_audit_runs`, `employee_audit_findings`, `users` (×2), `employee_versions`, `approval_requests`, `employee_test_runs` |
| Índices | `ix_emp_improvement_org`, `_employee`, `_finding`, `_status` |
| Constraint | `uq_emp_improvement_idempotency` (`organization_id`, `idempotency_key`) |
| Campos clave | `correlation_id`, `recommendation`, `work_item_ref`, `status`, `outcome_classification`, `factory_operation`, `evidence_json`, snapshots before/after |
| Depende tablas previas | `employee_audit_*` (1400), `employee_versions`/`approval_requests`/`employee_test_runs` (6b06) |

**NO cambiar** la migración por estética; solo reparentar `down_revision` si la cadena central difiere.

---

## F. Reparent Alembic requerido

General **NO** debe copiar `down_revision = 1330b1b2c3d4f` si central ya tiene esas tablas bajo otro revision_id.

| Migración | Acción en central |
|-----------|-------------------|
| Tablas ya existentes en central (agent factory, org, users) | **NO portar** — ya están |
| `6b06a1b2c3d4e` | **REPARENTAR** `down_revision` → head central real |
| `1400a1b2c3d4e` | **REPARENTAR** `down_revision` → mismo head (rama paralela) |
| `14b0c1d2e3f4` | **PORTAR** cuando existan ambos padres en central |
| `14b1c2d3e4f5` | **PORTAR** tras `14b0`; `down_revision` permanece `14b0` |

Si central ya tiene `6b06` o `1400` aplicados: **no re-aplicar**; saltar al merge/puente según corresponda.

---

## G. Pruebas después de cada etapa

| Tras etapa | Comando | Aborto si |
|------------|---------|-----------|
| Mi Trabajo | `pytest tests/test_bandeja_trabajo_humano.py -q` | cualquier FAIL |
| Auditor | `pytest tests/test_employee_auditor_mvp.py -q` | cualquier FAIL |
| Auditor→Trabajo | `pytest tests/test_auditor_integracion_mi_trabajo.py -q` | cualquier FAIL |
| Fábrica MB-06 | `pytest tests/test_employee_lifecycle_factory_mb06.py tests/test_agent_factory_e2e.py -q` | cualquier FAIL |
| Puente completo | `pytest tests/test_auditor_factory_cycle.py -q` | cualquier FAIL |
| Migraciones | `pytest tests/test_migration_control.py -q` | cualquier FAIL |
| Alembic SQLite | `alembic upgrade head && alembic downgrade -1 && alembic upgrade head` | error DDL |
| Frontend | `cd frontend && npm run build` | build FAIL |

**Suite focal certificada (rama origen):** 70 tests PASS (60 core + 10 e2e).

---

## H. Condición de aborto

Detener el port y escalar si ocurre **cualquiera**:

1. Segundo head Alembic tras merge de migraciones.
2. Colisión de `revision_id` con migración ya existente en central.
3. Duplicación detectada: segundo `ApprovalRequest`, segunda bandeja `/trabajo`, segundo `auditor_factory_bridge`, segundo workflow de mejora.
4. `auto_execution_blocked` ausente o `false` en contrato puente.
5. Fallo RBAC/multiempresa en tests de ciclo.
6. Regresión focal > 0 failed tras integrar una etapa.

---

## I. Recorrido visual final

```text
/trabajo
  → ítem hallazgo auditor (acción "Revisar en Fábrica")
  → /empleados/{id}?finding_id=...&correlation_id=...
  → banner contexto Auditor (recomendación, NO ejecución automática)
  → "Iniciar mejora" (traza idempotente)
  → acción fábrica autorizada (capacitar / probar / publicar según RBAC)
  → reauditoría opcional
  → clasificación resultado (PENDIENTE_VALIDACION | MEJORADO | SIN_CAMBIO | EMPEORADO | NO_DETERMINADO)
```

**Principio invariante:** RECOMENDACIÓN ≠ EJECUCIÓN (`auto_execution_blocked: true`).

---

## Inventario diff funcional por capa

### FÁBRICA MB-06 (`a5c518b`)

```
backend/alembic/versions/6b06a1b2c3d4e_employee_lifecycle_factory_mb06.py
backend/app/services/employee_lifecycle_service.py
backend/app/services/coordinator.py
backend/app/services/agent_factory.py
backend/app/routers/agent_factory.py
backend/app/schemas_factory.py
backend/app/orchestration_models.py
backend/app/enums.py
backend/app/permissions.py
frontend/src/pages/EmployeeDetailPage.tsx  (pestaña Aprobación — compartido)
frontend/src/api.ts
frontend/src/lib/labels.ts
tests/test_employee_lifecycle_factory_mb06.py
tests/test_agent_factory_e2e.py
```

### AUDITOR (`3d066ae`)

```
backend/alembic/versions/1400a1b2c3d4e_employee_auditor_mvp.py
backend/app/employee_audit_models.py  (parcial — sin EmployeeImprovementTrace)
backend/app/services/employee_audit_service.py
backend/app/services/employee_audit_events.py
backend/app/services/employee_audit_metrics.py
backend/app/routers/empleados_auditor.py  (MVP — sin endpoints puente)
backend/app/schemas_employee_audit.py
backend/app/notifications.py
frontend/src/pages/EmployeeAuditorPage.tsx
tests/test_employee_auditor_mvp.py
```

### MI TRABAJO (`40e76bc`)

```
backend/app/services/trabajo_service.py  (núcleo bandeja)
backend/app/routers/trabajo.py
backend/app/schemas_trabajo.py
frontend/src/pages/TrabajoPage.tsx
tests/test_bandeja_trabajo_humano.py
```

### AUDITOR → MI TRABAJO (`be761f6`)

```
backend/app/services/trabajo_service.py  (ítems auditor)
backend/app/services/employee_audit_service.py
backend/app/routers/trabajo.py
frontend/src/pages/TrabajoPage.tsx
tests/test_auditor_integracion_mi_trabajo.py
```

### PUENTE FINAL (`d575d06` selectivo + `817f501`)

```
backend/alembic/versions/14b0c1d2e3f4_merge_factory_auditor_mb06.py
backend/alembic/versions/14b1c2d3e4f5_auditor_factory_improvement_trace.py
backend/app/services/auditor_factory_bridge.py
backend/app/employee_audit_models.py  (EmployeeImprovementTrace)
backend/app/routers/empleados_auditor.py  (endpoints puente)
backend/app/services/trabajo_service.py  (acción revisar_fabrica)
frontend/src/pages/EmployeeDetailPage.tsx  (banner auditor)
tests/test_auditor_factory_cycle.py
```

---

## Verificación no-duplicación

| Componente | Instancias en rama | Estado |
|------------|-------------------|--------|
| Workflow mejora | 1 (`auditor_factory_bridge`) | OK |
| Bandeja `/trabajo` | 1 (`TrabajoPage`) | OK |
| `ApprovalRequest` | 1 (`orchestration_models`) | OK |
| Auditor MVP | 1 (`employee_audit_service`) | OK |
| Fábrica MB-06 | 1 (`employee_lifecycle_service`) | OK |
| Motor pruebas empleado | 1 (MB-06 `employee_test_runs`) | OK |
| Knowledge | 1 (`930a1` reutilizado) | OK |

---

*Documento generado para port selectivo por General. No rehacer desarrollo; seguir orden y abortar ante colisiones.*
