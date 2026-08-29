# CURSOR 1210 — Valoración económica, escenarios y retorno por oportunidad

**Fecha:** 2026-08-29  
**Rama:** `cursor/1210-valoracion-economica-roi-85e4`  
**Base:** `6234638` (bloque 1110)  
**HEAD:** `8f8e57f`  
**Estado:** **BLOQUE 1210 TERMINADO**  
**NO MERGE**

---

## Objetivo

Implementar el motor económico que convierte una oportunidad en un caso cuantificable y permite comparar:

**VALOR ESPERADO → COSTO → VALOR REAL → BENEFICIO NETO → RETORNO**

Extiende FinOps 1110 sin reconstruirlo. Compatible con integración futura del bloque 1200 (medición real / línea base).

---

## Arquitectura aplicada

```
Opportunity
     │
     ▼
OpportunityValuation (1 por oportunidad/empresa)
     ├── OpportunityValuationExpected  (valor bruto × probabilidad)
     ├── OpportunityValuationScenario  (CONSERVADOR / BASE / OPTIMISTA)
     ├── OpportunityValuationReal        (materializado + atribuible)
     ├── OpportunityExecutionCost        (IA vía FinOps + otros costos)
     └── OpportunityValuationHistory     (snapshots versionados)

FinOps 1110 ──► finops_records.opportunity_id ──► costo IA en total ejecución
Bloque 1200 ──► external_measurement_ref (contrato preparado, sin dependencia)
```

Cálculos determinísticos en `valuation_service.py` — sin IA generativa para aritmética.

---

## Alcance implementado

### Tipos de valor

AHORRO, PÉRDIDA EVITADA, INGRESO RECUPERADO, PRODUCTIVIDAD LIBERADA, NUEVO INGRESO, OPORTUNIDAD COMERCIAL, RIESGO MITIGADO, OTRO.

### Valor esperado

- Valor bruto, probabilidad, costo esperado ejecución, periodo
- `adjusted_expected = gross_value × probability`
- Supuestos, fuente, evidencia, naturaleza (MEDIDA/CALCULADA/ESTIMADA/PROPUESTA)

### Escenarios

CONSERVADOR, BASE, OPTIMISTA — valores ingresados por usuario, no autogenerados.

### Costos

- Reutiliza FinOps 1110 (`summarize_opportunity_economics`)
- Costos adicionales: HORAS HUMANAS, SERVICIOS, INFRAESTRUCTURA, LICENCIAS, OTRO

### Beneficio neto y retorno

- `beneficio_neto = valor_atribuible − costo_total_ejecución`
- `retorno % = beneficio_neto / costo_total × 100`
- Periodo de recuperación cuando hay periodo y valor atribuible
- `NO CALCULABLE` + lista de datos faltantes si insuficiente

### Atribución

VERIFICADO / ESTIMADO / POTENCIAL + NO ATRIBUIBLE / PARCIALMENTE ATRIBUIBLE / ATRIBUIBLE con porcentaje y justificación.

### Valor interno y externo

Campo `scope`: INTERNO | EXTERNO — soporta oportunidades de crecimiento, no solo ahorro.

### Histórico

`opportunity_valuation_history` con snapshots JSON por versión — no sobrescribe evidencia.

### RBAC

| Permiso | Descripción |
|---------|-------------|
| `valoracion.view` | Consultar valoración |
| `valoracion.manage` | Crear/modificar |
| `valoracion.validate` | Validar valoración |
| `valoracion.roi` | Consultar retorno |

### API (`/api/valoracion`)

| Método | Ruta | Permiso |
|--------|------|---------|
| GET | `/opportunities/{id}` | view |
| GET | `/opportunities/{id}/roi` | roi |
| POST | `/opportunities/{id}` | manage |
| PUT | `/opportunities/{id}/expected` | manage |
| PUT | `/opportunities/{id}/scenarios/{tipo}` | manage |
| POST | `/opportunities/{id}/real` | manage |
| POST | `/opportunities/{id}/costs` | manage |
| POST | `/opportunities/{id}/validate` | validate |

### UI

Pestaña **Valoración** en `OportunidadDetailPage.tsx` — esperado, real, escenarios, beneficio neto, retorno, recuperación, histórico. Textos en español.

---

## Archivos

| Archivo | Cambio |
|---------|--------|
| `backend/app/valuation_enums.py` | Enumeraciones |
| `backend/app/valuation_models.py` | Modelos SQLAlchemy |
| `backend/app/services/valuation_service.py` | Motor económico |
| `backend/app/schemas_valuation.py` | Schemas Pydantic |
| `backend/app/routers/valoracion.py` | API REST |
| `backend/app/permissions.py` | Permisos valoracion.* |
| `backend/app/main.py` | Registro router/modelos |
| `backend/alembic/versions/1210b2c3d4e5f_valuation_economic_roi_1210.py` | Migración |
| `frontend/src/api.ts` | Cliente API |
| `frontend/src/pages/OportunidadDetailPage.tsx` | UI valoración |
| `tests/test_valoracion_1210.py` | 19 pruebas focales |
| `tests/conftest.py` | Import valuation_models |

---

## Migración

- `revision`: `1210b2c3d4e5f`
- `down_revision`: `1110a1b2c3d4e`
- Cabeza única en esta rama

---

## Validación

| Prueba | Resultado |
|--------|-----------|
| `pytest tests/test_valoracion_1210.py` | 19/19 PASS |
| `pytest tests/test_finops_1110.py` | 8/8 PASS (regresión) |
| `npm run build` | PASS |

---

## Restricciones respetadas

- NO rama 1110 modificada
- NO PR #32 / V1 candidata
- NO bloques 1100/1120/1200
- NO pricing comercial / planes / Centro de Control
- NO OpenAI real / Docker / PostgreSQL harness

---

## Pendientes post-1210

1. Integración física con medición real del bloque 1200 vía `external_measurement_ref`
2. UI avanzada de comparación escenarios (gráficos)
3. Sincronización automática valor materializado desde `proactive_service.register_result`

**P0:** 0 | **P1:** 0

---

## Veredicto

```
EMPLEADOS_IA — BLOQUE 1210 TERMINADO

RAMA: cursor/1210-valoracion-economica-roi-85e4
BASE: 6234638

TIPOS DE VALOR: PASS
VALOR ESPERADO: PASS
ESCENARIOS: PASS
COSTOS: PASS
FINOPS 1110: PASS
VALOR REAL: PASS
ATRIBUCIÓN: PASS
BENEFICIO NETO: PASS
RETORNO: PASS
PERIODO RECUPERACIÓN: PASS
VALOR INTERNO: PASS
VALOR EXTERNO: PASS
HISTÓRICO: PASS
RBAC: PASS
MULTIEMPRESA: PASS
AUDITORÍA: PASS
UI: PASS

TESTS: 27 passed (19×1210 + 8×1110)
FRONTEND: PASS
ALEMBIC: 1210b2c3d4e5f

P0: 0
P1: 0

VEREDICTO: APTO
NO MERGE
```
