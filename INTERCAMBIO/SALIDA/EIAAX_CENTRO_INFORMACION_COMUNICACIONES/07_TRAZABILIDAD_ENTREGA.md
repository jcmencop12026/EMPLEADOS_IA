# 07 — Trazabilidad y entrega

## Cadena

organización → expediente/informe → evento → `CommMessage` → `CommDeliveryAttempt` → `CommEntregaInforme`

## Versionamiento

`comm_entregas_informe.informe_version` fija la versión entregada. Nuevas versiones del informe no modifican entregas previas.

## APIs

- `POST /api/comunicaciones/informes/{id}/entregar`
- `POST /api/resultados/informes/{id}/entregar` (puente)
- `GET /api/comunicaciones/informes/entregas`

## Contratos preparados (sin integrar aún)

Centro de Negocios (rama B): propuesta lista, presentada, contratación — vía event bus.
