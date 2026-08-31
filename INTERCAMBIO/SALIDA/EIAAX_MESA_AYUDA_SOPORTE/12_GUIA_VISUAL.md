# 12 — Guía visual

## Mesa de Ayuda (`/soporte`)
- **Vistas**: Todos/autorizados, Mis casos, Próximos a vencer, Vencidos, Problemas
- **Tabla**: `EiaaxTable` con referencia, tipo, asunto, estado (español), prioridad, SLA con badges
- **Ayuda**: `ContextualHelp` — flujo, prioridad, autoservicio
- **Autoservicio**: «¿Qué necesitas?» → sugerencias → crear caso sin repetir datos

## Detalle de caso (`/soporte/casos/{id}`)
Pestañas:
1. **Resumen** — descripción, asignación, resolver, validar
2. **Actividad** — comentarios/comunicaciones
3. **Diagnóstico** — síntoma/hipótesis/causa + propuesta KB
4. **Evidencias** — referencias tipadas
5. **SLA** — límites y estado en español
6. **Trazabilidad** — historial completo + problema vinculado

## Tokens y componentes reutilizados
- `AppShell` (navegación existente)
- `EiaaxTable`, `ContextualHelp`
- Clases `cc-tag`, `panel`, `tab-bar` del tema EIAAX

## Menú
Entrada «Mesa de Ayuda» → `/soporte` (sin cambio de ruta).
