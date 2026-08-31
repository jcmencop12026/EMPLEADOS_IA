# 03 — Propuesta inteligente y PDF formal

## PDF profesional

- Generación vía `negocio_pdf_service.py` (PDF estándar en español)
- Endpoint: `POST /api/centro-negocios/propuestas/{id}/pdf`
- Descarga: `GET /api/centro-negocios/documentos/{document_id}/pdf`

## Contenido del PDF (solo cliente)

Incluye: identidad, organización, prospecto, resumen, situación, oportunidad, solución, alcance, perspectivas Gerencia/Operaciones/Sistemas, inversión autorizada, modalidad, consumo IA, supuestos, próximos pasos.

**Excluye:** margen, costo interno, precio sugerido no aprobado, economía privada.

## Versionamiento documental

Cada presentación (`ENVIADA`) genera:

1. `NegocioProposalVersion` inmutable
2. `NegocioProposalDocument` con PDF vinculado (`pdf_document_id`)
3. Metadatos: `presented_by_id`, `precio_presentado`, `approved_by_id`

Modificaciones posteriores **no alteran** versiones ya presentadas.

## Tres perspectivas — un objeto

Persistidas en `perspectivas_json` y reflejadas en PDF.
