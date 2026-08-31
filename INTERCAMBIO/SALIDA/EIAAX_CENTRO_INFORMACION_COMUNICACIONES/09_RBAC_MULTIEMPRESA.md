# 09 — RBAC y multiempresa

## Permisos communications.*

- `communications.view`, `.send`, `.schedule`
- `.template.manage`, `.rule.manage`, `.channel.manage`
- `.history.view`

## Integración resultados

Entrega de informe requiere `communications.send` + `resultados.view`.

## Aislamiento

Todas las consultas filtran por `organization_id`. Tests verifican:

- Tenant A no lee mensajes B
- Destinatario fuera de org rechazado
- Manipulación API directa → 404/422
