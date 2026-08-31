# 06 — Visibilidad y privacidad

## Verificación previa al envío

`validate_delivery_privacy()`:

- Informe `INTERNO` → no destinatarios externos como visible entidad
- Contenido restringido → solo canal interno
- Destinatario debe pertenecer al tenant

## Sanitización

- `sanitize_comm_text()` — omite credenciales en texto visible
- `_sanitize_narrativa_para_entidad()` — elimina secciones internas al compartir

## Integración futura

Punto de extensión para clasificación Gobierno de Datos (rama A) — sin duplicar motor.
