# INTEGRACIÓN 1020 ↔ 1030 — Mapa real

**Rama integrada:** `cursor/preintegracion-1020-1030`
**Base:** PR #23 corregido (`9a11753`) + PR #24 (`922c8e1`)

## Cadena única verificada

```
SEÑAL (proactive_scheduler / API)
  → OPORTUNIDAD (proactive_service.process_signal)
  → CONTEXTO 360 + PERTINENCIA + MOMENTO
  → PRIORIZACIÓN GLOBAL (prioritize_opportunities_global)
  → SIGUIENTE MEJOR ACCIÓN (compute_next_best_action)
  → EQUIPO IA (orchestrator_selection.select_team — 1010)
  → APROBACIÓN/POLÍTICA (human_gate)
  → WORKPLAN (activate_opportunity → WorkPlan)
  → OPERACIONES (coordinator.execute_plan si auto_execute)
  → FINOPS (register_finops_values con work_plan_id + opportunity_id — G-02)
  → RESULTADO (register_result)
  → EXPERIENCIA (register_opportunity_learning → experience_core)
  → NUEVA SELECCIÓN (experiencia influye en select_team)
```

## Componentes — sin duplicación

| Componente | Implementación única | Usado por |
|------------|---------------------|-----------|
| WorkPlan | `orchestration_models.WorkPlan` | 1020 E2E, 1030 activate_opportunity |
| Experiencia | `experience_core.crear_experiencia` | 1020 sync SALUD, 1030 register_opportunity_learning |
| FINOPS | `finops_service.registrar_valor` | 1020 motor, 1030 activate/register_result |
| Orquestador | `orchestrator_selection.select_team` | 1010 SALUD, 1030 oportunidades |
| Coordinator | `coordinator.route_task` | Automatizaciones, 1030 auto_execute |
| Scheduler | `automation_scheduler` + `proactive_scheduler` | Distintos propósitos, no duplicados |

## Gaps cerrados en integración

| Gap | 1020 | 1030 | Estado integrado |
|-----|------|------|------------------|
| G-01 | Documentado | `domain_analysis.py` + `resolve_capability_code` | CERRADO |
| G-02 | Documentado | `finops_bridge` + columna `opportunity_id` | CERRADO |
| G-03 | Corregido (sync SALUD→core) | Reutiliza `experience_core` | COHERENTE |

## Duplicaciones detectadas

Ninguna duplicación funcional crítica. Los dos schedulers (`automation_scheduler` vs `proactive_scheduler`) tienen responsabilidades distintas:
- **automation_scheduler:** ejecuta automatizaciones configuradas por usuario
- **proactive_scheduler:** detecta indicadores sintéticos y crea señales proactivas

## Migraciones

| Revisión | Descripción |
|----------|-------------|
| `1010a1b2c3d4e` | Orquestador experiencia 1010 |
| `1030a1b2c3d4e` | Oportunidades proactivas 1030 |

Head único: `1030a1b2c3d4e`

## Tests integrados

| Módulo | Tests |
|--------|-------|
| 1020 | 13 |
| 1010 | 26 |
| 1000 | 16 |
| 1030 | 38 |
| **Total regresión** | **515 PASS** |
