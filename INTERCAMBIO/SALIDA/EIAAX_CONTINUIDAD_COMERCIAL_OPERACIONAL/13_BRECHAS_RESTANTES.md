# 13 — Brechas restantes y convergencia GENERAL

## Cerradas en esta misión

| ID | Descripción |
|----|-------------|
| B01 | Conversión con compromiso contractual |
| B02-B04 | Referencias + sub-entidades implementación |
| B05 | Entregables formales |
| B06 | FinOps desde contrato |
| B07-B08 | Renovación/expansión → oportunidad |
| B09 | Vista compromiso→resultado |
| B10 | Cambios de alcance |
| B13 | UI dual (banner + tabs continuidad) |
| B16 | Offboarding contractual mínimo |

## Pendiente GENERAL (no bloqueante)

| ID | Motivo |
|----|--------|
| B11 | Provisión automática empleados IA desde `ia_consumo_json` |
| B12 | Unificación soporte/incidentes post go-live |
| B14 | Sustituir `LocalNegocioApprovalAdapter` por Gobierno Operacional |
| B15 | Knowledge en Centro de Control |
| B17 | Offboarding organización (vs contractual) |
| B18 | Facturación SaaS completa |

## Adaptadores preparados

- `ApprovalPort` — frontera aprobaciones
- `LocalResultadoContinuidadAdapter` — frontera Inteligencia de Resultados

## Priorización entrega

- **P0:** B01, B06, B09, RBAC — cerrados
- **P1:** B05, B10, B16, entregables — cerrados
- **P2:** B07-B08 renovación UI, B13 UX — cerrados

## Integración

Rama `cursor/continuidad-comercial-operacional-3581` → base `cursor/centro-negocios-eiaax-3581`.

**NO merge** — GENERAL integrará posteriormente.
