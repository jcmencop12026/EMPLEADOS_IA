# 04 — Entregables formales

## Modelo

`ImplementacionEntregable` (`impl_entregables`):

- nombre, descripción, responsable_id
- fecha_objetivo, estado
- evidencia, documento_id (infraestructura documental CN existente)
- aceptacion (PENDIENTE/ACEPTADO/RECHAZADO)
- observaciones, version_referencia

## API

```
GET  /api/implementacion/proyectos/{proyecto_id}/entregables
POST /api/implementacion/proyectos/{proyecto_id}/entregables
PATCH /api/implementacion/entregables/{entregable_id}
```

## UI

Pestaña **Entregables** en `ImplementacionDetailPage`.

## Brecha cerrada

**B05** — Objeto formal de entregable vinculado al proyecto, sin gestor documental paralelo.
