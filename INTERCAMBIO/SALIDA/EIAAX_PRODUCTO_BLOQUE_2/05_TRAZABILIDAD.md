# 05 — Trazabilidad transversal

## Cadena `correlation_id`

Generado al crear una acción externa y propagado en:

1. Organización (`organization_id`)
2. Expediente (`expediente_id`)
3. Hallazgo (`hallazgo_id`, opcional)
4. Acción (`EvaluacionAccionExterna.correlation_id`)
5. Eventos (`EvaluacionAccionEvento.correlation_id`)
6. Resultado / referencia externa PIIAX

## Eventos empresariales

Tabla `evaluaciones_accion_eventos` — tipos como:

- `CREADA`, `SOLICITADA`, `APROBADA`, `RECHAZADA`
- `HANDOFF_PIIAX`, `RESULTADO_RECIBIDO`, `ERROR`

**No** se almacenan logs técnicos completos de PIIAX en EIAAX.

## API trazabilidad expediente

`GET /api/evaluaciones/{id}/trazabilidad` incluye:

- Historial de estados del expediente
- Acciones externas con `correlation_id` y resumen
- Cadena legible para auditoría empresarial

PIIAX mantendrá trazabilidad técnica detallada en su dominio.
