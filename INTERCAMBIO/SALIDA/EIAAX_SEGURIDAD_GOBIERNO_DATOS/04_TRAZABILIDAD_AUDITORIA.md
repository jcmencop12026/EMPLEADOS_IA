# 04 — Trazabilidad y auditoría consultable

## Trazabilidad empresarial

Vista lógica por `correlation_id`:

```
organización → solicitud → aprobación → evento → evidencia → visibilidad
```

API: `GET /api/empresa-seguridad/trazabilidad/{correlation_id}`

No duplica logs técnicos completos — agrega referencias cruzadas.

## Auditoría federada en español

`GET /api/empresa-seguridad/auditoria/consulta`

Fuentes federadas:
- `audit_logs` (global)
- `gobierno_eventos`

Campos en español: `accion_etiqueta`, `usuario`, `detalle` sanitizado.

## Auditoría legacy mejorada

`GET /api/audit/logs` — filtros `accion`, `user_id`, `desde`, `hasta` + `accion_etiqueta`.

## Etiquetas

`backend/app/empresa_audit_labels.py` — mapa extensible de acciones a español.
