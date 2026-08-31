# 05 — Plantillas y eventos

## Plantillas versionadas

Códigos por defecto (`bootstrap_default_comm_assets`):

- `INFORME_DISPONIBLE`
- `INFO_FALTANTE_EVAL`
- `RESULTADO_REGISTRADO`

Variables: `informe_titulo`, `informe_version`, `expediente`, `expediente_codigo`, etc.

## Eventos soportados

- `RESULTADOS_INFORME_GENERADO` — notificación interna al responsable
- `EVALUACION_INFO_FALTANTE` — solicitud de información
- Reglas `CommRule` para cualquier `event_type` del bus

## Programación

`PROGRAMADA` vía `programada_para` + scheduler 810C (sin scheduler paralelo).
