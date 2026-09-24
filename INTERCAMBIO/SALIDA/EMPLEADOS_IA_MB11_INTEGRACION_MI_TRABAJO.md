# EMPLEADOS IA — MB-11 Integración con Mi Trabajo

## Base

| Campo | Valor |
|-------|-------|
| MB-11 HEAD | `9d697f0c1755d4e836adc7219e43092ddd2aee37` |
| Mi Trabajo referencia | `e4ff40bf411fa5d91f69246e47e4805187a4d116` |
| Rama integración | `cursor/mb11-integracion-mi-trabajo` |
| Migración nueva | **NO** (sigue `1341a1b2c3d4e`) |

## Principio

**COMUNICACIÓN ≠ TRABAJO HUMANO.** Solo condiciones terminales o bloqueos reales generan ítems en `/trabajo`.

## Fuente

| Campo | Valor |
|-------|-------|
| `modulo` | `comunicaciones` |
| Etiqueta visible | Centro de Información y Comunicaciones |
| Función | `communications_service.collect_trabajo_items()` |
| Integración | `trabajo_service.collect_items()` |

## Estados accionables

| Tipo ítem | Condición real |
|-----------|----------------|
| `comunicacion_envio_critico` | `estado=FALLIDA`, `intentos >= max_intentos`, sin `proximo_intento` futuro |
| `comunicacion_canal_bloqueado` | Canal `activo` + `estado=ERROR` (o DEGRADADO con fallo terminal asociado) |
| `comunicacion_configuracion_requerida` | Correo sin `secret_ref` **y** fallo terminal en ese canal |

## Estados excluidos

- `ENVIADA`, `ENTREGADA`, `PROGRAMADA` normal
- `PENDIENTE_ENVIO` con reintento futuro
- `FALLIDA` con reintentos restantes
- Correo/webhook PREPARADO sin fallo real
- Eventos informativos

## Reintentos y 810C

Mientras `intentos < max_intentos` o `proximo_intento > now`: **sin ítem humano**.

`automation_scheduler._tick()` ejecuta reintentos; Mi Trabajo entra solo al agotar política terminal.

## Idempotencia Mi Trabajo

Claves de ítem estables:

- `comunicacion:msg:{id}`
- `comunicacion:canal:{id}`
- `comunicacion:config:{id}`

Mismo fallo → un solo ítem por ejecución de `collect_items()`.

## Deduplicación 820

Si existe notificación `source_type=communication` o `metadata.communication_id` para un ítem MB-11 ya presente, **no se duplica** la obligación humana en notificaciones.

## Deduplicación MB-11

Sin cambios en `SHA256(org|event_id|rule|destinatario|canal)` ni `comm_dedup`.

## Asignación

- Mensaje: `destinatario_id` si USUARIO, else `creador_id`, else admin organización
- Canal/config: admin organización

## API Mi Trabajo

- `GET /api/trabajo/items?modulo=comunicaciones`
- `GET /api/trabajo/items?communication_id={id}`
- `GET /api/trabajo/resumen` — cuenta ítems accionables de comunicaciones

## Navegación

- Ítem → `/comunicaciones?mensaje={id}` o `/comunicaciones?tab=canales`
- Sin formulario duplicado en Mi Trabajo

## RBAC

- Ver ítem: `communications.view` (vía `TRABAJO_VIEW_PERMISSIONS`)
- Acciones navegan a MB-11 que aplica su RBAC (`communications.send`, etc.)
- Viewer sin `communications.view`: bandeja accesible pero sin ítems de comunicaciones

## Secretos

Ítems usan `sanitize_comm_text()`; metadata sin `secret_ref`, passwords ni tokens.

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `communications_service.py` | `collect_trabajo_items()` |
| `trabajo_service.py` | integración + dedup 820 + filtro `communication_id` |
| `routers/trabajo.py` | query `communication_id` |
| `main.py` | router trabajo |
| `TrabajoPage.tsx` | tipos comunicaciones en español |
| `api.ts`, `App.tsx`, `AppShell.tsx`, `permissions.ts` | wiring |

## Archivos portados (base Mi Trabajo e4ff40bf)

- `trabajo_service.py`, `routers/trabajo.py`, `schemas_trabajo.py`
- `TrabajoPage.tsx`, `test_bandeja_trabajo_humano.py`

## Tests

`tests/test_mb11_integracion_mi_trabajo.py` — 7 pruebas:

- fallo recuperable → NO ítem
- reintentos agotados → SÍ ítem (idempotente)
- resuelto → desaparece
- scheduler 810C sin prematuro
- resumen, filtros, navegación, secretos
- multiempresa + RBAC
- contrato reutilizado

## Receta para General

1. Portar MB-11 (`e3fb206` o `9d697f0`) primero
2. Portar delta integración Mi Trabajo de esta rama
3. Resolver conflictos en `main.py`, `trabajo_service.py`, `api.ts`
4. Sin migración nueva
5. Ejecutar `test_mb11_integracion_mi_trabajo.py` + regresión focal
6. Verificar `/trabajo` y `/comunicaciones`

## Condición de aborto

- Ítems por fallos recuperables
- Duplicación 820 + Mi Trabajo
- Fuga multiempresa
- Secretos en ítems
- Nueva migración innecesaria
- Más de una cabeza Alembic
