# EMPLEADOS IA — Auditor MVP determinístico (Fase 1)

**Rama:** `cursor/auditor-empleados-ia-mvp-deterministico`  
**Base diseño:** `fccd21e` (diseño aprobado + bandeja unificada)  
**Tipo:** implementación funcional determinística — sin LLM real

---

## 1. Arquitectura ejecutada

| Componente | Ubicación | Rol |
|------------|-----------|-----|
| Modelos | `backend/app/employee_audit_models.py` | Política, run, assessment, finding |
| Métricas | `backend/app/services/employee_audit_metrics.py` | Agregación real (work_plans, LLM, FinOps, tests, grants, experiencia) |
| Motor | `backend/app/services/employee_audit_service.py` | Reglas, salud, hallazgos, recomendaciones, idempotencia, contratos |
| Eventos | `backend/app/services/employee_audit_events.py` | Bus existente + `employee.audit.scheduled` (810C) |
| API | `backend/app/routers/empleados_auditor.py` | REST `/api/empleados-auditor/*` |
| Frontend | `frontend/src/pages/EmployeeAuditorPage.tsx` | Vista `/empleados/auditoria` |
| Migración | `backend/alembic/versions/1400a1b2c3d4e_employee_auditor_mvp.py` | Genealogía única |

**No modificado:** `agent_factory`, Fábrica/ciclo de vida, `trabajo_service`, Centro de Control UI.

---

## 2. Modelo de datos

- `employee_audit_policies` — org default (`employee_id` NULL) u override por empleado
- `employee_audit_runs` — ejecución con `correlation_id`, `idempotency_key`, `cost_usd`
- `employee_audit_assessments` — salud por empleado en cada run
- `employee_audit_findings` — hallazgos con semántica `HECHO | INFERENCIA | RECOMENDACION`

---

## 3. APIs

| Método | Ruta | Permiso |
|--------|------|---------|
| GET | `/api/empleados-auditor/politicas` | `auditor_empleados.view` |
| GET | `/api/empleados-auditor/politica` | view |
| PATCH | `/api/empleados-auditor/politica` | `auditor_empleados.configure` |
| POST | `/api/empleados-auditor/ejecutar` | `auditor_empleados.execute` |
| GET | `/api/empleados-auditor/auditorias` | view |
| GET | `/api/empleados-auditor/auditorias/{id}` | view (+ multiempresa) |
| GET | `/api/empleados-auditor/hallazgos` | view |
| GET | `/api/empleados-auditor/salud` | view |
| GET | `/api/empleados-auditor/resumen-centro-control` | view |
| GET | `/api/empleados-auditor/contrato-trabajo` | view |

RBAC vía `resolve_organization_id` (patrón Centro de Control). SUPERADMIN con `platform.organization.view`.

---

## 4. Métricas reales (9 grupos activos por defecto)

`executions`, `errors`, `latency`, `tokens`, `cost`, `success_rate`, `approvals`, `tests`, `knowledge_grants`, `experience` — fuentes: `work_plans`, `llm_inference_logs`, `finops_records`, `employee_test_runs`, `approval_requests`, `employee_knowledge_grants`, `employee_experience_records`, `employee_limits`, lifecycle del empleado.

**No se infiere exactitud** sin evidencia en datos.

---

## 5. Umbrales y reglas

Umbrales por métrica: `advertencia` y `critico` (DEFAULT_THRESHOLDS en `employee_audit_metrics.py`).

Reglas implementadas: `FAILED_EXECUTIONS_HIGH`, `ERROR_RATE_HIGH`, `SUCCESS_RATE_LOW`, `LATENCY_HIGH`, `COST_LIMIT_*`, `TOKENS_HIGH`, `FAILED_TESTS`, `NO_KNOWLEDGE_GRANTS`, `APPROVAL_REJECTIONS_HIGH`, `EXPERIENCE_NEGATIVE`, `ACTIVE_WITHOUT_CERTIFICATION`, `LLM_ERRORS_HIGH`.

---

## 6. Salud determinística

Estados: `SALUDABLE`, `OBSERVAR`, `REQUIERE_MEJORA`, `REQUIERE_INTERVENCION`, `CRITICO`.

Fórmula (`_classify_health`):

1. Cualquier hallazgo `CRITICO` → `CRITICO` (score 20)
2. `ACTIVE_WITHOUT_CERTIFICATION` → `REQUIERE_INTERVENCION` (35)
3. ≥1 crítico o ≥3 advertencias → `REQUIERE_MEJORA` (50)
4. ≥1 advertencia → `OBSERVAR` (75)
5. lifecycle `FAILED_TEST` o `DRAFT` → `REQUIERE_INTERVENCION` (30)
6. else → `SALUDABLE` (95)

---

## 7. Hallazgos y recomendaciones

Campos mínimos: org, empleado, run, métrica/regla, valor, umbral, severidad, evidencia JSON, fecha, estado, `correlation_id`, `recommended_action`.

Acciones (solo recomendación, sin ejecución Fábrica): `CAPACITAR`, `ACTUALIZAR_CONOCIMIENTO`, `MEJORAR_INSTRUCCIONES`, `AGREGAR_HERRAMIENTA`, `CAMBIAR_HERRAMIENTA`, `CAMBIAR_MODELO`, `CAMBIAR_PROVEEDOR`, `AJUSTAR_AUTOMATIZACION`, `REDISEÑAR_EMPLEADO`, `SOLICITAR_REVISION_HUMANA`.

---

## 8. Integración 810C

- Evento `employee.audit.scheduled` → `process_scheduled_audits()` (sin scheduler paralelo).
- Automatización 810C puede emitir ese evento vía `INTERNAL_EVENT`.
- Eventos de dominio: `work.failed`, `EXECUTION_FAILED`, `FINOPS_LIMIT_REACHED`, `employee.certification_failed`, etc. → auditoría focal por empleado.

Anti-recursión: `_employee_audit_guard`, skip prefijo `employee.audit.*` (excepto `scheduled`).

---

## 9. Integración 820

Eventos `EMPLOYEE_AUDIT_CRITICAL`, `EMPLOYEE_AUDIT_INTERVENTION` en `notifications.py`. Dedupe 24h por org+empleado+regla antes de notificar crítico.

---

## 10. Contrato Mi Trabajo

`GET /api/empleados-auditor/contrato-trabajo` → lista portable (`list_trabajo_contract`). General puede fusionar en bandeja sin tocar `trabajo_service`:

```json
{
  "id": "auditoria_hallazgo:<finding_id>",
  "tipo": "auditoria_hallazgo",
  "modulo": "auditor_empleados",
  "requires_action": true,
  "enlace": "/empleados/auditoria?employee_id=..."
}
```

---

## 11. Contrato Centro de Control

`GET /api/empleados-auditor/resumen-centro-control`:

`total`, `saludables`, `en_observacion`, `requieren_mejora`, `requieren_intervencion`, `criticos`, `ultima_auditoria_at`, `hallazgos_abiertos`, `auditorias_vencidas`.

---

## 12. FinOps

`cost_usd = 0` en runs determinísticos. Sin consumo IA ficticio.

---

## 13. Salvaguardas (auditor del auditor)

- Límite ejecuciones por ventana (no aplica a `MANUAL`)
- Idempotencia por `idempotency_key` (SHA256 org+trigger+empleados+ventana)
- No modifica permisos ni política durante ejecución
- No re-audita en loop de eventos `employee.audit.*`

---

## 14. Multiempresa y RBAC

Permisos: `auditor_empleados.view`, `auditor_empleados.execute`, `auditor_empleados.configure` (seed vía `ALL_PERMISSIONS` + admin/operator/superadmin fallback).

---

## 15. Migraciones

| Campo | Valor |
|-------|-------|
| revision | `1400a1b2c3d4e` |
| down_revision | `1330b1b2c3d4f` |
| head | `1400a1b2c3d4e` (único) |

**Nota:** el identificador `1400a1b2c3d4e` es solo un revision_id Alembic portable del Auditor; **no** define un bloque funcional «1400» en el producto.

---

## CORRECCIÓN DE COLISIÓN ALEMBIC

| Campo | Valor |
|-------|-------|
| revision_id anterior | `1390a1b2c3d4e` |
| revision_id nuevo | `1400a1b2c3d4e` |
| motivo | Colisión con `1390a1b2c3d4e_merge_comercial_implementacion_fase1` en rama comercial `cursor/ensayo-comercial-implementacion-sobre-fase1` |
| down_revision | `1330b1b2c3d4f` (head real de `cursor/bandeja-trabajo-humano-unificada`) |
| heads | 1 (`1400a1b2c3d4e`) |
| roundtrip SQLite | upgrade → downgrade -1 → upgrade **PASS** |
| tests | `test_employee_auditor_mvp` 12 passed; `test_bandeja_trabajo_humano` 6 passed; `test_migration_control` 7 passed |
| archivos tocados | migración renombrada; `migration_ledger.json`; `schema_repair.py` HEAD_REVISION |
| commit corrección | `1033fcd` |

**Receta port para General:** conservar commits funcionales del Auditor; al portar sobre central, **reparentar** `1400a1b2c3d4e` al head central real del momento — no asumir `down_revision=1330b1b2c3d4f` si la cadena central divergió.

---

## 16. Tests

`tests/test_employee_auditor_mvp.py` — 12 casos: política, manual, salud/crítico, idempotencia, multiempresa, RBAC, FinOps=0, centro control, contrato trabajo, eventos, scheduled, notificaciones.

Regresión focal: `tests/test_bandeja_trabajo_humano.py` + auditor → **18 passed**.

---

## 17. Frontend

Ruta `/empleados/auditoria` — salud, hallazgos, auditoría manual (RBAC), detalle por empleado. Build Vite **PASS**.

---

## 18. Receta de integración central

1. Reparent migración `1400a1b2c3d4e` al head de Fase2 cuando General converja.
2. Registrar automatización 810C con `INTERNAL_EVENT` → `employee.audit.scheduled`.
3. Opcional: fusionar `contrato-trabajo` en `trabajo_service.list_items`.
4. Opcional: consumir `resumen-centro-control` en sección SALUD DE EMPLEADOS IA del Centro de Control.

---

## SALIDA FINAL

```
EMPLEADOS IA — AUDITOR MVP DETERMINÍSTICO TERMINADO

BASE:
fccd21e

RAMA:
cursor/auditor-empleados-ia-mvp-deterministico

HEAD:
9fbe416

POLÍTICAS:
PASS

MÉTRICAS REALES:
10

SALUD EMPLEADO:
PASS

AUDITORÍA MANUAL:
PASS

AUDITORÍA PERIÓDICA 810C:
PASS

AUDITORÍA POR EVENTO:
PASS

UMBRALES:
PASS

HALLAZGOS:
PASS

RECOMENDACIONES:
PASS

FINOPS:
PASS

NOTIFICACIONES 820:
PASS

MI TRABAJO:
CONTRATO PREPARADO

CENTRO CONTROL:
CONTRATO PREPARADO

FÁBRICA:
NO MODIFICADA

MULTIEMPRESA:
PASS

RBAC:
PASS

SUPERADMIN:
PASS

ANTI-RECURSIÓN:
PASS

IDEMPOTENCIA:
PASS

SECRETOS:
PASS

FRONTEND:
PASS

REGRESIÓN:
18 passed (bandeja + auditor)

ALEMBIC HEADS:
1

P0:
0

P1:
0

P2:
0

FASE2 CENTRAL:
NO

MAIN:
NO

V1:
NO

VEREDICTO:
APTO PARA PORTAR
```
