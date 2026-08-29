# EMPLEADOS IA — P1-ID-02 Semántica HECHO / INFERENCIA / RECOMENDACIÓN

**Fecha:** 2026-08-29  
**Base:** `700269b349b8d7887c988f4cf9ac94437f3e109c`  
**Rama:** `cursor/semantica-hecho-inferencia-recomendacion-p1`

---

## Objetivo

Contrato semántico transversal para que la plataforma no presente como equivalentes:

| Tipo | Significado |
|------|-------------|
| **HECHO** | Dato observado con evidencia o fuente trazable |
| **INFERENCIA** | Interpretación, correlación, hipótesis, estimación o predicción |
| **RECOMENDACIÓN** | Acción sugerida — no resultado realizado |

Fallback seguro: **SIN_CLASIFICAR** (nunca se promueve automáticamente a HECHO).

---

## Implementación

### Backend — `semantic_contract.py`

- `tipo_semantico`, `subtipo_semantico`, `etiqueta_visible`, `tooltip_semantico`
- Clasificadores por dominio: diagnóstico 1220, oportunidades 1100, señales 1120, externo 1240, valor 1210, LLM, atención requerida
- `enrich_control_center_payload()` aplicado en `get_executive_summary()` sin endpoint nuevo
- Cabecera `contrato_semantico` v1.0 en respuesta CC

### Frontend — `SemanticBadge.tsx`

- Componente reutilizable con texto explícito y tooltip
- No depende solo de color (`aria-label` + texto visible)
- Fallback a `SIN CLASIFICAR` si falta `tipo_semantico`

### Superficies CC enriquecidas

- ¿Por qué está pasando? (explicación 1220)
- Atención requerida
- Oportunidades (valor potencial/materializado)
- Valor y retorno (1210)
- IA / proveedores (inferencia)
- Inteligencia externa recientes

---

## Escenarios transversales demostrados

| Escenario | Flujo | Semántica |
|-----------|-------|-----------|
| **A** | Dato real → inferencia causal → recomendación | HECHO → INFERENCIA → RECOMENDACIÓN |
| **B** | Señal externa → tendencia → recomendación | HECHO → INFERENCIA (PREDICCION) → RECOMENDACIÓN |
| **C** | Valor potencial | INFERENCIA — no mostrado como realizado |
| **D** | Predicción / tendencia | INFERENCIA — no mostrada como hecho |
| **E** | Resultado verificado | HECHO con `RESULTADO_VERIFICADO` |

---

## Reglas validadas

| Regla | Estado |
|-------|--------|
| Correlación ≠ causalidad | PASS |
| Predicción ≠ hecho | PASS |
| Estimado/potencial ≠ realizado | PASS |
| IA generativa ≠ hecho | PASS |
| Evidencia / correlation_id preservados | PASS |
| Ausencia de clasificación no rompe API | PASS |
| RBAC — clasificación no amplía evidencia | PASS |
| Multiempresa — organization_id preservado | PASS |

---

## Pruebas

| Suite | Resultado |
|-------|-----------|
| Focal semántica (`test_semantic_contract_p1.py`) | 20 passed |
| Regresión SQLite acumulativa | **922 passed, 4 skipped, 0 failed** |
| Frontend build (`npm run build`) | PASS |
| PostgreSQL | PENDIENTE POR ENTORNO |
| Alembic | 1 head — `1380a1b2c3d4e` (sin migración) |

---

## Commits

| Pieza | SHA |
|-------|-----|
| **BACKEND** | `14db04d90048d27bdccfff48c7396091f8c64fd3` |
| **FRONTEND** | `303d140ed8d64c4ba2499c28e4dcf660ddeb5538` |
| **TESTS** | `19f2afe58a15b6084ebc5c60b7b92f0da9aacb3a` |
| **DOC** | `ed91736` *(HEAD de rama)* |

---

## Cierre P1-ID-02

| Ámbito | Estado |
|--------|--------|
| **Superficies convergidas** (1120/1220/1030/1100/1200/1210/1230/1240/1250 vía CC) | **CERRADO** |
| **P1-ID-02 global** | **PENDIENTE SOLO FASE 2** (módulos 1260–1340) |

---

## Adopción futura — receta Fase 2

| Módulo | Clasificación a adoptar | Punto de integración | Cambio mínimo | Prueba necesaria |
|--------|-------------------------|---------------------|---------------|------------------|
| **1260** | INFERENCIA (predicción), RECOMENDACIÓN (acción) | Adaptador CC / API agregada | Importar `semantic_contract.from_*` al serializar predicciones | test adaptador degradación + semántica |
| **1270** | INFERENCIA (salida IA), nunca HECHO sin evidencia | `_llm_section` / gateway router | `from_llm_output()` en respuestas LLM fuera de CC | test IA ≠ hecho |
| **1280** | HECHO (evento), INFERENCIA (patrón) | SenalesAdapter / event bus | `from_signal_item()` + subtipo patrón | test señal vs interpretación |
| **1290** | RECOMENDACIÓN exclusiva | Nuevo `RecomendacionAdapter` CC | `semantic_meta(RECOMENDACION)` + enlace ejecución | test recomendación ≠ resultado |
| **1310** | INFERENCIA (forecast), HECHO (dato histórico) | FinOps / forecast adapter | `valor_field_semantics` + `SUB_PREDICCION` | test forecast ≠ verificado |
| **1320** | HECHO (log), INFERENCIA (anomalía) | Observabilidad adapter | Clasificar métricas vs alertas inferidas | test anomalía etiquetada |
| **1330** | INFERENCIA (scoring), RECOMENDACIÓN (priorización) | Scoring service DTO | Envolver score en INFERENCIA | test score no es hecho |
| **1340** | HECHO (registro), INFERENCIA (evaluación) | Compliance adapter | Mapear verificado vs estimado | test cumplimiento verificado |

### Nota 1290 (cuando se porte)

Al integrar `cursor/1290-ejecucion-recomendacion-p1-9a85`:

1. NO cherry-pick `245cb778` en esta rama.
2. En Fase 2: añadir `RecomendacionAdapter` que consuma 1290 y etiquete **RECOMENDACIÓN** con `subtipo_semantico=ACCION_PROPUESTA`.
3. Reutilizar `enrich_control_center_payload()` — ~15 líneas en bloque `recomendaciones`.
4. Prueba: recomendación pendiente ≠ ejecución completada (HECHO solo tras evidencia de cierre).

---

## SALIDA FINAL

```
EMPLEADOS IA — P1 SEMÁNTICA DE DECISIÓN TERMINADO

BASE:
700269b349b8d7887c988f4cf9ac94437f3e109c

RAMA:
cursor/semantica-hecho-inferencia-recomendacion-p1

HEAD:
6af8f4591ed2fa0a5bf7389713c8dc79ee41b2e8

COMMIT BACKEND:
14db04d90048d27bdccfff48c7396091f8c64fd3

COMMIT FRONTEND:
303d140ed8d64c4ba2499c28e4dcf660ddeb5538

COMMIT TESTS:
19f2afe58a15b6084ebc5c60b7b92f0da9aacb3a

CONTRATO SEMÁNTICO:
PASS

HECHO:
PASS

INFERENCIA:
PASS

RECOMENDACIÓN:
PASS

CORRELACIÓN ≠ CAUSALIDAD:
PASS

PREDICCIÓN ≠ HECHO:
PASS

ESTIMADO/POTENCIAL ≠ REALIZADO:
PASS

IA GENERATIVA ≠ HECHO:
PASS

EVIDENCIA:
PASS

1120:
PASS

1220:
PASS

1030:
PASS

1100:
PASS

1200:
PASS

1210:
PASS

1230:
PASS

1240:
PASS

1250:
PASS

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

SQLITE:
PASS

POSTGRESQL:
PENDIENTE POR ENTORNO

REGRESIÓN:
922 passed, 4 skipped, 0 failed

FRONTEND:
PASS

MÓDULOS FUTUROS CON RECETA:
8/8

P1-ID-02 EN SUPERFICIES CONVERGIDAS:
CERRADO

P1-ID-02 GLOBAL:
PENDIENTE SOLO FASE2

P0:
0

P1:
0

P2:
0

RAMA CENTRAL MODIFICADA:
NO

MAIN:
NO MODIFICADO

V1:
NO MODIFICADA

MERGE:
NO

VEREDICTO:
APTO PARA PORTAR
```

**VEREDICTO:** APTO PARA PORTAR
