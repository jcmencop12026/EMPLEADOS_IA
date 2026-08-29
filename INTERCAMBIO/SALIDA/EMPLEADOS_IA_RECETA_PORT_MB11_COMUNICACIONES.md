# EMPLEADOS IA — Receta de port MB-11 Comunicaciones

Documento operativo para **General** al integrar MB-11 sobre la cabeza Alembic real del tramo central.

---

## 1. Prerrequisitos

| Requisito | Detalle |
|-----------|---------|
| Tablas base | `organizations`, `users` (FK de MB-11) |
| Infraestructura | RBAC 840, auditoría, event bus, `gateway/secrets`, `integration_security.validate_external_url` |
| 820 | Motor de notificaciones activo (no sustituir) |
| 810C | `automation_scheduler._tick()` activo (no crear scheduler nuevo) |
| Cabeza Alembic | Una sola cabeza antes de aplicar MB-11 |

**NO requiere:** Mi Trabajo, Mesa de Ayuda, Centro de Control, Auditor, Fábrica, MB-07, Conocimiento.

---

## 2. Commit funcional único

| SHA | Mensaje |
|-----|---------|
| `e3fb206e9a2dcb25b0014a249bc593f3ecae310e` | `feat(mb-11): centro de información y comunicaciones` |

General puede portar el **commit completo** o aplicar el diff archivo a archivo. La documentación (`INTERCAMBIO/SALIDA/*.md`) es opcional para el runtime.

---

## 3. Orden recomendado de integración

1. **Resolver conflictos en archivos compartidos** (ver §6).
2. **Copiar archivos nuevos MB-11** (backend + frontend + tests + migración).
3. **Aplicar wiring** en `main.py`, `permissions.py`, `automation_scheduler.py`.
4. **Reparentar migración** `1341a1b2c3d4e` → `down_revision = <HEAD_REAL_CENTRAL>`.
5. Actualizar `migration_ledger.json` y `schema_repair.py` HEAD.
6. `alembic upgrade head` (una sola cabeza).
7. `bootstrap_permissions` o re-seed de permisos `communications.*`.
8. Tests focales (§8).
9. `npm run build` frontend.
10. Recorrido UI `/comunicaciones`.

---

## 4. Migración y reparent

### Estado actual MB-11

```
revision     = 1341a1b2c3d4e
down_revision = 1340a1b2c3d4e   ← válido solo en base Tramo 4
```

### Reparent obligatorio al portar

Editar `backend/alembic/versions/1341a1b2c3d4e_centro_comunicaciones_mb11.py`:

```python
down_revision = "<HEAD_REAL_DEL_TRAMO_CENTRAL>"
```

**Verificar antes de upgrade:**

- `organizations` y `users` existen (FK).
- `revision_id` `1341a1b2c3d4e` no colisiona con otra revisión del repo destino.
- `alembic heads` → exactamente **1** cabeza tras el reparent.

### Inventario revision_id (rama MB-11)

57 revisiones en `backend/alembic/versions/`. `1341a1b2c3d4e` aparece **una sola vez**.

**No colisiona con:** `1390`, `1391`, `1400`, `1507`, `6b06`, `14b1c2d3e4f5` (ausentes en esta rama).

---

## 5. Archivos nuevos (copiar tal cual)

```
backend/app/communications_enums.py
backend/app/communications_models.py
backend/app/schemas_communications.py
backend/app/services/communications_service.py
backend/app/routers/comunicaciones.py
backend/alembic/versions/1341a1b2c3d4e_centro_comunicaciones_mb11.py
frontend/src/pages/ComunicacionesPage.tsx
tests/test_mb11_comunicaciones.py
```

---

## 6. Archivos compartidos — conflictos previsibles

| Archivo | Cambio MB-11 | Riesgo |
|---------|--------------|--------|
| `backend/app/main.py` | import models, router, `register_communications_handlers()` | **ALTO** — muchos agentes tocan main |
| `backend/app/permissions.py` | `COMMUNICATIONS_PERMISSIONS` + ALL_PERMISSIONS + roles | **ALTO** |
| `backend/app/services/automation_scheduler.py` | 1 línea: `process_scheduled_and_retries` | **MEDIO** |
| `backend/app/notifications.py` | `COMMUNICATION_SENT` en SUPPORTED_EVENTS | **BAJO** |
| `backend/alembic/migration_ledger.json` | baseline_head → 1341 | **ALTO** — reparent manual |
| `backend/scripts/schema_repair.py` | HEAD_REVISION | **MEDIO** |
| `frontend/src/App.tsx` | ruta `/comunicaciones` | **MEDIO** |
| `frontend/src/AppShell.tsx` | ítem menú | **BAJO** — General puede reubicar |
| `frontend/src/api.ts` | funciones API | **MEDIO** |
| `frontend/src/auth/permissions.ts` | permiso ruta | **BAJO** |
| `tests/conftest.py` | import communications_models | **BAJO** |

### Resolución manual típica en `main.py`

```python
from app import communications_models  # noqa: F401
from app.routers import ..., comunicaciones
from app.services.communications_service import register_communications_handlers

# lifespan:
register_communications_handlers()

# routers:
app.include_router(comunicaciones.router)
```

### Resolución en `automation_scheduler.py`

Al final del bucle `due` en `_tick()`, antes de `finally`:

```python
communications_service.process_scheduled_and_retries(db)
```

---

## 7. Tests después de cada etapa

| Etapa | Comando | Abortar si |
|-------|---------|------------|
| Post-merge archivos | `pytest tests/test_mb11_comunicaciones.py -q` | cualquier FAIL |
| Post-migración | `alembic upgrade head && alembic heads` | heads > 1 |
| Roundtrip SQLite | `alembic downgrade -1 && alembic upgrade head` | error |
| Regresión 820 | `pytest tests/test_notifications_820.py -q` | FAIL nuevo |
| Regresión 810C | `pytest tests/test_automations_810c.py -q` | FAIL nuevo |
| RBAC | `pytest tests/test_security_rbac_v1.py -q` | FAIL nuevo |
| Control migraciones | `python backend/scripts/migration_control.py` | error |
| Frontend | `cd frontend && npm run build` | build FAIL |

Suite focal certificada: **60 passed** (MB-11×10 + migration_control + 820 + 810C + RBAC).

---

## 8. Condición de aborto

Detener integración si aparece:

- Más de una cabeza Alembic
- Dependencia obligatoria no disponible (`organizations`, `users`, secrets gateway)
- Regresión nueva en 820 o 810C
- Doble emisión 820 por comunicación MB-11
- Segundo scheduler creado
- Fuga multiempresa (ORG-A ve datos ORG-B)
- `secret_ref` o contraseñas en API/logs/frontend
- Frontend build roto

---

## 9. Recorrido UI mínimo

1. Login admin
2. `/comunicaciones` → Bandeja
3. Nueva comunicación → plantilla → destinatario → canal → enviar
4. Historial → detalle (sin secretos)
5. Plantillas → crear → nueva versión
6. Reglas → crear regla
7. Canales → revisar estado

**Menú:** entrada actual en `AppShell.tsx` sección "Análisis y control". General puede reubicar en convergencia; no es bloqueante funcional.

---

## 10. Post-integración opcional (fuera de MB-11)

- Cablear `contrato_centro_control()` en Centro de Control
- Cablear `contrato_mi_trabajo()` en Mi Trabajo
- SMTP real / webhook HTTP real
- Traducciones adicionales de plantillas

MB-11 funciona sin estos pasos.

---

## Referencia

Documentación técnica completa: `INTERCAMBIO/SALIDA/EMPLEADOS_IA_MB11_CENTRO_INFORMACION_COMUNICACIONES.md`
