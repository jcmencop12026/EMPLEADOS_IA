# 05 — Versionamiento, negociación y aprobaciones

## Aprobación multinivel (frontera reemplazable)

`negocio_approval_adapter.py` implementa `ApprovalPort`:

- `LocalNegocioApprovalAdapter` — provisional hasta Gobierno Operacional (Agente A)
- Niveles: PREPARADOR, REVISOR, APROBADOR_COMERCIAL, AUTORIZADOR_FINAL
- Política por organización: `PUT /api/centro-negocios/politica-aprobacion`
- Default: REVISOR + APROBADOR_COMERCIAL

## Regla de publicación (backend)

`ENVIADA` rechazada con **422** si:

- Faltan aprobaciones de la política vigente
- No hay `precio_final` aprobado

Intento rechazado auditado: `negocio.presentacion.rechazada`

## Negociación reforzada

Flujo: presentada → observaciones → `crear_nueva_version` → BORRADOR → re-aprobaciones → nueva presentación.

Versiones anteriores y PDFs preservados.

## Fases de precio

`negocio_price_phase_records`:

| Fase | Momento |
|------|---------|
| RECOMENDADO | Motor económico (borrador) |
| APROBADO | Decisión humana |
| PRESENTADO | Al presentar al cliente |
| CONTRATADO | Al contratar |
