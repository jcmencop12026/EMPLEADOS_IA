# EMPLEADOS_IA — BLOQUE 1260 APRENDIZAJE, RETROALIMENTACIÓN Y REPRIORIZACIÓN

**Agente:** A  
**Rama:** `cursor/1260-aprendizaje-repriorizacion`  
**Base:** `062db083ab9439e74f766ea570cdfbddb1af49e1` (`062db08` — `cursor/1250a-convergencia-post-v1`)  
**Alembic HEAD:** `1260a1b2c3d4e`  
**Modo:** POST-V1 independiente — sin tocar V1, PR #32, Docker ni `DATABASE_URL`

---

## Objetivo

Motor de aprendizaje operacional trazable que cierra el ciclo:

**SEÑAL → DIAGNÓSTICO → OPORTUNIDAD → DECISIÓN → EJECUCIÓN → RESULTADO → IMPACTO → VALOR → APRENDIZAJE → NUEVA PRIORIZACIÓN**

Sin auto-modificación silenciosa de código ni modelos. Sin proveedor IA (reglas determinísticas).

---

## Entidades (referencias, no duplicación)

| Entidad | Tabla | Descripción |
|---------|-------|-------------|
| `CicloAprendizaje` | `ciclos_aprendizaje` | Esperado vs real, desviaciones, prioridad |
| `Retroalimentacion` | `retroalimentaciones` | Lecciones y calidad de recomendación |
| `Recalibracion` | `recalibraciones` | Propuesta con control humano |
| `PatronAprendizaje` | `patrones_aprendizaje` | Patrones repetidos por organización |
| `AprendizajeAuditoria` | `aprendizaje_auditoria` | Historial auditable del bloque |

Referencias a entidades existentes: `opportunities`, `work_plans`, `proactive_signals`, `diagnostics`, `opportunity_valuations`, `lineas_base`.

---

## Control humano

Estados de recalibración: **SUGERIDA → APROBADA / RECHAZADA → APLICADA**

Registra: quién, cuándo, campo, valor anterior/nuevo, justificación, evidencia.

No se aplican cambios críticos sin aprobación explícita.

---

## API (`/api/aprendizaje`)

| Método | Ruta | Permiso |
|--------|------|---------|
| GET | `/ciclos` | `aprendizaje.view` |
| GET | `/ciclos/{id}` | `aprendizaje.view` |
| POST | `/ciclos` | `aprendizaje.evaluate` |
| POST | `/ciclos/{id}/evaluar` | `aprendizaje.evaluate` |
| GET | `/desviaciones` | `aprendizaje.view` |
| GET | `/recalibraciones` | `aprendizaje.view` |
| POST | `/recalibraciones/{id}/aprobar` | `aprendizaje.approve` |
| POST | `/recalibraciones/{id}/rechazar` | `aprendizaje.approve` |
| POST | `/recalibraciones/{id}/aplicar` | `aprendizaje.recalibrate` |
| GET | `/patrones` | `aprendizaje.view` |
| GET | `/historial` | `aprendizaje.view` |

---

## Repriorización explicable

Fórmula documentada en `explicacion_prioridad_json`:

```
prioridad = (impacto + valor + urgencia + confianza - riesgo - costo) × factor_desviación
```

Componentes y factores almacenados para auditoría. No es caja negra.

---

## Permisos RBAC

- `aprendizaje.view`
- `aprendizaje.evaluate`
- `aprendizaje.recalibrate`
- `aprendizaje.approve`

Admin/superadmin: todos. Operator: view/evaluate/recalibrate. Viewer: solo view.

---

## UI (español)

- `/aprendizaje` — listado ciclos y patrones
- `/aprendizaje/:cicloId` — detalle: esperado/real, desviaciones, recalibraciones, historial

Menú: **Análisis y control → Aprendizaje**

---

## Archivos principales

| Archivo | Rol |
|---------|-----|
| `backend/app/learning_models.py` | Modelos ORM |
| `backend/app/services/learning_service.py` | Lógica de negocio |
| `backend/app/routers/aprendizaje.py` | API REST |
| `backend/alembic/versions/1260a1b2c3d4e_*.py` | Migración |
| `frontend/src/pages/AprendizajePage.tsx` | Vista listado |
| `frontend/src/pages/AprendizajeDetailPage.tsx` | Vista detalle |
| `tests/test_aprendizaje_1260.py` | Pruebas focales |

---

## Pruebas ejecutadas

```
tests/test_aprendizaje_1260.py — 6 passed, 0 failed (3.81s)
```

Cubre: ciclo completo, control humano, rechazo, RBAC viewer, multiempresa, sin IA, auditoría.

```
npm run build — PASS (1.09s)
```

---

## Veredicto

| Criterio | Estado |
|----------|--------|
| CICLO APRENDIZAJE | PASS |
| ESPERADO VS REAL | PASS |
| DESVIACIONES | PASS |
| RETROALIMENTACIÓN | PASS |
| PATRONES | PASS |
| RECALIBRACIÓN | PASS |
| REPRIORIZACIÓN | PASS |
| EXPLICABILIDAD | PASS |
| CONTROL HUMANO | PASS |
| RBAC | PASS |
| MULTIEMPRESA | PASS |
| AUDITORÍA | PASS |
| UI | PASS |
| ALEMBIC | PASS (`1260a1b2c3d4e`) |
| FRONTEND | PASS |
| P0 | 0 |
| P1 | 0 |
| P2 | 0 |

**VEREDICTO: APTO**

**NO MERGE.**

---

## Resumen ejecutivo

```
EMPLEADOS IA — BLOQUE 1260 TERMINADO

RAMA:
cursor/1260-aprendizaje-repriorizacion

BASE:
062db08

HEAD:
<ver git rev-parse HEAD tras commit>

CICLO APRENDIZAJE:
PASS

ESPERADO VS REAL:
PASS

DESVIACIONES:
PASS

RETROALIMENTACIÓN:
PASS

PATRONES:
PASS

RECALIBRACIÓN:
PASS

REPRIORIZACIÓN:
PASS

EXPLICABILIDAD:
PASS

CONTROL HUMANO:
PASS

RBAC:
PASS

MULTIEMPRESA:
PASS

AUDITORÍA:
PASS

UI:
PASS

ALEMBIC:
PASS

TESTS:
6 passed, 0 failed

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
