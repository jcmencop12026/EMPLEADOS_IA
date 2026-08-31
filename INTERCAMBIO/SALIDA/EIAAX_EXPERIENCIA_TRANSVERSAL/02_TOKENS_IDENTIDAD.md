# 02 — Tokens e identidad

## Identidad central

```typescript
// frontend/src/lib/brand.ts
EIAAX_BRAND = {
  name: "EIAAX",
  descriptor: "Ecosistema Inteligente de Procesos Empresariales",
  productLine: "EMPLEADOS IA",
  ...
}
```

## Niveles de marca

| Nivel | assetId | Uso actual |
|-------|---------|------------|
| `hero` | `eiaax-hero` | Login (texto; listo para imagen) |
| `corporativo` | `eiaax-corporativo` | Sidebar expandido |
| `ex08` | `ex-08` | Sidebar colapsado |
| `micro` | `ex-micro` | Espacios mínimos / favicon futuro |

## Activos oficiales

**Carpeta:** `frontend/public/assets/identity/`  
**README:** convención de nombres por identificador.

Mecanismo: `resolveIdentityAsset(id)` prueba `.svg`, `.png`, `.webp` sin hardcodear rutas por pantalla.

## Tokens semánticos CSS

Variables en `:root` y `[data-theme="dark"]`:

| Token | Uso |
|-------|-----|
| `--color-bg` | Fondo página |
| `--color-surface` | Paneles, cards |
| `--color-text` / `--color-text-muted` | Texto |
| `--color-primary` | Acciones primarias |
| `--color-success-*` | Éxito |
| `--color-warning-*` | Advertencia |
| `--color-critical-*` | Error / crítico |
| `--color-info-*` | Información |

Semántica preservada; adopción incremental en componentes nuevos y shell.

## No incluido (por alcance)

- Editor avanzado de branding
- White-label completo
- Logo inventado
