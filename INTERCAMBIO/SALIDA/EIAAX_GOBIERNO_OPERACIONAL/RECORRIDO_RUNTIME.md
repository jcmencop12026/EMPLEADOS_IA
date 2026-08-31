# Recorrido runtime — Gobierno Operacional EIAAX

## Precondiciones

- Backend en ejecución
- Usuario admin con permisos `gobierno.*`
- Migración `1410a1b2c3d4e` aplicada

## Paso 1 — Evaluar acción

```http
POST /api/gobierno-operacional/acciones/evaluar
Authorization: Bearer <token>
Content-Type: application/json

{
  "tipo_accion": "EJECUCION",
  "recurso_tipo": "integracion",
  "criticidad": "HIGH"
}
```

**Esperado:** `requiere_aprobacion_humana: true`

## Paso 2 — Crear solicitud

```http
POST /api/gobierno-operacional/solicitudes
Authorization: Bearer <token>

{
  "tipo_accion": "EJECUCION",
  "recurso_tipo": "integracion",
  "descripcion": "Ejecutar conector CRM",
  "motivo_solicitud": "Sincronización programada"
}
```

**Esperado:** `estado: PENDIENTE`, `correlation_id` presente

## Paso 3 — Aprobar (backend autoridad)

```http
POST /api/gobierno-operacional/solicitudes/{id}/decidir
Authorization: Bearer <token>

{
  "decision": "approve",
  "motivo": "Autorizado por responsable operaciones"
}
```

**Esperado:** `estado: EJECUTADA`, `aprobado_por` y `executed_at` poblados

## Paso 4 — Centro de Confianza

```http
GET /api/gobierno-operacional/confianza
Authorization: Bearer <token>
```

**Esperado:** controles `aislamiento`, `rbac`, `acciones_controladas`, `aprobaciones` con evidencia numérica

## Paso 5 — Visibilidad (dual-write BP1)

Desde evaluación existente:

```http
PATCH /api/evaluaciones/{expediente_id}/visibilidad
```

Verificar en:

```http
GET /api/gobierno-operacional/visibilidad?dominio=evaluacion
```

## Paso 6 — Cross-tenant (negativo)

Usuario org B intenta decidir solicitud org A → **404**

## Paso 7 — UI

Navegar a `/centro-confianza` — panel compacto con controles y solicitudes recientes.
