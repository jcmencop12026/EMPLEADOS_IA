# 03 — Implementación 1340 (evolución, no reconstrucción)

## Principio

No se creó un módulo Implementación nuevo. Se completaron brechas sobre el módulo existente.

## APIs sub-entidades añadidas/completadas

| Recurso | Método | Ruta |
|---------|--------|------|
| Completar tarea | POST | `/api/implementacion/tareas/{tarea_id}/completar` |
| Completar requisito | POST | `/api/implementacion/requisitos/{requisito_id}/completar` |
| Resolver bloqueador | POST | `/api/implementacion/bloqueadores/{bloqueador_id}/resolver` |
| Entregables CRUD | GET/POST/PATCH | `/api/implementacion/proyectos/{id}/entregables`, `/entregables/{id}` |
| Renovación | POST | `/api/implementacion/exito/renovaciones` |
| Expansión | POST | `/api/implementacion/exito/expansiones` |

## Servicio ampliado

`implementacion_service.py`:

- `completar_tarea`, `completar_requisito`, `resolver_bloqueador`
- CRUD `ImplementacionEntregable`
- Validación dependencias en `completar_hito`
- `proyecto_to_dict` con referencias contractuales y compromiso

## Brechas cerradas

- **B02** — Referencias canónicas en proyecto
- **B03** — Compromiso en conversión
- **B04** — APIs faltantes de sub-entidades
