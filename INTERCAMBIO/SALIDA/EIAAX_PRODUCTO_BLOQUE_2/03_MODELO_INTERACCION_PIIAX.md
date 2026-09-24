# 03 — Modelo de interacción PIIAX

## Estado de disponibilidad

`GET /api/evaluaciones/integracion/piiax`

Determina disponibilidad sin llamar endpoints PIIAX:

- Variable de entorno `PIIAX_BRIDGE_ENABLED`
- Config organización: `organization.config_json.piiax.enabled`
- URL opcional de detalle: `config_json.piiax.detalle_url`

Respuesta típica (no conectado):

```json
{
  "disponible": false,
  "modo": "no_conectado",
  "mensaje": "PIIAX no está conectado..."
}
```

## Handoff (stub)

`piiax_bridge_service.solicitar_ejecucion_piiax()`:

- Si no disponible → `PIIAX_NO_DISPONIBLE`, sin `referencia_externa`
- Si disponible (prep) → `SOLICITADA`, referencia `piiax-prep-{correlation_id}`

**No** se implementan conectores ni contratos incompatibles.

## Incorporación de resultado compatible

`POST /api/evaluaciones/{id}/acciones/{accion_id}/resultado`

Payload esperado (compatible con futuro PIIAX):

- `estado`: `COMPLETADA` | `ERROR`
- `resumen`, `evidencia_ref`, `referencia_externa` (opcional)
- `error_mensaje` si error

EIAAX actualiza acción, evento de trazabilidad y puede enlazar evidencia al hallazgo.

## UX desacoplada

- Barra compacta: PIIAX disponible / no disponible
- Por acción: estado, resultado, error comprensible
- Enlace «Ver detalle técnico en PIIAX» solo si hay `detalle_url` + referencia (usuarios autorizados)

No hay menú PIIAX dentro de EIAAX.
