# OPORTUNIDADES-PROACTIVAS-1030 — Mapa de capacidades

**HEAD base:** `cc77d83` (main — PR #22 integrado)  
**Rama:** `cursor/oportunidades-proactivas-1030`  
**Fecha:** 2026-08-27

## Matriz EXISTE / PARCIAL / NO EXISTE

| Capacidad | Estado | Componente actual | Endpoint/Servicio | Persistencia | GAP | Acción 1030 |
|-----------|--------|-------------------|-------------------|--------------|-----|-------------|
| Señales transversales | NO EXISTE | — | — | — | Sin modelo Signal | Crear `ProactiveSignal` + dedupe |
| Oportunidades transversales | NO EXISTE | `IpsPropuesta` (solo SALUD reactivo) | `/api/salud/*` | `ips_propuestas` | Vertical SALUD | Crear `Opportunity` transversal |
| Motor pertinencia | NO EXISTE | — | — | — | — | `evaluate_pertinence()` |
| Motor momento | NO EXISTE | — | — | — | — | `evaluate_momento()` |
| Priorización global | PARCIAL | `motor_analitico/prioritization.py` | Motor interno | JSON en análisis | Solo dentro de caso | `prioritize_opportunities_global()` |
| Siguiente mejor acción | NO EXISTE | — | — | — | — | `compute_next_best_action()` |
| Contexto 360 | PARCIAL | Contexto en SALUD/motor | `salud_engine` | JSON | No transversal | `build_context_360()` |
| Capacidad 360 | PARCIAL | `orchestrator_selection` | `select_team` | logs | No evalúa ejecutabilidad | `assess_capability_360()` |
| Orquestador equipo | EXISTE | `orchestrator_selection.select_team` | `/api/experiencia/seleccion-equipo` | `experience_selection_logs` | No ligado a oportunidades | Reutilizar en oportunidades |
| Estados oportunidad | NO EXISTE | WorkPlan estados | coordinator | `work_plans` | No FSM oportunidad | `OpportunityTransition` |
| Activación WorkPlan | PARCIAL | `salud_workplan_bridge` | SALUD | work_plans | Solo SALUD | `activate_opportunity()` |
| FINOPS valor | PARCIAL | `finops_bridge.register_finops_values` | `/api/finops` | `finops_values` | Sin work_plan_id/opportunity_id (G-02) | Extender bridge + columna |
| Seguimiento activo | PARCIAL | Operaciones | operations | tasks | No post-WorkPlan oportunidad | `OpportunityTracking` |
| Aprendizaje | EXISTE | `experience_core.crear_experiencia` | `/api/experiencia` | `employee_experience_records` | No desde oportunidad | `register_opportunity_learning()` |
| Scheduler proactivo | PARCIAL | `automation_scheduler` | automations | automations | Solo route_task genérico | `proactive_scheduler` |
| Coordinator dominio | PARCIAL | `coordinator._detect_route` | coordinator | — | Hardcode SALUD (G-01) | `domain_analysis` interface |
| Centro UI oportunidades | NO EXISTE | DiagnosticoIps tab oportunidades | `/salud/diagnostico` | — | Solo SALUD | `OportunidadesPage` |
| Permisos oportunidades | NO EXISTE | `permissions.py` | — | roles | — | `oportunidades.*` |
| Multi-tenant | EXISTE | org_id en modelos | todos | FK org | — | Reutilizar patrón |
| Trazabilidad | PARCIAL | audit, events | audit | audit_logs | Sin cadena señal→oportunidad | `OpportunityTrace` + correlation_id |
| Deduplicación | PARCIAL | notification idempotency | notifications | — | No señales | dedupe_key en Signal |
| Anti-prefabricado | PARCIAL | MOTOR casos A-E | tests motor | — | No oportunidades | Tests adversariales |
| Resumen negocio | PARCIAL | FINOPS dashboard | `/api/finops/dashboard` | finops | Sin agregado oportunidades | `/api/oportunidades/resumen` |

## Componentes reutilizados

- `orchestrator_selection.select_team`
- `experience_core` (aprendizaje)
- `motor_analitico/prioritization` (scoring base)
- `finops_service.registrar_valor`
- `salud_workplan_bridge` (patrón activación)
- `automation_scheduler` (patrón polling)
- `coordinator.route_task` / `execute_plan`
- `permissions.py` + `seed_permissions`
- UI: `AppShell`, `CostosValorPage` patrones

## Componentes nuevos 1030

- `opportunity_models.py`
- `services/domain_analysis.py` (G-01)
- `services/proactive_service.py`
- `services/proactive_scheduler.py`
- `routers/oportunidades.py`
- Migración `1030a1b2c3d4e`
- Frontend `OportunidadesPage`, `OportunidadDetailPage`
- `tests/test_oportunidades_proactivas_1030.py`

## Cierres de gaps

- **G-01:** Coordinator → `DomainAnalysisProvider` (SALUD como proveedor, no hardcode)
- **G-02:** FINOPS `register_finops_values` con `work_plan_id`, `opportunity_id`
