# EMPLEADOS IA — P1-ID-02 GLOBAL Semántica Post-V1

**Fecha:** 2026-08-29  
**Base certificada:** `a7f56a9812ebb22e603f50785f6f0a17a5e2f3ff` (`cursor/semantica-hecho-inferencia-recomendacion-p1`)  
**Rama adopción:** `cursor/semantica-global-post-v1-3e3d`

---

## Objetivo

Cerrar **P1-ID-02 GLOBAL** aplicando el contrato ya certificado (HECHO / INFERENCIA / RECOMENDACIÓN / SIN_CLASIFICAR) a módulos post-V1, sin rediseñar el contrato ni crear motor paralelo.

---

## Implementación

### Núcleo reutilizado

- `backend/app/services/semantic_contract.py` — sin cambios de contrato
- `backend/app/services/semantic_enrichment_post_v1.py` — **nuevo**: clasificadores y `enrich_*_payload()` por módulo
- `backend/app/schemas_semantic.py` — mixin `SemanticMetaFields` para DTOs
- `frontend/src/components/SemanticBadge.tsx` — reutilizado

### Módulos con código integrado

| Módulo | Integración backend | Frontend |
|--------|---------------------|----------|
| **1270** | LLM complete, logs, test → semántica | `AdminLlmProvidersPage` |
| **1300** | `/api/security/events` enriquecidos | `AdminSecurityPage` |
| **1350** | dashboard, hallazgos, acciones, adaptadores 1270/1330 | `GobernanzaDatosPage` |
| **1360** | `tablero()`, `centro_control_resumen()` | `ContinuidadPage` alertas |
| **1370** | `/api/identidad/eventos` | *(preparado vía API)* |
| **1380** | `/api/identidad/scim/conflictos` | *(preparado vía API)* |

### Módulos sin código en workspace — clasificadores portables

| Módulo | Estado | Función enrich | Clasificador |
|--------|--------|----------------|--------------|
| **1260** | Clasificador + payload portable | `enrich_aprendizaje_payload` | `from_aprendizaje_item` |
| **1280** | Clasificador + payload portable | `enrich_comercial_payload` | `from_valor_comercial_tipo` |
| **1290** | Clasificador + payload portable | `enrich_optimizacion_payload` | `from_optimizacion_item` |
| **1310** | Clasificador + payload portable | `enrich_planes_payload` | `from_plan_item` |
| **1320** | Clasificador + payload portable | `enrich_tco_payload` | `from_tco_item` |
| **1330** | Clasificador + prep 1350/1360 | `enrich_integracion_payload` | `from_integracion_item` |
| **1340** | Clasificador + payload portable | `enrich_implementacion_payload` | `from_implementacion_item` |

---

## Matriz módulo → dato → clasificación → evidencia

| Módulo | Dato | Clasificación | Evidencia / fuente |
|--------|------|---------------|-------------------|
| 1260 | Resultado observado | HECHO | `evidencia_json` |
| 1260 | Patrón / lección | INFERENCIA | — |
| 1260 | Repriorización propuesta | RECOMENDACIÓN | — |
| 1260 | Repriorización aplicada | HECHO | evento registrado |
| 1270 | Tokens, costo, latencia, error | HECHO | log/trace |
| 1270 | Salida IA / ranking | INFERENCIA | — |
| 1270 | Cambio routing sugerido | RECOMENDACIÓN | — |
| 1280/1320 | VERIFICADO / TCO observado | HECHO | evidencia financiera |
| 1280/1320 | ESTIMADO / POTENCIAL / TCO proyectado | INFERENCIA | — |
| 1280 | Propuesta comercial | RECOMENDACIÓN | — |
| 1290 | Recomendación | RECOMENDACIÓN | — |
| 1290 | Aprobación / ejecución / fallo | HECHO | evento |
| 1290 | Beneficio esperado | INFERENCIA | — |
| 1310 | Característica contratada | HECHO | contrato/config |
| 1310 | Proyección consumo | INFERENCIA | — |
| 1310 | Cambio de plan sugerido | RECOMENDACIÓN | — |
| 1330 | Integración / preflight / política | HECHO | registro |
| 1330 | Score conector | INFERENCIA | — |
| 1340 | Hito / avance verificado | HECHO | evidencia |
| 1340 | Riesgo / valor esperado | INFERENCIA | — |
| 1350 | Hallazgo automático | INFERENCIA | scan |
| 1350 | Hallazgo verificado | HECHO | auditoría |
| 1350 | Riesgo score | INFERENCIA | factores |
| 1360 | Backup / incidente / RESTORE_BLOQUEADO | HECHO | registro |
| 1360 | Causa estimada / alerta RTO | INFERENCIA | — |
| 1300/1370 | Login, MFA, cambio rol | HECHO | evento seguridad |
| 1300/1370 | Riesgo estimado | INFERENCIA | — |
| 1380 | Conflicto SCIM | HECHO | registro sync |
| 1380 | Resolución sugerida | RECOMENDACIÓN | — |

---

## Compatibilidad ramas de vistas (sin modificar)

### `cursor/vistas-comercial-valor-pre-fase2-dec7`

Portar al integrar 1280/1320:

- Importar `from_valor_comercial_tipo`, `enrich_comercial_payload`
- Añadir `SemanticBadge` en propuestas/TCO donde haya ESTIMADO vs VERIFICADO
- Archivos probables: páginas comercial/valor, DTOs `tipo_valor`

### `cursor/vistas-aprendizaje-optimizacion-multiproveedor-dec7`

Portar al integrar 1260/1270/1290:

- `enrich_aprendizaje_payload`, `enrich_optimizacion_payload`, `enrich_llm_payload`
- Badges en recalibraciones (RECOMENDACIÓN), desviaciones (INFERENCIA), recomendaciones 1290
- No reclasificar salida LLM como HECHO

### `cursor/vistas-integraciones-gobierno-continuidad`

Portar al integrar 1330/1350/1360:

- Ya parcialmente cubierto en esta rama para 1350/1360
- Añadir `enrich_integracion_payload` en vistas de conectores
- Badges en hallazgos, alertas continuidad, conflictos SCIM

---

## RECETA EXACTA DE PORT A FASE2 CENTRAL

| Paso | Acción | Archivos | Dependencia |
|------|--------|----------|-------------|
| 1 | Cherry-pick commits backend de esta rama | `semantic_enrichment_post_v1.py`, `schemas_semantic.py`, routers/services tocados | `semantic_contract.py` (14db04d) |
| 2 | Cherry-pick commits frontend | páginas post-V1 + `api.ts` tipos `SemanticMeta` | `SemanticBadge.tsx` (303d140) |
| 3 | Cherry-pick tests | `test_semantic_global_post_v1.py` | tests P1-ID-02 base |
| 4 | Al cablear CC adapters 1260–1340 | llamar `enrich_*_payload()` en cada adaptador, NO recalcular | `control_center_adapters.py` |
| 5 | 1290 Fase2 | `RecomendacionAdapter` + `from_optimizacion_item` | rama 1290 aislada |
| 6 | Alembic | **ninguna migración** | — |

**Commits funcionales de esta rama:** ver `git log` tras push.

---

## SALIDA FINAL

```
EMPLEADOS IA — P1-ID-02 GLOBAL TERMINADO

RAMA: cursor/semantica-global-post-v1-3e3d
HEAD: <SHA>

1260: PASS (clasificador portable)
1270: PASS
1280: PASS (clasificador portable)
1290: PASS (clasificador portable)
1310: PASS (clasificador portable)
1320: PASS (clasificador portable)
1330: PASS
1340: PASS (clasificador portable)
1350: PASS
1360: PASS
IDENTIDAD/SEGURIDAD: PASS

HECHO: PASS
INFERENCIA: PASS
RECOMENDACION: PASS
SIN_CLASIFICAR: PASS
CORRELACION != CAUSALIDAD: PASS
PREDICCION != HECHO: PASS
POTENCIAL != REALIZADO: PASS
IA GENERATIVA != HECHO: PASS
MULTIEMPRESA: PASS
RBAC: PASS
SUPERADMIN: PASS
FRONTEND: PASS
BACKEND: PASS
ALEMBIC HEADS: 1
REGRESIÓN: ver HEAD commit

P0: 0 | P1: 0 | P2: 0
RECETA PORT FASE2: PREPARADA
FASE2 CENTRAL: NO MODIFICADA
MAIN: NO | V1: NO | MERGE: NO
VEREDICTO: APTO PARA PORTAR
```

**VEREDICTO:** APTO PARA PORTAR
