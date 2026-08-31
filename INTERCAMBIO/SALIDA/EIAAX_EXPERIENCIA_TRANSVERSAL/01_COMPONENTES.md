# 01 — Componentes transversales

## BrandMark

**Ruta:** `frontend/src/components/identity/BrandMark.tsx`

| Prop | Tipo | Descripción |
|------|------|-------------|
| `level` | `hero \| corporativo \| ex08 \| micro` | Nivel de marca |
| `className` | string | Clase adicional |
| `title` | string | Tooltip accesible |

Resuelve activo gráfico vía `resolveIdentityAsset(assetId)`. Si no existe archivo en `/public/assets/identity/`, renderiza marca tipográfica (sin inventar logo).

## ThemeProvider / ThemeToggle

**Rutas:** `frontend/src/hooks/useTheme.tsx`, `frontend/src/components/ThemeToggle.tsx`

- Modos: `light`, `dark`, `system`
- Persistencia: `localStorage` clave `eiaax_theme_mode`
- Aplica `data-theme` en `<html>` para tokens CSS

## EiaaxTable

**Ruta:** `frontend/src/components/EiaaxTable.tsx`

Tabla genérica `<T>` con:

- Búsqueda integrada
- Orden ASC/DESC por columna
- Slot `filtersSlot` para filtros externos
- Paginación + registros por página
- Mostrar/ocultar columnas
- Redimensionar ancho de columnas (drag handle)
- Preferencias en `localStorage` cuando `prefsKey` está definido

## ContextualHelp

**Ruta:** `frontend/src/components/ContextualHelp.tsx`

Botón `? Ayuda` con panel estructurado:

- Qué hace la pantalla
- Qué necesita
- Pasos
- Ejemplo
- Resultado esperado
- Secciones adicionales opcionales

## VistaEntidadPreview

**Ruta:** `frontend/src/components/evaluacion/VistaEntidadPreview.tsx`

Sustituye JSON crudo en Vista Entidad por presentación legible en español.

## Labels BP1

**Ruta:** `frontend/src/lib/evaluacionLabels.ts` — traducción de códigos técnicos de evaluación.

## Help content BP1

**Ruta:** `frontend/src/lib/evaluacionHelp.ts` — textos de ayuda para superficies representativas.
