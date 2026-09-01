# 05 — Autonomía y gobierno operacional

## Niveles de autonomía

| Nivel | Comportamiento |
|-------|----------------|
| `ASISTIDO` | Requiere intervención humana frecuente; riesgo alto |
| `SUPERVISADO` | Ejecuta con revisión en excepciones (default) |
| `AUTONOMO_LIMITADO` | Autonomía dentro de límites y políticas |

Inferencia automática desde requerimiento Arquitecto según `supervision` y `riesgo`.

La autonomía **no elimina**: RBAC, políticas, aprobaciones, límites, auditoría.

## Clasificación de operaciones

`OPERATION_CLASSES`: `LECTURA`, `ANALISIS`, `PROPUESTA`, `EJECUCION`.

Cada `EmployeeBusinessCapability` declara su `operation_class`.

## Frontera Gobierno Operacional (rama A)

Endpoint: `GET /api/agent-factory/gobierno-operacional/boundary`

```json
{
  "estado": "FRONTERA_PREPARADA",
  "clasificacion_operaciones": ["LECTURA", "ANALISIS", "PROPUESTA", "EJECUCION"],
  "aprobaciones_actuales": "EmployeeFactoryApproval + ApprovalRequest (existente)",
  "integracion_pendiente": "GENERAL — Gobierno Operacional"
}
```

**No** se construyó motor de aprobaciones paralelo. Se reutiliza `EmployeeFactoryApproval` y `ApprovalRequest` existentes.

## Contrato para GENERAL

Al integrar Gobierno Operacional:

1. Mapear `operation_class` → política de aprobación transversal
2. Sustituir/adaptar `requires_approval()` para delegar en motor A
3. Conservar auditoría en `write_audit`
