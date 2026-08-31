# 01 — Arquitectura y reutilización

## Rama y base

| Campo | Valor |
|-------|-------|
| Base Motor Económico | `1c74dc7602b09257a162f487d3a2b7423b3c068f` |
| BP1 certificado | `7e9abba11f4c4f216142c6c70d662229ffc585bb` |
| Rama | `cursor/centro-negocios-eiaax-3581` |
| Alembic head | `1710a1b2c3d4e` |

## Principio

El Centro de Negocios **extiende** capacidades existentes. No crea motores paralelos de oportunidades, comercial ni economía.

## Capacidades reutilizadas

| Bloque | Uso |
|--------|-----|
| **1280** `commercial_service` | `CommercialProposal`, estados, valores, costos, `approve_proposal`, `set_final_price`, `import_from_valuation` |
| **1030** `proactive_service` | `Opportunity`, `transition_state` al presentar propuesta |
| **1210** `valuation_models` | Importación de valoración a propuesta |
| **1405** `evaluacion_models` | `EvaluacionExpediente`, links a oportunidades |
| **1600** `economic_motor_service` | `recommend_price` (BORRADOR), `sum_values_by_nature`, economía privada |
| **1340** `implementacion_service` | `create_proyecto` desde propuesta contratada |
| **Auditoría** | `write_audit` en cada transición relevante |
| **RBAC** | `permissions.py` + `control_center_service.resolve_organization_id` |

## Capacidades nuevas (extensión 1700)

- `negocio_proposal_extensions` — perspectivas, origen, IA, documento cliente/interno
- `negocio_proposal_versions` — snapshots inmutables
- `negocio_negotiation_entries` — negociación ligera
- `negocio_price_decisions` — decisión humana sobre precio recomendado
- `negocio_service` — orquestación del ciclo comercial
- API `/api/centro-negocios/*`
- `negocio_approval_adapter` — frontera `ApprovalPort` (reemplazable por Gobierno Operacional)
- `negocio_pdf_service` — PDF formal versionado
- `negocio_sync_service` — sincronización oportunidad ↔ negocio
- Vista detalle `/centro-negocios/propuestas/{id}`

## Diagrama de flujo

```
Evaluación (1405) ──┐
Oportunidad (1030) ─┼──► Propuesta (1280) + Extensión (1700)
Valoración (1210) ──┘         │
                              ├── Motor Económico (1600) → precio BORRADOR
                              ├── Perspectivas (GER/OPS/TI)
                              ├── Versión inmutable al presentar
                              ├── Negociación
                              └── Contratada → Implementación (1340)
```
