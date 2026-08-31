# 01 — Reutilización existente (MB-12)

## SHA base
- Inicial: `f32c8157d7f5576ba59f5ca895b88fbe7d06f8e9`
- Rama: `cursor/eiaax-mesa-ayuda-soporte-9a85` (derivada de `cursor/eiaax-centro-informacion-comunicaciones-9a85`)

## Capacidades reutilizadas (no duplicadas)

| Motor | Uso en MB-12 |
|-------|----------------|
| **Mesa de Ayuda 1391** | Tablas `support_*`, router `/api/soporte`, permisos `support.*` |
| **Notificaciones 820** | Eventos `SUPPORT_*` vía `emit_event` |
| **MB-11 Comunicaciones** | Bus de eventos + plantillas seed (`SOPORTE_*`) |
| **Knowledge** | Búsqueda en autoservicio (`knowledge_service.search_documents`) |
| **Mi Trabajo / Centro Control** | Contratos `contrato_mi_trabajo`, `contrato_centro_control` |
| **Inteligencia Resultados** | Indicadores extendidos en `/api/soporte/indicadores` |
| **RBAC / multiempresa** | `organization_id` en todas las tablas; filtros en API |
| **Auditoría / eventos** | Historial `support_case_history`, `correlation_id` |
| **Scheduler** | Preparado para autocierre post-validación (P1 integración) |

## No construido (según misión)
PIIAX, ITSM/CMDB, Fábrica Empleados IA, Knowledge paralelo, motor analítico paralelo, segundo scheduler.

## Migración nueva
- `1430a1b2c3d4e` — evolución MB-12 (depende de `1420a1b2c3d4e`)
- Sin reconciliar colisiones `1410`/`1420` de ramas externas
