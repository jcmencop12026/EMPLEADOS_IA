# 08 — Incidentes transversales

## Empleados IA
Tipo `EMPLEADO_IA` + referencias `origen_tipo`/`origen_id`, `entidad_relacionada`, `correlation_id`.

Casos automáticos vía `POST /api/soporte/casos/auto` con deduplicación 4h.

Sin implementar Fábrica — solo referencia futura.

## Capacidades externas / PIIAX
Tipo `INTEGRACION`, campo `servicio_componente`, `correlation_id`.

EIAAX gestiona el incidente aunque PIIAX no esté conectado.

## Incidente mayor
- Flag `es_incidente_mayor`
- `coordinador_id`
- Escalamiento con coordinador activa seguimiento reforzado
- Revisión posterior documentada

Sin plataforma de crisis separada.

## Continuidad 1360
Dominio `cont_incidentes` permanece separado; puente unificado pendiente P2.
