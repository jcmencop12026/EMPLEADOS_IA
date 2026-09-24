# EMPLEADOS_IA — BLOQUE 1100 — CIERRE OPERATIVO DE OPORTUNIDADES Y EJECUCIÓN

**Agente:** D
**Base:** `4c03cbe` (certificación V1 R2 PostgreSQL)
**Rama:** `cursor/1100-cierre-operativo-oportunidades`
**Alcance:** B1.1 cierre UI oportunidades + B1.4 cadena de ejecución
**Restricción:** Sin tocar `cursor/v1-integracion-final` ni PR #32

---

## Objetivo cumplido

Completar desde la interfaz el ciclo operativo de oportunidades reutilizando estados, modelos y API existentes del módulo 1030, sin rediseño ni ampliación de alcance.

---

## Cambios implementados

### Backend (mínimo)

| Archivo | Cambio |
|---------|--------|
| `backend/app/services/proactive_service.py` | `get_full_trace()` enriquecido: seguimiento con `fecha`, `responsable_id`, `bloqueo`; transiciones con `actor_id` y `fecha` |

### Frontend

| Archivo | Cambio |
|---------|--------|
| `frontend/src/api.ts` | Tipos `OpportunityTrackingItem`, `OpportunityTrace`; funciones `addOpportunityTracking`, `registerOpportunityResult`, `activateOpportunity(autoExecute)` |
| `frontend/src/hooks/usePermissions.ts` | Hook RBAC desde sesión |
| `frontend/src/pages/OportunidadDetailPage.tsx` | UI completa: pestañas (resumen, evidencia, seguimiento, resultado, ejecución, trazabilidad, finops), cadena operativa, aprobación/rechazo, seguimiento, resultado/materialización, aprobaciones de plan |
| `frontend/src/pages/OportunidadesPage.tsx` | Permisos, estados ampliados, priorizar, carga |
| `frontend/src/styles.css` | Estilos compactos: cadena, badges, formularios, paneles |

### Pruebas

| Archivo | Cobertura |
|---------|-----------|
| `tests/test_bloque_1100_oportunidades_operativo.py` | Seguimiento API, resultado/materialización, aprobación/rechazo, trazabilidad, cadena oportunidad→ejecución→resultado, aislamiento multiempresa, RBAC viewer |

---

## Funcionalidades UI (B1.1)

- Consulta y detalle de oportunidad
- Evidencia, valor esperado, prioridad, responsable IA, estado
- Seguimiento con fecha, acción, observación/bloqueo, responsable (vía trazabilidad)
- Registro de resultado y materialización (campos existentes)
- Aprobación y rechazo humano (sin autoaprobación)
- Cierre/descarte según reglas backend existentes

## Cadena de ejecución (B1.4)

Panel visual: Oportunidad → Acción → Aprobación → Plan → Ejecución → Resultado → Materialización, con enlaces a `/operaciones/{work_plan_id}` y `/ejecuciones/{work_plan_id}`.

---

## Verificación

### Pruebas focales (bloque 1100)

```
7 passed in 5.85s
```

### Regresión oportunidades 1030 + bloque 1100

```
45 passed in 29.41s
```

### Frontend build

```
vite build — PASS (82 modules, 0 errors)
```

---

## SALIDA

```
EMPLEADOS_IA — BLOQUE 1100 TERMINADO

RAMA:
cursor/1100-cierre-operativo-oportunidades

BASE:
4c03cbe

HEAD:
<commit tras push>

CIERRE OPORTUNIDADES UI:
PASS

SEGUIMIENTO:
PASS

RESULTADO:
PASS

MATERIALIZACIÓN:
PASS

APROBACIÓN/RECHAZO:
PASS

TRAZABILIDAD:
PASS

RBAC:
PASS

MULTIEMPRESA:
PASS

TESTS:
45 passed (1030 + 1100 focal)

FRONTEND:
PASS

VEREDICTO:
APTO

NO MERGE
```

---

## No modificado (según instrucciones)

- PostgreSQL harness
- Proveedor OpenAI / Ollama
- Docker
- FinOps B1.2/B1.3
- Línea base / pricing / análisis externo
- Rama `cursor/v1-integracion-final` / PR #32
