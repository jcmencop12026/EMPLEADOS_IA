# 01 — Reutilización

## EXISTE (reutilizado)

| Componente | Ubicación | Uso MB-08 |
|------------|-----------|-----------|
| Centro de Control agregador | `control_center_service.py` | Base extendida |
| 20+ adapters | `control_center_adapters.py` | FinOps, MB-07, operaciones, etc. |
| Centro de Operaciones | `operations_center.py` | Ejecuciones tácticas |
| Consumption Planner | `consumption_planner_service.py` | Capacidad/costo |
| FinOps | `finops_service.py` | Estimado vs real |
| Fábrica empleados | `agent_factory`, lifecycle | Fuerza laboral |
| Aprobaciones | `ApprovalRequest`, `EmployeeFactoryApproval` | Bandeja |
| LLM gateway | `llm_models`, health | Proveedores |
| Knowledge | `knowledge_service` | Adapter nuevo |
| UI | `CentroControlPage.tsx` | Evolucionada operacional |

## PARCIAL → cerrado en MB-08

| Brecha | Acción |
|--------|--------|
| CONOCIMIENTO_930 pendiente | `ConocimientoAdapter` |
| Fábrica sin vista operacional CC | `FabricaOperacionalAdapter` + `operational_control_service` |
| Atención sin priorización | Puntuación impacto/urgencia |
| UI solo ejecutiva | Pestañas operacionales |

## SE REUTILIZA (no duplicar)

- Sin segundo FinOps, scheduler, alertas, gateway, BI, Gobierno Operacional
- `/operaciones` sigue siendo centro táctico de acciones
- CC permanece **solo lectura** + acciones delegadas

## FALTA (reservado integración)

- Inteligencia de Resultados (agente D)
- PIIAX capacidades externas reales
- Gobierno Operacional transversal (frontera preparada)
- Gráficos time-series (MB08-08)
