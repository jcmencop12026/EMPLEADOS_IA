# CURSOR — INTEGRACIÓN SALUD → WORKPLAN (ENTREGA-002)

**Estado:** `SALUD → WORKPLAN LISTO PARA REAUDITORÍA`  
**Fecha:** 2026-08-25  
**Rama:** `cursor/integracion-salud-workplan-002`  
**NO MERGE**

---

## 1. Git y bases

| Concepto | SHA / valor |
|----------|-------------|
| HEAD base (OPERACIONES #13) | `7c536d2` (`origin/cursor/operations-center-940-12b6`) |
| HEAD base (SALUD #14) | `9ee91eb` (`origin/cursor/salud-ips-engine-960`) — verificado remoto |
| HEAD integración (inicial) | `7c536d2` |
| HEAD integración (final) | `a511ea1` |
| Git root | `/workspace` (= `D:\EMPLEADOS_IA`) |

Rama creada desde OPERACIONES-940 certificado; merge de SALUD-960 sin modificar ramas origen.

---

## 2. Archivos de entrada

| Archivo | Estado |
|---------|--------|
| `INTERCAMBIO/ENTRADA/CHATGPT_ENTREGA_002_SALUD_WORKPLAN.patch` | **No presente** en el repositorio |
| `INTERCAMBIO/ENTRADA/CHATGPT_ENTREGA_002_SALUD_WORKPLAN.md` | **No presente** en el repositorio |

**Adaptación:** cambios implementados manualmente según especificación semántica del pedido (puente `IpsActionPlan` → `WorkPlan` → `EmployeeTask`, idempotencia, multi-tenant, responsable único).

---

## 3. Archivos modificados / nuevos

### Backend
- `backend/app/services/salud_workplan_bridge.py` — **nuevo** — puente principal
- `backend/app/services/salud_engine.py` — `create_action_plan()` integra bridge; validación tenant; idempotencia; metadata en `tasks_json`
- `backend/app/routers/salud.py` — respuesta incluye `work_plan_id`; errores 400 en validación
- `backend/app/permissions.py` — merge OPERACIONES + SALUD
- `backend/alembic/versions/970a1b2c3d4e_merge_operaciones_salud_970.py` — **nuevo** — merge heads `940a1b2c3d4e` + `960a1b2c3d4e`

### Frontend
- `frontend/src/App.tsx` — rutas operaciones + salud (merge)
- `frontend/src/AppShell.tsx` — navegación Operaciones + Diagnóstico IPS
- `frontend/src/pages/DiagnosticoIpsPage.tsx` — enlace «Abrir en Operaciones» tras crear plan

### Tests
- `tests/test_salud_workplan_bridge.py` — **nuevo** — 5 tests del puente
- `tests/test_salud_960.py` — fix import `conftest`

### Otros (merge SALUD/QA)
- `pytest.ini`, `.github/workflows/qa.yml`, modelos/servicios SALUD-960, etc.

---

## 4. Resultado funcional

Flujo **Diagnóstico IPS → seleccionar propuestas → Crear plan de acción** produce:

```
IpsActionPlan → WorkPlan real → EmployeeTask(s) → visible en /operaciones
```

**Metadata conservada en `tasks_json` / `inputs_json`:**
- `organization_id` (por FK en modelos)
- `analysis_id`
- `action_plan_id`
- `hallazgo_id`
- `propuesta_id`
- `evidencia`
- `acción`
- `responsable_sugerido`
- `indicador`
- `meta`
- `confianza`
- `prioridad` (mapeada a `WorkPlan.prioridad`)
- `vencimiento` (derivado de `plazo` en propuestas)

---

## 5. Idempotencia

`find_idempotent_action_plan()` compara conjunto normalizado de `propuesta_ids` por `organization_id` + `analysis_id`.  
Reintento con mismo conjunto (orden distinto) devuelve el mismo `IpsActionPlan` y `work_plan_id` — **sin duplicar WorkPlan**.

---

## 6. Multiempresa

Propuestas de otro tenant → HTTP 400.  
WorkPlan de tenant B no accesible desde token de tenant A → HTTP 404 en `/api/operations/center/{id}`.

---

## 7. Responsable

`resolve_unique_employee()` asigna solo si hay **exactamente un** `AIEmployee` activo (`ACTIVE`/`PUBLISHED`/`CERTIFIED`) con nombre o código coincidente.  
Ambigüedad o inexistencia → tarea sin `employee_id`.

---

## 8. Aprobaciones

No se creó sistema paralelo. Aceptación de recomendaciones permanece en permiso `salud.aceptar_recomendaciones`. Operaciones conserva su flujo de aprobaciones central.

---

## 9. Operaciones

WorkPlan visible en `/operaciones` y detalle `/operaciones/:id` con:
- prioridad, vencimiento, tareas, actividad
- origen SALUD en `summary` / `resultado`
- navegación desde Diagnóstico IPS
- textos en español

---

## 10. Tests ejecutados

| Comando | Resultado |
|---------|-----------|
| `pytest tests/test_salud_workplan_bridge.py -q` | **5/5 PASS** |
| `pytest` (suite completa) | **113/113 PASS** |
| `npm run build` | **PASS** |
| `npm audit --audit-level=moderate` | **0 vulnerabilidades** |
| Alembic upgrade → downgrade `4355c73adcb8` → upgrade | **PASS** |
| `git diff --check origin/main...HEAD` | Trailing whitespace en docs `INTERCAMBIO/SALIDA/` heredados de ramas previas (no introducidos por el puente) |

**Nota local:** ejecutar pytest sin `DATABASE_URL` heredado de sesiones previas (`env -u DATABASE_URL pytest`) para SQLite fresco con schema actual.

---

## 11. GitHub Actions / PostgreSQL

Workflow `.github/workflows/qa.yml` incluye:
- PostgreSQL 16
- `alembic upgrade head` + downgrade/upgrade
- pytest completo
- frontend build + npm audit
- `git diff --check`

Pendiente de ejecución en CI tras push de la rama (recomendado reauditar con run verde).

---

## 12. E2E UI

Flujo validado manualmente en VM:

1. Login `admin` / `Admin2026*`
2. Diagnóstico IPS → demo completo
3. Seleccionar 2 propuestas → Crear plan de acción
4. «Abrir en Operaciones» → detalle con prioridad «Crítica», vencimiento, 2 tareas en español
5. Lista `/operaciones` muestra plan con origen SALUD
6. Reintento con mismas propuestas → **sin duplicado** (mismo `work_plan_id`)

**Hallazgo UI:** servidor dev con SQLite nuevo requiere columnas `prioridad`/`vencimiento` (vía Alembic o `create_all` con modelos actuales). En CI PostgreSQL esto queda cubierto por migraciones.

---

## 13. Hallazgos y pendientes

| # | Hallazgo | Severidad |
|---|----------|-----------|
| 1 | Archivos `.patch` / `.md` de entrada ausentes | Info — adaptación manual |
| 2 | `test_salud_960.py` importaba `tests.conftest` (corregido) | Bajo — fix aplicado |
| 3 | `git diff --check` falla por trailing whitespace en informes previos mergeados | Bajo — preexistente |
| 4 | CI GitHub Actions pendiente de run en rama de integración | Medio — verificar post-push |

**Pendientes para reauditoría:**
- Confirmar CI verde en PostgreSQL
- Revisión de seguridad multi-tenant en entorno staging
- Validar en Windows (`D:\EMPLEADOS_IA`) con archivos de entrada si se re-suben

---

## 14. Conclusión

Integración controlada **SALUD-960 + OPERACIONES-940** con puente funcional, idempotente y multi-tenant.  
Estado: **SALUD → WORKPLAN LISTO PARA REAUDITORÍA**.  
**NO MERGE** hasta aprobación explícita.
