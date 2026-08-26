# CURSOR — OPERACIONES-940 Centro de Operaciones V1

**Fecha:** 2026-08-25
**Estado:** OPERACIONES-940 LISTO PARA REAUDITORÍA
**No declarado apto para merge — NO MERGE**

---

## IDENTIFICACIÓN

| Campo | Valor |
|-------|-------|
| Código | OPERACIONES-940 |
| Rama | `cursor/operations-center-940-12b6` |
| Base | `main` (`b887a2e`) |
| HEAD inicial | `b887a2e77c646a5b0c82d47837dfaaaed9c491ce` |
| HEAD final | *(ver commit en rama)* |

---

## ARQUITECTURA

```
Solicitud (/operaciones/solicitud)
  → WorkPlan (orquestador existente)
  → EmployeeTask / ApprovalRequest / WorkEvent
  → Centro de Operaciones (/operaciones)
  → Detalle workspace con pestañas
```

Sin tablas nuevas. Reutiliza `WorkPlan`, `EmployeeTask`, `ApprovalRequest`, `WorkEvent`, `FinOpsRecord`.

---

## REUTILIZACIÓN

| Existente | Uso |
|-----------|-----|
| `WorkPlan` | Operación/trabajo principal |
| `EmployeeTask` | Tareas y ejecuciones |
| `ApprovalRequest` | Aprobaciones |
| `WorkEvent` | Actividad/timeline |
| `FinOpsRecord` | Metadata de costo/duración (contrato FINOPS) |
| `coordinator.execute_plan` / `decide_approval` | Acciones de ejecución y aprobación |

---

## ENDPOINTS NUEVOS/EXTENDIDOS

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/operations/summary` | Indicadores compactos |
| GET | `/api/operations/center` | Listado con filtros |
| GET | `/api/operations/center/{id}` | Detalle |
| PATCH | `/api/operations/center/{id}` | Actualización parcial (reasignación) |
| GET | `/api/operations/center/{id}/tasks` | Tareas |
| GET | `/api/operations/center/{id}/executions` | Ejecuciones |
| GET | `/api/operations/center/{id}/approvals` | Aprobaciones |
| GET | `/api/operations/center/{id}/results` | Resultados |
| GET | `/api/operations/center/{id}/activity` | Actividad |
| POST | `/api/operations/center/{id}/cancel` | Cancelar |
| POST | `/api/operations/center/{id}/pause` | Pausar |
| POST | `/api/operations/center/{id}/resume` | Reanudar |
| POST | `/api/operations/center/{id}/run` | Iniciar/ejecutar |

Endpoints legacy `/executions`, `/approvals`, etc. conservados con permisos `operations.*`.

---

## PERMISOS

| Permiso | Admin | Operator | Viewer |
|---------|-------|----------|--------|
| `operations.view` | Sí | Sí | Sí |
| `operations.manage` | Sí | Sí | No |
| `operations.cancel` | Sí | Sí | No |
| `operations.reassign` | Sí | Sí | No |
| `operations.approve` | Sí | Sí | No |

Fail closed. `approval_decide` exige `operations.approve`.

---

## TENANT ISOLATION

Todas las consultas filtran `organization_id`. Cross-tenant devuelve 404.

---

## FRONTEND (español)

| Vista | Ruta |
|-------|------|
| Centro de Operaciones (grilla + indicadores) | `/operaciones` |
| Nueva solicitud | `/operaciones/solicitud` |
| Detalle workspace (7 pestañas) | `/operaciones/:id` |
| Menú | **Operaciones** |

Estados visibles en español. Sin datos simulados; estados vacíos reales.

---

## CONTRATOS FUTUROS

- **PR #6 Scheduler:** acciones `iniciar/pausar/reanudar` preparadas sin acoplamiento
- **PR #7 Notificaciones:** integración vía eventos existentes
- **CONOCIMIENTO-930 / FINOPS-950:** metadata `costo_metadata` y referencias sin implementar módulos

---

## MIGRACIONES

No requeridas (reutilización de modelos existentes).

---

## TESTS

```
PYTHONPATH=backend python3 -m pytest -q
→ 56 passed (10 nuevos en test_operations_940.py)
```

Cobertura: listar, detalle, filtros, tenant, permisos, cancelación, transición inválida, reasignación, aprobaciones, actividad/resultados.

---

## VALIDACIÓN

| Comando | Resultado |
|---------|-----------|
| `pytest` | PASS (56) |
| `npm run build` | PASS |
| `npm audit` | 0 vulnerabilities |
| `git diff --check` | PASS |

---

## PENDIENTES REALES

1. Campo `vencimiento` sin dato en modelo — indicador muestra 0
2. Prioridad operativa no persistida (solo visual "Normal")
3. Integración visual con notificaciones/scheduler cuando se integren PRs
4. Pausa/reanudación limitada a estados `RUNNING`/`WAITING_DATA`

---

## ESTADO FINAL

**OPERACIONES-940 LISTO PARA REAUDITORÍA**

No merge.
