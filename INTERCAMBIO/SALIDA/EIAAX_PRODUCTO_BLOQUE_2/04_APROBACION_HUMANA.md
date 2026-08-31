# 04 — Aprobación humana

## Matriz tipo de acción

| Tipo | Modifica sistemas externos | Aprobación por defecto |
|------|---------------------------|------------------------|
| LECTURA | No | No |
| ANÁLISIS | No | No |
| PROPUESTA | Potencial | Sí |
| EJECUCIÓN | Sí | Sí |

Implementación: `TIPO_REQUIERE_APROBACION` en `piiax_bridge_service.py`.

## Estados de acción

`BORRADOR` → `PENDIENTE_APROBACION` → `APROBADA` / `RECHAZADA` → `SOLICITADA` / `PIIAX_NO_DISPONIBLE` → `EN_PROCESO` → `COMPLETADA` / `ERROR`

## API

- `POST .../acciones/solicitar` — permiso `evaluacion.accion.request`
- `POST .../acciones/{id}/aprobar` — permiso `evaluacion.accion.approve`  
  Body: `{ "aprobado": true|false, "motivo": "..." }`

EIAAX controla la decisión de negocio. PIIAX conservará límites técnicos propios cuando esté conectado.

## Intención F (agente)

El panel «Preguntar a EIAAX» puede clasificar intención **F** (requiere aprobación) sin ejecutar automáticamente ninguna acción externa.
