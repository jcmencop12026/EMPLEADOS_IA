# 11 — Guía visual UX

## Ruta

`/arquitecto-transformacion` — menú "Arquitecto de Transformación" (español).

## Pestañas progresivas

1. **Inicio** — estado dossier, recorrido, enlace expediente
2. **Necesidad** — formulario compacto (no interminable)
3. **Qué sabemos / qué falta** — suficiencia, conocimiento reutilizado, CTA expediente
4. **Qué encontramos** — causas con badges SINTOMA/PROBLEMA/CAUSA_PROBABLE
5. **Qué recomendamos** — tabla alternativas con score y recomendada
6. **Qué hacer ahora** — siguiente acción

## Convenciones

- Badges de estado y confianza
- Enlaces a expediente EIAAX para detalle
- Sin pantallas vacías — mensajes guía cuando falta datos
- Permisos: `transformacion.view|manage|execute`

## Integración experiencia transversal

No compite con MB experiencia — usa patrones `ops-page`, `compact-panel`, `tab-nav` existentes.
