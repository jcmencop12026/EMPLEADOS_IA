# 02 — Modelo canónico de caso

## Objeto principal: `SupportCase`

Representa el ciclo completo: organización, solicitante, origen, tipo, categoría, servicio/componente, descripción, prioridad (sugerida y ajustada), impacto, urgencia, responsables (principal, técnico, funcional, coordinador), estado, SLA, fechas, diagnóstico, resolución, validación, trazabilidad.

## Tipos (`TIPOS_CASO`)
`INCIDENTE`, `SOLICITUD`, `PROBLEMA`, `CONSULTA`, `MEJORA`, `ACCESO`, `INTEGRACION`, `AUTOMATIZACION`, `EMPLEADO_IA`, `FACTURACION_COSTOS`, `SEGURIDAD`, `OTRO`.

`MEJORA` ≠ oportunidad de transformación (objeto distinto).

## Estados (`ESTADOS_CASO`)
`NUEVO`, `CLASIFICADO`, `ASIGNADO`, `EN_ANALISIS`, `EN_PROCESO`, `PENDIENTE_USUARIO`, `PENDIENTE_TERCERO`, `RESUELTO`, `VALIDACION_PENDIENTE`, `CERRADO`, `CANCELADO`.

Etiquetas en español vía `ESTADO_ETIQUETAS`.

## Tablas relacionadas (1430)
- `support_problems` — problemas recurrentes
- `support_case_evidences` — referencias a evidencia
- `support_knowledge_proposals` — propuestas KB (no publicación automática)
- `support_post_reviews` — revisión posterior de incidentes

## Referencias externas
`correlation_id`, `origen_tipo`/`origen_id`, `modulo_relacionado`, `entidad_relacionada`, `servicio_componente` — para Empleados IA, PIIAX e integraciones sin duplicar objetos.
