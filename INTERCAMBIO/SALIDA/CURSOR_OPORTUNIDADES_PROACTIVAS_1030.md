# CURSOR — OPORTUNIDADES-PROACTIVAS-1030

## Veredicto

**OPORTUNIDADES-PROACTIVAS-1030 — APTO PARA REAUDITORÍA**

*(Pendiente confirmación CI 4/4 en GitHub Actions tras push)*

---

## Identificación

| Campo | Valor |
|-------|-------|
| HEAD base | `cc77d83` (main — PR #22 integrado) |
| HEAD final | *(ver commit de rama)* |
| Rama | `cursor/oportunidades-proactivas-1030` |
| PR | Draft — pendiente creación |
| Migración | `1030a1b2c3d4e` |
| Alembic head | `1030a1b2c3d4e` (único) |

**Nota:** PR #23 (E2E-1020) no estaba en `origin/main` al iniciar (`cc77d83`). Trabajo basado en main actual del remoto.

---

## Arquitectura

### Reutilizado
- `orchestrator_selection.select_team` — equipo IA (líder, validador, disidente)
- `experience_core` — aprendizaje post-resultado
- `motor_analitico/prioritization` — base de scoring
- `finops_service.registrar_valor` — valor potencial/materializado
- `coordinator` / WorkPlan — activación
- `automation_scheduler` — patrón polling
- Permisos y multi-tenant existentes

### Nuevo
- `opportunity_models.py` — Signal, Opportunity, Transition, Tracking, Trace
- `services/domain_analysis.py` — interfaz G-01
- `services/proactive_service.py` — motor transversal
- `services/proactive_scheduler.py` — detección proactiva real
- `routers/oportunidades.py` — API REST
- Frontend: `OportunidadesPage`, `OportunidadDetailPage`

---

## Cierres de gaps

### G-01 — Coordinator → Domain Analysis Interface
- `domain_analysis.py` con `DomainAnalysisProvider`, `SaludDomainAnalysisProvider`, `GenericDomainAnalysisProvider`
- `resolve_capability_code()` mantiene compatibilidad con códigos `rips`/`docint`/`ips-analitica`
- Coordinator delega a interfaz, no hardcode directo

### G-02 — FINOPS ↔ WorkPlan / Opportunity
- Columna `opportunity_id` en `finops_values`
- `register_finops_values()` acepta `work_plan_id`, `opportunity_id`, `employee_id`
- Activación de oportunidad registra valor potencial con ambos vínculos

---

## Capacidades implementadas

| Capacidad | Estado |
|-----------|--------|
| Señales transversales + dedupe | EXISTE |
| Oportunidades transversales | EXISTE |
| Contexto 360 + suficiencia | EXISTE |
| Capacidad 360 + human gate | EXISTE |
| Pertinencia | EXISTE |
| Momento | EXISTE |
| Priorización global explicable | EXISTE |
| Siguiente mejor acción | EXISTE |
| Máquina de estados | EXISTE |
| Activación WorkPlan | EXISTE |
| Seguimiento activo | EXISTE |
| Valor potencial vs materializado | EXISTE |
| Atribución | EXISTE |
| Aprendizaje → experiencia | EXISTE |
| Scheduler proactivo | EXISTE |
| Centro UI oportunidades | EXISTE |
| Resumen negocio | EXISTE |
| Permisos `oportunidades.*` | EXISTE |
| Trazabilidad correlation_id | EXISTE |

---

## Casos de certificación

| Caso | Resultado |
|------|-----------|
| OP-A financiera urgente | PASS |
| OP-B automatización bajo valor | PASS |
| OP-C cumplimiento | PASS |
| OP-D competencia capacidad | PASS |
| OP-E datos insuficientes | PASS → `DATOS_INSUFICIENTES` |
| OP-F información contradictoria | PASS → conflicto + `SOLICITAR_APROBACION` |
| NS-1 administrativo | PASS |
| NS-2 comercial | PASS |
| Anti-prefabricado | PASS |
| Idempotencia | PASS |
| Multi-tenant | PASS |
| E2E reactivo | PASS |
| E2E proactivo (scheduler) | PASS |

---

## Tests

- `tests/test_oportunidades_proactivas_1030.py` — **38 tests** (35+ requeridos)
- Regresión completa: **503 passed** (2 skipped)
- `npm run build` — PASS
- `alembic heads` — un solo head `1030a1b2c3d4e`
- Migración upgrade/downgrade/upgrade — PASS

---

## Evidencias

`INTERCAMBIO/SALIDA/oportunidades_1030/`:
- E2E_REACTIVO.json, E2E_PROACTIVO.json
- CASO_OP_A…F.json, CASO_NS_1.json, CASO_NS_2.json
- PRIORIZACION_GLOBAL.json, SEGUNDA_EJECUCION.json, TRAZABILIDAD.json

---

## Limitaciones

- Scheduler proactivo usa indicadores sintéticos genéricos (no conectores externos reales)
- PR #23 no integrado en base — G-03 E2E experiencia SALUD no re-certificado aquí
- CI GitHub pendiente de validación post-push

---

## NO MERGE

Este entregable no incluye merge automático a main.
