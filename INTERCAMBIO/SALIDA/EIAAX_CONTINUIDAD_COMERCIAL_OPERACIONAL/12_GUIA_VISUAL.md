# 12 — Guía visual (UX B13-B14)

## Navegación natural

```
Centro de Negocios → Propuesta → [Continuidad]
                ↓ Contratar e implementar
Implementación → [Entregables | Renovación | Continuidad]
```

## Cambios UI

### Centro de Negocios (`CentroNegociosDetailPage`)

- Pestaña **Continuidad**: cadena valor, referencias, cambios alcance, cierre
- Botón **Ver implementación** cuando existe proyecto
- Enlace desde resumen a expediente CN

### Implementación (`ImplementacionDetailPage`)

- Pestañas **Entregables**, **Renovación**, **Continuidad**
- Enlace a Centro de Negocios (no vista comercial duplicada)

### Comercial (`ComercialPropuestaDetailPage`)

- Banner: gestión autoritativa en Centro de Negocios (B13 redirect)

## Componente compartido

`frontend/src/components/continuidad/ContinuidadVistaPanel.tsx`

## Idioma

Todas las etiquetas en español.

## Brecha cerrada

**B13** — Superficie dual comercial/CN resuelta con banner y enlaces naturales.

**B14** — Parcial; aprobaciones siguen en CN hasta Gobierno Operacional (GENERAL).
