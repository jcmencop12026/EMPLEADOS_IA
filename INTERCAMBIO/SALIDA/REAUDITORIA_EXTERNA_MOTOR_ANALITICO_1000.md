# REAUDITORÍA EXTERNA — MOTOR-ANALITICO-1000

**PR:** [#21](https://github.com/jcmencop12026/EMPLEADOS_IA/pull/21)
**Rama auditada:** `cursor/motor-analitico-1000`
**HEAD:** `482a754c6d6a7a02c57831646d65735bdb0de774`
**Fecha:** 2026-08-26
**Auditor:** Cloud Agent (reauditoría externa independiente)
**Veredicto:** **MOTOR-ANALITICO-1000 — NO APTO PARA MERGE**

---

## 1. Metodología

1. Verificación de HEAD y ausencia de cambios al motor durante la auditoría (solo documentación/harness).
2. Búsqueda del paquete externo `MOTOR_ANALITICO_1000_DATASET_CERTIFICACION.zip` en `INTERCAMBIO/ENTRADA/` (ubicación acordada).
3. Preparación de runner ciego: `INTERCAMBIO/SALIDA/reauditoria_externa_motor_1000/run_blind_certification.py`.
4. **No** se usaron los fixtures internos `motor_analitico_datasets.py` como prueba principal de certificación.
5. Análisis estático del código frente a criterios decisivos A–E.
6. Análisis secundario de riesgo (solo gap analysis, no certificación) sobre Caso E con datos mínimos.
7. Regresión técnica Fase 7.
8. Revisión CI PR #21.

---

## 2. BLOQUEANTE — Paquete de certificación externo ausente

| Control | Estado |
|---------|--------|
| `INTERCAMBIO/ENTRADA/MOTOR_ANALITICO_1000_DATASET_CERTIFICACION.zip` | **NO ENCONTRADO** |
| `README_MAESTRO.md` | **NO ENCONTRADO** |
| `MATRIZ_EVALUACION.csv` | **NO ENCONTRADO** |
| `ANTI_RESPUESTA_PREFABRICADA.json` | **NO ENCONTRADO** |
| `CASOS/CASO_A` … `CASO_E` | **NO ENCONTRADO** |

Evidencia:

```
Paquete no encontrado. Coloque MOTOR_ANALITICO_1000_DATASET_CERTIFICACION.zip
en /workspace/INTERCAMBIO/ENTRADA o descomprima allí.
```

Archivo generado: `INTERCAMBIO/SALIDA/reauditoria_externa_motor_1000/PAQUETE_NO_DISPONIBLE.txt`

**Impacto:** Las Fases 1 (ejecución ciega), 2 (comparación oráculo), 4 (anti-prefab externo), 5 (trazabilidad con datos reales) y 6 (seguridad adversarial con tenants del paquete) **no pudieron ejecutarse**.

**Acción requerida:** Colocar el ZIP en `INTERCAMBIO/ENTRADA/` y re-ejecutar:

```bash
PYTHONPATH=backend python3 INTERCAMBIO/SALIDA/reauditoria_externa_motor_1000/run_blind_certification.py
```

Los resultados brutos se guardarán en `INTERCAMBIO/SALIDA/reauditoria_externa_motor_1000/brutos/CASO_*_antes_oraculo.json` **antes** de leer `resultado_esperado.json`.

---

## 3. Fase 1 — Ejecución ciega (A–E)

| Caso | Estado | Resultado bruto pre-oráculo |
|------|--------|----------------------------|
| CASO_A | **NO EJECUTADO** | Paquete ausente |
| CASO_B | **NO EJECUTADO** | Paquete ausente |
| CASO_C | **NO EJECUTADO** | Paquete ausente |
| CASO_D | **NO EJECUTADO** | Paquete ausente |
| CASO_E | **NO EJECUTADO** | Paquete ausente |

No se consultó ningún `resultado_esperado.json` (no existen en el entorno).

---

## 4. Fase 2 — Comparación contra oráculo

**NO APLICABLE** — sin ejecución ciega ni oráculos presentes.

---

## 5. Fase 3 — Pruebas decisivas (análisis estático + gap analysis)

Evaluación basada en revisión de código (`motor_analitico/`, `salud_engine.py`, `salud_knowledge.py`). **No sustituye** la certificación con el paquete externo.

### CASO A — Radicación tardía predominante

| Criterio | Evaluación estática | Riesgo |
|----------|---------------------|--------|
| H2 radicación como causa principal | **PROBABLE PASS** — `hypothesis_engine` puntúa demora >10 días y facturas sin radicar | MEDIO |
| Evidencia temporal | **PASS** — indicadores `tiempo_promedio_factura_radicacion_dias` | BAJO |
| Evidencia contractual | **PARCIAL** — conocimiento consultado vía `salud_knowledge`; motor no integra plazos contractuales en hipótesis directamente | MEDIO |
| No convertir glosas en problema principal | **PROBABLE PASS** — H4 penalizada si `% glosa` bajo | MEDIO |

### CASO B — Glosas/devoluciones/soportes

| Criterio | Evaluación | Riesgo |
|----------|------------|--------|
| Diferenciación material vs A | **PROBABLE PASS** — scoring distinto por indicadores | MEDIO |
| H3/H4/H5 predominantes | **PROBABLE PASS** si devoluciones/glosas altas en datos externos | MEDIO |
| Radicación no principal | **PROBABLE PASS** si `tiempo_rad <= 5` | MEDIO |

### CASO C — Pagador tardío (prueba crítica)

| Criterio | Evaluación | Riesgo |
|----------|------------|--------|
| Reconocer radicación oportuna | **PASS** — H2 penalizada con radicación ≤5 días | BAJO |
| Glosas mínimas | **PASS** — H4 penalizada si `% glosa < 4` | BAJO |
| H7 comportamiento pagador | **PROBABLE PASS** — lógica `rad_ok + glo_bajo + recaudo_bajo` | MEDIO |
| Acción hacia pagador/contratación/cobro | **PARCIAL** — alternativas de cartera incluyen mesa con pagador si H7 domina; no hay acción contractual explícita dedicada | **ALTO** |
| No culpar artificialmente a IPS | **PARCIAL** — H9 puede activarse si hay hallazgos internos | MEDIO |

### CASO D — Multicausal + contradicción documental 10 vs 15 días

| Criterio | Evaluación | Riesgo |
|----------|------------|--------|
| H10 combinación | **PARCIAL** — requiere ≥2 hipótesis fuertes simultáneas; puede perder ante H2 o H4 individual | **ALTO** |
| Detección contradicción 10/15 días | **PARCIAL** — `salud_knowledge.analyze_fragments` detecta conflicto y marca `requiere_validacion`; genera hallazgo de conflicto | MEDIO |
| Motor reduce confianza por conflicto | **FAIL POTENCIAL** — `knowledge_ctx` se guarda en traza pero **no** alimenta `hypothesis_engine` ni baja confianza de hipótesis | **BLOQUEANTE (diseño)** |
| No escoger silenciosamente un plazo | **PARCIAL** — conocimiento marca conflicto; motor puede aún recomendar acción con confianza MEDIA/ALTA en hipótesis operativas | **ALTO** |

### CASO E — No alucinación

| Criterio | Evaluación | Riesgo |
|----------|------------|--------|
| Clasificación INSUFICIENTE | **PASS** (gap analysis secundario) | BAJO |
| Hipótesis H0 sin causa confirmada | **PASS** | BAJO |
| Información faltante concreta | **PASS** — lista cartera/radicación/glosas/pagos | BAJO |
| Sin hallazgos inventados | **PASS** — 0 hallazgos con 2 registros mínimos | BAJO |
| Sin FINOPS sin base | **PASS** — 0 valores FINOPS | BAJO |
| Recomendación no causal | **PASS** — "Información insuficiente" | BAJO |

**Nota:** Gap analysis secundario usó estructura mínima equivalente a Caso E; **no** sustituye certificación con paquete externo.

---

## 6. Fase 4 — Anti-prefabricado

| Control | Estado |
|---------|--------|
| Comparación A/B/C/D/E con paquete externo | **NO EJECUTADO** |
| Test interno `test_anti_prefabricated_response` | **PASS** (14/14 tests motor) — usa fixtures internos, **no válido como certificación primaria** |

Matriz requerida — **incompleta por paquete ausente:**

| CASO | PROBLEMA APARENTE | SUFICIENCIA | ESPECIALISTA LÍDER | HALLAZGO PRINCIPAL | HIPÓTESIS PRINCIPAL | CONFIANZA | ACCIÓN #1 | VALOR CUANTIFICADO | INFORMACIÓN FALTANTE |
|------|-------------------|-------------|--------------------|--------------------|---------------------|-----------|-----------|-------------------|---------------------|
| A | — | NO EJEC. | NO EJEC. | NO EJEC. | NO EJEC. | NO EJEC. | NO EJEC. | NO EJEC. | NO EJEC. |
| B | — | NO EJEC. | NO EJEC. | NO EJEC. | NO EJEC. | NO EJEC. | NO EJEC. | NO EJEC. | NO EJEC. |
| C | — | NO EJEC. | NO EJEC. | NO EJEC. | NO EJEC. | NO EJEC. | NO EJEC. | NO EJEC. | NO EJEC. |
| D | — | NO EJEC. | NO EJEC. | NO EJEC. | NO EJEC. | NO EJEC. | NO EJEC. | NO EJEC. | NO EJEC. |
| E | — | NO EJEC. | NO EJEC. | NO EJEC. | NO EJEC. | NO EJEC. | NO EJEC. | NO EJEC. | NO EJEC. |

---

## 7. Fase 5 — Trazabilidad

**NO EJECUTADA** con datos del paquete externo.

Revisión de capacidad en código:

- Hallazgos incluyen `sources`, `evidence`, `indicator_code` — trazabilidad a dataset operacional **sí**.
- Hipótesis citan evidencia a favor/en contra derivada de indicadores — **sí**.
- Recomendaciones vinculadas a hallazgos vía `generate_propuestas` — **sí**.
- Documentos: `salud_knowledge.source_reference` registra `document_id`, `chunk_id`, extracto — **sí**, si documentos cargados en Conocimiento por caso.

---

## 8. Fase 6 — Seguridad adversarial (tenant)

| Prueba | Estado |
|--------|--------|
| Caso A no lee doc de B (paquete externo) | **NO EJECUTADO** |
| `test_tenant_isolation_motor` (código existente) | **PASS** — org B recibe 404 al consultar análisis de org A |

---

## 9. Fase 7 — Regresión

| Control | Resultado local | CI PR #21 |
|---------|-----------------|-----------|
| `pytest tests/` | **436 passed**, 1 failed, 2 skipped | **FAIL** (428 passed, 1 failed) |
| Test fallido | `test_pr_diff_isolated_from_805` — falso positivo: exige marcadores "810/automation" en **cualquier** PR | Igual |
| `npm run build` | **PASS** | **PASS** |
| `npm audit` (high) | **0 vulnerabilidades** | — |
| `git diff --check` | **PASS** (tras esta entrega) | **FAIL** — trailing whitespace en `CURSOR_MOTOR_ANALITICO_1000.md` |
| `alembic heads` | `972a1b2c3d4e` | — |
| MIGRATIONS-CONTROL-001 | Sin migraciones nuevas en PR | — |

**CI run:** [33023120600](https://github.com/jcmencop12026/EMPLEADOS_IA/actions/runs/33023120600) — 2/4 FAIL (Backend, Validación Git).

---

## 10. Defectos clasificados

| ID | Severidad | Descripción |
|----|-----------|-------------|
| D-01 | **BLOQUEANTE** | Paquete `MOTOR_ANALITICO_1000_DATASET_CERTIFICACION.zip` no disponible — imposible certificar Fases 1–2, 4–6 |
| D-02 | **BLOQUEANTE** | CI Backend falla por `test_pr_diff_isolated_from_805` en PR sin cambios de Automatizaciones |
| D-03 | **BLOQUEANTE** | CI Validación Git: trailing whitespace en documentación de entrega previa |
| D-04 | **ALTO** | Motor no propaga conflictos documentales (`knowledge_ctx.conflictos`) a confianza de hipótesis — riesgo Caso D |
| D-05 | **ALTO** | Caso C: acción hacia pagador/contratación puede no ser dominante si coexisten hallazgos internos |
| D-06 | **MEDIO** | H10 multicausal puede quedar subordinada a hipótesis simple con mayor puntaje |
| D-07 | **MENOR** | Runner ciego no carga aún documentos del caso al Centro de Conocimiento (TODO en script) |

---

## 11. Correcciones aplicadas en esta reauditoría

| Cambio | Tipo | Motivo |
|--------|------|--------|
| `REAUDITORIA_EXTERNA_MOTOR_ANALITICO_1000.md` | Documentación | Entrega obligatoria |
| `run_blind_certification.py` | Harness auditoría | Ejecución ciega cuando llegue el paquete |
| Trailing whitespace en `CURSOR_MOTOR_ANALITICO_1000.md` | Doc-only | Corregir Validación Git D-03 |

**No se modificó** la lógica del motor (`motor_analitico/*`, `salud_engine.py`) en esta reauditoría.

---

## 12. Resultados brutos pre-oráculo

No generados — paquete externo ausente.

Cuando esté disponible, ubicación esperada:

```
INTERCAMBIO/SALIDA/reauditoria_externa_motor_1000/brutos/
  CASO_A_antes_oraculo.json
  CASO_B_antes_oraculo.json
  ...
```

---

## 13. Conclusión

### MOTOR-ANALITICO-1000 — NO APTO PARA MERGE

**Motivos bloqueantes:**

1. **Certificación externa incompleta** — sin paquete ChatGPT en `INTERCAMBIO/ENTRADA/`, no se puede validar semánticamente A–E contra oráculo.
2. **CI 2/4 FAIL** en PR #21 (Backend por test de diff mal contextualizado; Validación Git por whitespace).
3. **Riesgo alto en Caso D** — conflicto documental detectado en Conocimiento pero no acoplado al motor de hipótesis.

**Para alcanzar "APTO PARA MERGE — PENDIENTE DE INTEGRACIÓN" se requiere:**

1. Entregar y ejecutar `MOTOR_ANALITICO_1000_DATASET_CERTIFICACION.zip` con runner ciego.
2. Pasar los 5 casos decisivos contra oráculo.
3. Corregir D-02 (test `test_pr_diff_isolated_from_805` debe distinguir PR de motor vs PR de automatizaciones).
4. Corregir D-04 si Caso D falla en ejecución real.
5. CI 4/4 PASS.

**NO MERGE** hasta completar lo anterior.

---

*Reauditoría externa — PR #21 — HEAD 482a754*
