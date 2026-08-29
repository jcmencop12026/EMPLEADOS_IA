# EMPLEADOS_IA — AUDITORÍA DE INTELIGENCIA PARA LA DECISIÓN

**Tipo:** Solo lectura — **NO desarrollar**  
**Fecha:** 2026-08-29  
**Base funcional de referencia:** `4b67183af1d527684e41cad0b02d7a997d3b2499` (`cursor/base-puente-v1-post-v1`)  
**Agente:** GENERAL

---

## 0. Propósito y principio rector

EMPLEADOS_IA debe ofrecer **inteligencia para la decisión**, no solo dashboard + KPI + alertas.

**Cadena objetivo:**

```
DATO → SEÑAL → QUÉ PASÓ → POR QUÉ → QUIÉN/DÓNDE → DESDE CUÁNDO → CUÁNTO
→ TENDENCIA → QUÉ PODRÍA PASAR → RIESGO/OPORTUNIDAD → QUÉ HACER
→ EVIDENCIA → APROBACIÓN → EJECUCIÓN → RESULTADO → APRENDIZAJE → REPRIORIZACIÓN
```

**Reglas de esta auditoría:**

- Solo lectura sobre código real (base puente + ramas fuente 1260–1360).
- **Existencia ≠ integración** — modelo/endpoint aislado no cuenta como capacidad completa.
- **Reutilizar y conectar** lo construido; no crear otro dashboard ni otro motor.
- **NO recalcular** matriz 94 ni porcentaje global del proyecto.

---

## 1. Resumen ejecutivo

| Hallazgo | Estado |
|----------|--------|
| **Núcleo transversal (base puente)** | Cadena **1120 → 1220 → 1030/1100 → ejecución → 1200/1210/1110** implementada con trazabilidad estructurada |
| **Centro de Control 1230/1250** | Dashboard único con agregación real vía 6 adapters; **parcial** en profundidad causal/evidencia |
| **Motor analítico 1000** | **Aislado** en vertical SALUD/IPS — no alimenta hub transversal |
| **Bloques 1260–1360** | **Parciales** en ramas feature; **ninguno integrado** al CC convergido |
| **Predictivo real** | **Parcial** — escenarios deterministas; sin forecast/ML transversal |
| **Aprendizaje cerrado** | **Parcial** — 1010/1260 piezas existen; circuito 1290→ejecución **abierto** |

**Veredicto:** **CADENA NÚCLEO SÓLIDA — INTEGRACIÓN TRANSVERSAL Y CIERRE DE BUCLE INCOMPLETOS**

---

## 2. Bloques examinados

| Bloque | Rama / ubicación | Rol en cadena decisión |
|--------|------------------|------------------------|
| 1000 | Base (`motor_analitico/`) | Motor causal IPS/SALUD |
| 1010 | Base (`experience_core`, `orchestrator_selection`) | Selección equipo + aprendizaje experiencia |
| 1030 | Base (`proactive_service`) | Hub oportunidades proactivas |
| 1100 | Base (extensión 1030) | Cierre operativo oportunidades |
| 1110 | Base (`finops_service`) | Costo/consumo/ROI operativo |
| 1120 | Base (`signal_ingestion_service`) | Entrada señales reales |
| 1200 | Base (`baseline_service`) | Línea base, variación, impacto |
| 1210 | Base (`valuation_service`) | Valoración formal, escenarios, ROI |
| 1220 | Base (`diagnostic_service`) | Diagnóstico, correlaciones, causas |
| 1230 | Base (`control_center_service`) | Vista ejecutiva única |
| 1240 | Base (`external_intelligence_service`) | Inteligencia externa |
| 1250 | Base (`control_center_adapters`) | Convergencia CC + cadena ejecutiva |
| 1260 | `cursor/1260-aprendizaje-repriorizacion` | Aprendizaje / repriorización |
| 1270 | `cursor/1270-multiproveedor-observabilidad-9a85` | Observabilidad LLM |
| 1280 | `cursor/1280-modelo-comercial-valor-85e4` | Valor comercial / propuestas |
| 1290 | `cursor/1290-optimizacion-recomendaciones` | Optimización portfolio |
| 1330 | `cursor/1330-integraciones-reales-conectores` | Conectores → señales |
| 1340 | `cursor/1340-implementacion-exito-cliente` | Implementación / éxito |
| 1350 | `cursor/1350-gobierno-datos-privacidad` | Gobierno datos |
| 1360 | `cursor/1360-continuidad-resiliencia` | Continuidad / incidentes |

**Total bloques evaluados:** **20**

---

## 3. Clasificación por tipo de presencia

| Clasificación | Cantidad (bloques) | Bloques |
|---------------|-------------------|---------|
| **IMPLEMENTADA E INTEGRADA** | **7** | 1030, 1100, 1110, 1120, 1210, 1220, 1250 (CC adapters) |
| **IMPLEMENTADA PERO AISLADA** | **2** | 1000 (SALUD), 1270 (rama feature sin CC) |
| **PARCIAL** | **11** | 1010, 1200, 1230, 1240, 1260, 1280, 1290, 1330, 1340, 1350, 1360 |
| **PREPARADA PERO NO IMPLEMENTADA** | **4** | Wiring 1350↔1270/1330; adapter CC 1240; `EJECUTADA` 1290; aprendizaje 1360→1260 |
| **NO EXISTE** | **0** | — (todos los bloques auditados tienen código) |

**Total capacidades de bloque evaluadas:** **20**  
**Filas matriz funcional (eslabones cadena):** **18**  
**Capacidades controladas (bloques × dimensiones críticas):** **62**

---

## 4. Estado por eslabón de la cadena

### 4.1 QUÉ (qué pasó)

| Aspecto | Estado | Evidencia código |
|---------|--------|------------------|
| KPI / variaciones | **INTEGRADA** | `baseline_service.calculate_variation`; indicadores CC; FinOps dashboard |
| Detección señales | **INTEGRADA** | `signal_ingestion_service.ingest_real_signal` → `proactive_service.process_signal` |
| Anomalías / hallazgos | **INTEGRADA** | `diagnostic_service` hallazgos tipados `HECHO`/`INTERPRETACION` |
| Comparación periodos | **PARCIAL** | FinOps/1220 por periodo; no universal en CC |
| Descripción hechos | **INTEGRADA** | `que_ocurre`, `evidencia_resumen`, traces |

**Servicios:** `proactive_service.py`, `diagnostic_service.py`, `baseline_service.py`, `finops_service.py`  
**API:** `/api/senales/*`, `/api/diagnosticos/*`, `/api/oportunidades/*`, `/api/centro-control/resumen-ejecutivo`  
**Tests:** `test_senales_reales_1120.py`, `test_diagnostico_transversal_1220.py`, `test_bloque_1230_centro_control.py`

---

### 4.2 POR QUÉ (causal / diagnóstico) — CRÍTICO

| Nivel | Estado | Evidencia |
|-------|--------|-----------|
| **CAUSA DEMOSTRADA** | **PARCIAL** | Umbrales + indicadores en 1220; motor 1000 con evidencia listada (SALUD) |
| **CAUSA PROBABLE** | **INTEGRADA** | `infer_probable_causes` en `diagnostic_service.py` con `justificacion` determinística |
| **HIPÓTESIS** | **INTEGRADA** | `tipo="HIPOTESIS"` en causas; externas marcadas «requiere validación» |
| **SIN EVIDENCIA** | **Rechazado por diseño** | Correlaciones con `es_causal=False`, `nota_causalidad` explícita |

**No se acepta** explicación libre IA sin evidencia en la cadena auditada (1030–1220, motor 1000): reglas + JSON trazable.

**Gap P1:** CC muestra agregados pero **no expone cadena causal completa** en resumen (profundización vía enlaces a `/diagnosticos/{id}`).

---

### 4.3 QUIÉN / DÓNDE (segmentación)

| Dimensión | Soportada | Bloque |
|-----------|-----------|--------|
| `organization_id` (empresa) | **SÍ** | Transversal multitenant |
| `proceso` | **SÍ** | Señales, diagnóstico, línea base |
| `dominio` / `subproceso` | **SÍ** | 1030, 1220 |
| `employee_id` / empleado IA | **SÍ** | 1010, operaciones, FinOps presupuesto |
| `opportunity_id` | **SÍ** | Hub 1030 |
| `work_plan_id` | **SÍ** | Ejecución |
| Cliente / pagador / sede / área | **NO / PARCIAL** | No modelo transversal dedicado |
| Proveedor / canal / integración | **PARCIAL** | 1240 fuente; 1330 conector (rama aislada) |
| Modelo IA | **PARCIAL** | 1270 logs inferencia (rama aislada) |

**Estado global:** **PARCIAL** — dimensiones núcleo sí; sectoriales parametrizables solo donde el bloque lo define.

---

### 4.4 DESDE CUÁNDO / TENDENCIA

| Capacidad | Estado | Evidencia |
|-----------|--------|-----------|
| Series temporales | **PARCIAL** | `LineaBaseHistorial`, `get_evolucion()` (1200) |
| Comparación periodos | **INTEGRADA** | 1220 `periodo_inicio/fin`; FinOps filtros MTD/7d/30d |
| Línea base | **INTEGRADA** | 1200 variación % vs `valor_base` |
| Persistencia problema | **PARCIAL** | Estados oportunidad + tracking 1100 |
| Estacionalidad | **NO EXISTE** | — |
| Aceleración/desaceleración | **NO EXISTE** | — |

**Estado global:** **PARCIAL**

---

### 4.5 CUÁNTO (cuantificación)

| Expresión | Estado | Fuente | Clasificación valor |
|-----------|--------|--------|---------------------|
| Valor afectado / potencial | **INTEGRADA** | 1030 `valor_potencial` | VERIFICADO / ESTIMADO |
| ROI / payback | **INTEGRADA** | 1210 `compute_economic_summary` | VERIFICADO o `NO CALCULABLE` |
| Costo IA | **INTEGRADA** | 1110 FinOps | VERIFICADO |
| Ahorro / beneficio neto | **INTEGRADA** | 1210 escenarios | ESTIMADO (probabilidad) |
| Impacto real vs esperado | **PARCIAL** | 1200 `impacto_real`; cierre manual | VERIFICADO si medición validada |
| Valor comercial | **AISLADA** | 1280 rama feature | ESTIMADO |
| Productividad liberada | **NO EXISTE** transversal | — | — |

**Integración 1200+1210+1110+1280:** **PARCIAL** en base puente (1280 no convergido).

**Estado global:** **PARCIAL** (fuerte en oportunidad; débil en CC agregado)

---

### 4.6 QUÉ PODRÍA PASAR (predictivo)

| Tipo | Estado | Evidencia | ¿Es predictivo real? |
|------|--------|-----------|----------------------|
| Escenarios CONSERVADOR/PROBABLE/OPTIMISTA | **INTEGRADA** | 1210, motor 1000 `scenarios.py` | **NO** — simulación con supuestos |
| Proyección presupuesto | **PARCIAL** | 1110 `project_budget_spend` | Tendencia lineal |
| Scoring oportunidad | **INTEGRADA** | 1030 `prioridad_componentes_json` | Heurística, no forecast |
| Forecast / probabilidad futura | **NO EXISTE** | — | — |
| Riesgo futuro modelado | **PARCIAL** | 1240 riesgo desde señal externa | Reglas + validación humana |

**GAP REAL predictivo:** no hay motor de forecast transversal; escenarios ≠ predicción.

**Estado global:** **PARCIAL** (escenarios sí; predictivo formal no)

---

### 4.7 RIESGO / OPORTUNIDAD

| Capacidad | Estado | Evidencia |
|-----------|--------|-----------|
| Detección oportunidad | **INTEGRADA** | 1030 pipeline completo |
| Clasificación riesgo | **INTEGRADA** | `urgencia`, `riesgo` en oportunidad; externo 1240 |
| Priorización global | **INTEGRADA** | `prioritize_opportunities_global` |
| Enlace diagnóstico→oportunidad | **INTEGRADA** | 1220 auto-creación HECHO+ALTA |

**Estado global:** **INTEGRADA**

---

### 4.8 QUÉ HACER (recomendación)

| Tipo | Estado | Bloque | Mecanismo |
|------|--------|--------|-----------|
| Regla determinística | **INTEGRADA** | 1030 | `compute_next_best_action`, `siguiente_accion_json` |
| Recomendación IA (equipo) | **INTEGRADA** | 1010 | `select_team` — no texto libre como verdad |
| Portfolio optimización | **AISLADA** | 1290 | `optimization_service` — sin `EJECUTADA` |
| Repriorización aprendida | **AISLADA** | 1260 | `aplicar_recalibracion` — rama no convergida |
| Acción automática | **PARCIAL** | 1030 | `AUTOMATICA_PERMITIDA` con gates |
| Acción con aprobación | **INTEGRADA** | 1030 + coordinator | `REQUIERE_APROBACION`, `ApprovalRequest` |

**Estado global:** **PARCIAL**

---

### 4.9 EVIDENCIA

| Requisito | Estado | Evidencia |
|-----------|--------|-----------|
| Dato / periodo / fuente en conclusión | **INTEGRADA** (backend) | `evidencia_json`, `OpportunityTrace`, `ExternalEvidence` |
| Distinción HECHO / INFERENCIA / RECOMENDACIÓN | **PARCIAL** | Tipos en modelos 1220/1240; UI CC no siempre distingue |
| Trazabilidad end-to-end | **INTEGRADA** | `correlation_id`, `/trazabilidad` en señales/diagnóstico/oportunidades |
| Sin external no verificado como hecho | **INTEGRADA** | 1240 `hecho_observado` vs `hipotesis`; validación explícita |

**Estado global:** **PARCIAL** (fuerte en API; mejorable en CC/UI)

---

### 4.10 DRILL-DOWN

| Ruta | Funciona hoy | Se corta en |
|------|--------------|-------------|
| CC KPI → módulo | **SÍ** | Enlaces `enlace` en indicadores |
| Oportunidad → señal → diagnóstico | **SÍ** | `cadena_ejecutiva` + `/trazabilidad` |
| FinOps drill-down | **SÍ** | `GET /api/finops/drill-down` |
| Diagnóstico → evidencia/causas | **SÍ** | `GET /api/diagnosticos/{id}/trazabilidad` |
| CC → causal → registro | **PARCIAL** | CC no muestra causas; salto a módulo |
| Comercial → valoración | **AISLADA** | 1280 no en base puente |
| Parametrizable por sector | **PARCIAL** | Dominios en 1220; no config UI transversal |

**Estado global:** **PARCIAL**

---

### 4.11 ACCIÓN (cadena ejecución)

```
recomendación → aprobación → orquestador → empleado IA / automatización → integración → auditoría
```

| Eslabón | Estado | Evidencia |
|---------|--------|-----------|
| Recomendación | **INTEGRADA** | `siguiente_accion_json` |
| Aprobación humana | **INTEGRADA** | `approve_opportunity`, `ApprovalRequest`, `/aprobaciones` |
| Orquestador | **INTEGRADA** | `coordinator.py`, `WorkPlan` |
| Empleado IA | **INTEGRADA** | `agent_factory`, ejecución tareas |
| Automatización | **INTEGRADA** | `automations` + scheduler |
| Integración/herramienta | **PARCIAL** | 1330 rama aislada |
| Auditoría | **INTEGRADA** | `write_audit`, `AuditLog` |

**Estado global:** **PARCIAL** (núcleo E2E operaciones sí; conectores fuera)

---

### 4.12 RESULTADO

| Capacidad | Estado | Evidencia |
|-----------|--------|-----------|
| Registrar resultado oportunidad | **INTEGRADA** | `register_result`, `POST .../resultado` |
| Comparar vs esperado | **INTEGRADA** | `valor_real` vs esperado en 1030/1210 |
| Comparar vs línea base | **PARCIAL** | 1200 manual; no auto al cerrar oportunidad |
| mejoró / empeoró / sin cambio | **PARCIAL** | `evaluate_direction` (1200); no unificado en cierre |
| Cuantificar impacto post-acción | **PARCIAL** | 1200 `impacto_real` si medición existe |

**Estado global:** **PARCIAL**

---

### 4.13 APRENDIZAJE / REPRIORIZACIÓN

| Circuito | Estado | Evidencia |
|----------|--------|-----------|
| Experiencia post-resultado | **INTEGRADA** (1010) | `register_opportunity_learning` → `crear_experiencia` |
| Ciclo 1260 desviación→recalibración | **AISLADA** | `learning_service.py` — rama no convergida |
| 1290 influencia aprendizaje | **AISLADA** | `_cargar_aprendizaje` en rama 1290 |
| Repriorización global | **INTEGRADA** | `prioritize_opportunities_global` (1030) |
| 1360 post-incidente → 1260 | **PREPARADA** | `integracion_1260_prep` stub |

**Estado global:** **PARCIAL**

---

### 4.14 INTERNO + EXTERNO (1240)

| Capacidad | Estado | Evidencia |
|-----------|--------|-----------|
| Fuentes externas | **INTEGRADA** | `ExternalSource`, ingesta |
| Hecho vs hipótesis externa | **INTEGRADA** | `ExternalSignalExtension` |
| Frescura / desactualización | **INTEGRADA** | `compute_freshness` |
| Enlace a señales 1120 | **INTEGRADA** | `ingest` → `ProactiveSignal` |
| Enlace a diagnóstico 1220 | **INTEGRADA** | `detect_findings_from_external_signals` |
| Combinar en CC | **PARCIAL** | Sin adapter dedicado; vía diagnóstico/señales |
| No presentar externo no verificado como hecho | **INTEGRADA** | Validación + tipos |

**Estado global:** **PARCIAL** (pipeline sí; CC incompleto)

---

### 4.15 CENTRO DE CONTROL (1230/1250)

| Requisito receta A | Estado actual |
|--------------------|---------------|
| Dashboard único | **SÍ** — `CentroControlPage` ruta `/` |
| Extender, no crear otro | **SÍ** — un endpoint `resumen-ejecutivo` |
| 6 adapters integrados | **SÍ** — 1100, 1200, 1110, 1210, 1220, 1120 |
| Cadena ejecutiva | **SÍ** — `_cadena_ejecutiva` con enlaces |
| 12 secciones (receta A) | **PARCIAL** — ~10 secciones UI; faltan profundidad causal/evidencia unificada |
| QUÉ→POR QUÉ→…→ACCIÓN en CC | **PARCIAL** — resumen + enlaces; no todas las dimensiones en una vista |
| RESUMEN → PROFUNDIZACIÓN → EVIDENCIA → ACCIÓN | **PARCIAL** — resumen sí; evidencia vía drill a módulos |
| Filtros `proceso`/`estado` | **PREPARADA** | Aceptados en API pero **no aplicados** en queries |

**Estado global:** **PARCIAL**

---

## 5. Matriz funcional

**Leyenda ESTADO:** II=Integrada | IA=Aislada | P=Parcial | PN=Preparada | NE=No existe  
**SEVERIDAD gap:** P0–P3 | **ACCIÓN:** Conectar / Extender / Completar / N/A

| CAPACIDAD | BLOQUE(S) | BACKEND | API | FRONTEND | PRUEBAS | INTEGRACIÓN | ESTADO | GAP | SEV | ACCIÓN NECESARIA |
|-----------|-----------|---------|-----|----------|---------|-------------|--------|-----|-----|------------------|
| **QUÉ** | 1120,1220,1030,1230 | `diagnostic_service`, `proactive_service`, CC | `/senales`, `/diagnosticos`, `/centro-control` | CC, módulos | 1120,1220,1230 | CC adapters | **P→II** | CC sin todos los KPIs causales | P2 | Extender adapters CC |
| **POR QUÉ** | 1220,1000 | `diagnostic_service`, `hypothesis_engine` | `/diagnosticos/{id}/trazabilidad` | Diagnóstico detail | 1220,1000 | 1220↔1030 sí; 1000 aislado | **P** | CC no muestra causas; 1000 no en hub | **P1** | Conectar 1000 o portar patrones; CC sección causal |
| **QUIÉN** | 1030,1220,1110 | modelos org/proceso/employee | filtros en APIs | parcial | multitenant | por módulo | **P** | dimensiones sectoriales limitadas | P2 | Parametrizar en 1220/config |
| **DÓNDE** | 1120,1240 | señal.proceso, ext.fuente | ingesta, contexto | IE pages | 1120,1240 | 1240→1120→1220 | **P** | sin geografía/sede transversal | P3 | Según vertical |
| **DESDE CUÁNDO** | 1200,1220,1110 | historial, periodos | lineas-base, finops | CC periodo | 1200,1110 | parcial CC | **P** | sin estacionalidad | P3 | N/A corto plazo |
| **CUÁNTO** | 1210,1110,1200,1280 | valuation, finops, baseline | `/valoracion`, `/finops` | CostosValor, opp | 1210,1110,1200 | 1280 aislado | **P** | 1280 fuera de puente | P2 | Converger cadena C |
| **TENDENCIA** | 1200,1110,1270 | evolución, MTD | lineas-base, llm/obs | CC periodo | 1200,1270 | 1270 aislado | **P** | sin tendencia unificada CC | P2 | Adapter 1270 en CC |
| **PREDICCIÓN** | 1210,1000 | scenarios | escenarios valoración | en valoración | 1210 | escenarios ≠ forecast | **P** | sin forecast real | P2 | Documentar como escenario; no inflar |
| **RIESGO** | 1030,1240 | oportunidad.urgencia | IE riesgo | oportunidades | 1030,1240 | integrado | **II** | — | — | N/A |
| **OPORTUNIDAD** | 1030,1100 | proactive pipeline | `/oportunidades` | Oportunidades | 1100 | CC adapter | **II** | — | — | N/A |
| **RECOMENDACIÓN** | 1030,1290,1260 | `compute_next_best_action`, optimization | `/oportunidades/.../siguiente-accion` | opp detail | 1030,1290 | 1290/1260 aislados | **P** | 1290 sin ejecutar | **P1** | Cerrar loop 1290→1030 |
| **EVIDENCIA** | 1220,1240,1030 | evidencia_json, traces | trazabilidad endpoints | parcial | 1220,1240 | API fuerte | **P** | UI no distingue siempre | **P1** | Badges HECHO/INFERENCIA en CC |
| **DRILL-DOWN** | CC,1110,1220 | adapters, drill-down | finops drill, trazas | enlaces CC | 1250c | por módulo | **P** | corte CC→causal | P2 | Enlaces causales en CC |
| **APROBACIÓN** | 1030,ops | approve, ApprovalRequest | aprobaciones | ApprovalsPage | 1100,ops | E2E | **II** | — | — | N/A |
| **EJECUCIÓN** | ops,1010 | coordinator, WorkPlan | ejecuciones | Executions | ops | E2E | **II** | — | — | N/A |
| **RESULTADO** | 1030,1200,1210 | register_result, baseline | resultado, valoración | opp detail | 1100,1200 | manual 1200 | **P** | sin auto línea base | **P1** | Hook cierre→1200 |
| **APRENDIZAJE** | 1010,1260,1360 | experience, learning | experiencia, aprendizaje | parcial | 1260 | 1260 aislado | **P** | bucle incompleto | P2 | Converger 1260; 1360→1260 |
| **REPRIORIZACIÓN** | 1030,1260 | prioritize, recalibración | priorizar, aprendizaje | parcial | 1260 | 1260 aislado | **P** | repriorización aprendida fuera | P2 | Integrar 1260 post-F2 |

---

## 6. Trazabilidad a código (referencias clave)

| Mecanismo | Archivo | Qué garantiza |
|-----------|---------|--------------|
| `correlation_id` | `proactive_service.py`, señales | Cadena auditable |
| `OpportunityTrace.etapa` | `opportunity_models.py` | Etapas discretas |
| `prioridad_componentes_json` | `Opportunity` | Score explicable |
| `es_causal=False` | `diagnostic_service.py:40,696` | No confundir correlación |
| `tipo HIPOTESIS` | `diagnostic_service.py:788-805` | Causa no demostrada marcada |
| `NO CALCULABLE` | `valuation_service.py` | No inventar ROI |
| `hypothesis_engine` H1–H10 | `motor_analitico/hypothesis_engine.py` | Evidencia listada (SALUD) |
| `_cadena_ejecutiva` | `control_center_service.py:409-474` | SEÑAL→…→COSTO con enlaces |
| 6 adapters CC | `control_center_adapters.py` | Integración real 1100–1220 |
| `ExternalEvidence` | `external_models.py` | Trazabilidad externa |

**LLM:** existe gateway (`llm_providers.py`) para ejecución de empleados; **no** es fuente de verdad de la cadena 1030–1220.

---

## 7. Gaps y severidades

| ID | Gap | Severidad | Justificación |
|----|-----|-----------|---------------|
| G-01 | CC no expone POR QUÉ/causas en resumen | **P1** | Decisión ejecutiva sin causal en punto único |
| G-02 | UI no distingue siempre HECHO/INFERENCIA/RECOMENDACIÓN | **P1** | Riesgo de decisión sobre hipótesis |
| G-03 | 1200 no enlaza automáticamente al cerrar oportunidad | **P1** | RESULTADO sin medición sistemática |
| G-04 | 1290 sin transición APROBADA→EJECUTADA | **P1** | Recomendación no vinculada a acción |
| G-05 | Motor 1000 aislado en SALUD | **P2** | Patrones causales no reutilizados transversalmente |
| G-06 | 1240 sin adapter CC dedicado | **P2** | Interno+externo incompleto en vista ejecutiva |
| G-07 | Filtros proceso/estado CC no aplicados | **P2** | QUIÉN/DÓNDE degradado en CC |
| G-08 | Bloques 1260–1360 no convergidos | **P2** | Aprendizaje/comercial/continuidad fuera del bucle |
| G-09 | Sin forecast/predictivo real | **P2** | Escenarios ≠ predicción — gap real documentado |
| G-10 | Wiring 1350↔1270/1330 preparado no runtime | **P2** | Gobierno no enforced en ejecución |
| G-11 | 1360→1260 aprendizaje stub | **P2** | Circuito aprendizaje incidentes incompleto |
| G-12 | Gaps UI CC (4 receta A) | **P3** | No bloquean núcleo |
| G-13 | SCIM rate limit memoria | **P3** | P2 conocido permitido |

| Severidad | Cantidad |
|-----------|----------|
| **P0** | **0** |
| **P1** | **4** |
| **P2** | **7** |
| **P3** | **2** |

---

## 8. Diez escenarios E2E de negocio (diseño de prueba)

Cada escenario debe recorrer la cadena objetivo. Estado **hoy** = capacidad en base puente sin convergencia 1260–1360.

| # | Escenario | Sector ejemplo | Recorrido esperado | Estado hoy |
|---|-----------|----------------|-------------------|------------|
| E1 | **Deterioro KPI** | Tasa rechazo facturas ↑ | Señal 1120 → diag 1220 → opp 1030 → CC | **P** — falta causal en CC |
| E2 | **Aumento costos IA** | Consumo LLM sobre presupuesto | FinOps 1110 alerta → drill-down → aprobación | **II** — E2E en FinOps+CC |
| E3 | **Pérdida ingresos** | Cartera morosa ↑ | Señal → diag → valoración 1210 ROI | **P** — cuantificación manual parcial |
| E4 | **Oportunidad nuevos ingresos** | Demanda externa 1240 | IE → señal → opp → valoración | **P** — 1240 sin CC |
| E5 | **Problema operativo** | Cola aprobaciones | CC atención → ops → aprobación | **II** |
| E6 | **Riesgo** | Señal externa regulación | 1240 riesgo → opp PENDIENTE_APROBACION | **P** — validación humana obligatoria |
| E7 | **Anomalía** | Indicador fuera umbral | 1220 hallazgo HECHO → trazabilidad | **II** en backend |
| E8 | **Oportunidad externa** | Competencia / mercado | 1240 → 1120 → 1030 | **P** |
| E9 | **Recomendación ejecutada** | Priorizar opp → aprobar → WorkPlan | 1030 → ops → resultado | **II** |
| E10 | **Recomendación sin resultado** | Cerrada sin materializar | resultado → desviación → (1260) | **P** — 1260 no convergido |

---

## 9. Criterios de aceptación final (convergencia)

La convergencia **NO se considera completa** para inteligencia de decisión si:

### 9.1 Obligatorios (P0/P1 = 0)

1. Cadena **1120→1220→1030→ejecución→resultado** preservada íntegra.
2. CC único (`1230`) con **todos los adapters** de bloques incorporados (incl. 1240, 1260–1360 según fase).
3. Toda conclusión en CC/API distingue **HECHO / INFERENCIA / RECOMENDACIÓN**.
4. **POR QUÉ** accesible desde CC (resumen o enlace directo a causal con evidencia).
5. **CUÁNTO** con clasificación VERIFICADO/ESTIMADO/POTENCIAL cuando hay datos.
6. Cierre oportunidad dispara **medición/impacto** (1200) o justificación documentada de omisión.
7. Recomendación 1290 (si incorporada) vinculada a **acción o repriorización** verificable.
8. **Multiempresa** intacto en toda la cadena (tests existentes PASS).
9. **Sin segundo dashboard** ejecutivo.
10. **Sin motor paralelo** — reutilizar motor 1000 patrones o integrar vía 1220.

### 9.2 Deseables (P2 aceptables documentados)

- Forecast formal (si no existe, etiquetar escenarios como simulación).
- Estacionalidad.
- Wiring governance runtime 1350↔1270/1330.
- SCIM rate limit compartido.

### 9.3 Matriz 94

**ACTUALIZAR DESPUÉS DE CONVERGENCIA FINAL 1260–1380** — este documento es insumo, no recálculo.

---

## 10. Criterio funcional obligatorio para convergencia

Al incorporar cada bloque en convergencia, verificar:

| # | Criterio |
|---|----------|
| C-01 | ¿Aporta a la cadena decisión o solo KPI aislado? |
| C-02 | ¿Tiene trazabilidad/evidencia estructurada? |
| C-03 | ¿Se integra al CC vía adapter (receta A)? |
| C-04 | ¿Mantiene distinción hecho/inferencia/recomendación? |
| C-05 | ¿Permite drill-down a registro/evidencia? |
| C-06 | ¿Cierra o alimenta bucle acción→resultado→aprendizaje? |
| C-07 | ¿Respeta multiempresa y V1? |
| C-08 | ¿No duplica dashboard ni motor existente? |

---

## Restricciones respetadas

- SOLO LECTURA — 0 modificaciones funcionales
- NO otro dashboard ni motor creado
- NO merge / rebase / main / V1 / PR #32
- NO recálculo matriz 94 ni porcentaje global
- NO `git add .`

---

## Salida final

```
EMPLEADOS IA — AUDITORÍA INTELIGENCIA PARA DECISIÓN PREPARADA

CAPACIDADES EVALUADAS:
62

IMPLEMENTADAS E INTEGRADAS:
7 (bloques núcleo)

IMPLEMENTADAS AISLADAS:
2

PARCIALES:
11

NO IMPLEMENTADAS:
0

QUÉ:
INTEGRADA EN NÚCLEO — PARCIAL EN CC

POR QUÉ:
PARCIAL — CAUSA PROBABLE/HIPÓTESIS EN 1220; GAP CC Y MOTOR 1000 AISLADO

QUIÉN/DÓNDE:
PARCIAL — ORG/PROCESO/DOMINIO SÍ; DIMENSIONES SECTORIALES LIMITADAS

CUÁNTO:
PARCIAL — 1210/1110/1200 FUERTES; 1280 NO CONVERGIDO

TENDENCIA:
PARCIAL — PERIODOS Y EVOLUCIÓN 1200; SIN UNIFICACIÓN CC

PREDICTIVO:
PARCIAL — ESCENARIOS SÍ; FORECAST REAL NO

RECOMENDACIÓN:
PARCIAL — 1030 INTEGRADA; 1290/1260 AISLADAS

EVIDENCIA:
PARCIAL — API FUERTE; UI/CC MEJORABLE

DRILL-DOWN:
PARCIAL — POR MÓDULO SÍ; CC→CAUSAL CORTADO

ACCIÓN:
PARCIAL — NÚCLEO OPS E2E; CONECTORES FUERA

RESULTADO:
PARCIAL — REGISTRO SÍ; LÍNEA BASE AUTO NO

APRENDIZAJE:
PARCIAL — 1010 SÍ; 1260/1290 NO CERRADOS

INTERNO + EXTERNO:
PARCIAL — PIPELINE 1240 SÍ; CC INCOMPLETO

CENTRO CONTROL:
PARCIAL — DASHBOARD ÚNICO CON 6 ADAPTERS; PROFUNDIDAD DECISIÓN INCOMPLETA

ESCENARIOS E2E DEFINIDOS:
10

P0:
0

P1:
4

P2:
7

P3:
2

MODIFICACIONES FUNCIONALES:
0

MATRIZ 94 RECALCULADA:
NO

VEREDICTO:
CADENA NÚCLEO SÓLIDA — CRITERIO CONVERGENCIA PREPARADO
```

---

## Veredicto

**CADENA NÚCLEO SÓLIDA — CRITERIO CONVERGENCIA PREPARADO**

El código base puente ya implementa inteligencia para la decisión en el eje **señal → diagnóstico → oportunidad → ejecución → valor/costo**, con trazabilidad estructurada y sin depender de narrativa IA libre. Los gaps críticos para la convergencia final son: **profundidad causal y evidencia en Centro de Control**, **cierre automático resultado→medición**, **integración de bloques 1260–1360**, y **honestidad predictiva** (escenarios ≠ forecast).

Este documento es **insumo** para la matriz 94 post-convergencia — no modifica porcentaje global.
