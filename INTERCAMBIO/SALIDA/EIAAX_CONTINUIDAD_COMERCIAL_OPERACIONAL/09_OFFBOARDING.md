# 09 — Cierre / offboarding (B16)

## Modelo mínimo

`NegocioContractClosure` (`negocio_contract_closures`):

- motivo, fecha_cierre, estado
- pendientes, empleados_retirar, accesos_retirar, exportaciones (JSON)
- confirmacion, observaciones
- referencias contract_id, proposal_id, proyecto_id

## API

```
POST /api/continuidad-comercial/contratos/{contract_id}/cierre
POST /api/continuidad-comercial/cierres/{closure_id}/confirmar
```

## Principios

- No borra trazabilidad histórica
- No plataforma separada de offboarding
- Permiso `continuidad_comercial.close`

## UI

Sección cierre en pestaña Continuidad del Centro de Negocios.

## Brecha cerrada

**B16** — Cierre contractual empresarial mínimo.
