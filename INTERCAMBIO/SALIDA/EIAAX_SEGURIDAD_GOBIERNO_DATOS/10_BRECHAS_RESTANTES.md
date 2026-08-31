# 10 — Brechas restantes (P0/P1/P2)

## P0

Ninguno identificado en esta entrega.

## P1 — Reservado integración BP2 (NO abordado aisladamente)

| ID | Descripción |
|----|-------------|
| P1-INT-01 | Integración `coordinator.decide_approval` con solicitudes gobierno |
| P1-INT-02 | Catálogo cerrado proveedores IA (`catalogo_proveedores_ref`) |
| P1-INT-03 | Enforcement `gobierno_ia_policies` en `llm_execution.py` runtime |

## P2 — Mejoras incrementales

| ID | Descripción |
|----|-------------|
| P2-01 | Auto-registro knowledge docs en `gov_catalog_entries` |
| P2-02 | Federación `security_events` + `gov_access_logs` en UI única |
| P2-03 | Visibilidad automática en dominios indicador/informe/plan |
| P2-04 | ABAC por clasificación en APIs generales |
| P2-05 | Notificación voz Centro de Confianza (no bloqueante) |

## Migración

`1420a1b2c3d4e` — tablas `empresa_objeto_clasificacion`, `empresa_evidencia_vinculo`; columnas en `gobierno_visibilidad_log` y `gobierno_ia_policies`.

## Componentes nuevos

- `empresa_seguridad_models.py`
- `empresa_audit_labels.py`
- `services/empresa_seguridad_service.py`
- `schemas_empresa_seguridad.py`
- `routers/empresa_seguridad.py`
- `tests/test_empresa_seguridad_gobierno_datos.py`

## Componentes modificados

- `gobierno_operacional_models.py` — visibilidad + IA
- `gobierno_operacional_service.py` — visibilidad enriquecida
- `routers/audit.py` — filtros + español
- `permissions.py` — 6 permisos nuevos
- `CentroConfianzaPage.tsx`, `AuditPage.tsx`
- `api.ts`, `labels.ts`
