# CURSOR — Bandeja unificada de trabajo humano

## Identificación

| Campo | Valor |
|-------|-------|
| Rama | `cursor/bandeja-trabajo-humano-unificada` |
| BASE SHA | `b3046cc95299f7e26d3f0bcd557fa995069a0609` |
| Descripción base | `feat(vistas): identidad, seguridad y accesos 1300/1370/1380` (antes de control visual) |

## Objetivo

Agregar `/trabajo` (Mi trabajo) como **capa de agregación** sobre capacidades existentes, sin nuevo motor de workflow, alertas ni duplicar 810C/820 ni modificar Centro de Control.

## Fuentes reutilizadas

| Dominio | Fuente backend | Permiso vista |
|---------|----------------|---------------|
| Aprobaciones operaciones | `approval_requests` (PENDING) | `operations.view` |
| Ejecuciones fallidas / vencidas | `work_plans` | `operations.view` |
| Automatizaciones fallidas | `automation_runs` FAILED | `automation.view` |
| Oportunidades pendientes aprobación | `opportunities` PENDIENTE_APROBACION | `oportunidades.view` |
| Alertas continuidad | `cont_alertas` no resueltas | `continuidad.view` |
| Integraciones degradadas | `integration_service.list_connectors_overview` (circuit_open) | `integraciones.view` |
| Presupuesto IA / FinOps | `FinOpsBudget` + `finops_service.budget_state` | `finops.view` |
| Notificaciones 820 | `notifications` NEW (visibilidad igual que `/api/notifications`) | `notification.view` |

**No reutilizado en base actual:** recomendaciones 1290 `PENDIENTE_EJECUCION_HUMANA` (modelos/servicio no presentes en `b3046cc`).

**Automatizaciones 810C:** no se duplica el scheduler; solo se listan runs FAILED ya persistidos.

**Notificaciones 820:** reutilizadas vía tabla y reglas de visibilidad existentes; la bandeja no reemplaza `/notificaciones`.

## Endpoints nuevos (agregación)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/trabajo/items` | Lista unificada con filtros |
| GET | `/api/trabajo/resumen` | Contadores: pendientes, vencidas, requieren aprobación |

Parámetros de filtro en `items`: `q`, `estado`, `prioridad`, `tipo`, `modulo`, `responsable_id`, `vencimiento` (`vencida` \| `proxima` \| `sin_limite`), `requires_action`, `sort`, `sort_dir`, `organization_id` (SuperAdmin).

## Agregación implementada

- Servicio: `backend/app/services/trabajo_service.py`
- Router: `backend/app/routers/trabajo.py`
- Esquemas: `backend/app/schemas_trabajo.py`
- Ítem unificado con: tipo, asunto, módulo, organización, prioridad, estado dominio + estado presentación, responsable, fechas, antigüedad, `correlation_id`, `requires_action` vs informativa, semántica (`HECHO` / `INFERENCIA` / `RECOMENDACION`), acciones RBAC.

Estados de presentación (no reemplazan estado dominio): `PENDIENTE`, `EN_CURSO`, `REQUIERE_APROBACION`, `VENCIDA`, `COMPLETADA`, `FALLIDA`.

## Deduplicación

1. **APPROVAL_REQUIRED (820)** + **aprobación operaciones** con mismo `approval_id` en metadata → solo ítem `aprobacion`.
2. **Notificación** con `source_type=opportunity` y oportunidad en `PENDIENTE_APROBACION` → solo ítem `oportunidad_aprobacion`.

Validado en `tests/test_bandeja_trabajo_humano.py::test_trabajo_deduplicacion_aprobacion_notificacion`.

## RBAC

- Acceso bandeja: al menos uno de los permisos de vista listados arriba.
- Acciones en UI/API existentes:
  - Aprobar/rechazar operaciones → `operations.approve`
  - Aprobar/rechazar oportunidad → `oportunidades.approve`
  - Leer notificación → `notification.view`
  - Atender notificación → `notification.acknowledge`
- Ver no implica ejecutar: botones deshabilitados sin permiso.

## Multiempresa

- Todos los queries filtran por `organization_id` resuelto vía `control_center_service.resolve_organization_id`.
- SuperAdmin con `platform.organization.view` puede `organization_id` explícito.
- Test: `test_trabajo_multiempresa_aislamiento`.

## Rutas frontend

| Ruta | Componente |
|------|------------|
| `/trabajo` | `TrabajoPage.tsx` |

Navegación: menú Operaciones → **Mi trabajo** (contador pendientes vía `/api/trabajo/resumen`, refresh 60s).

Trazabilidad: enlace a `/integraciones/trazabilidad?cid=` cuando hay `correlation_id`.

## Migración nueva

**NO.** Solo agregación sobre tablas y servicios existentes.

## Pruebas

```bash
python3 -m pytest tests/test_bandeja_trabajo_humano.py -q
cd frontend && npm run build
```

Resultado en entorno de desarrollo: 6 tests PASS, frontend build PASS.

## Recorrido visual preparado

1. Login
2. Operaciones → Mi trabajo (`/trabajo`)
3. Filtro «Solo requiere acción» / estado «Requiere aprobación»
4. Seleccionar fila → panel detalle (evidencia, correlation_id)
5. Acción permitida (aprobar / leer / navegar)
6. Volver a grilla → estado actualizado
7. Trazabilidad si hay correlation_id

## Receta port a Fase2 central

1. Cherry-pick o merge de rama `cursor/bandeja-trabajo-humano-unificada` sobre rama Fase2 compatible (misma línea que `b3046cc` o posterior sin conflictos).
2. Archivos a portar:
   - `backend/app/services/trabajo_service.py`
   - `backend/app/routers/trabajo.py`
   - `backend/app/schemas_trabajo.py`
   - `backend/app/main.py` (include router)
   - `frontend/src/pages/TrabajoPage.tsx`
   - `frontend/src/api.ts`, `App.tsx`, `AppShell.tsx`, `auth/permissions.ts`, `styles.css`
   - `tests/test_bandeja_trabajo_humano.py`
3. Si Fase2 incluye 1290: extender `collect_items()` con recomendaciones `PENDIENTE_EJECUCION_HUMANA` (solo navegación, sin marcar ejecutada desde bandeja).
4. Verificar permisos seed en Fase2 (sin ampliar privilegios).
5. Ejecutar tests bandeja + build frontend.

## Commits portables (tras push)

Ver `git log cursor/bandeja-trabajo-humano-unificada` desde BASE.

---

## SALIDA FINAL

```
EMPLEADOS IA — BANDEJA DE TRABAJO HUMANO TERMINADA

BASE:
b3046cc95299f7e26d3f0bcd557fa995069a0609

RAMA:
cursor/bandeja-trabajo-humano-unificada

HEAD:
40e76bcb1f1208562af83902c3dcf0fb683bd299

NOTIFICACIONES 820:
REUTILIZADAS

AUTOMATIZACIONES 810C:
REUTILIZADAS (runs FAILED persistidos)

TAREAS:
PASS

ALERTAS:
PASS

APROBACIONES:
PASS

PENDIENTE HUMANO 1290:
NO DISPONIBLE EN BASE

DEDUPLICACIÓN:
PASS

CORRELATION_ID:
PASS

MULTIEMPRESA:
PASS

RBAC:
PASS

SUPERADMIN:
PASS (organization_id query)

SECRETOS:
PASS (sin exposición en UI)

FRONTEND BUILD:
PASS

BACKEND:
PASS

MIGRACIÓN NUEVA:
NO

REGRESIÓN:
tests/test_bandeja_trabajo_humano.py 6 passed

RECORRIDO VISUAL:
PREPARADO

RECETA PORT FASE2:
PREPARADA

P0:
0

P1:
1 (1290 pendiente humano cuando exista en Fase2)

P2:
0

FASE2 CENTRAL:
NO MODIFICADA

MAIN:
NO

V1:
NO

VEREDICTO:
APTO PARA PORTAR
```

**EMPLEADOS IA. Bandeja unificada de trabajo humano terminada.**
