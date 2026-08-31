# EMPLEADOS IA — Auditor integrado con Mi Trabajo

**Rama:** `cursor/auditor-integracion-mi-trabajo`  
**Base:** `3d066ae` (Auditor MVP determinístico)  
**Tipo:** integración funcional real — sin nueva bandeja ni migración

---

## 1. Arquitectura

El Auditor es una **fuente agregada** en `trabajo_service.collect_items()`, igual que aprobaciones, notificaciones y FinOps.

| Componente | Cambio |
|------------|--------|
| `employee_audit_service.py` | `iter_human_work_findings`, `finding_requires_human_work`, tipos de trabajo |
| `trabajo_service.py` | Agregación, normalización, deduplicación 820 |
| `trabajo.py` | Filtro `employee_id` |
| `TrabajoPage.tsx` | Labels y detalle Auditor |

**No se creó:** tabla de tareas, scheduler, workflow, Centro de Control, Fábrica.

---

## 2. Qué entra a Mi Trabajo

Solo hallazgos **ABIERTOS** que `finding_requires_human_work` marca como accionables:

| Salud / severidad | ¿Mi Trabajo? |
|-------------------|--------------|
| SALUDABLE | No |
| OBSERVAR | No |
| REQUIERE_INTERVENCION | Sí |
| CRITICO | Sí |
| REQUIERE_MEJORA | Solo si `SOLICITAR_REVISION_HUMANA` o política `allowed_actions` exige humano |

---

## 3. Tipos (convención bandeja)

| tipo | Cuándo |
|------|--------|
| `auditor_empleado_critico` | salud CRITICO o severidad CRITICO |
| `auditor_empleado_intervencion` | salud REQUIERE_INTERVENCION |
| `auditor_empleado_revision` | revisión humana por política/recomendación |

`modulo`: `auditor_empleados` (presentación: «Auditor de Empleados IA»).

---

## 4. Normalización

Campos `TrabajoItem`: tipo, asunto, modulo, prioridad (presentación), estado_dominio (salud), `correlation_id`, `semantic_kind` del hallazgo, `metadata` con `employee_id`, `audit_run_id`, `finding_id`, `health_status`, `severity`, `recommended_action`, `rule_code`, `metric_name`, observado/umbral (sin evidencia JSON completa — sin secretos).

Acciones: solo navegación (`auditor_empleados.view`, `employee.view`) → `/empleados/auditoria`, `/empleados/{id}`.

---

## 5. Deduplicación 820

Antes de incluir notificaciones, se omiten las que duplican un ítem Auditor:

- `finding_id` en hallazgos agregados
- `notification_id` enlazado al hallazgo
- `employee_audit_guard` + misma clave `employee_id:correlation_id`
- `source_type=employee_audit` con mismo empleado y hallazgo

**Prevalencia:** ítem accionable del Auditor sobre notificación informativa.

---

## 6. Resumen `/api/trabajo/resumen`

Los contadores (`pendientes`, `vencidas`, `requieren_aprobacion`, `total_visible`) incluyen ítems Auditor en la agregación. Los tipos Auditor usan `estado_presentacion=PENDIENTE`, no `REQUIERE_APROBACION` salvo que sea aprobación real de otro módulo.

---

## 7. Filtros

- `modulo=auditor_empleados`
- `tipo=auditor_empleado_*`
- `employee_id` (query param nuevo)
- `prioridad`, `estado`, `requires_action` — sin romper filtros existentes

---

## 8. RBAC y multiempresa

- Ver ítems Auditor en Mi Trabajo requiere `auditor_empleados.view` (además de acceso bandeja).
- Ver bandeja **no** concede `execute`, `configure`, `publish`, `rollback`.
- Aislamiento org vía `resolve_organization_id` + filtros por `organization_id` en hallazgos.

---

## 9. Trazabilidad

Cadena: métrica (snapshot en assessment) → `audit_run_id` → `finding_id` → ítem `auditor_empleado:*` → `correlation_id` → enlaces auditoría / trazabilidad integraciones.

---

## 10. Migración Alembic

**NO** — cabeza sigue `1400a1b2c3d4e`.

---

## 11. Tests

- `tests/test_auditor_integracion_mi_trabajo.py` — 8 casos
- Regresión: `test_employee_auditor_mvp` (12) + `test_bandeja_trabajo_humano` (6) + `test_migration_control` (7) = **33 passed**

---

## 12. Receta para General

1. Portar commits de esta rama sobre Auditor MVP (o merge lineal).
2. Verificar que `trabajo_service.collect_items` mantiene bloque `auditor_empleados.view`.
3. Fábrica (MB-06): futuro enlace recomendación → acción en Fábrica; **no** incluido aquí.
4. Centro de Control: sin cambios; sigue `/api/empleados-auditor/resumen-centro-control`.

**Commits portables:**

- Funcional integración Mi Trabajo
- Tests `test_auditor_integracion_mi_trabajo.py`
- Entregable este documento

---

## SALIDA FINAL

```
EMPLEADOS IA — AUDITOR INTEGRADO CON MI TRABAJO

BASE:
3d066ae

RAMA:
cursor/auditor-integracion-mi-trabajo

HEAD:
<SHA post-push>

FUENTE AUDITOR:
PASS

REQUIERE_INTERVENCION:
PASS

CRITICO:
PASS

REQUIERE_MEJORA:
PASS

SALUDABLE EXCLUIDO:
PASS

OBSERVAR EXCLUIDO:
PASS

DEDUPLICACION 820:
PASS

CORRELATION_ID:
PASS

RESUMEN:
PASS

FILTROS:
PASS

MULTIEMPRESA:
PASS

RBAC:
PASS

SUPERADMIN:
PASS

SECRETOS:
PASS

FRONTEND:
PASS

AUDITOR TESTS:
12 passed

MI TRABAJO TESTS:
14 passed (6 bandeja + 8 integración)

REGRESIÓN:
33 passed

MIGRACIÓN NUEVA:
NO

ALEMBIC HEADS:
1

CENTRO CONTROL:
NO MODIFICADO

FÁBRICA:
NO MODIFICADA

FASE2 CENTRAL:
NO

MAIN:
NO

V1:
NO

VEREDICTO:
APTO PARA PORTAR
```
