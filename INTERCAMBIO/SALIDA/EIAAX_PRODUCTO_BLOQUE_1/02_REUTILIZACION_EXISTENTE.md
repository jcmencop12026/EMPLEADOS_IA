# 02 — Reutilización existente

## Motores reutilizados (sin reconstruir)

| Motor | Uso en Bloque 1 |
|-------|-----------------|
| **Diagnósticos (1220)** | FK `diagnostic_id`, `correlation_id`; extensible a generación futura |
| **Oportunidades (1030)** | `proactive_service.run_proactive_pipeline` para crear oportunidad desde hallazgo |
| **Línea base (1200)** | Modelo de impacto ANTES/PROYECTADO/REAL en representación |
| **Valoración (1210)** | Referencia para valor potencial (no duplicado) |
| **Assistant / Coordinator** | Panel «Preguntar a EIAAX» vía `route_task` con contexto expediente |
| **LLM Gateway (1270)** | Detección de proveedor; estado controlado si no hay proveedor |
| **RBAC (840)** | Permisos `evaluacion.*` |
| **Auditoría** | `write_audit` en crear/evaluar/visibilidad/vincular |
| **Multiempresa C2** | `organization_id` en todas las tablas |

## Infraestructura UI reutilizada

- `AppShell`, sidebar C2, `OrganizationContext`
- Patrones `ops-page`, `compact-tabs`, `metrics-grid`, `data-table`
- `RequirePermission`, `usePermissions`
- Login MFA/SSO sin cambios de flujo

## No duplicado

- No se recreó payload de diagnóstico ni oportunidad.
- Expediente = capa orquestadora con punteros FK y hallazgos propios del recorrido comercial.
