# 08 — Renovación / expansión (B07-B08)

## Evolución sobre éxito del cliente

Columnas añadidas en `ExitoClienteRenovacion` y `ExitoClienteExpansion`:

- `opportunity_id` — vínculo a oportunidad 1030 sin duplicar

## API extendida

```
POST /api/implementacion/exito/renovaciones
  body: { proyecto_id, crear_oportunidad, titulo_oportunidad, ... }

POST /api/implementacion/exito/expansiones
  body: { proyecto_id, tipo, descripcion, crear_oportunidad, ... }
```

`implementacion_service.create_renovacion` / `create_expansion` delegan en `continuidad_comercial_service.crear_oportunidad_desde_renovacion`.

## Flujo

Operación/resultado → registro renovación/expansión → (opcional) oportunidad 1030 → Centro de Negocios.

## UI

Pestaña **Renovación** en detalle de implementación.

## Brechas cerradas

**B07** — Renovación próxima detectable/registrable  
**B08** — Ampliación vinculada a oportunidad existente
