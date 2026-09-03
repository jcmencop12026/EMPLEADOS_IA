# EIAAX — Inteligencia económica + simulación + valor empresarial (1740)

**Rama:** `cursor/inteligencia-economica-simulacion-3581`  
**Base:** `cursor/flujo-comercial-v1-3581`  
**Migración:** `1740a1b2c3d4e`  
**Estado:** Aislado — sin integración a GENERAL ni V1 estable

---

## 1. Qué existía (auditoría)

| Ámbito | Módulo existente | Ruta |
|--------|------------------|------|
| FinOps / consumo / presupuestos | 950/1110 + MB-07 | `/api/finops` |
| Motor económico canónico | 1600 | `/api/motor-economico` |
| Valoración / ROI | 1210 | `/api/valoracion` |
| Comercial / pricing | 1280 | `/api/comercial` |
| Centro de Negocios | 1700/1710 | `/api/centro-negocios` |
| TCO / escenarios | 1320 | `/api/tco` |
| Línea base / impacto | 1200 | `/api/linea-base` |
| Optimización portfolio | 1290 | `/api/optimizacion` |

**Brecha principal:** simuladores fragmentados; faltaba orquestador unificado de escenarios multi-tipo, vista consolidada resultado económico/valor empresarial, facade economía empleado IA y contratos de integración GENERAL.

---

## 2. Qué reutilizó (no reconstruido)

- `economic_motor_service` — costos unificados, valores por naturaleza, indicadores ANTES/PROYECTADO/REAL
- `finops_service.dashboard_summary` — consumo real
- `consumption_planner_service` — simulate, employee_cost_detail, presupuesto_summary, org_resumen
- `commercial_service._compute_economics` — pricing comercial
- `motor_svc.recommend_price` — recomendación BORRADOR
- `tco_service.calcular_tco` — TCO propuesta (inteligencia comercial interna)
- Enums `EconomicValueType`, `RealValueNature`, `COST_CLASSES`

---

## 3. Qué desarrolló (1740)

### Backend

| Componente | Archivo |
|------------|---------|
| Enums escenarios/dimensionamiento | `backend/app/inteligencia_economica_enums.py` |
| Modelo persistencia runs | `backend/app/inteligencia_economica_models.py` |
| Contratos integración GENERAL | `backend/app/inteligencia_economica_ports.py` |
| Servicio orquestador | `backend/app/services/inteligencia_economica_service.py` |
| Schemas API | `backend/app/schemas_inteligencia_economica.py` |
| Router | `backend/app/routers/inteligencia_economica.py` |
| Migración | `backend/alembic/versions/1740a1b2c3d4e_inteligencia_economica_escenarios.py` |

### Capacidades

1. **Motor económico canónico** — agregación vía motor 1600 (DIRECTO / TRANSVERSAL_ATRIBUIBLE / PLATAFORMA)
2. **Valor empresarial** — rollup por tipo y naturaleza; POTENCIAL excluido de realizado
3. **Resultado económico** — beneficio neto, ROI, payback, proyectado vs real, desviaciones
4. **Simulador escenarios** — ACTUAL → SOLUCION_COMBINADA (6 tipos)
5. **Dimensionamiento** — capacidad liberada sin despido obligatorio
6. **Economía empleado IA** — facade planner + motor
7. **Economía empresa** — presupuesto, consumo, capacidad, alertas
8. **Inteligencia comercial interna** — `auto_publicado: false`
9. **Pricing basado en valor** — fracción configurable; separación COSTO/PRECIO/VALOR/MARGEN

### APIs

```
GET  /api/inteligencia-economica/auditoria
GET  /api/inteligencia-economica/valor-empresarial
GET  /api/inteligencia-economica/resultado-economico
POST /api/inteligencia-economica/escenarios/comparar
POST /api/inteligencia-economica/dimensionar
GET  /api/inteligencia-economica/empleados/{id}/economia
GET  /api/inteligencia-economica/empresa
GET  /api/inteligencia-economica/comercial-interna
POST /api/inteligencia-economica/precio-recomendado-valor
GET  /api/inteligencia-economica/escenarios/runs
```

### Permisos

- `inteligencia_economica.view`
- `inteligencia_economica.simulate`
- `inteligencia_economica.private`

### Frontend

- Tab **Inteligencia económica** en `CostosValorPage.tsx`
- Funciones API en `frontend/src/api.ts`

---

## 4. Contrato integración futura (GENERAL)

`inteligencia_economica_ports.py` define:

- `EconomicIntelligencePort` — resultado + valor
- `ScenarioSimulatorPort` — comparar + dimensionar
- `EmployeeEconomicsPort` — resumen empleado
- `CommercialPricingIntelligencePort` — comercial interna + precio valor
- `LocalEconomicIntelligenceAdapter` — implementación local reemplazable
- `get_economic_intelligence_adapter(db, user)` — factory

GENERAL puede sustituir el adaptador sin acoplar V1.

---

## 5. Pruebas

**Archivo:** `tests/test_inteligencia_economica_1740.py` — **12 passed**

Cobertura: auditoría, valor POTENCIAL excluido, casos cero, 6 escenarios, dimensionamiento, economía empleado/empresa, pricing BORRADOR, comercial interna, multiempresa, decimales, persistencia runs.

**Regresión:** `tests/test_economic_motor_1600.py` — **9 passed**

---

## 6. Riesgos

| Riesgo | Mitigación |
|--------|------------|
| Simulación escenarios usa heurísticas (no TCO completo) | Documentado; reutiliza MB-07 para costos IA |
| Pricing valor depende de motor 1600 + comercial 1280 | Sin publicación automática; status BORRADOR |
| Tabla `economic_scenario_runs` nueva | Migración 1740 aislada |

---

## 7. Restricciones respetadas

- No modifica V1 estable
- No modifica `scripts/windows/**`
- No altera login/arranque certificado
- No integra a GENERAL
- Rama aislada propia
