# 06 — Comunicaciones y evidencias

## MB-11 integrado
Eventos publicados al bus desde `support_service._publish_comm_event`:
- `SUPPORT_CASE_ASSIGNED`
- `SUPPORT_CASE_STATUS`
- `SUPPORT_CASE_RESOLVED`
- `SUPPORT_CASE_COMMENT`
- `SUPPORT_SLA_WARNING`
- `SUPPORT_CASE_ESCALATED`

Plantillas seed en `bootstrap_default_comm_assets`:
- `SOPORTE_CASO_ASIGNADO`
- `SOPORTE_SLA_ALERTA`
- `SOPORTE_CASO_RESUELTO`

Reglas MB-11 pueden configurarse por organización; destinatarios dinámicos `SOLICITANTE`, `RESPONSABLE_CASO`.

## Evidencias
Tabla `support_case_evidences` — solo referencias, sin copiar blobs.

Tipos: `LOG`, `CAPTURA`, `DOCUMENTO`, `ERROR`, `EVENTO`, `EJECUCION`, `OBJETO_EIAAX`, `OTRO`.

API: `POST /api/soporte/casos/{id}/evidencias`

Historial en detalle del caso (pestaña Evidencias en UI).
