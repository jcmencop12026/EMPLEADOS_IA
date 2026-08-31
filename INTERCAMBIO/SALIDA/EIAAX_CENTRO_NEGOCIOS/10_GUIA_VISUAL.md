# 10 — Guía visual (actualizada)

## Rutas

| Ruta | Descripción |
|------|-------------|
| `/centro-negocios` | Dashboard + pipeline |
| `/centro-negocios/propuestas/{id}` | Detalle operativo con pestañas |

## Detalle — pestañas

1. **Resumen** — origen, oportunidad, responsable, próximo paso
2. **Economía** — fases de precio (recomendado → aprobado → presentado → contratado)
3. **Versiones** — historial inmutable + enlace PDF
4. **Aprobaciones** — niveles configurables, botón aprobar
5. **Negociación** — rondas y nueva versión
6. **Trazabilidad** — log sincronización oportunidad

## Etiquetas en español

Fuente única: `frontend/src/lib/negocioLabels.ts` y `backend/app/negocio_labels.py`

Estados visibles: Borrador, En revisión, Aprobada internamente, Presentada, Contratada, etc.

## Acciones principales

- **Generar PDF** — borrador o pre-presentación
- **Presentar** — solo con aprobaciones + precio aprobado
- **Sincronizar oportunidad** — bidireccional controlada
- **Contratar e implementar** — desde versión presentada

## Nota POTENCIAL

Visible en pie de página; no suma a inversión ni ROI realizado.
