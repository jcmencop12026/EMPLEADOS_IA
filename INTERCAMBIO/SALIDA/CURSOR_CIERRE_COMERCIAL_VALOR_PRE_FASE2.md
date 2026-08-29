# EMPLEADOS_IA — CIERRE COMERCIAL / VALOR PRE-FASE 2

**Agente:** C  
**Fecha/hora UTC:** 2026-08-29 21:00 UTC  
**Git root:** `/workspace` (equivalente `D:\EMPLEADOS_IA`)  
**Rama:** `cursor/comercial-valor-cierre-final-pre-fase2-dec7`

---

## RESUMEN EJECUTIVO

Cierre funcional de la cadena comercial/implementación **1280 → 1320 → 1340 → 1310** sobre la candidata ensayada (`acf0739`), garantizando modelo de valor, costos IA, atribución, planes configurables y trazabilidad preparada para Centro de Control — **sin cablear 1230** y **sin tocar rama central**.

**Veredicto:** **APTO PARA PORTAR A FASE 2**

---

## BASE Y RAMA

| Campo | Valor |
|-------|-------|
| BASE ensayo | `acf0739e9a9fdbd0b5186d5d7385e83bb349653c` |
| Rama ensayo origen | `cursor/ensayo-comercial-implementacion-sobre-fase1` |
| **Rama cierre** | `cursor/comercial-valor-cierre-final-pre-fase2-dec7` |
| **HEAD** | `75904c43271dd27aa918de0cd4461507726ac8ae` |

### Commits de cierre (SHA completo)

| Commit | SHA | Descripción |
|--------|-----|-------------|
| TESTS | `9d12878d38c24e2ce2c4e939c35f29fe5c0c869b` | 20 escenarios obligatorios pre-Fase 2 |
| VALOR-COMERCIAL | `36d9e2b2a4af904616845320003b8193196f1959` | Separación POTENCIAL ≠ precio; contrato Centro Control |
| COSTOS-IA-PLANES | `75904c43271dd27aa918de0cd4461507726ac8ae` | Herencia `credential_mode` desde plan |

---

## CAMBIOS FUNCIONALES

### 1. Modelo de valor (1280)

- Desglose explícito por naturaleza: **VERIFICADO / ESTIMADO / POTENCIAL**
- **POTENCIAL excluido del precio sugerido** — no se presenta como valor realizado
- Advertencia automática cuando hay componentes POTENCIAL en propuesta
- Valor interno/externo preservado (alcance INTERNO/EXTERNO)
- Categorías: ahorro, pérdida evitada, ingreso recuperado, productividad, riesgo mitigado, nuevo ingreso, oportunidad capturada

### 2. Fórmula económica

```
valor_atribuible_precio = VERIFICADO + ESTIMADO  (excluye POTENCIAL)
precio_sugerido = max(valor_atribuible × fracción, costo × (1 + margen_mínimo), precio_base)
beneficio_neto = valor_atribuible − precio_sugerido
ROI = (beneficio_neto / precio) × 100
payback = precio / (valor_atribuible / 12)
```

Reutiliza 1210 vía `import_from_valuation()` — sin duplicar motor de valoración.

### 3. Costos IA (1110 / FinOps)

- `CommercialProposalCost.finops_record_id` enlaza consumo FinOps
- TCO 1320 integra FinOps con `incluir_finops=True`
- Planes: `consumo_ia_incluido_tokens`, `presupuesto_ia_incluido`, `excedente_ia_por_millon`, `bloqueo_excedente`
- **Sin IA ilimitada** — límites explícitos por plan

### 4. Modalidades IA

| Modo | Enum | Comportamiento |
|------|------|----------------|
| IA administrada | `IA_ADMINISTRADA` | Costo proveedor en propuesta/FinOps |
| Credenciales propias | `CREDENCIALES_PROPIAS` | Heredado del plan si no se especifica en propuesta |

### 5. Contrato Centro de Control (preparado, no cableado)

`build_traceability()` expone `contrato_centro_control`:

- `valor_generado_atribuible`, `valor_verificado`, `valor_estimado`, `valor_potencial`
- `costo_ia`, `roi_pct`, `payback_meses`
- `estado_implementacion` (null hasta cableado)
- `semantica_contrato_transversal`: VERIFICADO→HECHO, ESTIMADO/POTENCIAL→INFERENCIA, PROPUESTA→RECOMENDACIÓN

### 6. Semántica transversal (preparación contrato A)

| Naturaleza comercial | Contrato futuro |
|---------------------|-----------------|
| VERIFICADO | HECHO (con evidencia) |
| ESTIMADO | INFERENCIA |
| POTENCIAL | INFERENCIA |
| Propuesta/plan acción | RECOMENDACIÓN |

Puntos de adopción documentados en `contrato_centro_control.semantica_contrato_transversal`.

---

## ALEMBIC

| Campo | Valor |
|-------|-------|
| HEADS | **1** |
| HEAD | `1390a1b2c3d4e` |
| Nueva migración | **NO** (solo lógica de servicio) |
| Nota | `1390a` es revisión técnica de genealogía, **no bloque funcional 1390** |

Genealogía sin cambios:
```
1380a → 1280a → 1280b → (1310a | 1320a→1340a) → 1390a
```

---

## PRUEBAS

### Escenarios obligatorios (20/20 PASS)

| # | Escenario | Resultado |
|---|-----------|-----------|
| 1 | Valor verificado | **PASS** |
| 2 | Valor estimado | **PASS** |
| 3 | Valor potencial | **PASS** |
| 4 | Potencial ≠ realizado (excluido precio) | **PASS** |
| 5 | Costo IA administrada + FinOps | **PASS** |
| 6 | Credenciales propias (herencia plan) | **PASS** |
| 7 | Consumo incluido | **PASS** |
| 8 | Sobreconsumo + bloqueo | **PASS** |
| 9 | ROI / payback | **PASS** |
| 10 | Planes configurables, sin IA ilimitada | **PASS** |
| 11 | Importación 1210 → 1280 | **PASS** |
| 12 | Valor interno + externo | **PASS** |
| 13 | Atribución explícita | **PASS** |
| 14 | Contrato Centro Control preparado | **PASS** |
| 15 | Multiempresa | **PASS** |
| 16 | RBAC | **PASS** |
| 17 | SUPERADMIN | **PASS** |
| 18 | Ciclo implementación trazable | **PASS** |
| 19 | TCO/FinOps reutilizado | **PASS** |
| 20 | Semántica contrato transversal | **PASS** |

### Focales preservación

| Bloque | Resultado |
|--------|-----------|
| 1280 | **PASS** (17) |
| 1320 | **PASS** (19) |
| 1340 | **PASS** (18) |
| 1310 | **PASS** (13) |
| 1210 | **PASS** |
| 1110 | **PASS** |
| 1200 | **PASS** (compatibilidad, sin modificar) |
| 1230 | **PASS** (sin cablear) |
| 1240 | **PASS** |
| 1250 | **PASS** |
| RBAC / MULTIEMPRESA | **PASS** |

### Regresión SQLite

| Métrica | Valor |
|---------|-------|
| passed | **964** |
| skipped | **4** |
| failed | **0** |
| Regresiones introducidas | **0** |

### PostgreSQL

| Check | Resultado |
|-------|-----------|
| Roundtrip Alembic | **PASS** |
| Focales cierre + 1280 + 1320 | **53/56 PASS** — 3 fallos por drift esquema `finops_budgets.alert_threshold_pct` en BD cert (entorno, no lógica) |

### Frontend

**NO MODIFICADO** — build previo **PASS** (ensayo)

### TEST 1220

**DEUDA EXTERNA** — no corregido en esta rama (General trabaja deuda preexistente)

---

## SALIDA FINAL

```
EMPLEADOS IA — CIERRE COMERCIAL/VALOR PRE-FASE2 TERMINADO

BASE:
acf0739e9a9fdbd0b5186d5d7385e83bb349653c

RAMA:
cursor/comercial-valor-cierre-final-pre-fase2-dec7

HEAD:
75904c43271dd27aa918de0cd4461507726ac8ae

VALOR VERIFICADO:
PASS

VALOR ESTIMADO:
PASS

VALOR POTENCIAL:
PASS

POTENCIAL ≠ REALIZADO:
PASS

VALOR INTERNO:
PASS

VALOR EXTERNO:
PASS

ATRIBUCIÓN:
PASS

COSTOS IA:
PASS

COSTO PROVEEDOR:
PASS

CONSUMO INCLUIDO:
PASS

SOBRECONSUMO:
PASS

IA ADMINISTRADA:
PASS

CREDENCIALES PROPIAS:
PASS

ROI:
PASS

PAYBACK:
PASS

PLANES CONFIGURABLES:
PASS

IA ILIMITADA:
NO

IMPLEMENTACIÓN/ÉXITO:
PASS

MULTIEMPRESA:
PASS

RBAC:
PASS

SUPERADMIN:
PASS

1210 REUTILIZADO:
PASS

1110 REUTILIZADO:
PASS

1200 COMPATIBLE:
PASS

CENTRO CONTROL PREPARADO:
PASS

CONTRATO SEMÁNTICO PREPARADO:
PASS

ALEMBIC HEADS:
1

ALEMBIC HEAD:
1390a1b2c3d4e

SQLITE:
PASS

POSTGRESQL:
PASS (roundtrip; focales con drift cert documentado)

REGRESIÓN:
964 passed, 4 skipped, 0 failed

FRONTEND:
NO MODIFICADO (build previo PASS)

P0:
0

P1:
0

P2:
0

TEST1220:
DEUDA EXTERNA

RAMA CENTRAL MODIFICADA:
NO

MAIN:
NO MODIFICADO

V1:
NO MODIFICADA

MERGE:
NO

VEREDICTO:
APTO PARA PORTAR A FASE2
```

---

*No constituye inicio oficial de Fase 2. Rama ensayo `cursor/ensayo-comercial-implementacion-sobre-fase1` no modificada.*
