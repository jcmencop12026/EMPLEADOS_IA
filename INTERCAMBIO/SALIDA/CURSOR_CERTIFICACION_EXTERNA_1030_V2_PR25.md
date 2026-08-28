# CURSOR — CERTIFICACIÓN EXTERNA 1030 V2 — PR #25

**Fecha UTC:** 2026-08-28
**Proyecto:** EMPLEADOS_IA
**PR:** #25 — `cursor/preintegracion-1020-1030`
**NO MERGE**

---

## VEREDICTO DEFINITIVO

### **OPORTUNIDADES-PROACTIVAS-1030 V2 — CERTIFICACIÓN EXTERNA FAIL**

### **INTEGRACIÓN-1020-1030 / PR #25 — NO APTO PARA MERGE**

---

## 1. SHA-256 del paquete

| Campo | Valor |
|-------|-------|
| Archivo | `INTERCAMBIO/ENTRADA/OPORTUNIDADES_PROACTIVAS_1030_CERTIFICACION_V2.zip` |
| Recuperado desde | `origin/transporte-certificacion-1030-v2` (commit `ccc914e`, sin merge) |
| SHA-256 | `1cc1a197b40ba914067f0b4c9a078b96def370d0b413ff03de89a55ad4954be0` |
| Verificación | **COINCIDE** |

---

## 2. SHA Git certificado

| Referencia | SHA |
|------------|-----|
| HEAD certificado | `c8a67b3` |
| Funcional equivalente | `2e86ae3` (sin cambios de producto vs `c8a67b3`) |
| `origin/main` | `f9e0406` |

---

## 3. Cegamiento

| Regla | Cumplimiento |
|-------|--------------|
| Fase ciega antes de oráculo | **SÍ** — 12 brutos congelados |
| `ORACULO_SELLADO/` no consultado durante ejecución | **SÍ** |
| Código no modificado durante fase ciega | **SÍ** |
| Brutos no alterados post-congelación | **SÍ** |

---

## 4. Resultados por caso (12)

| Caso | Resultado | Observación clave |
|------|-----------|-------------------|
| V2-OP-A | **FAIL** | Sin WorkPlan; aprobación automática vs requerida |
| V2-OP-B | **FAIL** | Señal inmadura → oportunidad ACTUAR+AHORA (R02) |
| V2-OP-C | **PASS** | Momento PROGRAMAR correcto |
| V2-OP-D | **PASS** | D1 priorizado globalmente |
| V2-OP-E | **PASS** | OBSERVAR, sin valor inventado |
| V2-OP-F | **FAIL** | Conflicto conservado pero momento AHORA vs OBSERVAR |
| V2-NS-1 | **PASS** | Transversal logística, sin SALUD |
| V2-NS-2 | **PASS** | Manufactura, sin FINOPS |
| V2-PX-1 | **PASS** | Idempotencia 1 señal / 1 oportunidad |
| V2-PX-2 | **PASS** | Cross-tenant fail-closed |
| V2-PX-3 | **PASS** | Potencial ≠ materializado |
| V2-PX-4 | **PASS** | Cadena completa + aprendizaje |

**9 PASS / 3 FAIL**

---

## 5. Matriz R01–R12 (bloqueantes)

| Control | Resultado | Casos |
|---------|-----------|-------|
| R01 Proactividad real | **PASS** | V2-PX-1 |
| R02 Señal ≠ oportunidad | **FAIL** | V2-OP-B |
| R03 Priorización global | **PASS** | V2-OP-D |
| R04 Momento | **FAIL** | V2-OP-F |
| R05 Datos insuficientes | **PASS** | V2-OP-E, V2-NS-2 |
| R06 Contradicción | **FAIL** | V2-OP-F (momento) |
| R07 Transversalidad | **PASS** | V2-NS-1, V2-NS-2 |
| R08 Idempotencia | **PASS** | V2-PX-1 |
| R09 Valor materializado | **PASS** | V2-PX-3 |
| R10 Cross-tenant | **PASS** | V2-PX-2 |
| R11 Siguiente mejor acción | **FAIL** | V2-OP-A |
| R12 Trazabilidad | **PASS** | V2-PX-4 |

**8 PASS / 4 FAIL**

---

## 6. Defectos bloqueantes concretos

### V2-OP-B (R02)
- **Requisito:** señal inmadura con evidencia insuficiente no debe convertirse en oportunidad ACTUAR+AHORA.
- **Observado:** oportunidad creada con `pertinencia=ACTUAR`, `momento=AHORA`.
- **Componente:** `evaluate_pertinence` / `build_context_360` — no discrimina evidencia insuficiente del paquete V2.

### V2-OP-A (R11)
- **Requisito:** WorkPlan + aprobación humana para oportunidad urgente con capacidad.
- **Observado:** `estado=PRIORIZADA`, `work_plan_id=null`, `autorizacion=AUTOMATICA_BAJO_POLITICA`.
- **Componente:** `run_proactive_pipeline` — no activa ni exige aprobación según política del caso.

### V2-OP-F (R04/R06)
- **Requisito:** con contradicción, momento OBSERVAR (no AHORA).
- **Observado:** `pertinencia=SOLICITAR_APROBACION` (correcto), `conflicto=true` (correcto), pero `momento=AHORA`.
- **Componente:** `evaluate_momento` — no considera conflicto para posponer.

---

## 7. Controles especiales PX

| Control | Resultado |
|---------|-----------|
| PX-1 Idempotencia | **PASS** |
| PX-2 Cross-tenant | **PASS** |
| PX-3 Valor potencial/materializado | **PASS** |
| PX-4 Trazabilidad/aprendizaje | **PASS** |

---

## 8. Hashes brutos

Ver `CERTIFICACION_EXTERNA_1030_V2/02_BRUTOS_ANTES_ORACULO/CONGELADO_SHA256.csv` (12 archivos, HEAD `c8a67b3`).

---

## 9–11. Regresión / PostgreSQL / Migraciones

**NO reejecutados** — certificación externa V2 FAIL (requisito: PASS externo primero).

Referencias previas @ `2e86ae3`: focal 93 PASS, regresión 515 PASS, PostgreSQL 2 PASS, head `1030a1b2c3d4e`.

---

## 12. CI GitHub

CI previo @ `c8a67b3`: **4/4 PASS** ([run 33127535714](https://github.com/jcmencop12026/EMPLEADOS_IA/actions/runs/33127535714)).

CI verde **no sustituye** certificación externa V2 FAIL.

---

## 13. Corrección recomendada (iteración independiente)

1. **R02:** En `evaluate_pertinence` / pipeline, detectar `evidencia_insuficiente` o contexto parcial del payload V2 → `OBSERVAR` o no crear oportunidad.
2. **R11:** Para oportunidades urgentes con política de aprobación, transicionar a `PENDIENTE_APROBACION` y crear WorkPlan tras aprobación.
3. **R04/R06:** En `evaluate_momento`, si `contexto.conflicto=true` → `OBSERVAR` o `PROGRAMAR`, no `AHORA`.

**No se modificó código en esta corrida** (regla ante FAIL).

---

## 14. PR #24

Sustituido funcionalmente por PR #25. **NO cerrado.**

---

## 15. Evidencias

```
INTERCAMBIO/SALIDA/CERTIFICACION_EXTERNA_1030_V2/
  00_CONTROL/FASE_CIEGA_CERRADA.md
  00_CONTROL/VERIFICACION_PAQUETE.md
  02_BRUTOS_ANTES_ORACULO/ (12 casos + CONGELADO_SHA256.csv)
  04_COMPARACION_ORACULO/RESULTADOS_CASOS.json
  04_COMPARACION_ORACULO/RESULTADOS_R01_R12.csv
  run_blind_v2.py
  run_compare_oraculo_v2.py
```

Evidencias históricas conservadas: `reauditoria_externa_1030/`, `RECUPERACION_CERTIFICACION_1030/`.

---

*Certificación externa adversarial V2 completada — FAIL bloqueante*
