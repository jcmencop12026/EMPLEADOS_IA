# EMPLEADOS IA — MB-11 Centro de Información y Comunicaciones

## Base y rama

| Campo | Valor |
|-------|-------|
| Base | `cursor/fase2-central-integracion` @ `cda96774909576e589ee1fddcbabf08aeec65540` |
| Rama | `cursor/mb11-centro-informacion-comunicaciones` |
| Migración | `1341a1b2c3d4e` (down: `1340a1b2c3d4e`) |

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

## Modelos (`communications_models.py`)

- `comm_channels` — canales por organización
- `comm_templates` + `comm_template_versions` — versionado inmutable por envío
- `comm_rules` — evento → condición → destinatario → plantilla → canal
- `comm_messages` — comunicaciones con estados e idempotencia
- `comm_delivery_attempts` — reintentos trazables
- `comm_preferences` — preferencias usuario/org
- `comm_dedup` — antispam / deduplicación

## Estados de comunicación

`BORRADOR`, `PROGRAMADA`, `PENDIENTE_ENVIO`, `ENVIANDO`, `ENVIADA`, `FALLIDA`, `CANCELADA`.

No se registra `ENTREGADA` sin confirmación real del canal.

## Canales

Implementados: `CORREO_ELECTRONICO`, `INTERNO_PLATAFORMA`, `WEBHOOK`.

Arquitectura preparada para SMS, WhatsApp, Teams, Slack, PUSH.

Secretos vía `secret_ref` + `gateway/secrets.py` — nunca en API/logs/UI.

## Plantillas y variables

Lista blanca: `{{nombre}}`, `{{empresa}}`, `{{fecha}}`, `{{caso}}`, `{{empleado_ia}}`, `{{valor}}`, `{{estado}}`, etc.

Bloqueo de expresiones peligrosas (`import`, `exec`, `javascript:`…).

## Reglas

JSON de condición (`match`) sin código arbitrario. Destinatarios dinámicos: `RESPONSABLE_CASO`, `ADMIN_ORGANIZACION`, `SOLICITANTE`, etc.

## Idempotencia y antispam

Clave SHA-256: `org + event_id + rule + destinatario + canal`. Tabla `comm_dedup` con ventana configurable.

## Reintentos

Máximo 3, backoff 60/120/300 s. Integrado en `automation_scheduler._tick()` (810C).

## API

Prefijo `/api/comunicaciones`:

- `GET/POST /canales`, `/plantillas`, `/reglas`, `/mensajes`
- `POST /mensajes/{id}/cancelar`
- `GET /contrato/centro-control`, `/contrato/mi-trabajo`
- `PUT /preferencias`

## RBAC

`communications.view`, `communications.send`, `communications.schedule`, `communications.template.manage`, `communications.rule.manage`, `communications.channel.manage`, `communications.history.view`.

## Frontend

Ruta `/comunicaciones` — pestañas: Bandeja, Plantillas, Reglas, Canales, Programadas, Historial. UI en español.

## Tests

`tests/test_mb11_comunicaciones.py` — 8 pruebas cubriendo plantillas, versionado, reglas, idempotencia, canales, programación, 810C, multiempresa, RBAC, contratos, timezone.

## Commits portables (rama)

1. Modelos, enums, esquemas, migración `1341a1b2c3d4e`
2. Servicio, router, permisos, wiring main/810C
3. Frontend `/comunicaciones`
4. Tests y entregable

## Receta de integración

1. Cherry-pick o merge de `cursor/mb11-centro-informacion-comunicaciones` sobre rama destino.
2. Verificar `alembic upgrade head` → `1341a1b2c3d4e` única cabeza.
3. Confirmar `register_communications_handlers()` en lifespan.
4. Confirmar `process_scheduled_and_retries` en scheduler 810C.
5. Ejecutar `tests/test_mb11_comunicaciones.py` + regresión 820/810C.
6. Build frontend.

## Restricciones respetadas

- NO modificación de `cursor/fase2-central-integracion`, `main`, V1
- NO reemplazo 820, NO scheduler nuevo, NO Mi Trabajo / Mesa / Centro Control nuevos
- NO credenciales reales ni LLM obligatorio
