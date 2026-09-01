# 09 — Brechas P0 / P1 / P2 (pendientes reales)

## Cerrado en continuación V1

| Brecha material | Estado |
|-----------------|--------|
| Economía privada completa (margen/precio/ROI) | **CERRADO** |
| Persistencia dossier en flujos escritura | **CERRADO** |
| ContinuidadAdapter degradados lista | **CERRADO** + test regresión |
| Privacidad economía backend | **CERRADO** + tests |

## P0 — defectos/bloqueantes reales pendientes

| ID | Pendiente |
|----|-----------|
| P0-1 | Reconciliación migraciones 1410/1420 (heredado plataforma, no específico estratégico) |

## P1 — mejoras no bloqueantes

| ID | Pendiente |
|----|-----------|
| P1-1 | Exportación gráficos CSV/PNG |
| P1-2 | Drill-down temporal y agrupación avanzada |
| P1-3 | UI modo comité side-by-side |
| P1-4 | Selector organización SuperAdmin en UI estratégica |
| P1-5 | Escritura directa escenarios transformación (hoy vía `diagnosticar`) |

## P2 — post-V1

| ID | Pendiente |
|----|-----------|
| P2-1 | Voz accesibilidad (`speechSynthesis`) |
| P2-2 | Notificación in-app al publicar dossier |
| P2-3 | Persistencia lectura activa por usuario |

## Riesgos integración (documentados)

| Riesgo | Mitigación |
|--------|------------|
| Rama independiente vs convergencia GENERAL | Adapter fail-closed publicación |
| Confusión MB-08 / estratégico | Rutas separadas + tests |
| Permisos no sembrados en tenants legacy | Seed admin incluye `STRATEGIC_CONTROL_PERMISSIONS` |
