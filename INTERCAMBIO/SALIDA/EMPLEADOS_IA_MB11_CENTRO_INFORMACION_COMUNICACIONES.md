# EMPLEADOS IA — MB-11 Centro de Información y Comunicaciones

## Base y rama

| Campo | Valor |
|-------|-------|
| Base | `cursor/fase2-central-integracion` @ `cda96774909576e589ee1fddcbabf08aeec65540` |
| Rama | `cursor/mb11-centro-informacion-comunicaciones` |
| HEAD | `e3fb206e9a2dcb25b0014a249bc593f3ecae310e` |
| Migración | `1341a1b2c3d4e` (down actual: `1340a1b2c3d4e`) |
| PR | #88 |

## Arquitectura

MB-11 **organiza, orquesta y traza comunicaciones** sin reemplazar el motor de notificaciones 820 ni crear un scheduler nuevo.

| Concepto | Responsable | MB-11 |
|----------|-------------|-------|
| Notificación | 820 (IN_APP) | No duplica |
| Comunicación | MB-11 | Plantilla + canal + entrega |
| Mi Trabajo | Bandeja humana | Solo contrato portable |
| Mesa de Ayuda | Casos | Contrato futuro, sin cablear |

### Flujo

```
Evento (bus) → Regla MB-11 → Plantilla versionada → Canal → Estado + intentos
Manual UI    → Plantilla opcional → Canal → Envío / programación
810C tick    → process_scheduled_and_retries() → reintentos y programadas
```

---

## CERTIFICACIÓN FINAL DE PORTABILIDAD

Fecha certificación: 2026-08-29. Rama sin funcionalidad nueva; solo inventario, pruebas y documentación de port.

### 1. Inventario de commits

Un único commit funcional en la rama:

| SHA | Ámbito |
|-----|--------|
| `e3fb206e9a2dcb25b0014a249bc593f3ecae310e` | **TODO MB-11** (monolítico) |

Desglose interno por categoría (mismo SHA):

| Categoría | Archivos |
|-----------|----------|
| **BACKEND core** | `communications_enums.py`, `communications_models.py`, `schemas_communications.py`, `communications_service.py`, `routers/comunicaciones.py` |
| **MIGRACIÓN** | `1341a1b2c3d4e_centro_comunicaciones_mb11.py`, `migration_ledger.json`, `schema_repair.py` |
| **RBAC** | `permissions.py` |
| **EVENTOS** | `communications_service.register_communications_handlers`, `notifications.py` (SUPPORTED_EVENTS) |
| **SCHEDULER 810C** | `automation_scheduler.py` |
| **WIRING** | `main.py` |
| **FRONTEND** | `ComunicacionesPage.tsx`, `App.tsx`, `AppShell.tsx`, `api.ts`, `permissions.ts` |
| **TESTS** | `test_mb11_comunicaciones.py`, `conftest.py` |
| **DOCUMENTACIÓN** | `EMPLEADOS_IA_MB11_*.md`, `EMPLEADOS_IA_RECETA_PORT_MB11_*.md` (opcional para runtime) |

### 2. Diff exacto (base → HEAD)

**20 archivos**, +2842 / −3 líneas.

| Clasificación | Archivos |
|---------------|----------|
| **Nuevos MB-11** | 9 backend + 1 frontend + 1 test + 1 migración + 2 docs |
| **Centrales modificados** | `main.py`, `permissions.py`, `automation_scheduler.py`, `notifications.py` |
| **Compartidos infra** | `migration_ledger.json`, `schema_repair.py`, `conftest.py` |
| **Compartidos frontend** | `App.tsx`, `AppShell.tsx`, `api.ts`, `auth/permissions.ts` |
| **Conflictivos previsibles** | `main.py`, `permissions.py`, `migration_ledger.json`, `api.ts` |

### 3. Dependencias reales

| Dependencia | Uso MB-11 | Obligatoria |
|-------------|-----------|-------------|
| **820 notificaciones** | Consume eventos vía bus; no reemplaza | Sí (event bus) |
| **810C scheduler** | `process_scheduled_and_retries()` en `_tick()` | Sí |
| **users / organizations** | FK, destinatarios, multiempresa | Sí |
| **RBAC 840** | `check_permission`, seed permisos | Sí |
| **auditoría** | `write_audit` en cambios sensibles | Sí |
| **event bus** | `subscribe` + `publish` para reglas | Sí |
| **secretos** | `gateway/secrets`, `secret_configured` | Sí (canales correo/webhook) |
| **integration_security** | `validate_external_url` (webhook SSRF) | Sí si webhook |

**NO depende de:** Mi Trabajo, Mesa de Ayuda, Centro de Control, Auditor, Fábrica, MB-07, Conocimiento.

Contratos CC/Mi Trabajo son endpoints locales en MB-11; no importan módulos externos.

### 4. Integración 820

- 820 sigue siendo el motor de **notificaciones** (`notifications.py`, tabla `notifications`).
- MB-11 **no llama** `emit_event()` al enviar comunicaciones (eliminado en implementación final).
- Reglas MB-11 escuchan el **event bus** (`events/bus.py`), mismo bus que alimenta 820 vía `_event_subscriber`.
- No hay doble emisión: idempotencia propia (`comm_dedup` + `idempotency_key`) + idempotencia 820 separada.
- `COMMUNICATION_SENT` añadido a `SUPPORTED_EVENTS` solo como catálogo; sin DEFAULTS ni reglas auto-creadas.

### 5. Integración 810C

| Función | Dónde | Qué hace |
|---------|-------|----------|
| `automation_scheduler._tick()` | `backend/app/services/automation_scheduler.py` | Tras procesar automatizaciones SCHEDULE |
| `communications_service.process_scheduled_and_retries(db)` | invocado desde `_tick()` | Mensajes `PROGRAMADA` vencidos + `PENDIENTE_ENVIO` con `proximo_intento` vencido |

No se creó hilo ni scheduler adicional.

### 6. Migración 1341

| Campo | Valor |
|-------|-------|
| revision_id | `1341a1b2c3d4e` |
| down_revision actual | `1340a1b2c3d4e` |
| Unicidad | 1 ocurrencia en 57 revisiones del repo |
| Colisiones prohibidas | 0 (ninguna de 1390/1391/1400/1507/6b06/14b1c2d3e4f5 existe) |

**Reparent General:** cambiar `down_revision` al HEAD real del tramo central. Requiere tablas `organizations`, `users` preexistentes.

### 7. Esquema MB-11 (tablas 1341)

#### `comm_channels`
- **PK:** `id` (String 36)
- **FK:** `organization_id` → `organizations.id`
- **UQ:** `(organization_id, nombre)`
- **Sensibles:** `secret_ref` (solo referencia, nunca API)
- **Fechas:** `created_at`, `updated_at` (timezone=True)

#### `comm_templates`
- **PK:** `id`
- **FK:** `organization_id`
- **UQ:** `(organization_id, codigo)`
- **Fechas:** `created_at`, `updated_at`

#### `comm_template_versions`
- **PK:** `id`
- **FK:** `template_id`, `organization_id`, `creador_id` → `users.id`
- **UQ:** `(template_id, version)`
- **Fechas:** `vigencia_desde`, `vigencia_hasta`, `created_at`

#### `comm_rules`
- **PK:** `id`
- **FK:** `organization_id`, `template_version_id`, `channel_id`
- **Fechas:** `created_at`, `updated_at`

#### `comm_messages`
- **PK:** `id`
- **FK:** `organization_id`, `channel_id`, `template_version_id`, `rule_id`, `creador_id`
- **UQ:** `(organization_id, idempotency_key)`
- **Índices:** `ix_comm_messages_org`, `ix_comm_messages_estado`
- **Fechas:** `programada_para`, `proximo_intento`, `created_at`, `updated_at`, `enviada_at`, `entregada_at`, `cancelada_at`

#### `comm_delivery_attempts`
- **PK:** `id`
- **FK:** `message_id`, `organization_id`
- **Fechas:** `created_at`

#### `comm_preferences`
- **PK:** `id`
- **FK:** `organization_id`, `user_id`
- **UQ:** `(organization_id, user_id)`

#### `comm_dedup`
- **PK:** `id`
- **FK:** `organization_id`, `message_id`
- **UQ:** `(organization_id, dedup_key)`
- **Fechas:** `ventana_fin`, `created_at`

### 8. Fechas y timezone

- Helpers `_utcnow()` y `_as_utc()` en servicio: naive → UTC aware.
- Campos DB: `DateTime(timezone=True)`.
- Test focal: `test_timezone_aware_scheduling` (naive + aware → `PROGRAMADA`).
- Sin nueva deuda naive/aware detectada.

### 9. Idempotencia (código real)

Función `build_idempotency_key()`:

```
SHA256( organization_id | event_id | rule_id | destinatario | channel_id )
```

- Persistido en `comm_messages.idempotency_key` (UQ por org).
- Ventana antispam: tabla `comm_dedup` con `dedup_key` + `ventana_fin` (minutos de regla).
- `IntegrityError` en insert → reutiliza mensaje existente.

### 10. Reintentos

| Parámetro | Valor |
|-----------|-------|
| Máximo | `MAX_REINTENTOS = 3` |
| Backoff | 60, 120, 300 segundos |
| Estado tras fallo recuperable | `PENDIENTE_ENVIO` + `proximo_intento` |
| Estado terminal | `FALLIDA` cuando `intentos >= max_intentos` |
| Loop infinito | No — condición `intentos < max_intentos` |

### 11. Canal WEBHOOK — PREPARADO

| Implementado | Pendiente producción |
|--------------|---------------------|
| Modelo + adaptador en `_deliver_channel` | HTTP POST real al destino |
| Validación SSRF (`validate_external_url`) | Política de allowlist por org |
| Estado `ENVIADA` = aceptado, no ENTREGADA | Confirmación de respuesta HTTP |
| `secret_ref` para firma | Implementación de firma HMAC |

### 12. Canal CORREO — PREPARADO/PASS adaptador

| Implementado | Pendiente producción |
|--------------|---------------------|
| Adaptador simulado sin `secret_ref` | SMTP/API real |
| Con `secret_ref`: `resolve_secret()` sin exponer | Proveedor configurado |
| Estado `ENVIADA` sin fingir entrega | DSN/bounce tracking |

### 13. Contratos portables

| Endpoint | Retorna |
|----------|---------|
| `GET /api/comunicaciones/contrato/centro-control` | pendientes, fallidas, enviadas, tasa_fallo, canales_degradados, reintentos, críticas |
| `GET /api/comunicaciones/contrato/mi-trabajo` | config_faltante, canales_bloqueados, reintentos_agotados |

Sin CC/Mi Trabajo cableados: app arranca y endpoints responden. Test: `test_contratos_portables_sin_acoplamiento_modulos`.

### 14. Frontend

| Elemento | Valor |
|----------|-------|
| Ruta | `/comunicaciones` |
| Componente | `frontend/src/pages/ComunicacionesPage.tsx` |
| Pestañas | Bandeja, Plantillas, Reglas, Canales, Programadas, Historial |
| Idioma UI | Español |
| Permiso ruta | `communications.view` |

### 15. Menú

Entrada provisional en `AppShell.tsx` → sección "Análisis y control". **General decide ubicación final** en convergencia; no bloqueante.

### 16. RBAC (permisos creados)

| Permiso | Separación |
|---------|------------|
| `communications.view` | Ver bandeja, catálogo |
| `communications.send` | Enviar ahora |
| `communications.schedule` | Programar / cancelar |
| `communications.template.manage` | Plantillas |
| `communications.rule.manage` | Reglas |
| `communications.channel.manage` | Canales |
| `communications.history.view` | Detalle historial |

Asignados a `admin`, `superadmin`; operator tiene view/send/schedule/history.

### 17. Secretos

- `channel_to_dict()` filtra config con password/secret.
- API devuelve `secret_configured: bool`, nunca `secret_ref`.
- `sanitize_comm_text()` en mensajes e intentos.
- Test: `test_secret_ref_no_expuesto_en_api`.

### 18. Auditoría

Acciones registradas:

- `communications.channel.created`
- `communications.template.created`
- `communications.template.versioned`
- `communications.rule.created`
- `communications.message.created`
- `communications.message.cancelled`
- `communications.preferences.updated`

### 19. Pruebas ejecutadas (certificación)

| Suite | Resultado |
|-------|-----------|
| `test_mb11_comunicaciones.py` | 10 passed |
| `test_migration_control.py` | passed |
| `test_notifications_820.py` | passed |
| `test_automations_810c.py` | passed |
| `test_security_rbac_v1.py` | passed |
| **Total focal** | **60 passed, 0 failed** |
| Frontend build | PASS |

### 20. Alembic roundtrip (SQLite)

| Paso | Resultado |
|------|-----------|
| upgrade head | PASS → `1341a1b2c3d4e` |
| downgrade -1 | PASS → `1340a1b2c3d4e` |
| re-upgrade head | PASS → `1341a1b2c3d4e` |
| heads | 1 |
| PostgreSQL | PENDIENTE POR ENTORNO |

### 21. Receta General

Ver: `INTERCAMBIO/SALIDA/EMPLEADOS_IA_RECETA_PORT_MB11_COMUNICACIONES.md`

---

## API (referencia)

Prefijo `/api/comunicaciones` — ver router `comunicaciones.py`.

## Restricciones respetadas

- NO modificación de `cursor/fase2-central-integracion`, `main`, V1
- NO reemplazo 820, NO scheduler nuevo
- NO Mi Trabajo / Mesa / Centro Control / Auditor / Fábrica / Conocimiento nuevos
- NO credenciales reales ni LLM obligatorio
