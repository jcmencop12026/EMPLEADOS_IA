# EMPLEADOS_IA — BLOQUE 1290 OPTIMIZACIÓN Y RECOMENDACIONES

**Agente:** A  
**Rama:** `cursor/1290-optimizacion-recomendaciones`  
**Base:** `6a6cfbcfaf64fde501e0586700d8e6639498f644` (Bloque 1260)  
**Alembic HEAD:** `1290a1b2c3d4e`  
**Modo:** POST-V1 — sin V1, Docker, 1250, 1270, 1280

---

## Objetivo

Motor determinista y explicable que responde:

- ¿Qué conviene hacer primero y por qué?
- ¿Cuál es la mejor combinación de acciones con los recursos disponibles?

Ciclo: diagnóstico → oportunidades → valor/costo/impacto/riesgo → aprendizaje 1260 → restricciones → optimización → recomendaciones → plan priorizado.

---

## Componentes

| Componente | Descripción |
|------------|-------------|
| `optimization_models.py` | Configuración, recomendaciones, items, auditoría |
| `optimization_service.py` | Scoring explicable, portafolio combinatorio (≤18 items), integración 1260 |
| `routers/optimizacion.py` | API REST con RBAC |
| Migración `1290a1b2c3d4e` | Tablas del bloque |

### Objetivos configurables

- MAXIMIZAR_VALOR
- MAXIMIZAR_ROI
- MAXIMIZAR_IMPACTO
- MINIMIZAR_RIESGO
- RESULTADO_EQUILIBRADO

### Restricciones

Presupuesto, tiempo, capacidad, máximo iniciativas, riesgo máximo, obligatorias, excluidas, dependencias (`requiere`), incompatibles, orden previo.

### Estados recomendación

PROPUESTA → REVISADA → APROBADA / RECHAZADA → EJECUTADA / RECALCULADA

### Sin solución factible

Retorna `factible: false` con lista de conflictos — no inventa resultado.

### Algoritmo portafolio

- Scoring ponderado explicable por oportunidad
- Selección combinatoria acotada (máx. 18 candidatos, enumeración de subconjuntos)
- Documentado en código: escala limitada para evitar explosión exponencial sin límite

### Integración aprendizaje 1260

Ajusta confianza, probabilidad de éxito y riesgo según `CicloAprendizaje` y `PatronAprendizaje`. Trazado en `aprendizaje_influencia_json` e items.

---

## API (`/api/optimizacion`)

| Endpoint | Permiso |
|----------|---------|
| GET/PUT `/configuracion` | view / configure |
| POST `/simular` | simulate |
| POST `/recomendaciones` | create |
| GET `/recomendaciones`, `/{id}` | view |
| POST `/{id}/recalcular` | create |
| POST `/{id}/aprobar`, `/rechazar`, `/revisar` | approve / create |
| POST `/comparar` | simulate |
| GET `/historial` | view |

---

## UI (español)

- `/optimizacion` — simulador + listado recomendaciones
- `/optimizacion/:recId` — detalle portafolio, explicación, aprobación

Menú: **Análisis y control → Optimización**

---

## Pruebas

```
tests/test_optimizacion_1290.py — 13 passed, 0 failed (7.38s)
```

Cubre: priorización, presupuesto, objetivos, obligatorias/excluidas, dependencias, sin solución, aprendizaje 1260, control humano, reoptimización, comparación escenarios, RBAC, multiempresa, auditoría, explicabilidad, rechazo.

```
npm run build — PASS
```

---

## Veredicto

| Criterio | Estado |
|----------|--------|
| MOTOR OPTIMIZACIÓN | PASS |
| PRIORIZACIÓN | PASS |
| PORTAFOLIO | PASS |
| RESTRICCIONES | PASS |
| OBJETIVOS | PASS |
| APRENDIZAJE 1260 | PASS |
| RECOMENDACIONES | PASS |
| COMPARACIÓN ESCENARIOS | PASS |
| DEPENDENCIAS | PASS |
| EXPLICABILIDAD | PASS |
| REOPTIMIZACIÓN | PASS |
| CONTROL HUMANO | PASS |
| SIN SOLUCIÓN FACTIBLE | PASS |
| TRAZABILIDAD | PASS |
| RBAC | PASS |
| MULTIEMPRESA | PASS |
| AUDITORÍA | PASS |
| UI EN ESPAÑOL | PASS |
| ALEMBIC | PASS |
| FRONTEND | PASS |
| P0 | 0 |
| P1 | 0 |
| P2 | 0 |

**VEREDICTO: APTO**

**NO MERGE.**

---

## Resumen ejecutivo

```
EMPLEADOS IA — BLOQUE 1290 TERMINADO

RAMA:
cursor/1290-optimizacion-recomendaciones

BASE:
6a6cfbc

HEAD:
<SHA>

MOTOR OPTIMIZACIÓN:
PASS

PRIORIZACIÓN:
PASS

PORTAFOLIO:
PASS

RESTRICCIONES:
PASS

OBJETIVOS:
PASS

APRENDIZAJE 1260:
PASS

RECOMENDACIONES:
PASS

COMPARACIÓN ESCENARIOS:
PASS

DEPENDENCIAS:
PASS

EXPLICABILIDAD:
PASS

REOPTIMIZACIÓN:
PASS

CONTROL HUMANO:
PASS

SIN SOLUCIÓN FACTIBLE:
PASS

TRAZABILIDAD:
PASS

RBAC:
PASS

MULTIEMPRESA:
PASS

AUDITORÍA:
PASS

UI EN ESPAÑOL:
PASS

ALEMBIC:
PASS

ALEMBIC HEAD:
1290a1b2c3d4e

TESTS:
13 passed, 0 failed

FRONTEND:
PASS

P0:
0

P1:
0

P2:
0

VEREDICTO:
APTO
```
