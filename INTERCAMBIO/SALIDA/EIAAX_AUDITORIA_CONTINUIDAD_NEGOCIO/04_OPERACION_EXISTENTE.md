# 04 — Operación existente

**Alcance:** Capacidades posteriores a go-live (`EN_PRODUCCION`)  
**Base:** SHA `fbfd6a2`

## Respuesta directa

Tras la puesta en marcha, EIAAX **ya puede operar** mediante Empleados IA, automatizaciones, ejecuciones, FinOps/consumo, soporte, incidentes (módulo separado), bandeja de trabajo y Centro de Control. La continuidad automática contrato→operación **no está cableada**; el operador enlaza manualmente vía `proposal_id` y organización.

---

## Capacidades post go-live

| Capacidad | Clasificación | Evidencia |
|-----------|---------------|-----------|
| Servicios / Empleados IA | OPERATIVA | `AIEmployee`, ciclo de vida, `DirectoryPage`, `EmployeeDetailPage` |
| Automatizaciones | OPERATIVA | `Automation`, scheduler cron, `AutomationsPage` |
| Ejecuciones | OPERATIVA | `WorkPlan`, `operations.py`, `ExecutionsPage` |
| Consumo / FinOps | OPERATIVA | `FinOpsRecord`, `finops.py`, MB-07 planificador |
| Resultados | PARCIAL | Distribuido: oportunidades, valoración, éxito cliente, línea base |
| Alertas | OPERATIVA | FinOps budgets, `impl_alertas`, notificaciones 820 |
| Incidencias | PARCIAL | Continuidad 1360; no unificado con soporte |
| Soporte | OPERATIVA | MB-12 mesa ayuda, SLA policies, `SoportePage` |
| Cambios | PARCIAL | Versionado empleado, rollback; sin change management contractual |

---

## 1. Empleados IA

### Ciclo de vida
`employee_lifecycle_service.py`: CONFIGURAR → CERTIFICAR → ACTIVAR → RETIRAR

| Operación | API | Permiso |
|-----------|-----|---------|
| Publicar | `POST .../publish` | `employee.publish` |
| Activar | `POST .../activate` | `employee.activate` |
| Retirar | `POST .../retire` | `employee.retire` |
| Rollback versión | `POST .../rollback` | `employee.rollback` |

### Auditor empleados (MVP determinístico)
- `employee_audit_service.py`, `empleados_auditor.py`
- Puente fábrica: `auditor_factory_bridge.py` — puede disparar `retire_employee` por hallazgo

### Knowledge por empleado
- `EmployeeKnowledgeSource`, `KnowledgeIngestion` en `orchestration_models.py`
- Centro conocimiento 930 independiente

**Gap operación:** No hay provisión automática de empleados desde `ia_consumo_json` de propuesta negocio.

---

## 2. Automatizaciones

| Componente | Archivo |
|------------|---------|
| Modelo | `automation_models.py` — `Automation`, `AutomationRun` |
| Servicio | `automation_service.py`, `automation_scheduler.py` |
| Eventos | `automation_events.py` |
| UI | `AutomationsPage`, `AutomationWizardPage`, `AutomationRunsPage` |
| Tests | `test_automations_810.py`, `810b`, `810c` |

Operación: triggers cron/evento, ejecución con fence 810c, historial runs.

---

## 3. Ejecuciones y operaciones

| Componente | Archivo |
|------------|---------|
| Hub | `OperationsHubPage.tsx`, `OperationsCenterPage.tsx` |
| Detalle | `OperationDetailPage.tsx`, `ExecutionDetailPage.tsx` |
| API | `routers/operations.py` |
| Coordinación | `coordinator.py` — aprobaciones en ejecución |
| Tests | `test_operations_940.py` |

Vinculación FinOps: cada ejecución puede generar `FinOpsRecord`.

---

## 4. Consumo y costos

### FinOps 950/1110
- Presupuestos, alertas, bloqueo ejecución si excede
- Dashboard en `/api/finops/dashboard`

### Motor Económico 1600
- Costos REAL → FinOps + motor (`test_register_cost_real_creates_finops_and_motor_entry`)
- Consumo real período vía planificador MB-07

### LLM Gateway
- `LlmInferenceLog` — observabilidad por inferencia
- Admin proveedores: `AdminLlmProvidersPage.tsx`

**Continuidad económica post-contrato:** consumo real trazable por org/período; **no** amarrado automáticamente a `precio_contratado` ni `modelo_comercial` del contrato.

---

## 5. Resultados e indicadores

| Fuente | Qué mide | Enlace contrato |
|--------|----------|-----------------|
| `ExitoClienteObjetivo` | Valor esperado vs medido por proyecto | vía `proyecto_id` |
| Valoración 1210 | Esperado/real por oportunidad | vía `opportunity_id` indirecto |
| Línea base 1200 | Impacto real post-implementación | proceso independiente |
| Oportunidades `register_result` | Resultado cierre oportunidad | `oportunidades.py` L306 |
| Centro de Control | Indicadores ejecutivos agregados | multi-módulo |
| Comunicaciones MB-11 | Reportes ejecutivos | manual |

**Clasificación:** PARCIAL — capacidad existe pero sin hilo único prometido→real a nivel plataforma.

---

## 6. Alertas

| Tipo | Origen |
|------|--------|
| Presupuesto FinOps | `FinOpsBudgetAlertState` |
| Implementación | `impl_alertas` — riesgo alto, bloqueador crítico, baja adopción |
| Notificaciones | `notifications.py` — bandeja usuario |
| Planificador MB-07 | Alertas desviación consumo |

---

## 7. Soporte e incidentes

### Mesa de ayuda MB-12 — OPERATIVA
- `SupportCase`, SLA policies, deduplicación
- Integración Mi Trabajo: `test_mesa_ayuda_integracion_mi_trabajo.py`
- UI: `SoportePage`, `SoporteCasoDetailPage`

### Continuidad 1360 — PARCIAL
- `ContinuidadIncidente`, planes DR/BCP
- UI: `ContinuidadPage`
- **DUPLICADA** conceptualmente con soporte para gestión incidentes

**Gap:** Sin caso de soporte auto-creado al go-live ni SLA derivado del contrato.

---

## 8. Cambios en operación

| Tipo cambio | Capacidad |
|-------------|-----------|
| Cambio configuración empleado | `update_employee`, nueva versión |
| Rollback empleado | `rollback_to_version` con aprobación |
| Cambio alcance contractual | Negociación comercial + nueva versión propuesta (pre o post contrato según estado) |
| Change request formal post-go-live | **AUSENTE** como entidad |

---

## 9. Centro de Control en operación

`control_center_service.py` consolida en home (`CentroControlPage.tsx`):
- Oportunidades, línea base, FinOps, valoración, comercial, implementación, señales, aprendizaje, etc.

`ImplementacionAdapter` (L1069): proyectos activos, hitos atrasados, riesgos abiertos.

---

## 10. Bandeja Mi Trabajo

**OPERATIVA** — unifica aprobaciones, soporte, tareas humanas  
`trabajo_service.py`, `TrabajoPage.tsx`, `test_bandeja_trabajo_humano.py`

---

## Matriz operación

| | YA EXISTE Y NO TOCAR | EXISTE PERO REQUIERE INTEGRACIÓN | EXISTE PARCIAL Y REQUIERE EVOLUCIÓN | REALMENTE AUSENTE |
|--|---------------------|----------------------------------|-------------------------------------|-------------------|
| Empleados + automatizaciones | ✓ | Provisión desde contrato | — | — |
| FinOps + consumo | ✓ | Precio contratado vs consumo real | Alertas por contrato | Facturación |
| Soporte | ✓ | Caso desde go-live | SLA contractual | — |
| Incidentes | — | Unificar con soporte | ✓ Continuidad 1360 | — |
| Resultados | — | CC + impl + valoración | ✓ hilo único | Módulo IR nuevo |
| Cambios operativos | ✓ empleado | — | Change request post-contrato | — |

---

## Conclusión

La **operación diaria** de EIAAX es madura en empleados, automatizaciones, ejecución y costos. Lo que falta no es un "módulo de operación" sino **integración transversal**: contrato → presupuesto operativo → medición de valor prometido, y unificación soporte/incidentes.
