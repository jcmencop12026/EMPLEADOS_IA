# 10 — Puente Arquitecto → Fábrica

## Flujo cerrado

```
Diagnóstico (DossierEmpresarial)
  → Oportunidad / Alternativa / Iniciativa
  → EmpleadoIARequerimiento (estado=PENDIENTE)
  → POST /api/agent-factory/employees/from-requerimiento/{id}
  → AIEmployee (source_type=ARQUITECTO, lifecycle=DRAFT)
  → Requerimiento (estado=CONSUMIDO, employee_id)
```

## API

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/transformacion/requerimientos-empleado-ia` | Lista pendientes |
| POST | `/api/agent-factory/employees/from-requerimiento/{id}` | Crea borrador prellenado |

## Trazabilidad conservada

- `dossier_id` en empleado
- `requerimiento_id` bidireccional
- `source_ref` = id requerimiento
- `trazabilidad` en respuesta: origen, dossier_id, alternativa_id, iniciativa_id

## Sin duplicar dossier

El servicio **consume** datos del requerimiento existente:

- objetivo → name, objective, instructions
- responsabilidad → role
- entradas/salidas → context_notes JSON
- herramientas → EmployeeBusinessCapability
- riesgo/supervisión → risk_level, autonomy_level

Reutilización idempotente: si requerimiento ya CONSUMIDO, devuelve empleado existente.

## diagnostic_id → findings

Pendiente de convergencia con otras ramas. Contrato para GENERAL:

```json
{
  "dossier_id": "uuid",
  "requerimiento_id": "uuid",
  "employee_id": "uuid",
  "correlation_id": "opcional"
}
```

Resolver en integración acumulada sin motor paralelo de findings.
