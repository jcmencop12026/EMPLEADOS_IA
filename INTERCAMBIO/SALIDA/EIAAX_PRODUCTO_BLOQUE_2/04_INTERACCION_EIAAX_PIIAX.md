# 04 — Interacción EIAAX ↔ PIIAX

## Regla arquitectónica

- EIAAX **no depende** obligatoriamente de PIIAX.
- PIIAX es proveedor **preferente** cuando está disponible.
- PIIAX funciona independientemente de EIAAX.
- **No** se construye PIIAX dentro de EIAAX.

## Adaptador desacoplado

**Módulo:** `evaluacion_proveedor_externo_service.py`

Interfaz `ProveedorExternoAdapter`:

- `disponible()`, `listar_capacidades()`
- `solicitar_ejecucion()`, `consultar_estado()`, `cancelar()`
- `trazabilidad_resumida()`, `detalle_tecnico_url()`

Implementación: `PiiaxAdapter` (stub). Registro extensible vía `registrar_adaptador()`.

**Puente legacy:** `piiax_bridge_service.py` delega en la capa de proveedores.

## APIs

- `GET /api/evaluaciones/integracion/piiax`
- `GET /api/evaluaciones/proveedores-externos`
- `GET /api/evaluaciones/capacidades`

## Sin simulación de éxito

Si PIIAX no conectado → `NO DISPONIBLE` / `PIIAX_NO_DISPONIBLE`. Nunca `COMPLETADO` sin resultado explícito.
