# 10 — Escrituras y persistencia dossier

## Principio

Lectura: `get_dossier_completo(create=False)` — no crea filas.

Escritura: `get_or_create_dossier` vía servicios canónicos — un dossier por organización (`uq_dossier_org`).

## Endpoints POST

| Ruta | Delega a | Permiso dominio |
|------|----------|-----------------|
| `/acciones/registrar-necesidad` | `transformacion_service.registrar_necesidad` | `transformacion.manage` |
| `/acciones/preparar-publicacion` | `evaluacion_service.set_visibilidad` | `evaluacion.visibility` |
| `/acciones/actualizar-supuesto` | `evaluacion_service.update_informacion_item` | `evaluacion.manage` |
| `/acciones/priorizar-oportunidades` | `proactive_service.prioritize_opportunities_global` | `oportunidades.evaluate` |
| `/acciones/registrar-decision` | `proactive_service.approve_opportunity` | `oportunidades.approve` |

## Trazabilidad

Cada acción registra `AuditLog` con acción `strategic_control.{accion}`:

- empresa, dossier_id, correlation_id, expediente_id
- objeto_tipo, objeto_id
- valor_anterior, valor_nuevo, motivo

Publicación efectiva: autoridad `evaluacion.visibility` (no paralela).

## Sin StrategicDossier

No hay tablas ni modelos nuevos. Dossier duplicado: **0** (verificado en tests).
