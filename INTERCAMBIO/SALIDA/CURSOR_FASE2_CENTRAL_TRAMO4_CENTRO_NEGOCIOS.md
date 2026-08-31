# EMPLEADOS_IA — FASE 2 CENTRAL TRAMO 4 (CENTRO DE NEGOCIOS + VALOR + COMERCIAL + IMPLEMENTACIÓN)

**Tipo:** Integración selectiva acumulativa — MB-09 Centro de Negocios  
**Fecha:** 2026-08-29  
**Agente:** GENERAL  
**Rama:** `cursor/fase2-central-integracion`

---

## 0. Base y método

| Campo | Valor |
|-------|-------|
| **BASE central antes** | `f8d1ae1dfc86d4cc1390478b408db624d7101131` |
| **HEAD Tramo 4** | ver sección final |
| **Método** | Cherry-pick selectivo — **sin merge bruto** |
| **main / V1** | NO modificados |

### Commits portados

| Orden | SHA central | Origen | Contenido |
|-------|-------------|--------|-----------|
| 1 | `9e2d4b9` | `aa1f1b5` (1280) | Modelo comercial basado en valor |
| 2 | `f6dc1e1` | `dc1e88c` (1320) | TCO, ecosistema y aliados |
| 3 | `9ac902e` | `7621c26` (1340) | Implementación y éxito del cliente |
| 4 | `4235618` | `bf4de57` (1310) | Segmentación, paquetes y planes |
| 5 | `dbfb41a` | `9d12878` | Tests cierre comercial/valor (20 escenarios) |
| 6 | `3df0574` | `36d9e2b` | POTENCIAL excluido de precio/ROI realizado |
| 7 | `bdbaaf1` | `75904c4` | credential_mode heredado del plan |
| 8 | `343ba83`–`d64cb4e` | vistas dec7 | UI planes, valor, TCO, implementación + tests contrato |
| 9 | `44fea58` | `42712f8` | Terminología español portable (rama comercial) |
| 10 | `8bed205` | — | Reparent Alembic lineal sin bloque 1390 |

**No portados:** bloque funcional 1390, documentación histórica innecesaria, cableado ejecutivo comercial al Centro de Control, demo, Mesa de Ayuda, CC-DT, semántica global duplicada.

---

## 1. Alembic — CRÍTICO

| Campo | Valor |
|-------|-------|
| **Head antes** | `1270a1b2c3d4e` |
| **Revisiones portadas** | `1280a1`, `1280b2`, `1310a1`, `1320a1`, `1340a1` |
| **Reparent** | `1280a1.down_revision`: `1380a1` → **`1270a1b2c3d4e`**; `1320a1.down_revision`: `1280b2` → **`1310a1b2c3d4e`** (linealización) |
| **1390a1** | **NO portado** — era merge técnico vacío entre ramas paralelas |
| **Head después** | `1340a1b2c3d4e` |
| **Cabezas (`alembic heads`)** | **1** |

Cadena lineal Tramo 4:

```
1270a1b2c3d4e → 1280a1b2c3d4e → 1280b2c3d4e5f → 1310a1b2c3d4e → 1320a1b2c3d4e → 1340a1b2c3d4e (HEAD)
```

---

## 2. Componentes integrados (MB-09 Centro de Negocios)

### 1280 — Modelo comercial basado en valor

- Propuestas, planes, escenarios, costos, precio sugerido/final
- Valor: VERIFICADO / ESTIMADO / POTENCIAL (metodología 1210 preservada)
- **POTENCIAL** excluido de precio, ROI realizado y payback realizado
- Tests: `test_modelo_comercial_1280.py`

### 1310 — Segmentación y planes

- Perfiles, paquetes, verticales, recomendación de plan
- Límites medibles (sin IA ilimitada)
- credential_mode: IA_ADMINISTRADA vs CREDENCIALES_PROPIAS
- Tests: `test_segmentacion_1310.py`

### 1320 — TCO y aliados

- Categorías, proveedores, costos, tablero, rentabilidad, make-or-buy
- Tests: `test_tco_1320.py`

### 1340 — Implementación y éxito cliente

- Proyectos, hitos, readiness, pilotos, go-live, adopción, salud
- Sin duplicar Mi Trabajo; compatibilidad futura bandeja
- Tests: `test_implementacion_1340.py`

### Cierre comercial/valor

- `test_cierre_comercial_valor_pre_fase2.py` — 20 escenarios obligatorios PASS
- Separación POTENCIAL documentada en `commercial_service.py`

### FinOps

- Reutiliza 1110 y 1270 — **sin nuevo FinOps**
- Costos IA vinculados a propuestas y planes

---

## 3. Regla económica crítica — VALIDADA

| Control | Resultado |
|---------|-----------|
| VERIFICADO / ESTIMADO / POTENCIAL separados | PASS |
| POTENCIAL excluido de precio sugerido | PASS (`test_04_potencial_no_como_realizado`) |
| POTENCIAL excluido de ROI realizado | PASS |
| POTENCIAL excluido de payback realizado | PASS |
| Precio como fracción del valor atribuible | PASS |
| credential_mode heredado del plan | PASS |

---

## 4. Vistas comerciales

| Vista | Ruta | Menú | Qué demuestra |
|-------|------|------|---------------|
| Comercial y valor | `/comercial` | Análisis → Comercial y valor | Propuestas, planes, tabs |
| Detalle plan | `/comercial/planes/:planId` | Desde comercial/segmentación | Límites, credential_mode, precio |
| Detalle propuesta | `/comercial/propuestas/:proposalId` | Desde comercial | Valor VERIFICADO/ESTIMADO/POTENCIAL, ROI, precio |
| Segmentación | `/comercial/segmentacion` | Análisis → Segmentación y planes | Paquetes, recomendación |
| Costos y valor | `/costos-valor` | Análisis → Costos y valor | FinOps 1110 (preservado) |
| TCO | `/tco` | Análisis → TCO y aliados | Desglose categorías español |
| Implementación | `/implementacion` | Análisis → Implementación | Ciclo y seguimiento |
| Detalle implementación | `/implementacion/:proyectoId` | Desde listado | Hitos, barra de ciclo, valor |

---

## 5. Preservaciones

| Control | Estado |
|---------|--------|
| Centro de Control sin cableado comercial | PASS — `control_center_service.py` sin referencias 1280/1310/1320/1340 |
| FinOps único (1110+1270) | PASS |
| Multiempresa cross-org | PASS (tests 1280/1310/1320/1340 + cierre) |
| RBAC sin ampliación | PASS |
| Secretos no expuestos en vistas | PASS |
| Semántica global no duplicada | PASS — badges preparatorios existentes |

---

## 6. Validación diferencial

| Métrica | Antes (Tramo 3) | Después (Tramo 4) | Δ |
|---------|-----------------|-------------------|---|
| passed | 968 | **1061** | +93 |
| skipped | 4 | **4** | 0 |
| failed | 0 | **0** | 0 |
| errors | 0 | **0** | 0 |

**FALLOS NUEVOS: 0**  
**ERRORES NUEVOS: 0**

### Focales ejecutados

| Suite | Resultado |
|-------|-----------|
| 1280, 1310, 1320, 1340 | PASS |
| Cierre comercial/valor (20) | PASS |
| Vistas API contract | PASS |
| Migration control + SCIM head | PASS |
| Frontend `npm run build` | PASS |
| PostgreSQL | **PENDIENTE POR ENTORNO** |

| Severidad | Conteo |
|-----------|--------|
| P0 | **0** |
| P1 | **0** |
| P2 | **0** |

---

## 7. Correcciones de integración

1. **Alembic lineal** sin revisión 1390 (merge vacío innecesario)
2. **`frontend/src/api.ts`** — `comparePackages` y `simulateCommercialProposal` restaurados post-merge
3. **`tests/test_scim_1380.py`** — head actualizado a `1340a1b2c3d4e`

---

## 8. Recorrido visual preparado

Login → Centro de Control → Comercial → Planes → Costos IA → Valor (VERIFICADO/ESTIMADO/POTENCIAL) → Propuesta → Precio/ROI → TCO → Implementación → Seguimiento

**RECORRIDO VISUAL: PREPARADO**

---

## 9. Veredicto

**TRAMO 4 APTO** — Centro de Negocios integrado; regresión 0 failed; Alembic cabeza única; CC preservado.
