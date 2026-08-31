# 02 — Modelo de comunicación

## Objeto canónico: `CommMessage`

Representa organización, tipo, canal, destinatarios, contenido, estado, intentos, trazabilidad (`correlation_id`, `event_id`, `origen`, `origen_id`).

Estados: `BORRADOR`, `PROGRAMADA`, `PENDIENTE_ENVIO`, `ENVIANDO`, `ENVIADA`, `ENTREGADA`, `FALLIDA`, `CANCELADA`.

## Tipos (`TIPOS_COMUNICACION`)

INFORMATIVA, OPERATIVA, ALERTA, RECORDATORIO, SOLICITUD, RESULTADO, INFORME, APROBACION, INCIDENTE.

## Entidades relacionadas

- `CommChannel`, `CommTemplate` + `CommTemplateVersion`
- `CommRule` — disparadores por evento
- `CommDeliveryAttempt` — intentos y errores
- `CommPreference` — preferencias usuario/org
- `CommEntregaInforme` — registro inmutable de entrega con versión fijada
