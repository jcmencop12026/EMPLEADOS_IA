# EMPLEADOS IA — MB-12 Mesa de Ayuda y Soporte

**Rama:** `cursor/mesa-ayuda-soporte-empresarial`  
**Base:** `cursor/fase2-central-integracion` @ `3049cc586d60fecfe18c035e94e5ea412b649270`  
**HEAD:** `562e255c29ffe28d15cb424b0563f230b39266b1`  
**Alcance:** Mesa de ayuda empresarial conectada al ecosistema existente (notificaciones 820, RBAC, multiempresa). Sin duplicar Centro de Control, Mi trabajo, auditoría ni automatizaciones.

---

## Componentes implementados

### Backend
| Archivo | Rol |
|---------|-----|
| `backend/app/support_enums.py` | Tipos, estados, prioridad/impacto/urgencia, SLA |
| `backend/app/support_models.py` | `SupportCase`, `SupportCaseHistory`, `SupportCaseComment`, `SupportSlaPolicy`, `SupportAutoDedup` |
| `backend/app/schemas_support.py` | DTOs Pydantic |
| `backend/app/services/support_service.py` | CRUD, SLA, dedup automático (4 h), historial, sanitización, contratos |
| `backend/app/routers/soporte.py` | API `/api/soporte/*` |
| `backend/alembic/versions/1390a1b2c3d4e_mesa_ayuda_soporte_1390.py` | Migración (down: `1330b1b2c3d4f`) |
| `backend/app/permissions.py` | `support.view/create/assign/update/resolve/close/admin` |
| `backend/app/notifications.py` | Eventos 820: `SUPPORT_CASE_*`, `SUPPORT_SLA_WARNING` |
| `backend/app/main.py` | Registro modelos + router |

### Frontend
| Archivo | Rol |
|---------|-----|
| `frontend/src/pages/SoportePage.tsx` | Grilla, filtros, creación |
| `frontend/src/pages/SoporteCasoDetailPage.tsx` | Detalle, asignar, resolver, comentarios, historial |
| `frontend/src/App.tsx` | Rutas `/soporte`, `/soporte/casos/:caseId` |
| `frontend/src/AppShell.tsx` | Menú «Mesa de Ayuda» |
| `frontend/src/api.ts` | Cliente API soporte |
| `frontend/src/auth/permissions.ts` | Guard ruta soporte |

### Tests
- `tests/test_mesa_ayuda_mb12.py` — 14 casos (crear, asignar, estado, resolver, cerrar, SLA, dedup, comentarios, historial, correlation_id, multiempresa, RBAC, SUPERADMIN, secretos, idempotencia)

---

## API principal

| Método | Ruta | Permiso | Descripción |
|--------|------|---------|-------------|
| GET | `/api/soporte/casos` | `support.view` o `support.create` (solo míos) | Listado con filtros |
| POST | `/api/soporte/casos` | `support.create` | Creación manual |
| POST | `/api/soporte/casos/auto` | `support.admin` | Origen automático con dedup |
| GET | `/api/soporte/casos/{id}` | Propietario o `support.view` | Detalle + historial + comentarios |
| POST | `/api/soporte/casos/{id}/asignar` | `support.assign` | Asignación manual |
| PATCH | `/api/soporte/casos/{id}/estado` | `support.update` | Cambio de estado |
| POST | `/api/soporte/casos/{id}/resolver` | `support.resolve` | Resolución |
| POST | `/api/soporte/casos/{id}/cerrar` | `support.close` | Cierre (idempotente) |
| POST | `/api/soporte/casos/{id}/comentarios` | Solicitante o agente | Comentarios |
| POST | `/api/soporte/sla` | `support.admin` | Política SLA por org/prioridad |
| GET | `/api/soporte/contrato/mi-trabajo` | Autenticado | Contrato portable Mi trabajo |
| GET | `/api/soporte/contrato/centro-control` | `support.view` | Contrato portable Centro de Control |
| GET | `/api/soporte/tipos` | Público autenticado | Catálogo tipos/estados/prioridades |

---

## Contratos portables (sin cablear CC ni Mi trabajo)

### Mi trabajo — `GET /api/soporte/contrato/mi-trabajo`
```json
{
  "casos_asignados": 3,
  "casos_vencidos": 1,
  "casos_accion_requerida": 2,
  "endpoint": "/api/soporte/contrato/mi-trabajo"
}
```

### Centro de Control — `GET /api/soporte/contrato/centro-control`
```json
{
  "casos_abiertos": 12,
  "casos_criticos": 2,
  "casos_vencidos": 1,
  "tiempo_medio_respuesta_min": 45.2,
  "tiempo_medio_resolucion_min": 180.5,
  "principales_categorias": [{"categoria": "INCIDENTE", "cantidad": 5}],
  "endpoint": "/api/soporte/contrato/centro-control"
}
```

---

## Origen automático y deduplicación

`create_case_auto(org, payload)` deduplica por `SHA256(org|origen_tipo|origen_id)` con ventana de **4 horas**.  
Orígenes previstos: `continuity_incident`, `integration_degraded`, `automation_failed`, `auth_failure`, `service_degraded`.

**No** se cierra automáticamente un incidente técnico al recuperarse la plataforma.

---

## Notificaciones 820 reutilizadas

| Evento | Cuándo |
|--------|--------|
| `SUPPORT_CASE_ASSIGNED` | Asignación a responsable |
| `SUPPORT_CASE_STATUS` | Cambio importante de estado |
| `SUPPORT_CASE_RESOLVED` | Resolución |
| `SUPPORT_CASE_COMMENT` | Solicitud de información |
| `SUPPORT_SLA_WARNING` | SLA próximo a vencer |

---

## Receta exacta — port selectivo a Fase2

Desde rama destino `cursor/fase2-central-integracion` (o integración posterior):

```bash
# 1. Traer solo archivos MB-12 (ajustar SHA al HEAD de mesa-ayuda)
git fetch origin cursor/mesa-ayuda-soporte-empresarial
SHA=562e255

git checkout $SHA -- \
  backend/app/support_enums.py \
  backend/app/support_models.py \
  backend/app/schemas_support.py \
  backend/app/services/support_service.py \
  backend/app/routers/soporte.py \
  backend/alembic/versions/1390a1b2c3d4e_mesa_ayuda_soporte_1390.py \
  tests/test_mesa_ayuda_mb12.py \
  frontend/src/pages/SoportePage.tsx \
  frontend/src/pages/SoporteCasoDetailPage.tsx

# 2. Aplicar parches de cableado (revisar conflictos):
#    backend/app/main.py          — import support_models + include_router(soporte)
#    backend/app/permissions.py   — SUPPORT_PERMISSIONS en roles admin/operator/viewer
#    backend/app/notifications.py — eventos SUPPORT_*
#    backend/alembic/migration_ledger.json — baseline_head 1390a1b2c3d4e
#    backend/scripts/schema_repair.py      — HEAD_REVISION 1390a1b2c3d4e
#    frontend/src/App.tsx, AppShell.tsx, api.ts, auth/permissions.ts

# 3. Migración
cd backend && alembic upgrade head

# 4. Verificación
pytest tests/test_mesa_ayuda_mb12.py -v
cd ../frontend && npm run build
```

**Conflictos probables:** `permissions.py`, `main.py`, `migration_ledger.json` si Fase2 avanzó más allá de `1330b1b2c3d4f`. Resolver manteniendo down_revision coherente con el head actual de Fase2.

---

## Verificación

| Área | Resultado |
|------|-----------|
| CASOS | PASS — 14/14 tests |
| INCIDENTES | PASS |
| SOLICITUDES | PASS |
| SLA | PASS |
| ASIGNACIÓN | PASS |
| HISTORIAL | PASS |
| NOTIFICACIONES 820 | REUTILIZADAS |
| CONTRATO MI TRABAJO | PREPARADO |
| CONTRATO CENTRO CONTROL | PREPARADO |
| MULTIEMPRESA | PASS |
| RBAC | PASS |
| SUPERADMIN | PASS |
| SECRETOS | PASS |
| FRONTEND | PASS — `npm run build` OK |
| MIGRACIONES | 1 (`1390a1b2c3d4e`) |

**P0:** 0 | **P1:** 0 | **P2:** 0

**VEREDICTO:** APTO PARA PORTAR

**NO MERGE** a Fase2 central, main ni V1 — entrega en rama aislada.
