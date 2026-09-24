# 05 — Seguridad y visibilidad

## Permisos nuevos

| Código | Descripción |
|--------|-------------|
| `evaluacion.view` | Consultar expedientes |
| `evaluacion.manage` | Crear/editar expedientes e información |
| `evaluacion.evaluate` | Ejecutar evaluación y hallazgos |
| `evaluacion.visibility` | Cambiar visibilidad para entidad |
| `evaluacion.vista_entidad` | Ver previsualización vista entidad |

Asignados a roles `admin`, `superadmin`, `operator` (fallback seed).

## Visibilidad backend (no solo UI)

- Campo `visible_entidad` en `evaluaciones_hallazgos`.
- Endpoint `GET /vista-entidad` filtra en servidor:
  - Solo hallazgos con `visible_entidad=true`
  - Sin `notas_internas`, sin `valor_potencial` interno
  - Oportunidades solo si hallazgo vinculado visible
- Tabla `evaluaciones_visibilidad_log`: `changed_by`, `created_at`, `objeto_id`, `visible_entidad`.

## Multitenant

Todas las consultas filtran por `organization_id`. Acceso cross-tenant → 404.

## RBAC

Deny by default. Usuario `viewer` sin `evaluacion.view` → 403 en listado.
