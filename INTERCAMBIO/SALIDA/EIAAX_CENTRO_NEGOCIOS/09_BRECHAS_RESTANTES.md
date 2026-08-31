# 09 — Brechas restantes (post-cierre integral)

## P0 — CERRADOS

| Brecha anterior | Estado |
|-----------------|--------|
| Export PDF formal | ✅ `negocio_pdf_service` + documento versionado |
| Aprobación multi-nivel | ✅ Adaptador `ApprovalPort` + política configurable |

## P1 — CERRADOS

| Brecha anterior | Estado |
|-----------------|--------|
| Vista detalle Centro de Negocios | ✅ `/centro-negocios/propuestas/{id}` |
| Sync oportunidad ↔ negocio | ✅ `negocio_sync_service` + log |

## P1 — Pendiente integración externa

| Brecha | Dependencia |
|--------|-------------|
| Reemplazar `LocalNegocioApprovalAdapter` por Gobierno Operacional transversal | Rama Agente A — contrato `ApprovalPort` documentado |

## P2 — Futuro

- Plantillas PDF sectoriales con diseño gráfico avanzado (reportlab/weasyprint)
- Portal cliente para firma electrónica
- Integración Sistema Transversal de Experiencia (GENERAL)

## No hecho (por diseño)

PIIAX, Partners, CRM completo, implementación completa, merge central.
