# CURSOR 1280 — Modelo comercial basado en valor + planes configurables

**Fecha:** 2026-08-29  
**Rama:** `cursor/1280-modelo-comercial-valor-85e4`  
**Base:** `076bca62d3a53022599edded638749845d7bdc29` (1210 FinOps+valoración) integrado con `0278177b434de7f04c4727f796e8e3e4006aadfd` (1200 línea base) en merge `0dd9cf7`  
**HEAD:** `64fb7d91790f5b68e50dc718dd7d33f2147f22b0`  
**Estado:** **BLOQUE 1280 TERMINADO**  
**NO MERGE**

---

## Objetivo

Construir el módulo comercial operativo que convierte:

**DIAGNÓSTICO → OPORTUNIDADES → LÍNEA BASE → IMPACTO ESPERADO → VALOR ECONÓMICO → COSTO IA / FINOPS → PROPUESTA → PLAN COMERCIAL → PRECIO → RETORNO DEL CLIENTE**

Trazable al valor económico real (1110, 1200, 1210) sin calculadora aislada.

---

## Rama base seleccionada

| Criterio | Rama | SHA |
|----------|------|-----|
| 1110 FinOps | `cursor/1210-valoracion-economica-roi-85e4` | incluido |
| 1210 Valoración / ROI | `cursor/1210-valoracion-economica-roi-85e4` | `076bca62d3a53022599edded638749845d7bdc29` |
| 1200 Línea base / impacto | `cursor/1200-linea-base-impacto` | `0278177b434de7f04c4727f796e8e3e4006aadfd` |
| Merge base 1280 | `cursor/1280-modelo-comercial-valor-85e4` | `0dd9cf7` |

No se arrastraron convergencias 1250 ni V1.

---

## Arquitectura aplicada

```
Diagnóstico / Oportunidades (1100/1220)
        │
        ▼
Valoración 1210 ──► OpportunityValuation / Real
Línea base 1200 ──► referencias en trazabilidad
FinOps 1110     ──► costos IA / consumo
        │
        ▼
CommercialProposal
  ├── CommercialProposalValue     (VERIFICADO / ESTIMADO / POTENCIAL + atribución)
  ├── CommercialProposalScenario  (CONSERVADOR / BASE / ALTO)
  ├── CommercialProposalCost      (proveedor / interno / precio / margen)
  ├── CommercialProposalPriceHistory (aprobación humana)
  └── CommercialDoubleCountAlert  (doble conteo)
        │
        ▼
CommercialPlan (parametrizable, multi-tenant)
  ├── consumo IA incluido / presupuesto / excedentes / alertas
  └── modo credenciales: ADMINISTRADA | PROPIA_INSTITUCION
```

Motor determinístico en `commercial_service.py`. Sin PDF avanzado ni facturación electrónica.

---

## Alcance implementado

### 1. Valor atribuible

- Naturalezas: `VERIFICADO`, `ESTIMADO`, `POTENCIAL`
- Categorías: ahorros, pérdidas evitadas, ingresos recuperados, productividad, errores, tiempos, riesgos, nuevos ingresos, oportunidades capturadas
- Validación de categorías incompatibles (no suma indiscriminada)

### 2. Atribución explícita

- `atribucion_pct`, `criterio_atribucion`, `justificacion_atribucion`, `evidencia_atribucion`, `responsable_atribucion`, `fecha_atribucion`
- Rechaza 100% automático sin criterio

### 3. Escenarios

- `CONSERVADOR`, `BASE`, `ALTO`
- Valor esperado, probabilidad/confianza, costo, tiempo, riesgo
- Escenario recomendado explicable vía API

### 4. Costos totales EMPLEADOS_IA

- Implementación, configuración, licencias, infraestructura, soporte, operación, consumo IA, integraciones, servicios adicionales
- Clases: `COSTO_PROVEEDOR_IA`, `COSTO_INTERNO`, `PRECIO_CLIENTE`, referencia margen
- Integración FinOps cuando hay `finops_ref`

### 5. Consumo IA en planes

- `consumo_ia_incluido`, `presupuesto_ia_incluido`, política excedentes, alertas, bloqueo opcional
- Sin concepto de IA ilimitada

### 6. Modos de credenciales

- `ADMINISTRADA` (IA administrada por nosotros)
- `PROPIA_INSTITUCION` (credenciales propias)
- Impacta costos, precio y facturación simulada — sin almacenar claves

### 7. Planes comerciales configurables

- Parámetros: empleados IA, usuarios, automatizaciones, consumo IA, proveedores/modelos, almacenamiento, integraciones, auditoría, soporte, SLA, presupuesto, excedentes, capacidades
- Planes globales (SuperAdmin) y por organización

### 8–9. Precio basado en valor y regla económica

```
precio_sugerido = max(
  valor_atribuible × fracción_valor,
  costo_total × (1 + margen_minimo),
  precio_base_plan
)
```

- Respeta mínimo, máximo, piso de costos, margen mínimo
- Advertencia si supera valor capturable razonable
- Sugiere, no impone

### 10. Beneficio neto del cliente

- Beneficio bruto − inversión total = beneficio neto
- ROI, payback, % valor conservado por el cliente

### 11–12. Propuesta comercial y aprobación humana

Estados: `BORRADOR`, `EN_REVISION`, `APROBADA`, `RECHAZADA`, `ENVIADA`, `ACEPTADA`, `VENCIDA`

- `precio_sugerido` ≠ `precio_final` automático
- Historial de precio con justificación, usuario y fecha

### 13. Trazabilidad

Endpoint `/api/comercial/propuestas/{id}/trazabilidad` enlaza diagnóstico, oportunidades, valoraciones 1210, líneas base 1200, referencias FinOps 1110 y supuestos.

### 14. Doble conteo

Alertas por oportunidad duplicada, categorías incompatibles y claves de deduplicación repetidas.

### 15. API (`/api/comercial`)

| Área | Rutas principales |
|------|-------------------|
| Planes | CRUD `/planes` |
| Propuestas | CRUD `/propuestas`, valores, escenarios, costos |
| Simulación | `POST /simular` |
| Precio | `POST /propuestas/{id}/recalcular-precio` |
| Aprobación | `POST /propuestas/{id}/aprobar`, historial precio |
| Trazabilidad | `GET /propuestas/{id}/trazabilidad` |
| Doble conteo | `GET /propuestas/{id}/alertas-doble-conteo` |

### 16. RBAC

| Permiso | Descripción |
|---------|-------------|
| `comercial.view` | Consultar planes y propuestas |
| `comercial.simulate` | Simulador de valor |
| `comercial.create` | Crear/editar propuestas |
| `comercial.approve` | Aprobar precio final |
| `comercial.manage_plans` | Administrar planes |

### 17. Multiempresa

Aislamiento estricto por `organization_id`. Planes globales vs por organización.

### 18. Auditoría

Eventos auditados: creación, recálculo, cambio supuesto/atribución/precio, aprobación, rechazo, envío, aceptación.

### 19. UI (español)

| Vista | Ruta |
|-------|------|
| Comercial (planes, propuestas, simulador) | `/comercial` |
| Detalle propuesta | `/comercial/propuestas/:id` |

Muestra: valor generado, atribuible, costo, precio sugerido/final, beneficio neto, ROI, payback, margen, consumo IA incluido.

---

## Archivos principales

| Archivo | Cambio |
|---------|--------|
| `backend/app/commercial_enums.py` | Enumeraciones comerciales |
| `backend/app/commercial_models.py` | Modelos SQLAlchemy |
| `backend/app/services/commercial_service.py` | Motor comercial |
| `backend/app/schemas_commercial.py` | Schemas Pydantic |
| `backend/app/routers/comercial.py` | API REST |
| `backend/app/permissions.py` | Permisos comercial.* |
| `backend/app/main.py` | Registro router/modelos |
| `backend/alembic/versions/1200b1c2d3e4f_merge_1110_1200_1210.py` | Merge cabezas 1210+1200 |
| `backend/alembic/versions/1280a1b2c3d4e_modelo_comercial_valor_1280.py` | Migración 1280 |
| `frontend/src/pages/ComercialPage.tsx` | UI principal |
| `frontend/src/pages/ComercialPropuestaDetailPage.tsx` | Detalle propuesta |
| `frontend/src/App.tsx`, `AppShell.tsx`, `api.ts` | Rutas, menú, cliente API |
| `tests/test_modelo_comercial_1280.py` | 12 pruebas focales |

---

## Migración Alembic

- Merge: `1200b1c2d3e4f` (down: `1210b2c3d4e5f` + `1200a1b2c3d4e`)
- Bloque 1280: `1280a1b2c3d4e` (down: `1200b1c2d3e4f`)
- Cabeza única en esta rama
- No se modificaron migraciones históricas

---

## Validación

| Prueba | Resultado |
|--------|-----------|
| `pytest tests/test_modelo_comercial_1280.py` | 12/12 PASS |
| `pytest tests/test_finops_1110.py` | PASS (regresión 1110) |
| `pytest tests/test_valoracion_1210.py` | PASS (regresión 1210) |
| `pytest tests/test_migration_control.py` | 7/7 PASS |
| Regresión focal 1280+1110+1210+migraciones | **46 passed** |
| `npm run build` | PASS |

---

## Restricciones respetadas

- NO V1 / NO PR #32 / NO candidata V1
- NO Docker / NO 1250 / NO 1260 / NO 1270
- NO OpenAI real / NO Ollama / NO scraping
- NO facturación electrónica / NO pagos / NO CRM completo
- NO PDF comercial avanzado
- NO `git add .` (archivos añadidos explícitamente)

---

## Pendientes post-1280

1. Integración UI directa con diagnóstico 1220 (campo `diagnostic_id` preparado)
2. Comparación visual avanzada de escenarios (gráficos)
3. Motor documental/PDF comercial formal
4. Sincronización automática de costos FinOps en recálculo periódico

**P0:** 0 | **P1:** 0 | **P2:** 0

---

## Veredicto

```
EMPLEADOS IA — BLOQUE 1280 TERMINADO

RAMA: cursor/1280-modelo-comercial-valor-85e4
BASE: 076bca62d3a53022599edded638749845d7bdc29 (+ merge 1200 0dd9cf7)
HEAD: 64fb7d91790f5b68e50dc718dd7d33f2147f22b0

VALOR ATRIBUIBLE: PASS
VALOR VERIFICADO/ESTIMADO/POTENCIAL: PASS
ESCENARIOS: PASS
COSTOS IA: PASS
PLANES: PASS
CONSUMO INCLUIDO: PASS
PRECIO BASADO EN VALOR: PASS
PISO COSTOS: PASS
MARGEN: PASS
BENEFICIO NETO: PASS
ROI: PASS
PAYBACK: PASS
PROPUESTAS: PASS
APROBACIÓN HUMANA: PASS
DOBLE CONTEO: PASS
TRAZABILIDAD: PASS
RBAC: PASS
MULTIEMPRESA: PASS
AUDITORÍA: PASS
UI: PASS
ALEMBIC: PASS (1280a1b2c3d4e)
TESTS: 46 passed (focal 1280+regresión)
FRONTEND: PASS

P0: 0
P1: 0
P2: 0

VEREDICTO: APTO
NO MERGE
```

**EMPLEADOS IA. Modelo comercial basado en valor terminado.**
