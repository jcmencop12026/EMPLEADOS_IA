# 06 — Aprobaciones y capacidades externas

## Aprobaciones

Bloque `aprobaciones` unifica:

| Origen | Modelo |
|--------|--------|
| Operaciones | `ApprovalRequest` |
| Fábrica | `EmployeeFactoryApproval` |

Campos: acción, desde cuándo, contexto, impacto, enlace.

`gobierno_operacional: FRONTERA_PREPARADA` — sin motor paralelo.

## Capacidades externas

Bloque `capacidades_externas` desde `EmployeeBusinessCapability`:

Estados canónicos: DISPONIBLE, NO_DISPONIBLE, EN_COLA, ESPERANDO_APROBACION, EN_EJECUCION, FALLIDA.

`piiax_conectado: false` — EIAAX opera sin PIIAX. GENERAL integrará resolución real.
