# 09 — Indicadores y mejora continua

## Indicadores (`GET /api/soporte/indicadores`)
Reutiliza contrato Centro Control + métricas adicionales:
- Casos abiertos / cerrados / totales
- Tiempo medio primera respuesta y resolución
- Cumplimiento SLA (vencidos, críticos)
- Reaperturas (historial)
- Problemas abiertos
- Volumen por categoría

Compatible con Inteligencia de Resultados (consumo vía API, sin motor paralelo).

## Mejora continua
- Tipo `MEJORA` en casos
- Problemas → acciones preventivas
- Propuestas KB → procedimientos
- Revisión posterior → tareas/acciones (integración motores existentes P1)

No se construyó segundo gestor de oportunidades.

## Validación / cierre
- `RESUELTO` + `validacion_solicitante=PENDIENTE`
- `POST /api/soporte/casos/{id}/validar` — aceptar → `CERRADO`; rechazar → `EN_PROCESO`
- Autocierre programado: P1 vía scheduler existente
