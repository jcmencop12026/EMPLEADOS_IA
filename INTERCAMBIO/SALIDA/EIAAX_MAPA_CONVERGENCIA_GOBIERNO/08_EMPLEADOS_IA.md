# 08 — Empleados IA — convergencia

**Ramas:** base + `2afd673` (fábrica/arquitecto) + `c433bac` (gobierno/seguridad)

---

## Componentes a converger

| Área | Componente | Rol |
|------|------------|-----|
| Identidad | `AIEmployee` | Entidad principal |
| Ciclo vida | `employee_lifecycle_service` | Estados, certificación, publicación |
| Aprobaciones | `EmployeeFactoryApproval` → `ApprovalRequest` | Dominio fábrica |
| Gobierno | `GobiernoAccionSolicitud`, políticas acción | PROPUESTA/EJECUCIÓN transversal |
| Knowledge | `EmployeeKnowledgeSource`, knowledge center 930 | Fuentes empleado |
| Capacidades | `EmployeeBusinessCapability`, `EmployeeCapability` | Negocio + técnica |
| Provider/model | `EmployeeModelPolicy`, gateway LLM | Modelo autorizado |
| FinOps | `FinOpsRecord` en ejecución | Costo por tarea |
| Auditoría | `write_audit`, factory metrics | Operación |
| Arquitecto→Fábrica | `factory_bridge_service`, `EmpleadoIARequerimiento` | Puente MB-06 |
| Validación | `validate_provider_for_test` | Conformidad catálogo |

---

## Boundaries temporales (GENERAL debe resolver)

### B-01 — Arquitecto → Fábrica

| Campo | Valor |
|-------|-------|
| **ORIGEN** | `2afd673` `factory_bridge_service` |
| **COMPONENTES** | `EmpleadoIARequerimiento`, `create_employee_from_requerimiento` |
| **AUTORIDAD** | Requerimiento arquitecto; empleado en fábrica |
| **CONSERVAR** | Bridge completo |
| **ADAPTAR** | Propagar `correlation_id` desde dossier; clasificar empleado |
| **RETIRAR** | Creación directa sin requerimiento en flujo arquitecto |
| **RIESGO** | Empleado huérfano sin trazabilidad transformación |

### B-02 — Publicación sin gobierno

| Campo | Valor |
|-------|-------|
| **ORIGEN** | `publish_with_guards` |
| **COMPONENTES** | lifecycle, `EmployeeFactoryApproval` |
| **AUTORIDAD** | Guards fábrica + solicitud gobierno EJECUCIÓN |
| **CONSERVAR** | Guards certificación, riesgo, aprobación |
| **ADAPTAR** | Alta riesgo → `GobiernoAccionSolicitud` además de factory approval |
| **RETIRAR** | Publish sin política acción org |
| **RIESGO** | Empleado autónomo sin registro gobierno |

### B-03 — Modelo vs política org

| Campo | Valor |
|-------|-------|
| **ORIGEN** | `EmployeeModelPolicy` vs `GobiernoIaPolicy` |
| **COMPONENTES** | agent_factory, gobierno |
| **AUTORIDAD** | Intersección: empleado ⊆ org |
| **CONSERVAR** | Ambos |
| **ADAPTAR** | `validate_provider` consulta ambos |
| **RETIRAR** | Override empleado más permisivo |
| **RIESGO** | Modelo prohibido en producción |

### B-04 — Coordinator ejecución sin visibilidad

| Campo | Valor |
|-------|-------|
| **ORIGEN** | `coordinator` ejecuta tareas con outputs |
| **COMPONENTES** | `run_llm_for_task`, knowledge |
| **AUTORIDAD** | Outputs heredan clasificación fuente |
| **CONSERVAR** | Execution guard |
| **ADAPTAR** | Registrar evidencia vínculo en outputs sensibles |
| **RETIRAR** | — |
| **RIESGO** | Output LLM expuesto sin clasificar |

### B-05 — Consumption planner (MB-07)

| Campo | Valor |
|-------|-------|
| **ORIGEN** | `1507` planner en base |
| **COMPONENTES** | `consumption_planner_service`, bridge fábrica |
| **AUTORIDAD** | FinOps + límites `EmployeeLimits` |
| **CONSERVAR** | Planner |
| **ADAPTAR** | Costos en trazabilidad correlation empleado |
| **RETIRAR** | — |
| **RIESGO** | Desborde costo sin alerta gobierno |

---

## Flujo convergido deseado

```
EmpleadoIARequerimiento (arquitecto)
        │ correlation_id dossier
        ▼
create_employee_from_requerimiento (bridge)
        │ clasificación INTERNO; política IA org
        ▼
Diseño + knowledge + capacidades + tests
        │
        ▼
Certificación → EmployeeFactoryApproval (si riesgo)
        │ decide_approval
        ▼
GobiernoAccionSolicitud EJECUCIÓN (si política org)
        │
        ▼
PUBLICADO → coordinator ejecuta con gateway + FinOps
        │
        ▼
Evidencia + eventos + auditoría (mismo correlation_id)
```

---

## Qué NO duplicar

| Evitar | Usar en su lugar |
|--------|------------------|
| Segundo ciclo vida | `employee_lifecycle_service` |
| Aprobación fábrica paralela a ApprovalRequest | Patrón actual enlazado |
| Catálogo modelo en bridge | `llm_model_catalog` |
| Auditoría solo factory | `write_audit` + gobierno eventos |

---

## Migración 1430 (fábrica)

En rama `2afd673`: `1430a1b2c3d4e_fabrica_mb06_puente.py` depende de `1420` arquitecto.

**Colisión:** `1420` ya usado por seguridad (`c433bac`) y entregas (`f32c815`). GENERAL debe renumerar antes de merge físico (ver `10_MIGRACIONES_COLISIONES.md`).

---

## Tests de regresión requeridos (merge)

- Gate post6d: `EmployeeFactoryApproval` único pendiente
- `decide_approval` segregación solicitante
- `validate-provider` contra catálogo
- Multitenant empleado cross-org → 404
- Publish sin certificación → bloqueado
