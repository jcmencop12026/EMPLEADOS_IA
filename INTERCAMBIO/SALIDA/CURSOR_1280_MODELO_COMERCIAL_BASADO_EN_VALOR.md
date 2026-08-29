# CURSOR 1280 — Modelo comercial basado en valor + planes configurables

**Fecha:** 2026-08-29  
**Rama:** `cursor/1280-modelo-comercial-valor-85e4`  
**Estado:** **BLOQUE 1280 TERMINADO**  
**NO MERGE**

---

## Base de desarrollo

| Campo | Valor |
|-------|-------|
| **Rama base** | `cursor/1210-valoracion-economica-roi-85e4` |
| **SHA base (1210)** | `076bca62d3a53022599edded638749845d7bdc29` |
| **Integración 1200** | `0278177b434de7f04c4727f796e8e3e4006aadfd` (merge `0dd9cf7`) |
| **Razón técnica** | Única combinación POST-V1 con 1110+1210 sin convergencias 1250/V1; 1200 integrado por merge explícito sin arrastrar 1220/1240/1250 |

**Git root verificado:** `/workspace` (equivalente `D:\EMPLEADOS_IA`)

---

## HEAD final

Ver `git rev-parse HEAD` en rama tras último commit.

---

## Arquitectura

```
Diagnóstico (1220) ──► diagnostic_id
Oportunidades (1100) ──► opportunity_id
Línea base (1200) ──► linea_base_id
Valoración (1210) ──► valuation_id
FinOps (1110) ──► finops_record_id
Inteligencia externa (1240 prep) ──► external_intelligence_ref
        │
        ▼
CommercialProposal
  ├── CommercialProposalValue (naturaleza, alcance INTERNO/EXTERNO, atribución)
  ├── CommercialProposalScenario (CONSERVADOR / BASE / ALTO)
  ├── CommercialProposalCost (proveedor / interno / precio)
  ├── CommercialProposalPriceHistory (aprobación humana)
  └── CommercialDoubleCountAlert
        │
        ▼
CommercialPlan (parametrizable, consumo IA, credenciales, excedentes)
```

Flujo operativo: **DIAGNÓSTICO → OPORTUNIDADES → LÍNEA BASE → IMPACTO → VALOR ECONÓMICO → COSTO IA/FINOPS → PROPUESTA → PLAN → PRECIO → RETORNO**

---

## Entidades principales

| Entidad | Descripción |
|---------|-------------|
| `CommercialPlan` | Plan configurable (empleados IA, usuarios, consumo IA, excedentes, credenciales, SLA, etc.) |
| `CommercialProposal` | Propuesta comercial con estados BORRADOR…VENCIDA |
| `CommercialProposalValue` | Componente de valor (VERIFICADO/ESTIMADO/POTENCIAL, INTERNO/EXTERNO, atribución) |
| `CommercialProposalScenario` | Escenario conservador/base/alto |
| `CommercialProposalCost` | Costo desglosado (proveedor IA, interno, precio cliente) |
| `CommercialProposalPriceHistory` | Historial precio sugerido vs final |
| `CommercialDoubleCountAlert` | Alerta doble conteo |

---

## Valor interno y externo

| Ámbito | Categorías típicas |
|--------|-------------------|
| **INTERNO** | Ahorro, pérdida evitada, ingreso recuperado, productividad, errores, tiempos, riesgo |
| **EXTERNO** | Nuevo ingreso, oportunidad capturada |

Campo `external_intelligence_ref` preparado para integración 1240 sin duplicar ese bloque.

---

## Cálculos económicos (determinísticos)

```
valor_atribuible = valor_bruto × atribucion_pct / 100

precio_sugerido = max(
  valor_atribuible × fracción_valor,
  costo_total × (1 + margen_mínimo),
  precio_base_plan
)

beneficio_neto_cliente = valor_atribuible − precio
ROI % = beneficio_neto / precio × 100
payback_meses = precio / (valor_atribuible / 12)
% conservado cliente = beneficio_neto / valor_atribuible × 100
% capturado EMPLEADOS_IA = precio / valor_atribuible × 100
margen % = (precio − costo_total) / precio × 100

excedente_tokens = max(0, tokens_usados − consumo_ia_incluido)
costo_excedente = excedente_tokens / 1_000_000 × excedente_ia_por_millon
```

La plataforma **sugiere**, no impone. Precio final requiere aprobación humana.

---

## Migración Alembic

| Revision | Archivo | Descripción |
|----------|---------|-------------|
| `1200b1c2d3e4f` | merge 1210 + 1200 | Cabeza convergente base |
| `1280a1b2c3d4e` | modelo comercial | Tablas comerciales |
| `1280b2c3d4e5f` | scope externo | `alcance`, `external_intelligence_ref`, `pct_valor_capturado_empleados_ia` |

**ALEMBIC HEAD:** `1280b2c3d4e5f` (cabeza única)

---

## API (`/api/comercial`)

| Método | Ruta | Permiso |
|--------|------|---------|
| GET | `/planes` | comercial.view |
| GET | `/planes/{id}` | comercial.view |
| POST | `/planes` | comercial.manage_plans |
| GET | `/propuestas` | comercial.view |
| POST | `/propuestas` | comercial.create |
| GET | `/propuestas/{id}` | comercial.view |
| POST | `/propuestas/{id}/valores` | comercial.create |
| POST | `/propuestas/{id}/escenarios` | comercial.create |
| POST | `/propuestas/{id}/costos` | comercial.create |
| POST | `/propuestas/{id}/precio-sugerido` | comercial.simulate |
| POST | `/propuestas/{id}/precio-final` | comercial.approve |
| POST | `/propuestas/{id}/aprobar` | comercial.approve |
| POST | `/propuestas/{id}/simular` | comercial.simulate |
| POST | `/propuestas/{id}/detectar-doble-conteo` | comercial.view |
| POST | `/propuestas/{id}/importar-valoracion` | comercial.create |
| GET | `/propuestas/{id}/trazabilidad` | comercial.view |
| POST | `/simular` | comercial.simulate |

---

## UI (español)

| Vista | Ruta |
|-------|------|
| Planes, simulador, propuestas | `/comercial` |
| Detalle propuesta + comparación escenarios + simulación | `/comercial/propuestas/:id` |

---

## Permisos RBAC

| Permiso | Descripción |
|---------|-------------|
| `comercial.view` | Consultar planes y propuestas |
| `comercial.simulate` | Simulador y precio sugerido |
| `comercial.create` | Crear/editar propuestas |
| `comercial.approve` | Precio final y aprobación |
| `comercial.manage_plans` | Administrar planes |

---

## Auditoría

Eventos: `comercial.propuesta.creada`, `comercial.valor.agregado`, `comercial.escenario.agregado`, `comercial.costo.agregado`, `comercial.precio.sugerido`, `comercial.precio.modificado`, `comercial.propuesta.aprobada`, `comercial.plan.creado`

---

## Archivos modificados (bloque 1280)

| Archivo | Cambio |
|---------|--------|
| `backend/app/commercial_enums.py` | ValueScope, categorías interno/externo |
| `backend/app/commercial_models.py` | alcance, external_intelligence_ref, pct_capturado |
| `backend/app/commercial_service.py` | Motor económico, simulación, excedentes, trazabilidad |
| `backend/app/schemas_commercial.py` | Schemas ampliados |
| `backend/app/routers/comercial.py` | API planes detalle, simular propuesta |
| `backend/app/permissions.py` | Permisos comercial.* |
| `backend/app/main.py` | Registro router/modelos |
| `backend/alembic/versions/1280a1b2c3d4e_*.py` | Migración tablas |
| `backend/alembic/versions/1280b2c3d4e5f_*.py` | Migración scope externo |
| `frontend/src/pages/ComercialPage.tsx` | UI principal |
| `frontend/src/pages/ComercialPropuestaDetailPage.tsx` | Detalle + escenarios + simulación |
| `frontend/src/api.ts` | Cliente API |
| `tests/test_modelo_comercial_1280.py` | 17 pruebas focales |

---

## Pruebas

| Suite | Resultado |
|-------|-----------|
| `pytest tests/test_modelo_comercial_1280.py` | **17/17 PASS** |
| Regresión focal 1110+1210+migraciones | **51 passed** |
| `npm run build` | **PASS** |

Cobertura: valor verificado/estimado/potencial, interno/externo, atribución, escenarios, costos, precio basado en valor, piso costos, margen, beneficio neto, ROI, payback, planes, consumo IA, excedentes, credenciales, doble conteo, simulación no destructiva, aprobación humana, RBAC, multiempresa, auditoría, trazabilidad.

---

## Hallazgos

| ID | Severidad | Descripción | Estado |
|----|-----------|-------------|--------|
| — | — | Sin hallazgos P0/P1 en bloque 1280 | — |

**P0:** 0 | **P1:** 0 | **P2:** 0

---

## Pendientes post-1280

1. Integración UI directa con diagnóstico 1220
2. Enlace automático con señales 1240 vía `external_intelligence_ref`
3. Motor documental/PDF comercial formal
4. Gráficos avanzados comparación escenarios

---

## Veredicto

```
EMPLEADOS IA — BLOQUE 1280 TERMINADO

RAMA: cursor/1280-modelo-comercial-valor-85e4
BASE: cursor/1210-valoracion-economica-roi-85e4 @ 076bca62 (+ merge 1200 0dd9cf7)
HEAD: <SHA final>

VALOR ATRIBUIBLE: PASS
VALOR VERIFICADO/ESTIMADO/POTENCIAL: PASS
VALOR INTERNO: PASS
VALOR EXTERNO PREPARADO: PASS
ESCENARIOS: PASS
COSTOS IA: PASS
COSTOS TOTALES: PASS
PLANES: PASS
CONSUMO INCLUIDO: PASS
EXCEDENTES: PASS
MODALIDADES CREDENCIALES: PASS
PRECIO BASADO EN VALOR: PASS
PISO DE COSTOS: PASS
MARGEN: PASS
BENEFICIO NETO: PASS
ROI: PASS
PAYBACK: PASS
PROPUESTAS: PASS
SIMULADOR: PASS
APROBACIÓN HUMANA: PASS
DOBLE CONTEO: PASS
TRAZABILIDAD: PASS
RBAC: PASS
MULTIEMPRESA: PASS
AUDITORÍA: PASS
UI EN ESPAÑOL: PASS
ALEMBIC: PASS
ALEMBIC HEAD: 1280b2c3d4e5f
TESTS: 51 passed (17×1280 + regresión focal)
FRONTEND: PASS
SECRETOS: PASS
DIFF CONTROLADO: PASS

P0: 0
P1: 0
P2: 0

VEREDICTO: APTO
NO MERGE
```

**EMPLEADOS IA. Modelo comercial basado en valor terminado.**
