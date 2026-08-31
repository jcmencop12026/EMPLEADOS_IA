# 10 — RBAC y multiempresa

## Permisos (existentes, adaptados al brief)
| Permiso | Equivalente brief |
|---------|-------------------|
| `support.view` | soporte.view |
| `support.create` | soporte.create |
| `support.update` | soporte.manage (parcial) |
| `support.assign` | soporte.assign |
| `support.resolve` | soporte.resolve |
| `support.close` | cierre |
| `support.admin` | soporte.admin |

## Aislamiento
- Todas las consultas filtran `organization_id`
- Caso/evidencia/comentario de tenant A → 403/404 para tenant B (probado)
- Backend es autoridad; frontend no expone datos cruzados

## Perfiles
- Solicitante (`support.create`): solo sus casos
- Agente (`support.assign`, `support.update`): casos asignados + vista operativa
- Admin soporte (`support.admin`): SLA, problemas, revisión posterior
