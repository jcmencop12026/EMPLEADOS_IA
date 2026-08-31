# 04 — Asignación y escalamiento

## Asignación
`POST /api/soporte/casos/{id}/asignar`

Campos:
- `responsable_id` — agente principal
- `responsable_tecnico_id` — responsable técnico
- `responsable_funcional_id` — responsable funcional
- `grupo` — equipo/rol

Agentes: `GET /api/soporte/agentes-asignables` (usuarios con permisos `support.assign|view|admin|update`).

Preparado para futura asignación a Empleado IA (referencia por `entidad_relacionada`, sin integración directa).

## Escalamiento
`POST /api/soporte/casos/{id}/escalar`

Motivos: `CRITICIDAD`, `VENCIMIENTO`, `SIN_RESPUESTA`, `COMPLEJIDAD`, `DEPENDENCIA_EXTERNA`, `RECURRENCIA`.

- Incrementa `escalamiento_nivel`
- Opcional `coordinador_id` para incidentes mayores
- Evento `SUPPORT_CASE_ESCALATED` → notificaciones + MB-11

## Clasificación
`POST /api/soporte/casos/{id}/clasificar` — tipo, categoría, servicio → estado `CLASIFICADO`.
