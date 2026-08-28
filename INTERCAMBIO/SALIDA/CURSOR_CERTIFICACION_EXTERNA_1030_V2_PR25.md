# CURSOR — CERTIFICACIÓN EXTERNA 1030 V2 — PR #25

**Fecha UTC:** 2026-08-28
**Proyecto:** EMPLEADOS_IA
**PR:** #25 — `cursor/preintegracion-1020-1030`
**NO MERGE**

---

## VEREDICTO DEFINITIVO (ACTUALIZADO TRAS CORRECCIÓN)

### **OPORTUNIDADES-PROACTIVAS-1030 V2 — CERTIFICACIÓN EXTERNA PASS**

### **INTEGRACIÓN-1020-1030 / PR #25 — APTO PARA MERGE**

---

## Historial de corridas

| Corrida | HEAD | Resultado | Evidencias |
|---------|------|-----------|------------|
| R1 (pre-corrección) | `c4803e5` | **FAIL** 9/12 | `CERTIFICACION_EXTERNA_1030_V2/` |
| R2 (post-corrección) | `3af0be5` | **PASS** 12/12 | `CERTIFICACION_EXTERNA_1030_V2_R2/` |

---

## R2 — Certificación adversarial PASS

### Paquete

| Campo | Valor |
|-------|-------|
| Archivo | `OPORTUNIDADES_PROACTIVAS_1030_CERTIFICACION_V2.zip` |
| SHA-256 | `1cc1a197b40ba914067f0b4c9a078b96def370d0b413ff03de89a55ad4954be0` |

### Cegamiento

- Fase ciega: 12 brutos congelados
- Oráculo NO consultado antes de congelar
- HEAD certificado: `3af0be5`

### Resultados R2

- Casos: **12/12 PASS**
- R01–R12: **12/12 PASS**
- PX-1..4: **PASS**

### Validación técnica post-PASS

| Suite | Conteo |
|-------|--------|
| Focal 1030 | 43 PASS |
| Regresión | 513 PASS |
| Certificación rápida | 28 PASS |
| PostgreSQL | 2 PASS |
| Alembic head | `1030a1b2c3d4e` único |

---

## R1 — FAIL documentado (conservado)

Casos FAIL originales: V2-OP-A, V2-OP-B, V2-OP-F
Corregidos en `3af0be5` — ver `CURSOR_CIERRE_CORRECCION_1030_PR25.md`

---

## Entregables

- `INTERCAMBIO/SALIDA/CERTIFICACION_EXTERNA_1030_V2/` — R1 FAIL (histórico)
- `INTERCAMBIO/SALIDA/CERTIFICACION_EXTERNA_1030_V2_R2/` — R2 PASS
- `INTERCAMBIO/SALIDA/CURSOR_CIERRE_CORRECCION_1030_PR25.md`

---

*Certificación externa V2 R2 PASS — PR #25 APTO PARA MERGE (sin merge automático)*
