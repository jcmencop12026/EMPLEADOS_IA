# CURSOR — MOTOR-ANALITICO-1000

**Rama:** `cursor/motor-analitico-1000`  
**Base:** `main` @ `9d5c8de`  
**Estado:** **MOTOR-ANALITICO-1000 LISTO PARA REAUDITORÍA** (NO MERGE)

---

## 1. Arquitectura encontrada y principio reutilizado

El repositorio ya contenía un pipeline IPS en `salud_engine.py` (SALUD-960) con:

| Componente existente | Uso en MOTOR-1000 |
|---------------------|-------------------|
| `salud_indicators.py` | Indicadores determinísticos (base de evidencia) |
| `salud_findings.py` | Hallazgos HECHO/INSUFICIENTE |
| `salud_specialist_selection.py` | Orquestación dinámica de especialistas |
| `salud_knowledge.py` | Conocimiento autorizado |
| `salud_experience.py` | Experiencia y casos similares |
| `salud_workplan_bridge.py` | Plan → WorkPlan/Operaciones |
| `finops_service.registrar_valor` | Valor estimado (FINOPS-950) |
| `DiagnosticoIpsPage.tsx` | UI demo IPS (ampliada, no rediseñada) |

**MOTOR-ANALITICO-1000** se implementó como capa transversal en `backend/app/services/motor_analitico/` que **orquesta y fortalece** lo anterior sin duplicar SALUD, Conocimiento, Operaciones, WorkPlan, FINOPS ni Orquestador.

---

## 2. Qué agregó

### Módulos nuevos (`backend/app/services/motor_analitico/`)

| Módulo | Responsabilidad |
|--------|-----------------|
| `data_sufficiency.py` | SUFICIENTE / PARCIAL / INSUFICIENTE + información faltante |
| `hypothesis_engine.py` | H1–H10, estados CONFIRMADA…REFUTADA, evidencia a favor/en contra |
| `contrast.py` | Contraste APOYAR / CUESTIONAR / REFUTAR / COMPLEMENTAR |
| `alternatives.py` | Ideación multiagente (≥2 alternativas por hallazgo) |
| `prioritization.py` | Ranking documentado con metodología explícita |
| `scenarios.py` | CONSERVADOR / PROBABLE / OPTIMISTA con supuestos |
| `consolidation.py` | Recomendación ejecutiva (14 preguntas) |
| `finops_bridge.py` | Costo/beneficio/ROI ESTIMADO — nunca como real |
| `pipeline.py` | Orquestación `run_motor_analitico()` + huella anti-prefab |

### Fixtures adversariales

`backend/app/fixtures/motor_analitico_datasets.py` — casos A, B, C, D, E + CONSULTOR.

### API

- `GET /api/salud/motor/casos`
- `GET /api/salud/motor/demo/{case_id}`

### Integración

- `salud_engine.run_ips_analysis()` invoca el motor y persiste resultados en `summary_json` / `traceability_json`.
- `get_diagnostico()` expone: hipótesis, contrastes, alternativas, priorización, escenarios, FINOPS, recomendación consolidada.
- `salud_questions.py` ampliado para preguntas naturales trazables.

### UI

`DiagnosticoIpsPage.tsx` — pestañas nuevas: Hipótesis, Alternativas, Impacto/FINOPS, Trazabilidad; botones Caso A–E y CONSULTOR.

### Tests

`tests/test_motor_analitico_1000.py` — 14 pruebas incluyendo **anti-respuesta-prefabricada** y aislamiento tenant.

---

## 3. Modelos y persistencia

**Sin migración Alembic nueva.** Los artefactos del motor se almacenan en JSON existente:

- `IpsAnalysis.summary_json` → clave `motor`
- `IpsAnalysis.traceability_json` → clave `motor`

Tablas SALUD existentes reutilizadas: `ips_analyses`, `ips_hallazgos`, `ips_propuestas`, `ips_experience_cases`, `ips_action_results`.

---

## 4. Orquestación dinámica de especialistas

`select_specialists()` elige por dominio según solicitud + datos disponibles + capacidades + herramientas + experiencia.

El motor registra **por qué** cada especialista fue seleccionado en `trazabilidad_motor.especialistas[].razon_seleccion`.

---

## 5. Cinco datasets adversariales y resultados

| Caso | Problema diseñado | Hipótesis principal esperada | Señal clave |
|------|-------------------|------------------------------|-------------|
| **A** | Cartera por radicación tardía | H2 Radicación tardía | ~36 días factura→radicación, 3 sin radicar |
| **B** | Glosas/devoluciones | H3/H4 Glosas/devoluciones | >8% glosa, devoluciones |
| **C** | Pagador tardío, proceso interno bueno | H7 Comportamiento pagador | Radicación ≤5 días, mora alta |
| **D** | Combinado | H10 Combinación | Radicación + glosas + concentración |
| **E** | Datos insuficientes | H0 Insuficiente | Solo 2 registros facturación |

**Anti-prefab:** `test_anti_prefabricated_response` exige ≥3 hipótesis principales distintas entre A–D y rankings no mecánicamente iguales.

---

## 6. Demostración textual — Caso A (radicación tardía)

**Solicitud:** ¿Por qué aumentó mi cartera? Analiza si la radicación está afectando el recaudo.

**Suficiencia de datos:** PARCIAL (cartera/radicación/glosas presentes; pagos parciales).

**Hipótesis principal:** H2 — Radicación tardía (**CONFIRMADA**, confianza ALTA)

- Evidencia a favor: demora promedio 36,6 días; 3 facturas sin radicar.
- Evidencia en contra: (ninguna significativa en este dataset).

**Hallazgos (HECHO):**

1. 3 facturas sin radicar  
2. Demora promedio factura→radicación: 36,6 días  
3. Alta concentración en un pagador: 100%

**Contraste de especialistas:** especialista de radicación APOYA; otro CUESTIONA/COMPLEMENTA; consolidador sintetiza.

**Priorización (top 3):**

1. Control diario de pendientes de radicación con alertas automáticas  
2. Auditoría de cuellos de botella facturación→radicación  
3. Outsourcing parcial de radicación para picos  

**Escenario PROBABLE:** valor recuperable estimado ~$36.360.000 (PROYECTADO — no real).

**Recomendación consolidada:** implementar control diario de radicación; medir días factura→radicación (<7).

---

## 7. Seguridad (tenant)

`test_tenant_isolation_motor`: organización B no puede leer diagnóstico de organización A (404).

---

## 8. Migraciones

- Head Alembic: `972a1b2c3d4e` (sin cambios)
- MIGRATIONS-CONTROL-001: sin modificación de historia certificada

---

## 9. Regresión ejecutada

| Control | Resultado |
|---------|-----------|
| Suite completa pytest | **437 passed**, 2 skipped |
| Tests MOTOR-1000 | **14 passed** |
| `npm run build` | PASS |
| `npm audit` (high) | 0 vulnerabilidades |
| `git diff --check` | PASS |
| `alembic heads` | `972a1b2c3d4e` |

---

## 10. Limitaciones reales

1. Embeddings para casos similares: arquitectura preparada vía `salud_experience`; V1 usa filtros estructurados/keywords.
2. FINOPS valor: registro opcional; si falla no bloquea el análisis.
3. Devoluciones: fuente opcional `devoluciones` + detección vía glosas `DEVUELTA`.
4. El coordinador global no invoca automáticamente `run_ips_analysis` — la ruta certificada es API SALUD / UI Diagnóstico IPS.
5. Caso E clasifica INSUFICIENTE cuando faltan ≥3 dimensiones críticas para la pregunta de cartera.

---

## 11. Archivos principales tocados

```
backend/app/services/motor_analitico/     (nuevo paquete)
backend/app/fixtures/motor_analitico_datasets.py
backend/app/services/salud_engine.py
backend/app/services/salud_indicators.py   (+ devoluciones)
backend/app/services/salud_normalization.py (+ devoluciones)
backend/app/services/salud_questions.py
backend/app/routers/salud.py
frontend/src/pages/DiagnosticoIpsPage.tsx
tests/test_motor_analitico_1000.py
pytest.ini
```

---

**MOTOR-ANALITICO-1000 — LISTO PARA REAUDITORÍA**  
**NO MERGE** (pendiente aprobación humana)
