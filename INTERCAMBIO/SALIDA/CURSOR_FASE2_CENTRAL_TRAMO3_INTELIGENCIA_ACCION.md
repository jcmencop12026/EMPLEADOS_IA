# EMPLEADOS_IA — FASE 2 CENTRAL TRAMO 3 (ID03 + 1260 → 1290 → 1270 + VISTAS)

**Tipo:** Integración selectiva acumulativa — inteligencia, aprendizaje, optimización y multiproveedor  
**Fecha:** 2026-08-29  
**Agente:** GENERAL  
**Rama:** `cursor/fase2-central-integracion`

---

## 0. Base y método

| Campo | Valor |
|-------|-------|
| **BASE central antes** | `3049cc586d60fecfe18c035e94e5ea412b649270` |
| **HEAD Tramo 3** | ver sección final (post-commit doc) |
| **Método** | Cherry-pick selectivo — **sin merge bruto** |
| **main / V1** | NO modificados |

### Commits portados (funcionales + vistas)

| Orden | SHA central | Origen | Contenido |
|-------|-------------|--------|-----------|
| 1 | `db4be9b` | `1012b10` (P1-ID-03) | Oportunidad → línea base → medición/impacto |
| 2 | `9cf033f` | `5769b45` (1260) | Aprendizaje, retroalimentación, repriorización |
| 3 | `1d1d90a` | `0342728` (1290) | Optimización, priorización, recomendaciones |
| 4 | `7b9ca6a` | `245cb77` (P1-ID-04) | Ejecución trazable APROBADA→EJECUTADA/PENDIENTE/FALLIDA |
| 5 | `984de3d` | `2e8dcb2` (1270) | Multiproveedor, routing, observabilidad, FinOps |
| 6 | `dee0ff6` | — | Reparent Alembic 1260 sobre `1330b1b2c3d4f` |
| 7 | `17eefc9` | `785218b` | UI Aprendizaje 1260 |
| 8 | `75cc953` | `ab3586d` | UI Optimización 1290 + P1-ID-04 visible |
| 9 | `4a0ee4f` | `d176c20` | UI Multiproveedor 1270 |
| 10 | `39b1bfc` | `683db69` | Tests contrato API vistas |

**No portados:** semántica global (A), comercial/valor, identidad visual, integraciones visuales, demo, CC-DT, cableado 1260/1290/1270 al Centro de Control, rama auditoría documental P1-ID-03.

---

## 1. Alembic — CRÍTICO

| Campo | Valor |
|-------|-------|
| **Head antes** | `1330b1b2c3d4f` |
| **Revisiones portadas** | `1260a1b2c3d4e`, `1290a1b2c3d4e`, `1270a1b2c3d4e` |
| **Reparent** | `1260a1b2c3d4e.down_revision`: `1250f1a2b3c4d` → **`1330b1b2c3d4f`** |
| **Head después** | `1270a1b2c3d4e` |
| **Cabezas (`alembic heads`)** | **1** |
| **schema_repair.HEAD_REVISION** | `1270a1b2c3d4e` |
| **migration_ledger.baseline_head** | `1270a1b2c3d4e` |

Cadena lógica Tramo 3:

```
1330b1b2c3d4f → 1260a1b2c3d4e → 1290a1b2c3d4e → 1270a1b2c3d4e (HEAD)
```

---

## 2. Componentes integrados

### P1-ID-03 — Oportunidad → línea base → medición

- `baseline_service.py`, extensión `proactive_service.py`
- Aprobación oportunidad → identificación/creación línea base
- Cierre oportunidad → medición resultado
- Valor: VERIFICADO / ESTIMADO / POTENCIAL
- Atribución: INFERENCIA
- `learning_refs` para cadena 1260
- Idempotencia y aislamiento multiempresa
- Tests: `test_bloque_1200_linea_base_impacto.py`

### 1260 — Aprendizaje y repriorización

- `learning_models.py`, `learning_service.py`, router `/api/aprendizaje/*`
- Esperado vs observado, resultado, aprendizaje, evidencia, `correlation_id`
- Repriorización y patrones
- `learning_refs` funcional (sin aprendizaje ficticio)
- Tests: `test_aprendizaje_1260.py`

### 1290 — Optimización y recomendaciones

- `optimization_models.py`, `optimization_service.py`, router `/api/optimizacion/*`
- Recomendación, prioridad, aprobación, simulación
- Tests: `test_optimizacion_1290.py`

### P1-ID-04 — Ejecución de recomendaciones

- Flujos preservados:
  - PROPUESTA → APROBADA → EJECUTADA
  - PROPUESTA → APROBADA → PENDIENTE_EJECUCION_HUMANA
  - PROPUESTA → APROBADA → FALLIDA (nunca EJECUTADA si falló)
- Idempotencia, `learning_refs`, plan de trabajo, oportunidad asociada
- RBAC `optimizacion.execute`
- **No duplicado** desde rama visual (backend ya portado en `7b9ca6a`)

### 1270 — Multiproveedor, routing, observabilidad, FinOps

- Adaptadores: anthropic, azure-openai, gemini, http_utils
- Servicios: health, observability, routing
- Router `/api/llm/*` extendido
- **NO** Ollama instalado; **NO** OpenAI real
- Tests: `test_bloque_1270_multiproveedor.py` (incl. `test_1270_api_no_expone_secretos`)

### Vistas UI

| Vista | Ruta | Menú | Qué se ve | Qué demuestra |
|-------|------|------|------------|---------------|
| Aprendizaje | `/aprendizaje` | Operaciones → Aprendizaje | Ciclos, repriorización, patrones; badges semánticos | Cadena resultado→aprendizaje; filtros; correlation_id |
| Detalle aprendizaje | `/aprendizaje/:cicloId` | Desde listado | Evidencia, referencias, repriorización asociada | Trazabilidad 1260 |
| Optimización | `/optimizacion` | Operaciones → Optimización | Recomendaciones, simulación, estados ejecución | 1290 + P1-ID-04 (aprobar/ejecutar/pendiente/fallida) |
| Detalle optimización | `/optimizacion/:recId` | Desde listado | Panel ejecución, plan, confirmación humana | Estados EJECUTADA/PENDIENTE/FALLIDA |
| Proveedores IA | `/administracion/proveedores-ia` | Administración → Proveedores IA | Tabs: proveedores, modelos, salud, observabilidad, logs, enrutamiento | 1270 multiproveedor sin exponer secretos |
| Centro de Control | `/centro-control` | Dashboard → Centro de Control | Sin cambios Tramo 3 | CC preservado — **no cableado** a 1260/1290/1270 |

---

## 3. Cadena validada ID03 + 1260

```
oportunidad → línea base → ejecución → resultado → medición → aprendizaje
```

`learning_refs` conecta medición (1200/P1-ID-03) con ciclos 1260. Validado en tests 1200 y 1260.

---

## 4. Preservaciones y exclusiones

| Control | Estado |
|---------|--------|
| Centro de Control sin cableado 1260/1290/1270 | PASS — `control_center_service.py` sin referencias |
| Semántica global (A) no portada | PASS — solo badges preparatorios en UI |
| main / V1 / merge main | NO |
| Ollama instalado | NO |
| OpenAI real | NO |

---

## 5. Validación diferencial

| Métrica | Antes (Tramo 2) | Después (Tramo 3) | Δ |
|---------|-----------------|-------------------|---|
| passed | 927 | **968** | +41 |
| skipped | 4 | **4** | 0 |
| failed | 0 | **0** | 0 |
| errors | 0 | **0** | 0 |

**FALLOS NUEVOS INTRODUCIDOS: 0** (1 fallo transitorio en `test_scim_1380::test_migration_head` por head desactualizado — corregido)

### Focales ejecutados

| Suite | Resultado |
|-------|-----------|
| P1-ID-03 (`test_bloque_1200_linea_base_impacto`) | PASS |
| 1260 (`test_aprendizaje_1260`) | PASS |
| 1290 (`test_optimizacion_1290`) | PASS |
| P1-ID-04 (en `test_optimizacion_1290`) | PASS |
| 1270 (`test_bloque_1270_multiproveedor`) | PASS |
| Vistas API contract | PASS |
| 1030–1380 preservados (muestra: wiring, CC, RBAC, finops, 1300) | PASS |
| Multiempresa / RBAC / SUPERADMIN / V1 | PASS |
| Secretos (`test_1270_api_no_expone_secretos`) | PASS |
| Centro Control preservado | PASS |
| Frontend `npm run build` | PASS |
| PostgreSQL | **PENDIENTE POR ENTORNO** |

| Severidad | Conteo |
|-----------|--------|
| P0 | **0** |
| P1 | **0** |
| P2 | **0** |

---

## 6. Correcciones de integración

1. **Alembic reparent** `1260a1` → `1330b1b2c3d4f` (evita segunda cabeza)
2. **`frontend/src/api.ts`** — eliminada llave extra post-merge 1270/P1-ID-04
3. **`tests/test_scim_1380.py`** — `test_migration_head` actualizado a head `1270a1b2c3d4e`

---

## 7. Recorrido visual preparado

| Paso | Ruta | Menú |
|------|------|------|
| Login | `/login` | — |
| Centro de Control | `/centro-control` | Dashboard |
| Oportunidades | `/oportunidades` | Operaciones |
| Línea base | `/linea-base` | Operaciones |
| Aprendizaje | `/aprendizaje` | Operaciones |
| Repriorización | `/aprendizaje` (tab) | Operaciones |
| Recomendaciones | `/optimizacion` | Operaciones |
| Aprobar / ejecutar | `/optimizacion/:recId` | Operaciones |
| Proveedores IA | `/administracion/proveedores-ia` | Administración |
| Modelos / routing / observabilidad / FinOps | tabs en Proveedores IA | Administración |

**RECORRIDO VISUAL: PREPARADO** (requiere datos seed y servicios en ejecución)

---

## 8. Veredicto

**TRAMO 3 APTO** — integración selectiva completada; regresión 0 failed; Alembic cabeza única; CC preservado.
