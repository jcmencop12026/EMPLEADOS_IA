# EMPLEADOS_IA — CORRECCIÓN DEUDA PREEXISTENTE 1220 test_08

**Tipo:** Fix aislado — sin tocar rama central Fase 1  
**Fecha:** 2026-08-29  
**Agente:** GENERAL  
**Base:** `041209f4acabd595b5249c979a7e61031f598048`  
**Rama:** `cursor/fix-deuda-1220-test08`

---

## 0. Reproducción inicial (antes del fix)

**Comando:**

```bash
python3 -m pytest tests/test_diagnostico_transversal_1220.py::test_08_opportunity_and_deduplication -v --tb=long
```

**Error exacto:**

```
tests/test_diagnostico_transversal_1220.py:236: in test_08_opportunity_and_deduplication
    assert opps_first  # al menos una oportunidad
E   assert set()
```

| Campo | Valor |
|-------|-------|
| **Assertion** | `assert opps_first` |
| **Esperado** | Conjunto no vacío de `opportunity_id` en primera generación |
| **Recibido** | `set()` |
| **Fixture** | `client` (session-scoped), `token` (admin bootstrap) |
| **Datos** | `_setup_signals(client, token)` — una señal financiera `_financiero_signal()` |
| **Traceback** | Línea 236 — `opps_first` vacío tras `POST /api/diagnosticos/generar` 201 |

**Archivo completo (15 tests):** PASS — dependía de señales acumuladas de tests 03–07 en BD session-scoped.

---

## 1. Qué valida test_08

`test_08_opportunity_and_deduplication` protege la capacidad **1220** de:

1. **Vincular oportunidades** al generar un diagnóstico transversal desde señales con impacto.
2. **Consultar detalle** del diagnóstico con oportunidades asociadas.
3. **Regenerar** diagnóstico sin error (segunda llamada a `generar`).

Contrato API: respuesta de `generar` incluye `oportunidades[]` con `opportunity_id` cuando hallazgos HECHO son accionables (severidad ALTA/MEDIA, no riesgo).

---

## 2. Investigación

### 2.1 Dependencia entre tests

| Ejecución | Resultado |
|-----------|-----------|
| `test_08` aislado | **FAIL** |
| Archivo completo 01→15 | **PASS** |
| `test_08` tras tests 03–07 | PASS por contaminación: `generate_diagnostic` consolida **todas** las señales del periodo (30 días) de la org admin |

Tests 03–07 ingieren señales de correlación (`correlation=True`) que producen hallazgos ALTA → oportunidades. test_08 solo añade una señal financiera pero hereda el resto.

### 2.2 Causa en código 1220

En `_create_finding_from_signal` (`diagnostic_service.py`):

- `impacto_estimado` en payload activa `breach=True` → se crea hallazgo HECHO.
- Sin indicador/umbral, `_severity_from_magnitude(valor, None)` usa `ref = abs(valor)` → ratio = 1.0 → **severidad BAJA**.
- Creación de oportunidad exige `severidad in ("ALTA", "MEDIA")` → **ninguna oportunidad** con una sola señal financiera aislada.

Inconsistencia: hallazgo accionable por impacto pero severidad BAJA bloquea oportunidad.

### 2.3 Multiempresa

Sin fuga. El fix de test usa tenant dedicado (`_create_tenant_user`) como test_10.

### 2.4 Causalidad 1220

No se modificó `es_causal=False`, `nota_causalidad`, ni inferencia de causas.

---

## 3. Clasificación de causa

| Campo | Valor |
|-------|-------|
| **CAUSA** | **CÓDIGO** + **FIXTURE** |
| **EVIDENCIA** | (1) Severidad BAJA con breach por impacto bloquea oportunidades en producción. (2) test_08 reutilizaba `token` admin y BD session-scoped contaminada por tests previos — falso PASS en suite completa. |

---

## 4. Corrección aplicada

### 4.1 Código — commit `8f09f6d`

`backend/app/services/diagnostic_service.py` — en `_create_finding_from_signal`:

Si `severidad == "BAJA"` y no hay umbral configurado, elevar a MEDIA/ALTA según `signal.severidad` o `impacto_estimado` que activó el breach.

### 4.2 Test — commit `e28650f`

`tests/test_diagnostico_transversal_1220.py` — test_08:

- Tenant dedicado vía `_create_tenant_user` (sin fixture `token` compartido).
- Elimina dependencia de orden de ejecución / contaminación de sesión.

---

## 5. Pruebas ejecutadas

| Prueba | Resultado |
|--------|-----------|
| test_08 aislado × 5 consecutivas | **5/5 PASS** |
| Archivo `test_diagnostico_transversal_1220.py` | **15 passed** |
| Focales núcleo (1120, 1220, 1030, 1100, 1200, 1210, 1230, 1250c) | **100 passed** |
| RBAC + multitenant + admin | **55 passed** |
| Regresión completa `tests/` | **877 passed, 4 skipped, 0 failed** |
| Alembic heads | **1** — `1380a1b2c3d4e` |
| Frontend | **NO MODIFICADO** |
| PostgreSQL | **NO APLICA** (causa no depende de motor SQL) |

---

## 6. Commits

| Tipo | SHA | Mensaje |
|------|-----|---------|
| FIX-1220-TEST08 (código) | `8f09f6d` | fix(1220): alinear severidad de hallazgo con impacto de señal sin umbral |
| TEST | `e28650f` | test(1220): aislar test_08 en tenant propio sin depender de sesión compartida |
| DOC | *(este commit)* | docs: entregable fix deuda 1220 test_08 |

---

## SALIDA FINAL

```
EMPLEADOS IA — DEUDA 1220 TEST08 TERMINADA

BASE:
041209f4acabd595b5249c979a7e61031f598048

RAMA:
cursor/fix-deuda-1220-test08

HEAD:
<e28650f + doc>

COMMIT FUNCIONAL:
8f09f6d

COMMIT TEST:
e28650f

CAUSA:
CÓDIGO + FIXTURE

TEST08 ANTES:
FAIL

TEST08 DESPUÉS:
PASS

TEST08 5 EJECUCIONES:
5/5 PASS

ARCHIVO 1220:
15 passed

FOCALES 1220:
15 passed (archivo completo)

NÚCLEO INTELIGENCIA:
100 passed

MULTIEMPRESA:
PASS

RBAC:
PASS

SUPERADMIN:
PASS

ALEMBIC HEADS:
1

ALEMBIC HEAD:
1380a1b2c3d4e

POSTGRESQL:
NO APLICA

REGRESIÓN:
877 passed, 4 skipped, 0 failed

REGRESIONES INTRODUCIDAS:
0

FRONTEND:
NO MODIFICADO

P0:
0

P1:
0

P2:
0

DEUDA 1220:
CERRADA

RAMA CENTRAL MODIFICADA:
NO

MAIN:
NO MODIFICADO

V1:
NO MODIFICADA

MERGE:
NO

VEREDICTO:
APTO PARA PORTAR A CONVERGENCIA
```

---

*Rama `cursor/convergencia-final-post-v1-integracion` no modificada.*
