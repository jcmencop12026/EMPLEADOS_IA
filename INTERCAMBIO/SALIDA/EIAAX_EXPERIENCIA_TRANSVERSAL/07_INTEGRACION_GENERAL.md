# 07 — Integración GENERAL

## Principio

Esta rama **no se mergea** a la rama central. GENERAL integrará posteriormente.

## Archivos de alto contacto

Si GENERAL modifica simultáneamente:

| Archivo | Recomendación |
|---------|---------------|
| `AppShell.tsx` | Fusionar: preservar C2 org context + adoptar BrandMark/ThemeToggle |
| `styles.css` | Fusionar tokens al inicio; evitar duplicar bloques EIAAX |
| `EvaluacionesPage.tsx` | Priorizar EiaaxTable + labels si GENERAL toca BP1 |
| `EvaluacionConsolePage.tsx` | Priorizar VistaEntidadPreview sobre JSON |

## Archivos nuevos (bajo conflicto)

```
frontend/src/lib/brand.ts (extendido)
frontend/src/lib/identityAssets.ts
frontend/src/lib/evaluacionLabels.ts
frontend/src/lib/evaluacionHelp.ts
frontend/src/hooks/useTheme.tsx
frontend/src/components/EiaaxTable.tsx
frontend/src/components/ContextualHelp.tsx
frontend/src/components/ThemeToggle.tsx
frontend/src/components/identity/BrandMark.tsx
frontend/src/components/evaluacion/VistaEntidadPreview.tsx
frontend/public/assets/identity/README.md
frontend/vitest.config.ts
frontend/src/lib/*.test.ts
```

## Dependencias añadidas

- `vitest`, `jsdom`, `@testing-library/react` (dev)

## No competir con BP2

- Sin cambios en lógica backend evaluación
- Sin PIIAX / Partners
- Sin reconstrucción de funcionalidades existentes
