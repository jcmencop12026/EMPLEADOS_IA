# 04 — Gobierno y aprobaciones

## Autoridad canónica

**Gobierno Operacional** (`gobierno_operacional_service`) es la autoridad transversal de políticas y aprobaciones.

## Flujo consolidado

```
acción / intención (BP2)
  → evaluacion_integracion_gobierno.evaluar_politica_aprobacion
  → gobierno_operacional_service.evaluar_accion
  → (si requiere) crear_solicitud → decisión humana → ejecución / continuación
```

## Integración BP2

| Punto | Comportamiento |
|-------|----------------|
| `evaluacion_integracion_gobierno.py` | `INTEGRACION_GOBIERNO_DISPONIBLE = True`; delega con db + organization_id |
| `evaluacion_accion_service.py` | Política al crear acciones externas |
| `evaluacion_siguiente_accion_service.py` | Pasa contexto org a evaluación de política |
| `evaluacion_service.set_visibilidad` | Integra visibilidad generalizada de gobierno |

## Modelo de acciones

- LECTURA, ANÁLISIS, PROPUESTA, EJECUCIÓN
- Políticas por tipo, recurso, criticidad, capacidad externa
- Solicitudes con `correlation_id` para trazabilidad con expediente

## Compatibilidad ApprovalRequest

- Se preserva el flujo existente de aprobaciones del orquestador (`ApprovalRequest`).
- Gobierno no reemplaza el sistema legacy; lo complementa para acciones operacionales BP2.
- Un solo criterio de necesidad de aprobación vía política gobierno cuando el contexto está disponible.

## API principal

- `POST /api/gobierno-operacional/acciones/evaluar`
- `GET/POST /api/gobierno-operacional/solicitudes`
- `POST /api/gobierno-operacional/solicitudes/{id}/decidir`
- `GET /api/gobierno-operacional/confianza`

## Permisos RBAC

- `gobierno.view`, `gobierno.manage`, `gobierno.execute`, `gobierno.approve`
- `gobierno.visibility`, `gobierno.ia_policy`, `gobierno.audit`
- `gobierno.confianza.view` — Centro de Confianza

## Centro de Confianza

- Superficie con controles y evidencia real (aislamiento, RBAC, auditoría, etc.)
- Sin certificaciones ficticias
- UI: `/centro-confianza`
