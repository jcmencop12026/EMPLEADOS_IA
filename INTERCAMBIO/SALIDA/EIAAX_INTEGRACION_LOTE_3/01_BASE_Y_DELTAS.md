# Lote 3 — Base y deltas

## Base obligatoria

| Campo | Valor |
|-------|-------|
| Rama base | `cursor/integracion-lote-2-85e4` |
| SHA base | `c536f24` |
| Rama integración | `cursor/integracion-lote-3-85e4` |
| Alembic head Lote 2 | `1600a1b2c3d4e` |
| Alembic head Lote 3 | `1770a1b2c3d4e` |

## Descendientes integrados (selectivo)

| Cadena | SHA origen | Delta principal |
|--------|------------|-----------------|
| A — Seguridad/Gobierno datos | `c433bac` | Clasificación, visibilidad, auditoría consultable, Centro Confianza evolucionado |
| B — Centro Negocios + Continuidad | `f0f8cf5` | PDF, aprobaciones multinivel, contrato→implementación, entregables, FinOps, offboarding |
| C — Arquitecto/Fábrica/CC | `a877572` | Transformación, puente fábrica, MB-08 operacional evolucionado |
| D — Resultados/Comunicaciones/Soporte | `a104645` | ANTES/PROYECTADO/REAL, MB-11 entregas, MB-12 soporte evolucionado |

## Ya presente en c536f24 (no reintegrado)

- Gobierno Operacional (1411) — autoridad
- Partners (1412)
- Motor Económico (1600)
- BP1 evaluación, BP2 negocio base, Implementación 1340 canónica
- Experience System, sidebar, tema claro/oscuro

## Superposiciones resueltas

- **Aprobaciones negocio**: `GobiernoNegocioApprovalAdapter` → Gobierno Operacional; `LocalNegocioApprovalAdapter` conservado solo como implementación interna
- **coordinator.decide_approval**: espejo en Gobierno Operacional vía `_mirror_decision_to_gobierno`
- **Centro Control**: evolución MB-08, no segundo CC
- **Migraciones**: IDs históricos colisionados renumerados 1610–1770 sobre cadena 1600

## Deltas descartados

- Implementación completa Partners desde cadena C (ya en Lote 2)
- PIIAX / endpoints externos no certificados
- Segundos motores: FinOps, Gobierno, Resultados, Soporte, CC
- Cherry-pick ciego de ramas completas
