# EMPLEADOS IA — Mesa de Ayuda integrada con Mi Trabajo

**Rama:** `cursor/mesa-ayuda-integracion-mi-trabajo`  
**HEAD:** `632be4a` *(actualizar tras commit doc)*  
**Base MB-12:** `6d40aad52032d6a4f6aaab66a5d50e743d8dbc76`  
**Base Mi Trabajo:** `cursor/bandeja-trabajo-humano-unificada` @ `40e76bc` (núcleo)  
**Migración:** `1391a1b2c3d4e` (sin cambio — agregación únicamente)

---

## Objetivo

Convertir el contrato `GET /api/soporte/contrato/mi-trabajo` en **integración funcional real** con la bandeja existente:

- `GET /api/trabajo/items`
- `GET /api/trabajo/resumen`

Mesa de Ayuda es ahora una **fuente** de Mi Trabajo. No se creó bandeja, motor de tareas, workflow ni tabla genérica nueva.

---

## Arquitectura

```
SupportCase (MB-12)
        ↓
support_service.compute_sla_estado / sanitize_text
        ↓
trabajo_service.collect_items()  ← bloque soporte + dedup 820
        ↓
GET /api/trabajo/items | /resumen
        ↓
TrabajoPage.tsx (/trabajo)  →  navegación /soporte/casos/:id
```

**Centro de Control:** sin modificar — `GET /api/soporte/contrato/centro-control` permanece portable.

**Auditor:** sin integrar (General unirá fuentes).

---

## Fuente agregada

| Campo | Valor |
|-------|-------|
| `modulo` | `soporte` |
| `metadata.origen` | `Mesa de Ayuda` |
| Tipos mínimos | `soporte_caso`, `soporte_asignacion`, `soporte_sla_riesgo`, `soporte_sla_vencido` |

### Visibilidad (casos accionables)

| Estado | Quién lo ve en Mi Trabajo |
|--------|---------------------------|
| `NUEVO` sin responsable | Usuarios con `support.assign` / `support.admin` |
| `ASIGNADO`, `EN_PROCESO`, `PENDIENTE_TERCERO` | Responsable asignado |
| `PENDIENTE_USUARIO` | Solicitante |
| `RESUELTO`, `CERRADO`, `CANCELADO` | **Excluidos** |

### SLA

Reutiliza `support_service.compute_sla_estado` — sin segundo motor.  
Metadata: `sla_estado`, `sla_restante_minutos`, `fecha_limite`, `vencida`.

Prioridad de tipo: SLA vencido/riesgo prevalece sobre asignación.

### Deduplicación 820

Si existe ítem de soporte accionable para un `case_id`, se suprime la notificación 820 asociada (`source_type=support_case`, tipos `SUPPORT_*`, `correlation_id` coincidente).

### RBAC

- Ver Mi Trabajo **no** concede `support.resolve`, `support.assign`, etc.
- Acciones en bandeja: solo `ver` → `/soporte/casos/:id`
- Permisos de acceso a bandeja ampliados con `support.view`, `support.create`, `support.assign`

### Filtros

- `modulo=soporte` — origen Mesa de Ayuda
- `case_id=<uuid>` — caso específico
- Filtros existentes: `tipo`, `prioridad`, `estado`, `responsable_id`, `vencimiento`

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `backend/app/services/trabajo_service.py` | Bloque soporte, dedup 820, filtros `case_id` |
| `backend/app/routers/trabajo.py` | Query param `case_id` |
| `frontend/src/pages/TrabajoPage.tsx` | Labels Mesa de Ayuda |
| `frontend/src/App.tsx` | Permisos soporte en ruta `/trabajo` |
| `frontend/src/auth/permissions.ts` | Permisos soporte en `/trabajo` |
| `tests/test_mesa_ayuda_integracion_mi_trabajo.py` | 20 tests integración |

**Cherry-pick base Mi Trabajo:** commit `40e76bc` (bandeja unificada).

---

## Receta portable para General

```bash
git fetch origin cursor/mesa-ayuda-integracion-mi-trabajo
SHA=<HEAD_INTEGRACION>

# 1. MB-12 completo (si no está ya)
git checkout $SHA -- \
  backend/app/support_*.py \
  backend/app/schemas_support.py \
  backend/app/services/support_service.py \
  backend/app/routers/soporte.py \
  backend/alembic/versions/1391a1b2c3d4e_mesa_ayuda_soporte_mb12.py \
  frontend/src/pages/Soporte*.tsx \
  tests/test_mesa_ayuda_mb12.py

# 2. Mi Trabajo + integración
git checkout $SHA -- \
  backend/app/services/trabajo_service.py \
  backend/app/routers/trabajo.py \
  backend/app/schemas_trabajo.py \
  frontend/src/pages/TrabajoPage.tsx \
  tests/test_bandeja_trabajo_humano.py \
  tests/test_mesa_ayuda_integracion_mi_trabajo.py

# 3. Cableado (revisar conflictos)
# main.py, App.tsx, AppShell.tsx, api.ts, auth/permissions.ts, styles.css

pytest tests/test_mesa_ayuda_mb12.py tests/test_mesa_ayuda_integracion_mi_trabajo.py \
  tests/test_bandeja_trabajo_humano.py tests/test_migration_control.py -q
cd frontend && npm run build
```

**Nota:** General integra Mi Trabajo en Fase2 central por separado; esta rama asume coexistencia de ambos módulos.

---

## Verificación

| Área | Resultado |
|------|-----------|
| Integración MB-12 | 20/20 PASS |
| MB-12 regresión | 14/14 PASS |
| Mi Trabajo regresión | 6/6 PASS |
| migration_control | 7/7 PASS |
| Frontend build | PASS |
| Migración nueva | NO |
| Alembic head | `1391a1b2c3d4e` (1) |
| Centro Control | NO MODIFICADO |
| Auditor | NO MODIFICADO |

**P0:** 0 | **P1:** 0 | **P2:** 0

**VEREDICTO:** APTO PARA PORTAR
