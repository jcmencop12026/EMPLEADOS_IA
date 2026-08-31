# 04 — Notificaciones y preferencias

## Dos sistemas complementarios

1. **820 Notificaciones** — alertas in-app (`/notificaciones`)
2. **MB-11 Comunicaciones** — mensajes gobernados con plantillas y entrega

## Preferencias (`CommPreference`)

- Canales permitidos
- Tipos silenciados (no críticos)
- Idioma
- API: `GET/PUT /api/comunicaciones/preferencias`
- UI: pestaña Preferencias en Centro de Información

## Regla obligatoria

`_preference_allows()` respeta flag `obligatoria` en reglas — alertas críticas no se silencian.
